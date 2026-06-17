from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import sessionmaker

from app.api import routes_events
from app.core.database import build_engine
from app.core.security import AuthContext
from app.db.base import Base, import_model_modules
from app.db.session import get_db
from app.main import app
from app.orm.event import Event
from app.orm.event_dna import EventDna
from app.orm.event_prediction import EventPrediction
from app.orm.system_audit_log import SystemAuditLog
from app.orm.user_account import UserAccount
from app.services.event_dna_service import persist_event_dna, rebuild_event_dna_records
from app.services.feature_engineering_service import build_features_for_event
from app.services.hotspot_service import rebuild_hotspots


def _build_session_factory(tmp_path, name: str):
    engine = build_engine(f"sqlite:///{tmp_path / name}")
    import_model_modules()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _seed_event_dna_events(session) -> None:
    start = datetime(2026, 6, 19, 8, 0, tzinfo=timezone.utc)
    session.add_all(
        [
            Event(
                id="DNA-001",
                event_type="unplanned",
                latitude=12.9716,
                longitude=77.5946,
                event_cause_clean="vehicle_breakdown",
                requires_road_closure=True,
                start_datetime=start,
                description_language="kn",
                description_for_features="traffic junction vehicle breakdown",
                description_normalization_method="skipped_low_confidence",
                priority="High",
                corridor="Central Spine",
                police_station="Ashok Nagar",
                zone="Central",
                junction="MG Road",
                route_path="MG Road -> Residency Road",
                veh_type="Truck",
            ),
            Event(
                id="DNA-002",
                event_type="unplanned",
                latitude=12.9720,
                longitude=77.5950,
                event_cause_clean="vehicle_breakdown",
                requires_road_closure=False,
                start_datetime=start + timedelta(minutes=20),
                description_language="en",
                description_for_features="heavy vehicle traffic near junction",
                description_normalization_method="raw_ascii",
                priority="Critical",
                corridor="Central Spine",
                police_station="Ashok Nagar",
                zone="Central",
                junction="MG Road",
                veh_type="Truck",
            ),
            Event(
                id="DNA-003",
                event_type="planned",
                latitude=12.9724,
                longitude=77.5948,
                event_cause_clean="construction",
                requires_road_closure=False,
                start_datetime=start + timedelta(hours=9),
                description_language="en",
                description_for_features="planned construction at major road junction",
                description_normalization_method="raw_ascii",
                priority="Medium",
                corridor="Central Spine",
                police_station="Ashok Nagar",
                zone="Central",
                junction="MG Road",
            ),
        ]
    )
    session.commit()


def test_persist_event_dna_prefers_structured_fields_and_downweights_low_confidence_text(tmp_path):
    session_factory = _build_session_factory(tmp_path, "phase6-persist.db")

    with session_factory() as session:
        _seed_event_dna_events(session)
        rebuild_hotspots(session)
        event = session.get(Event, "DNA-001")
        feature = build_features_for_event(session, event)[0]

        record, created = persist_event_dna(session, event, feature=feature)

        assert created is True
        assert "ignored in DNA scoring" in record.cause_context
        assert record.risk_indicators_json["description_signal"] == 0.0
        assert record.risk_indicators_json["description_normalization_method"] == "skipped_low_confidence"
        assert "Duration" in record.time_context
        assert "Corridor: Central Spine." in record.location_context
        assert "Historical corridor risk" in record.historical_pattern
        assert record.weather_context == "Weather context deferred to Phase 10 weather integration."
        assert record.multi_event_context == "Multi-event conflict context deferred to Phase 13 analysis."


def test_event_detail_route_returns_dna_and_similar_events(tmp_path):
    session_factory = _build_session_factory(tmp_path, "phase6-route.db")
    actor_id = uuid4()

    with session_factory() as session:
        _seed_event_dna_events(session)
        rebuild_hotspots(session)
        session.add(
            UserAccount(
                id=actor_id,
                role="admin",
                display_name="Event DNA Admin",
                auth_provider="firebase",
                auth_provider_uid="firebase-admin-dna",
                is_active=True,
            )
        )
        session.commit()

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[routes_events.require_internal_event_access] = lambda: AuthContext(
        firebase_uid="firebase-admin-dna",
        email="admin@example.com",
        role="admin",
        user_account_id=str(actor_id),
    )

    try:
        with TestClient(app) as client:
            response = client.get("/api/events/DNA-001")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["event"]["id"] == "DNA-001"
    assert payload["features"]["location_cluster_id"] == "CL-001"
    assert payload["event_dna"]["event_id"] == "DNA-001"
    assert payload["event_dna"]["weather_context"] == "Weather context deferred to Phase 10 weather integration."
    assert payload["event_dna"]["multi_event_context"] == "Multi-event conflict context deferred to Phase 13 analysis."
    assert len(payload["similar_events"]) == 2
    assert payload["similar_events"][0]["event_id"] == "DNA-002"
    assert payload["map_overlays"]["hotspot"]["location_cluster_id"] == "CL-001"

    with session_factory() as session:
        assert session.query(EventDna).filter(EventDna.event_id == "DNA-001").count() == 0
        assert session.query(EventPrediction).filter(EventPrediction.event_id == "DNA-001").count() == 0


def test_rebuild_event_dna_route_updates_records_and_audit_log(tmp_path):
    session_factory = _build_session_factory(tmp_path, "phase6-rebuild-route.db")
    actor_id = uuid4()

    with session_factory() as session:
        _seed_event_dna_events(session)
        session.add(
            UserAccount(
                id=actor_id,
                role="admin",
                display_name="Event DNA Admin",
                auth_provider="firebase",
                auth_provider_uid="firebase-admin-dna",
                is_active=True,
            )
        )
        session.commit()

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[routes_events.require_event_dna_rebuild_access] = lambda: AuthContext(
        firebase_uid="firebase-admin-dna",
        email="admin@example.com",
        role="admin",
        user_account_id=str(actor_id),
    )

    try:
        with TestClient(app) as client:
            response = client.post("/api/events/rebuild-dna?limit_similar=2")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "events_processed": 3,
        "dna_created": 3,
        "dna_updated": 0,
        "message": "Dataset-backed Event DNA records rebuilt.",
    }

    with session_factory() as session:
        assert session.query(EventDna).count() == 3
        audit_log = session.query(SystemAuditLog).one()
        assert audit_log.action == "event_dna_rebuild"
        assert audit_log.metadata_json["limit_similar"] == 2
