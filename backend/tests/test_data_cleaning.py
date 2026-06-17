from __future__ import annotations

from io import StringIO
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.routes_datasets import require_admin_or_control_room
from app.core.config import get_settings
from app.core.security import AuthContext
from app.db.base import Base, import_model_modules
from app.db.session import get_db
from app.main import app
from app.orm.event import Event
from app.orm.system_audit_log import SystemAuditLog
from app.services.data_cleaning_service import clean_astram_row, ingest_astram_csv_text
from app.services.text_normalization_service import detect_description_language, normalize_description


CSV_HEADER = ",".join(
    [
        "id",
        "event_type",
        "latitude",
        "longitude",
        "endlatitude",
        "endlongitude",
        "address",
        "end_address",
        "event_cause",
        "requires_road_closure",
        "start_datetime",
        "end_datetime",
        "status",
        "authenticated",
        "modified_datetime",
        "direction",
        "description",
        "veh_type",
        "veh_no",
        "corridor",
        "priority",
        "cargo_material",
        "reason_breakdown",
        "age_of_truck",
        "created_date",
        "route_path",
        "client_id",
        "created_by_id",
        "last_modified_by_id",
        "assigned_to_police_id",
        "citizen_accident_id",
        "comment",
        "police_station",
        "meta_data",
        "kgid",
        "resolved_at_address",
        "resolved_at_latitude",
        "resolved_at_longitude",
        "closed_by_id",
        "closed_datetime",
        "resolved_by_id",
        "resolved_datetime",
        "gba_identifier",
        "zone",
        "junction",
    ]
)


def build_csv(*rows: str) -> str:
    return "\n".join((CSV_HEADER, *rows))


def test_normalize_description_detects_kannada_and_glossary():
    normalized = normalize_description("ಸಂಚಾರ ರಸ್ತೆ ಅಪಘಾತ")

    assert detect_description_language("ಸಂಚಾರ ರಸ್ತೆ ಅಪಘಾತ") == "kn"
    assert normalized.language == "kn"
    assert normalized.text_for_features == "road accident traffic"
    assert normalized.method == "static_kannada_glossary"


def test_normalize_description_detects_hindi_and_glossary():
    normalized = normalize_description("सड़क दुर्घटना भारी ट्रैफिक")

    assert detect_description_language("सड़क दुर्घटना भारी ट्रैफिक") == "hi"
    assert normalized.language == "hi"
    assert normalized.text_for_features == "road accident traffic heavy"
    assert normalized.method == "static_hindi_glossary"


def test_clean_astram_row_masks_sensitive_fields_and_normalizes_coordinates():
    cleaned = clean_astram_row(
        {
            "id": "FKID000000",
            "event_type": "unplanned",
            "latitude": "13.0400041",
            "longitude": "77.5180991",
            "endlatitude": "0",
            "endlongitude": "0",
            "address": "Mumbai Bengaluru Highway",
            "event_cause": "vehicle_breakdown",
            "requires_road_closure": "FALSE",
            "start_datetime": "2024-03-07 17:01:48.111+00",
            "status": "closed",
            "authenticated": "yes",
            "description": "s m circle in coming man track",
            "veh_type": "lcv",
            "veh_no": "FKN00GL0000",
            "corridor": "Tumkur Road",
            "priority": "High",
            "client_id": "1",
            "created_by_id": "FKUSR00000",
            "last_modified_by_id": "FKUSR00001",
            "assigned_to_police_id": "NULL",
            "kgid": "FKKG000000",
            "police_station": "Peenya",
        }
    )

    assert cleaned["endlatitude"] is None
    assert cleaned["endlongitude"] is None
    assert cleaned["authenticated"] is True
    assert cleaned["veh_no_hash"] == cleaned["veh_no_masked"]
    assert len(cleaned["veh_no_hash"]) == 16
    assert cleaned["description_language"] == "en"
    assert cleaned["description_for_features"] == "s m circle in coming man track"
    assert "client_id" not in cleaned["raw_payload"]
    assert "veh_no" not in cleaned["raw_payload"]
    assert cleaned["raw_payload"]["police_station"] == "Peenya"


