from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import routes_events
from app.core.security import AuthContext
from app.db.base import Base, import_model_modules
from app.db.session import get_db
from app.main import app
from app.orm.event import Event
from app.orm.event_prediction import EventPrediction
from app.orm.event_recommendation import EventRecommendation
from app.orm.system_audit_log import SystemAuditLog
from app.orm.user_account import UserAccount
from app.services.multi_event_service import (
    EventCoordinationInput,
    analyze_multi_event_conflicts,
    detect_pair_conflict,
    time_overlap_minutes,
)


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


def _weather_payload() -> dict[str, object]:
    return {
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
    }


def _coordination_input(
    event_id: str,
    *,
    latitude: float,
    longitude: float,
    start_offset_minutes: int = 0,
    corridor: str = "Central Spine",
    station: str = "Ashok Nagar",
    personnel: int = 12,
) -> EventCoordinationInput:
    start = datetime(2026, 6, 24, 18, 0, tzinfo=timezone.utc) + timedelta(minutes=start_offset_minutes)
    return EventCoordinationInput(
        event_id=event_id,
        latitude=latitude,
        longitude=longitude,
        start_datetime=start,
        end_datetime=start + timedelta(hours=2),
        corridor=corridor,
        police_station=station,
        zone="Central",
        junction="MG Road",
        estimated_impact_score=82.0,
        impact_radius_km=3.0,
        recommended_personnel=personnel,
        diversion_strategy="hotspot_bypass",
        diversion_corridor=corridor,
        upstream_focus_points=("MG Road", "Trinity Circle"),
    )


def _seed_actor(session, *, actor_id) -> None:
    session.add(
        UserAccount(
            id=actor_id,
            role="control_room",
            display_name="Control Room",
            auth_provider="firebase",
            auth_provider_uid="control-room-firebase",
            is_active=True,
        )
    )
    session.commit()


def _seed_event_bundle(
    session,
    *,
    event_id: str,
    latitude: float,
    longitude: float,
    start_offset_minutes: int,
    corridor: str,
    station: str,
    impact_score: float,
    officers: int,
) -> None:
    start = datetime(2026, 6, 24, 18, 0, tzinfo=timezone.utc) + timedelta(minutes=start_offset_minutes)
    session.add(
        Event(
            id=event_id,
            event_type="planned",
            latitude=latitude,
            longitude=longitude,
            event_cause_clean="public_event",
            requires_road_closure=False,
            start_datetime=start,
            end_datetime=start + timedelta(hours=2),
            description_language="en",
            priority="High",
            corridor=corridor,
            police_station=station,
            zone="Central",
            junction="MG Road",
        )
    )
    session.add(
        EventPrediction(
            event_id=event_id,
            predicted_priority="High",
            priority_confidence=0.82,
            road_closure_probability=0.68,
            predicted_road_closure=True,
            estimated_clearance_minutes=90.0,
            clearance_prediction_method="rule_fallback",
            clearance_confidence=0.45,
            clearance_confidence_note="Rule estimate",
            historical_clearance_range_min=45.0,
            historical_clearance_range_max=130.0,
            estimated_impact_score=impact_score,
            impact_category="Critical" if impact_score >= 75 else "High",
            impact_radius_km=3.0,
            vehicle_impact_factor=1.0,
            vehicle_impact_note="No vehicle adjustment",
            baseline_risk_score=40.0,
            additional_event_delta=impact_score - 40.0,
            weather_adjustment_json=_weather_payload(),
            multi_event_conflict_json={},
            prediction_explanation_json={},
            model_version="priority_rule_or_optional_ml_v1",
        )
    )
    session.add(
        EventRecommendation(
            event_id=event_id,
            risk_summary_json={
                "impact_score": impact_score,
                "impact_category": "Critical" if impact_score >= 75 else "High",
                "estimated_radius_km": 3.0,
            },
            weather_risk_json=_weather_payload(),
            recommended_total_officers=officers,
            deployment_plan_json={
                "recommended_total_officers": officers,
                "deployment_style": "incident_command_posture",
            },
            barricade_plan_json={},
            diversion_plan_json={
                "strategy": "hotspot_bypass",
                "corridor_to_protect": corridor,
                "upstream_focus_points": ["MG Road", "Trinity Circle"],
            },
            emergency_corridor_json=None,
            logistics_impact_json=None,
            action_confidence_ledger_json=[],
            recommended_action_summary="Seeded recommendation",
        )
    )
    session.commit()


