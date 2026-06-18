from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import routes_events, routes_live_updates
from app.core.security import AuthContext
from app.db.base import Base, import_model_modules
from app.db.session import get_db
from app.main import app
from app.orm.event import Event
from app.orm.event_prediction import EventPrediction
from app.orm.live_event_update import LiveEventUpdate
from app.orm.system_audit_log import SystemAuditLog
from app.orm.user_account import UserAccount
from app.services.live_escalation_service import LiveUpdateInput, apply_live_update


def _build_session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    import_model_modules()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _seed_live_event(session) -> None:
    session.add(
        Event(
            id="LIVE-001",
            event_type="unplanned",
            latitude=12.9716,
            longitude=77.5946,
            event_cause_clean="vehicle_breakdown",
            requires_road_closure=False,
            start_datetime=datetime(2026, 6, 24, 18, 0, tzinfo=timezone.utc),
            description_language="en",
            priority="High",
            corridor="Central Spine",
            police_station="Ashok Nagar",
            zone="Central",
            junction="MG Road",
        )
    )
    session.add(
        EventPrediction(
            event_id="LIVE-001",
            predicted_priority="High",
            priority_confidence=0.81,
            road_closure_probability=0.62,
            predicted_road_closure=True,
            estimated_clearance_minutes=56.0,
            clearance_prediction_method="rule_fallback",
            clearance_confidence=0.45,
            clearance_confidence_note="Rule estimate",
            historical_clearance_range_min=35.0,
            historical_clearance_range_max=90.0,
            estimated_impact_score=72.0,
            impact_category="Warning",
            impact_radius_km=2.5,
            vehicle_impact_factor=1.2,
            vehicle_impact_note="LCV multiplier",
            baseline_risk_score=41.0,
            additional_event_delta=31.0,
            weather_adjustment_json={
                "weather_condition": "clear",
                "weather_factor": 1.0,
                "rain_mm": 0.0,
                "visibility_m": 5000,
                "low_visibility": False,
                "waterlogging_risk": "low",
                "reason_codes": [],
                "source": "historical_default",
                "provider": None,
                "provider_status": "not_requested",
                "note": "No weather override was applied for this seeded prediction.",
            },
            multi_event_conflict_json={},
            prediction_explanation_json={},
            model_version="priority_rule_or_optional_ml_v1",
        )
    )
    session.commit()


def _seed_actor(session, *, actor_id, role: str) -> None:
    session.add(
        UserAccount(
            id=actor_id,
            role=role,
            display_name=f"{role.title()} User",
            auth_provider="firebase",
            auth_provider_uid=f"{role}-firebase",
            is_active=True,
        )
    )
    session.commit()


def _officer_auth_context(actor_id: str) -> AuthContext:
    return AuthContext(
        firebase_uid="officer-firebase",
        email="officer@example.com",
        role="police_officer",
        user_account_id=actor_id,
        officer_profile_id=str(uuid4()),
        officer_id="BTP-LIVE-001",
        police_station="Ashok Nagar",
        assigned_corridors=["Central Spine"],
        assigned_zones=["Central"],
    )


def test_apply_live_update_marks_critical_when_field_signals_stack():
    result = apply_live_update(
        LiveUpdateInput(
            current_congestion_level="Critical",
            field_update="Crowd spillover near the upstream junction",
            road_closure_active=True,
            officer_shortage=True,
            crowd_increase=True,
            rain_waterlogging=True,
            new_nearby_incident=False,
            expected_impact_score=72.0,
            corroborating_reports=3,
        )
    )

    assert result["expected_impact_score"] == 72.0
    assert result["current_impact_score"] == 100.0
    assert result["impact_deviation"] == 28.0
    assert result["alert_level"] == "Critical"
    assert "Notify control room" in str(result["adaptive_action"])
    assert "Activate the stored diversion plan" in str(result["adaptive_action"])


def test_live_update_route_persists_update_and_event_detail_returns_timeline():
    session_factory = _build_session_factory()
    actor_id = uuid4()

    with session_factory() as session:
        _seed_live_event(session)
        _seed_actor(session, actor_id=actor_id, role="police_officer")

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    auth_context = _officer_auth_context(str(actor_id))
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[routes_live_updates.require_live_update_access] = lambda: auth_context
    app.dependency_overrides[routes_events.require_internal_event_access] = lambda: auth_context

    try:
        with TestClient(app) as client:
            update_response = client.post(
                "/api/events/LIVE-001/live-update",
                json={
                    "current_congestion_level": "Warning",
                    "field_update": "Crowd spillover near upstream junction",
                    "road_closure_active": True,
                    "officer_shortage": True,
                    "crowd_increase": True,
                    "rain_waterlogging": False,
                    "new_nearby_incident": False,
                },
            )
            detail_response = client.get("/api/events/LIVE-001")
    finally:
        app.dependency_overrides.clear()

    assert update_response.status_code == 200
    update_payload = update_response.json()
    assert update_payload["event_id"] == "LIVE-001"
    assert update_payload["update_source"] == "field_officer"
    assert update_payload["current_impact_score"] > update_payload["expected_impact_score"]
    assert update_payload["alert_level"] in {"Warning", "Critical"}
    assert update_payload["honesty_note"].startswith("Simulated live escalation guidance")

    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert len(detail_payload["live_updates"]) == 1
    assert detail_payload["live_updates"][0]["field_update"] == "Crowd spillover near upstream junction"
    assert detail_payload["live_updates"][0]["update_source"] == "field_officer"

    with session_factory() as session:
        assert session.query(LiveEventUpdate).count() == 1
        assert session.query(SystemAuditLog).filter(SystemAuditLog.action == "live_update_submit").count() == 1


def test_live_update_route_rejects_unassigned_officer():
    session_factory = _build_session_factory()
    actor_id = uuid4()

    with session_factory() as session:
        _seed_live_event(session)
        _seed_actor(session, actor_id=actor_id, role="police_officer")

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[routes_live_updates.require_live_update_access] = lambda: AuthContext(
        firebase_uid="officer-firebase",
        email="officer@example.com",
        role="police_officer",
        user_account_id=str(actor_id),
        officer_profile_id=str(uuid4()),
        officer_id="BTP-LIVE-002",
        police_station="Whitefield",
        assigned_corridors=["Outer Ring Road"],
        assigned_zones=["East"],
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/events/LIVE-001/live-update",
                json={
                    "current_congestion_level": "Warning",
                    "field_update": "Officer is far from assigned corridor",
                    "road_closure_active": False,
                    "officer_shortage": False,
                    "crowd_increase": False,
                    "rain_waterlogging": False,
                    "new_nearby_incident": False,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "OFFICER_ASSIGNMENT_REQUIRED"
