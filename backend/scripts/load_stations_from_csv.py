import sys
import csv
from pathlib import Path

# Add backend to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.orm.traffic_station import TrafficStation
from app.core.config import get_settings

def is_empty(val):
    if val is None:
        return True
    if str(val).strip().upper() in ("NULL", "NONE", ""):
        return True
    return False

def main():
    csv_path = get_settings().resolved_raw_data_path
    
    unique_stations = {}
    
    print(f"Reading from {csv_path}...")
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                station_name = row.get("police_station")
                if station_name and not is_empty(station_name):
                    name = station_name.strip()
                    if name not in unique_stations:
                        try:
                            lat = float(row.get("latitude"))
                            lon = float(row.get("longitude"))
                        except (ValueError, TypeError):
                            lat = 12.9716 # default Bangalore lat
                            lon = 77.5946 # default Bangalore lon
                        unique_stations[name] = {"lat": lat, "lon": lon}
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return
                
    print(f"Found {len(unique_stations)} unique stations in CSV.")
    
    with SessionLocal() as db:
        # Get existing stations to prevent duplicates
        existing = {s.name for s in db.query(TrafficStation).all()}
        
        added = 0
        for name, coords in unique_stations.items():
            if name not in existing:
                # Generate a unique station code
                code = "".join(c if c.isalnum() else "_" for c in name.upper())
                # ensure no double underscores
                while "__" in code:
                    code = code.replace("__", "_")
                code = code.strip("_")
                
                # Check if code already exists (just in case)
                base_code = code
                counter = 1
                while db.query(TrafficStation).filter_by(station_code=code).first() is not None:
                    code = f"{base_code}_{counter}"
                    counter += 1
                
                station = TrafficStation(
                    station_code=code,
                    name=name,
                    locality=name, # default locality to name
                    latitude=coords["lat"],
                    longitude=coords["lon"],
                    active=True
                )
                db.add(station)
                added += 1
                existing.add(name)
        
        db.commit()
        print(f"Successfully added {added} new stations to the database. Total stations now: {len(existing)}")

if __name__ == "__main__":
    main()