def test_time_overlap_and_pair_conflict_detect_core_signals():
    left = _coordination_input("EVT-1", latitude=12.9716, longitude=77.5946)
    right = _coordination_input("EVT-2", latitude=12.9720, longitude=77.5950, start_offset_minutes=30)

    assert time_overlap_minutes(left, right) == 90.0

    conflict = detect_pair_conflict(left, right, available_personnel=16)

    assert conflict["conflict_level"] in {"high", "critical"}
    assert conflict["manpower_gap"] == 8
    assert "time_overlap" in conflict["reason_codes"]
    assert "shared_corridor" in conflict["reason_codes"]
    assert "diversion_route_conflict" in conflict["reason_codes"]


def test_analyze_multi_event_conflicts_returns_joint_command_summary():
    left = _coordination_input("EVT-1", latitude=12.9716, longitude=77.5946)
    right = _coordination_input("EVT-2", latitude=12.9720, longitude=77.5950, start_offset_minutes=30)

    analysis = analyze_multi_event_conflicts([left, right], available_personnel=16)

    assert analysis["conflict_detected"] is True
    assert analysis["combined_risk"] in {"High", "Critical"}
    assert analysis["coordination_mode"] == "joint_command"
    assert "shared corridor" in analysis["conflict_signals"]
    assert analysis["officer_gap"] == 8
    assert analysis["map_overlay"]["type"] == "FeatureCollection"


def test_multi_event_analysis_route_updates_prediction_snapshots_and_audit_log():
    session_factory = _build_session_factory()
    actor_id = uuid4()

    with session_factory() as session:
        _seed_actor(session, actor_id=actor_id)
        _seed_event_bundle(
            session,
            event_id="ME-001",
            latitude=12.9716,
            longitude=77.5946,
            start_offset_minutes=0,
            corridor="Central Spine",
            station="Ashok Nagar",
            impact_score=82.0,
            officers=12,
        )
        _seed_event_bundle(
            session,
            event_id="ME-002",
            latitude=12.9720,
            longitude=77.5950,
            start_offset_minutes=30,
            corridor="Central Spine",
            station="Ashok Nagar",
            impact_score=78.0,
            officers=12,
        )

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[routes_events.require_internal_event_access] = lambda: AuthContext(
        firebase_uid="control-room-firebase",
        email="control@example.com",
        role="control_room",
        user_account_id=str(actor_id),
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/events/multi-event-analysis",
                json={"event_ids": ["ME-001", "ME-002"], "available_officers": 16},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["conflict_detected"] is True
    assert payload["coordination_mode"] == "joint_command"
    assert payload["officer_gap"] == 8
    assert payload["conflicts"][0]["event_ids"] == ["ME-001", "ME-002"]

    with session_factory() as session:
        prediction = session.query(EventPrediction).filter(EventPrediction.event_id == "ME-001").one()
        assert prediction.multi_event_conflict_json["status"] == "analyzed"
        assert prediction.multi_event_conflict_json["combined_risk"] in {"High", "Critical"}
        assert session.query(SystemAuditLog).filter(SystemAuditLog.action == "multi_event_analysis_run").count() == 1


def test_multi_event_analysis_route_rejects_unassigned_officer():
    session_factory = _build_session_factory()
    actor_id = uuid4()

    with session_factory() as session:
        session.add(
            UserAccount(
                id=actor_id,
                role="police_officer",
                display_name="Officer",
                auth_provider="firebase",
                auth_provider_uid="officer-firebase",
                is_active=True,
            )
        )
        session.commit()
        _seed_event_bundle(
            session,
            event_id="ME-003",
            latitude=12.9716,
            longitude=77.5946,
            start_offset_minutes=0,
            corridor="Central Spine",
            station="Ashok Nagar",
            impact_score=82.0,
            officers=12,
        )
        _seed_event_bundle(
            session,
            event_id="ME-004",
            latitude=12.9720,
            longitude=77.5950,
            start_offset_minutes=30,
            corridor="Central Spine",
            station="Ashok Nagar",
            impact_score=78.0,
            officers=12,
        )

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[routes_events.require_internal_event_access] = lambda: AuthContext(
        firebase_uid="officer-firebase",
        email="officer@example.com",
        role="police_officer",
        user_account_id=str(actor_id),
        officer_profile_id=str(uuid4()),
        officer_id="BTP-ME-001",
        police_station="Whitefield",
        assigned_corridors=["Outer Ring Road"],
        assigned_zones=["East"],
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/events/multi-event-analysis",
                json={"event_ids": ["ME-003", "ME-004"], "available_officers": 16},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "OFFICER_ASSIGNMENT_REQUIRED"
