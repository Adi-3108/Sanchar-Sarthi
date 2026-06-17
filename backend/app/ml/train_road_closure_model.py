from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.ml.feature_pipeline import (
    REPO_ROOT,
    ROAD_CLOSURE_MODEL_NAME,
    ROAD_CLOSURE_MODEL_PATH,
    ROAD_CLOSURE_MODEL_VERSION,
    build_road_closure_feature_row,
    build_session_factory,
    ensure_artifacts_root,
    list_event_feature_bundles,
    missing_optional_modules,
    upsert_model_run,
)
from app.services.feature_engineering_service import rebuild_event_features

TARGET_VARIABLE = "requires_road_closure_true"


def train() -> dict[str, object] | None:
    session_factory = build_session_factory()
    with session_factory() as session:
        rebuild_event_features(session, commit=False)
        bundles = list_event_feature_bundles(session)
        rows = [build_road_closure_feature_row(bundle.event, bundle.feature) for bundle in bundles]
        labels = [1 if bundle.event.requires_road_closure else 0 for bundle in bundles]

        available_rows = len(rows)
        positive_rows = sum(labels)
        positive_rate = round((positive_rows / available_rows), 4) if available_rows else 0.0
        artifact_path = str(ROAD_CLOSURE_MODEL_PATH.relative_to(REPO_ROOT))

        if available_rows == 0 or len(set(labels)) < 2:
            metrics = {
                "status": "skipped_insufficient_label_diversity",
                "available_rows": available_rows,
                "positive_rows": positive_rows,
                "positive_rate": positive_rate,
            }
            upsert_model_run(
                session,
                model_name=ROAD_CLOSURE_MODEL_NAME,
                model_version=ROAD_CLOSURE_MODEL_VERSION,
                target_variable=TARGET_VARIABLE,
                training_rows=available_rows,
                test_rows=0,
                metrics_json=metrics,
                feature_list_json=list(rows[0].keys()) if rows else [],
                artifact_path=artifact_path,
            )
            print("[road_closure_model] Skipping training: need both TRUE and FALSE examples.")
            return None

        missing_modules = missing_optional_modules()
        if missing_modules:
            metrics = {
                "status": "skipped_missing_dependencies",
                "available_rows": available_rows,
                "positive_rows": positive_rows,
                "positive_rate": positive_rate,
                "missing_modules": missing_modules,
            }
            upsert_model_run(
                session,
                model_name=ROAD_CLOSURE_MODEL_NAME,
                model_version=ROAD_CLOSURE_MODEL_VERSION,
                target_variable=TARGET_VARIABLE,
                training_rows=available_rows,
                test_rows=0,
                metrics_json=metrics,
                feature_list_json=list(rows[0].keys()),
                artifact_path=artifact_path,
            )
            print(
                "[road_closure_model] Skipping training: install optional ML dependencies "
                f"{', '.join(missing_modules)}."
            )
            return None

        import joblib  # type: ignore[import-not-found]
        import pandas as pd  # type: ignore[import-not-found]
        from sklearn.compose import ColumnTransformer  # type: ignore[import-not-found]
        from sklearn.ensemble import RandomForestClassifier  # type: ignore[import-not-found]
        from sklearn.metrics import average_precision_score, f1_score, recall_score  # type: ignore[import-not-found]
        from sklearn.model_selection import train_test_split  # type: ignore[import-not-found]
        from sklearn.pipeline import Pipeline  # type: ignore[import-not-found]
        from sklearn.preprocessing import OneHotEncoder, StandardScaler  # type: ignore[import-not-found]

        frame = pd.DataFrame(rows)
        target = pd.Series(labels)
        categorical = ["event_type", "event_cause_clean", "corridor", "police_station", "priority"]
        numeric = [
            "event_hour",
            "event_weekday",
            "historical_corridor_risk",
            "historical_police_station_risk",
            "historical_cluster_risk",
            "historical_cause_closure_rate",
            "historical_corridor_closure_rate",
            "historical_police_station_closure_rate",
            "historical_cluster_closure_rate",
            "is_peak_hour",
        ]

        pipeline = Pipeline(
            [
                (
                    "features",
                    ColumnTransformer(
                        [
                            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
                            ("num", StandardScaler(), numeric),
                        ],
                        remainder="drop",
                    ),
                ),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=250,
                        class_weight="balanced",
                        random_state=42,
                    ),
                ),
            ]
        )
        x_train, x_test, y_train, y_test = train_test_split(
            frame,
            target,
            test_size=0.2,
            random_state=42,
            stratify=target,
        )
        pipeline.fit(x_train, y_train)
        predictions = pipeline.predict(x_test)
        probabilities = pipeline.predict_proba(x_test)[:, 1]
        metrics = {
            "status": "trained",
            "f1": round(float(f1_score(y_test, predictions, zero_division=0)), 4),
            "pr_auc": round(float(average_precision_score(y_test, probabilities)), 4),
            "recall_true": round(float(recall_score(y_test, predictions, zero_division=0)), 4),
            "positive_rows": positive_rows,
            "positive_rate": positive_rate,
        }

        ensure_artifacts_root()
        joblib.dump(
            {
                "pipeline": pipeline,
                "metrics": metrics,
                "model_name": ROAD_CLOSURE_MODEL_NAME,
                "model_version": ROAD_CLOSURE_MODEL_VERSION,
                "features": list(frame.columns),
            },
            ROAD_CLOSURE_MODEL_PATH,
        )
        upsert_model_run(
            session,
            model_name=ROAD_CLOSURE_MODEL_NAME,
            model_version=ROAD_CLOSURE_MODEL_VERSION,
            target_variable=TARGET_VARIABLE,
            training_rows=len(x_train),
            test_rows=len(x_test),
            metrics_json=metrics,
            feature_list_json=list(frame.columns),
            artifact_path=artifact_path,
        )
        print(
            "[road_closure_model] "
            f"PR-AUC={metrics['pr_auc']:.4f} | Recall_TRUE={metrics['recall_true']:.4f} "
            f"| Positive rate={metrics['positive_rate']:.4f}"
        )
        return metrics


if __name__ == "__main__":
    result = train()
    print(result if result is not None else "Training skipped. Rule-history scoring remains primary.")
