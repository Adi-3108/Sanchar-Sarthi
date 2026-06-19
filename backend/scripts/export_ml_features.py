from __future__ import annotations

# ==========================================
# RUN THIS SCRIPT LOCALLY ON YOUR COMPUTER!
# ==========================================
# Do NOT run this script on Kaggle.
# This script connects to your local SQLite database (sqlite.db) to extract 
# all the historical events and their features into a flat CSV file.
# 
# Step 1: Run this locally on Windows -> `python backend/scripts/export_ml_features.py`
# Step 2: It will generate a file called `training_data.csv`
# Step 3: Upload `training_data.csv` to Kaggle.
# Step 4: Run `kaggle_xgboost_training_gpu.py` on Kaggle to train the model.
# ==========================================

import csv
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db.session import SessionLocal
from app.orm.event import Event
from app.orm.event_feature import EventFeature

def main() -> int:
    output_path = BACKEND_ROOT / "training_data.csv"
    
    with SessionLocal() as session:
        # We query the events and eager load the features
        stmt = select(Event).options(joinedload(Event.features)).order_by(Event.start_datetime)
        events = session.scalars(stmt).unique().all()
        
        if not events:
            print("No events found in the database. Ensure seed data is loaded.")
            return 1
            
        print(f"Exporting {len(events)} events to {output_path}...")
        
        with open(output_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            
            # Write the header row
            header = [
                "event_id",
                # Inputs (Features)
                "event_cause",
                "corridor",
                "police_station",
                "latitude",
                "longitude",
                "is_weekend",
                "is_peak_hour",
                "is_night_event",
                "historical_corridor_risk",
                "historical_police_station_risk",
                "historical_cluster_risk",
                "historical_cause_closure_rate",
                "historical_corridor_closure_rate",
                
                # Targets (What we want to predict)
                "target_priority",
                "target_requires_road_closure",
                "target_event_duration_minutes",
            ]
            writer.writerow(header)
            
            for event in events:
                # Get the associated feature record if it exists
                feature = event.features[0] if event.features else None
                
                row = [
                    event.id,
                    event.event_cause_clean or "unknown",
                    event.corridor or "unknown",
                    event.police_station or "unknown",
                    event.latitude,
                    event.longitude,
                    
                    # Feature data (or defaults if missing)
                    feature.is_weekend if feature else False,
                    feature.is_peak_hour if feature else False,
                    feature.is_night_event if feature else False,
                    float(feature.historical_corridor_risk) if feature and feature.historical_corridor_risk else 0.0,
                    float(feature.historical_police_station_risk) if feature and feature.historical_police_station_risk else 0.0,
                    float(feature.historical_cluster_risk) if feature and feature.historical_cluster_risk else 0.0,
                    float(feature.historical_cause_closure_rate) if feature and feature.historical_cause_closure_rate else 0.0,
                    float(feature.historical_corridor_closure_rate) if feature and feature.historical_corridor_closure_rate else 0.0,
                    
                    # Targets
                    event.priority or "low",
                    1 if event.requires_road_closure else 0,
                    float(feature.event_duration_minutes) if feature and feature.event_duration_minutes else 0.0,
                ]
                writer.writerow(row)
                
    print(f"Successfully exported {len(events)} rows to training_data.csv!")
    print("You can now upload this file to Kaggle to train your XGBoost model.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
