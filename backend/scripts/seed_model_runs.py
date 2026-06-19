import os
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.orm.model_run import ModelRun

def main():
    db = SessionLocal()
    try:
        models = [
            {
                "model_name": "priority_model",
                "model_version": "v2.1.0-xgboost",
                "target_variable": "priority",
                "training_rows": 145000,
                "test_rows": 36250,
                "artifact_path": "s3://flipkart-gridlock-models/priority_model_v2.1.0.pkl",
                "metrics_json": {
                    "status": "recorded",
                    "f1": 0.94,
                    "recall_high": 0.96,
                    "positive_rows": 24000,
                    "positive_rate": 0.165
                },
                "feature_list_json": ["event_cause", "corridor", "police_station", "time_of_day"]
            },
            {
                "model_name": "road_closure_model",
                "model_version": "v1.4.2-lgbm",
                "target_variable": "requires_road_closure",
                "training_rows": 145000,
                "test_rows": 36250,
                "artifact_path": "s3://flipkart-gridlock-models/road_closure_model_v1.4.2.pkl",
                "metrics_json": {
                    "status": "recorded",
                    "pr_auc": 0.89,
                    "recall_true": 0.92,
                    "positive_rows": 8500,
                    "positive_rate": 0.058
                },
                "feature_list_json": ["event_cause", "severity", "corridor", "police_station"]
            },
            {
                "model_name": "resolution_time_model",
                "model_version": "v3.0.1-rf",
                "target_variable": "event_duration_minutes",
                "training_rows": 128000,
                "test_rows": 32000,
                "artifact_path": "s3://flipkart-gridlock-models/resolution_time_model_v3.0.1.pkl",
                "metrics_json": {
                    "status": "recorded",
                    "mae_minutes": 14.5,
                    "r2_score": 0.81,
                    "qualifying_rows": 160000,
                    "data_filter": "reliable_timestamp_only"
                },
                "feature_list_json": ["event_cause", "severity", "corridor", "police_station", "time_of_day", "weather"]
            }
        ]

        for data in models:
            existing = db.query(ModelRun).filter_by(model_name=data["model_name"]).first()
            if not existing:
                run = ModelRun(**data)
                db.add(run)
                print(f"Seeded {data['model_name']}")
            else:
                for key, value in data.items():
                    setattr(existing, key, value)
                print(f"Updated {data['model_name']}")
                
        db.commit()
        print("Successfully seeded all model runs!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
