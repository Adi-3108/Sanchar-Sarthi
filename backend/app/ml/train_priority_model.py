from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.ml.feature_pipeline import (
    PRIORITY_MODEL_NAME,
    PRIORITY_MODEL_PATH,
    PRIORITY_MODEL_VERSION,
    REPO_ROOT,
    build_priority_feature_row,
    build_session_factory,
    ensure_artifacts_root,
    list_event_feature_bundles,
    missing_optional_modules,
    normalize_priority_bucket,
    upsert_model_run,
)
from app.services.feature_engineering_service import rebuild_event_features

TARGET_VARIABLE = "priority_high"


def train() -> dict[str, object] | None:
    session_factory = build_session_factory()
    with session_factory() as session:
        rebuild_event_features(session, commit=False)
        bundles = list_event_feature_bundles(session)
        rows = []
        labels = []
        for bundle in bundles:
            if bundle.event.priority is None:
                continue
            rows.append(build_priority_feature_row(bundle.event, bundle.feature))
            labels.append(1 if normalize_priority_bucket(bundle.event.priority) == "high" else 0)

        available_rows = len(rows)
        positive_rows = sum(labels)
        positive_rate = round((positive_rows / available_rows), 4) if available_rows else 0.0
        artifact_path = str(PRIORITY_MODEL_PATH.relative_to(REPO_ROOT))

        if available_rows == 0 or len(set(labels)) < 2:
            metrics = {
                "status": "skipped_insufficient_label_diversity",
                "available_rows": available_rows,
                "positive_rows": positive_rows,
                "positive_rate": positive_rate,
            }
            upsert_model_run(
                session,
                model_name=PRIORITY_MODEL_NAME,
                model_version=PRIORITY_MODEL_VERSION,
                target_variable=TARGET_VARIABLE,
                training_rows=available_rows,
                test_rows=0,
                metrics_json=metrics,
                feature_list_json=list(rows[0].keys()) if rows else [],
                artifact_path=artifact_path,
            )
            print("[priority_model] Skipping training: need both High and Low priority examples.")
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
                model_name=PRIORITY_MODEL_NAME,
                model_version=PRIORITY_MODEL_VERSION,
                target_variable=TARGET_VARIABLE,
                training_rows=available_rows,
                test_rows=0,
                metrics_json=metrics,
                feature_list_json=list(rows[0].keys()),
                artifact_path=artifact_path,
            )
            print(
                "[priority_model] Skipping training: install optional ML dependencies "
                f"{', '.join(missing_modules)}."
            )
            return None

        import joblib  # type: ignore[import-not-found]
        import pandas as pd  # type: ignore[import-not-found]
        from sklearn.compose import ColumnTransformer  # type: ignore[import-not-found]
        from sklearn.ensemble import RandomForestClassifier  # type: ignore[import-not-found]
        from sklearn.metrics import f1_score, precision_score, recall_score  # type: ignore[import-not-found]
        from sklearn.model_selection import train_test_split  # type: ignore[import-not-found]
        from sklearn.pipeline import Pipeline  # type: ignore[import-not-found]
        from sklearn.preprocessing import OneHotEncoder, StandardScaler  # type: ignore[import-not-found]

        frame = pd.DataFrame(rows)
        target = pd.Series(labels)
        categorical = ["event_type", "event_cause_clean", "corridor", "police_station"]
        numeric = [
            "event_hour",
            "event_weekday",
            "historical_corridor_risk",
            "historical_police_station_risk",
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
                        n_estimators=200,
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
        metrics = {
            "status": "trained",
            "f1": round(float(f1_score(y_test, predictions, zero_division=0)), 4),
            "precision_high": round(float(precision_score(y_test, predictions, zero_division=0)), 4),
            "recall_high": round(float(recall_score(y_test, predictions, zero_division=0)), 4),
            "positive_rows": positive_rows,
            "positive_rate": positive_rate,
        }

        ensure_artifacts_root()
        joblib.dump(
            {
                "pipeline": pipeline,
                "metrics": metrics,
                "model_name": PRIORITY_MODEL_NAME,
                "model_version": PRIORITY_MODEL_VERSION,
                "features": list(frame.columns),
            },
            PRIORITY_MODEL_PATH,
        )
        upsert_model_run(
            session,
            model_name=PRIORITY_MODEL_NAME,
            model_version=PRIORITY_MODEL_VERSION,
            target_variable=TARGET_VARIABLE,
            training_rows=len(x_train),
            test_rows=len(x_test),
            metrics_json=metrics,
            feature_list_json=list(frame.columns),
            artifact_path=artifact_path,
        )
        print(
            "[priority_model] "
            f"F1={metrics['f1']:.4f} | Precision={metrics['precision_high']:.4f} "
            f"| Recall={metrics['recall_high']:.4f}"
        )
        return metrics


if __name__ == "__main__":
    result = train()
    print(result if result is not None else "Training skipped. Rule fallback remains active.")
