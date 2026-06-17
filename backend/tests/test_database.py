from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import sessionmaker

from app.core.database import build_engine, get_database_status
from app.db.base import Base, import_model_modules
from app.orm.event import Event
from app.orm.user_account import UserAccount


def test_model_metadata_contains_phase_two_tables():
    import_model_modules()

    expected_tables = {
        "user_accounts",
        "police_officer_profiles",
        "officer_event_assignments",
        "system_audit_logs",
        "events",
        "event_features",
        "event_dna",
        "model_runs",
        "event_predictions",
        "event_recommendations",
        "hotspot_clusters",
        "citizen_reports",
        "live_event_updates",
        "post_event_reports",
        "demo_scenarios",
        "map_api_usage_logs",
    }

    assert expected_tables.issubset(set(Base.metadata.tables))


def test_updated_phase_one_and_two_contract_columns_are_present():
    import_model_modules()

    event_columns = set(Base.metadata.tables["events"].columns.keys())
    prediction_columns = set(Base.metadata.tables["event_predictions"].columns.keys())
    officer_columns = set(Base.metadata.tables["police_officer_profiles"].columns.keys())

    assert {"assigned_corridors_json", "assigned_zones_json"}.issubset(officer_columns)
    assert {"veh_no_hash", "veh_no_masked", "raw_payload"}.issubset(event_columns)
    assert {
        "estimated_clearance_minutes",
        "clearance_prediction_method",
        "clearance_confidence",
        "clearance_confidence_note",
        "historical_clearance_range_min",
        "historical_clearance_range_max",
        "vehicle_impact_factor",
        "vehicle_impact_note",
    }.issubset(prediction_columns)


def test_sqlite_database_status_reports_connected(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'phase2-health.db'}")

    status, detail = get_database_status(engine)

    assert status == "connected"
    assert detail is None


def test_sqlite_session_round_trip(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'phase2-roundtrip.db'}")
    import_model_modules()
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    with session_factory() as session:
        session.add(
            UserAccount(
                role="admin",
                display_name="Phase Two Admin",
                auth_provider="firebase",
                auth_provider_uid="firebase-admin-1",
                is_active=True,
            )
        )
        session.add(
            Event(
                id="EVT-001",
                event_type="planned",
                latitude=12.9716,
                longitude=77.5946,
                event_cause_clean="public_event",
                requires_road_closure=False,
                start_datetime=datetime(2026, 6, 17, 10, 0, tzinfo=timezone.utc),
                description_language="en",
            )
        )
        session.commit()

    with session_factory() as session:
        assert session.query(UserAccount).count() == 1
        event = session.query(Event).one()
        assert event.id == "EVT-001"
        assert event.event_cause_clean == "public_event"