def test_ingest_astram_csv_text_upserts_and_counts_invalid_rows(tmp_path):
    import_model_modules()
    engine = create_engine(f"sqlite:///{(tmp_path / 'phase3-ingest.db').as_posix()}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    csv_text = build_csv(
        "EVT-1,unplanned,12.9716,77.5946,0,0,MG Road,,vehicle_breakdown,FALSE,2024-03-07 17:01:48.111+00,,closed,yes,,northbound,simple traffic delay,lcv,FKN00GL0000,ORR East 1,High,,,,2024-03-07 17:03:51.164032+00,,1,USR-1,USR-2,,,,HSR Layout,,KGID-1,,,,,,,,East,Junction A",
        "EVT-1,planned,12.9716,77.5946,0,0,MG Road,,procession,TRUE,2024-03-08 18:01:48.111+00,,resolved,yes,,northbound,updated description,bus,FKN00GL0000,ORR East 1,Critical,,,,2024-03-08 18:03:51.164032+00,,1,USR-1,USR-2,,,,HSR Layout,,KGID-1,,,,,,,,East,Junction A",
        "EVT-2,unplanned,,77.5946,0,0,MG Road,,accident,TRUE,2024-03-08 18:01:48.111+00,,open,yes,,northbound,broken row,bus,FKN00GL0001,ORR East 1,High,,,,2024-03-08 18:03:51.164032+00,,1,USR-1,USR-2,,,,HSR Layout,,KGID-2,,,,,,,,East,Junction B",
    )

    with session_factory() as session:
        report = ingest_astram_csv_text(session, csv_text)

    with session_factory() as session:
        event = session.query(Event).one()
        assert report.rows_processed == 3
        assert report.rows_upserted == 2
        assert report.invalid_rows == 1
        assert report.columns_detected == 45
        assert event.id == "EVT-1"
        assert event.event_type == "planned"
        assert event.status == "resolved"
        assert event.requires_road_closure is True


def test_load_demo_dataset_route_uses_configured_csv_and_audits(tmp_path, monkeypatch):
    import_model_modules()
    csv_path = tmp_path / "demo-events.csv"
    csv_path.write_text(
        build_csv(
            "EVT-LOAD-1,unplanned,12.9716,77.5946,0,0,MG Road,,vehicle_breakdown,FALSE,2024-03-07 17:01:48.111+00,,closed,yes,,northbound,simple traffic delay,lcv,FKN00GL0000,ORR East 1,High,,,,2024-03-07 17:03:51.164032+00,,1,USR-1,USR-2,,,,HSR Layout,,KGID-1,,,,,,,,East,Junction A"
        ),
        encoding="utf-8",
    )

    engine = create_engine(f"sqlite:///{(tmp_path / 'phase3-routes.db').as_posix()}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    auth = AuthContext(
        firebase_uid="demo-admin",
        email="admin@example.com",
        role="admin",
        user_account_id=str(uuid4()),
    )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_admin_or_control_room] = lambda: auth

    monkeypatch.setenv("RAW_DATA_PATH", str(csv_path))
    get_settings.cache_clear()

    client = TestClient(app)
    response = client.post("/api/datasets/load-demo")

    app.dependency_overrides.clear()
    get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json()["rows_loaded"] == 1
    assert response.json()["invalid_rows"] == 0

    with session_factory() as session:
        assert session.query(Event).count() == 1
        assert session.query(SystemAuditLog).count() == 1


def test_upload_dataset_route_accepts_csv_and_persists_rows(tmp_path):
    import_model_modules()
    engine = create_engine(f"sqlite:///{(tmp_path / 'phase3-upload.db').as_posix()}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    auth = AuthContext(
        firebase_uid="demo-control-room",
        email="control-room@example.com",
        role="control_room",
        user_account_id=str(uuid4()),
    )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_admin_or_control_room] = lambda: auth

    client = TestClient(app)
    response = client.post(
        "/api/datasets/upload",
        files={
            "file": (
                "events.csv",
                build_csv(
                    "EVT-UPLOAD-1,unplanned,12.9716,77.5946,0,0,MG Road,,vehicle_breakdown,FALSE,2024-03-07 17:01:48.111+00,,closed,yes,,northbound,simple traffic delay,lcv,FKN00GL0000,ORR East 1,High,,,,2024-03-07 17:03:51.164032+00,,1,USR-1,USR-2,,,,HSR Layout,,KGID-1,,,,,,,,East,Junction A"
                ),
                "text/csv",
            )
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["rows_loaded"] == 1

    with session_factory() as session:
        assert session.query(Event).count() == 1
        assert session.query(SystemAuditLog).count() == 1
