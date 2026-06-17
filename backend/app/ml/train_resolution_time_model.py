from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.ml.feature_pipeline import (
    DATA_FILTER_APPLIED,
    REPO_ROOT,
    RESOLUTION_TIME_MODEL_NAME,
    RESOLUTION_TIME_MODEL_PATH,
    RESOLUTION_TIME_MODEL_VERSION,
    build_resolution_time_feature_row,
    build_session_factory,
    ensure_artifacts_root,
    list_event_feature_bundles,
    missing_optional_modules,
    reliable_clearance_minutes,
    upsert_model_run,
)
from app.services.feature_engineering_service import rebuild_event_features

TARGET_VARIABLE = "estimated_clearance_minutes"
MIN_TRAINING_ROWS = 200


def train() -> dict[str, object] | None:
    session_factory = build_session_factory()
    with session_factory() as session:
        rebuild_event_features(session, commit=False)
        bundles = list_event_feature_bundles(session)
        rows = []
        targets = []
        for bundle in bundles:
            clearance_minutes = reliable_clearance_minutes(bundle.event)
            if clearance_minutes is None:
                continue
            rows.append(build_resolution_time_feature_row(bundle.event, bundle.feature))
            targets.append(clearance_minutes)

        qualifying_rows = len(rows)
        artifact_path = str(RESOLUTION_TIME_MODEL_PATH.relative_to(REPO_ROOT))
        feature_names = list(rows[0].keys()) if rows else []

        if qualifying_rows < MIN_TRAINING_ROWS:
            metrics = {
                "status": "skipped_insufficient_rows",
                "qualifying_rows": qualifying_rows,
                "minimum_required_rows": MIN_TRAINING_ROWS,
                "data_filter": DATA_FILTER_APPLIED,
            }
            upsert_model_run(
                session,
                model_name=RESOLUTION_TIME_MODEL_NAME,
                model_version=RESOLUTION_TIME_MODEL_VERSION,
                target_variable=TARGET_VARIABLE,
                training_rows=qualifying_rows,
                test_rows=0,
                metrics_json=metrics,
                feature_list_json=feature_names,
                artifact_path=artifact_path,
            )
            print(
                "[resolution_time_model] "
                f"Only {qualifying_rows} qualifying rows. Skipping ML training."
            )
            return None

        missing_modules = missing_optional_modules()
        if missing_modules:
            metrics = {
                "status": "skipped_missing_dependencies",
                "qualifying_rows": qualifying_rows,
                "minimum_required_rows": MIN_TRAINING_ROWS,
                "data_filter": DATA_FILTER_APPLIED,
                "missing_modules": missing_modules,
            }
            upsert_model_run(
                session,
                model_name=RESOLUTION_TIME_MODEL_NAME,
                model_version=RESOLUTION_TIME_MODEL_VERSION,
                target_variable=TARGET_VARIABLE,
                training_rows=qualifying_rows,
                test_rows=0,
                metrics_json=metrics,
                feature_list_json=feature_names,
                artifact_path=artifact_path,
            )
            print(
                "[resolution_time_model] Skipping training: install optional ML dependencies "
                f"{', '.join(missing_modules)}."
            )
            return None

        import joblib  # type: ignore[import-not-found]
        import pandas as pd  # type: ignore[import-not-found]
        from sklearn.compose import ColumnTransformer  # type: ignore[import-not-found]
        from sklearn.ensemble import GradientBoostingRegressor  # type: ignore[import-not-found]
        from sklearn.metrics import mean_absolute_error, r2_score  # type: ignore[import-not-found]
        from sklearn.model_selection import train_test_split  # type: ignore[import-not-found]
        from sklearn.pipeline import Pipeline  # type: ignore[import-not-found]
        from sklearn.preprocessing import OneHotEncoder, StandardScaler  # type: ignore[import-not-found]

        frame = pd.DataFrame(rows)
        target = pd.Series(targets)
        categorical = ["event_cause_clean", "event_type", "corridor", "police_station", "priority", "veh_type"]
        numeric = ["event_hour", "event_weekday", "historical_corridor_risk", "is_peak_hour"]

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
                    GradientBoostingRegressor(
                        n_estimators=200,
                        learning_rate=0.05,
                        max_depth=4,
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
        )
        pipeline.fit(x_train, y_train)
        predictions = pipeline.predict(x_test)
        metrics = {
            "status": "trained",
            "mae_minutes": round(float(mean_absolute_error(y_test, predictions)), 4),
            "r2_score": round(float(r2_score(y_test, predictions)), 4),
            "training_rows": len(x_train),
            "test_rows": len(x_test),
            "qualifying_rows": qualifying_rows,
            "data_filter": DATA_FILTER_APPLIED,
        }

        ensure_artifacts_root()
        joblib.dump(
            {
                "pipeline": pipeline,
                "metrics": metrics,
                "model_name": RESOLUTION_TIME_MODEL_NAME,
                "model_version": RESOLUTION_TIME_MODEL_VERSION,
                "features": list(frame.columns),
            },
            RESOLUTION_TIME_MODEL_PATH,
        )
        upsert_model_run(
            session,
            model_name=RESOLUTION_TIME_MODEL_NAME,
            model_version=RESOLUTION_TIME_MODEL_VERSION,
            target_variable=TARGET_VARIABLE,
            training_rows=len(x_train),
            test_rows=len(x_test),
            metrics_json=metrics,
            feature_list_json=list(frame.columns),
            artifact_path=artifact_path,
        )
        print(
            "[resolution_time_model] "
            f"MAE={metrics['mae_minutes']:.4f} min | R2={metrics['r2_score']:.4f} "
            f"| Qualifying rows={qualifying_rows}"
        )
        return metrics


if __name__ == "__main__":
    result = train()
    print(result if result is not None else "Training skipped. Rule fallback remains active.")
