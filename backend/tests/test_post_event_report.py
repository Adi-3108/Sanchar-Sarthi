from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import routes_post_event
from app.core.security import AuthContext
from app.db.base import Base, import_model_modules
from app.db.session import get_db
from app.main import app
from app.orm.citizen_report import CitizenReport
from app.orm.event import Event
from app.orm.event_prediction import EventPrediction
from app.orm.event_recommendation import EventRecommendation
from app.orm.live_event_update import LiveEventUpdate
from app.orm.post_event_report import PostEventReport
from app.orm.system_audit_log import SystemAuditLog
from app.orm.user_account import UserAccount
from app.services.post_event_report_service import generate_post_event_report


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
        "weather_condition": "heavy_rain",
        "weather_factor": 1.22,
        "rain_mm": 14.0,
        "visibility_m": 900,
        "low_visibility": True,
        "waterlogging_risk": "elevated",
        "reason_codes": ["rain_or_wet_roads", "heavy_rain_waterlogging_risk", "low_visibility"],
        "source": "manual_event_plan_override",
        "provider": None,
        "provider_status": "manual_override",
        "note": "Weather modifier uses a manual scenario override for MVP planning and remains an operational estimate.",
    }


def _seed_actor(session, *, actor_id, role: str) -> None:
    session.add(
        UserAccount(
            id=actor_id,
            role=role,
            display_name=f"{role.title()} reviewer",
            auth_provider="firebase",
            auth_provider_uid=f"{role}-post-event",
            is_active=True,
        )
    )
    session.commit()


def _seed_post_event_bundle(session) -> None:
    session.add(
        Event(
            id="POST-001",
            event_type="planned",
            latitude=12.9716,
            longitude=77.5946,
            event_cause_clean="public_event",
            requires_road_closure=True,
            start_datetime=datetime(2026, 6, 24, 18, 0, tzinfo=timezone.utc),
            end_datetime=datetime(2026, 6, 24, 20, 0, tzinfo=timezone.utc),
            description_language="en",
            priority="High",
            status="resolved",
            corridor="Central Spine",
            police_station="Ashok Nagar",
            zone="Central",
            junction="MG Road",
        )
    )
    session.add(
        EventPrediction(
            event_id="POST-001",
            predicted_priority="High",
            priority_confidence=0.84,
            road_closure_probability=0.74,
            predicted_road_closure=True,
            estimated_clearance_minutes=68.0,
            clearance_prediction_method="rule_fallback",
            clearance_confidence=0.45,
            clearance_confidence_note="Rule estimate",
            historical_clearance_range_min=44.0,
            historical_clearance_range_max=102.0,
            estimated_impact_score=78.0,
            impact_category="Critical",
            impact_radius_km=3.2,
            vehicle_impact_factor=1.18,
            vehicle_impact_note="LCV multiplier",
            baseline_risk_score=43.0,
            additional_event_delta=35.0,
            weather_adjustment_json=_weather_payload(),
            multi_event_conflict_json={},
            prediction_explanation_json={},
            model_version="priority_rule_or_optional_ml_v1",
        )
    )
    session.add(
        EventRecommendation(
            event_id="POST-001",
            risk_summary_json={
                "impact_score": 78.0,
                "impact_category": "Critical",
                "estimated_radius_km": 3.2,
            },
            weather_risk_json=_weather_payload(),
            recommended_total_officers=10,
            deployment_plan_json={
                "recommended_total_officers": 10,
                "deployment_style": "corridor_ring_control",
                "officer_gap": 2,
            },
            barricade_plan_json={"barricade_level": "controlled_entry_exit_points"},
            diversion_plan_json={"strategy": "weather_buffered_hotspot_bypass"},
            emergency_corridor_json={"priority": "high_protection"},
            logistics_impact_json={"impact_level": "high"},
            action_confidence_ledger_json=[],
            recommended_action_summary="Deploy 10 officers in corridor ring control posture with controlled entry exit barricades and weather buffered hotspot bypass operations.",
        )
    )
    session.add_all(
        [
            CitizenReport(
                report_source="citizen",
                report_type="road_blockage",
                latitude=12.9715,
                longitude=77.5944,
                severity="High",
                description="Heavy slowdown at the junction",
                language="en",
                source_language="en",
                translated_description="Heavy slowdown at the junction",
                translation_provider="disabled",
                translation_status="not_required",
                event_id="POST-001",
                matched_event_id="POST-001",
                location_match_confidence=0.91,
                report_confidence=0.74,
                impact_score_change=9.0,
                new_alert_level="Warning",
                recommended_action="Move reserve officers upstream",
                status="accepted",
            ),
            CitizenReport(
                report_source="field_officer",
                report_type="crowd_buildup",
                latitude=12.9714,
                longitude=77.5943,
                severity="Critical",
                description="Crowd building near upstream junction",
                language="en",
                source_language="en",
                translated_description="Crowd building near upstream junction",
                translation_provider="disabled",
                translation_status="not_required",
                event_id="POST-001",
                matched_event_id="POST-001",
                location_match_confidence=0.95,
                report_confidence=0.88,
                impact_score_change=14.0,
                new_alert_level="Critical",
                recommended_action="Activate diversion plan",
                status="accepted",
            ),
            CitizenReport(
                report_source="control_room",
                report_type="waterlogging",
                latitude=12.9717,
                longitude=77.5945,
                severity="High",
                description="Waterlogging pressure at low-lying approach",
                language="en",
                source_language="en",
                translated_description="Waterlogging pressure at low-lying approach",
                translation_provider="disabled",
                translation_status="not_required",
                event_id="POST-001",
                matched_event_id="POST-001",
                location_match_confidence=0.93,
                report_confidence=0.81,
                impact_score_change=11.0,
                new_alert_level="Critical",
                recommended_action="Extend barricade taper",
                status="accepted",
            ),
        ]
    )
    session.add_all(
        [
            LiveEventUpdate(
                event_id="POST-001",
                update_source="field_officer",
                current_congestion_level="Warning",
                field_update="Crowd spillover at upstream junction",
                road_closure_active=True,
                officer_shortage=False,
                crowd_increase=True,
                rain_waterlogging=True,
                new_nearby_incident=False,
                expected_impact_score=78.0,
                current_impact_score=89.0,
                impact_deviation=11.0,
                alert_level="Critical",
                adaptive_action="Activate the stored diversion plan",
            ),
            LiveEventUpdate(
                event_id="POST-001",
                update_source="control_room",
                current_congestion_level="Critical",
                field_update="Waterlogging expanded near the corridor edge",
                road_closure_active=True,
                officer_shortage=True,
                crowd_increase=True,
                rain_waterlogging=True,
                new_nearby_incident=False,
                expected_impact_score=78.0,
                current_impact_score=94.0,
                impact_deviation=16.0,
                alert_level="Critical",
                adaptive_action="Reallocate reserve officers immediately",
            ),
        ]
    )
    session.commit()


def test_generate_post_event_report_builds_learning_record():
    session_factory = _build_session_factory()

    with session_factory() as session:
        _seed_post_event_bundle(session)
        record = generate_post_event_report(session, "POST-001", commit=False)
        session.commit()
        session.refresh(record)

        assert record.event_id == "POST-001"
        assert float(record.predicted_impact_score) == 78.0
        assert float(record.simulated_actual_impact_score) == 94.0
        assert float(record.impact_deviation) == 16.0
        assert "Predicted Critical impact" in record.prediction_summary
        assert "10 officers" in record.recommendation_summary
        assert "3 linked reports" in str(record.citizen_report_summary)
        assert "2 live updates" in str(record.live_escalation_summary)
        assert "Multiple reports reinforced" in record.lessons_learned
        assert "Weather-aware planning changed" in record.lessons_learned
        assert record.report_json["report_count"] == 3
        assert record.report_json["critical_live_update_count"] == 2


def test_generate_post_event_report_uses_latest_recommendation_snapshot():
    session_factory = _build_session_factory()

    with session_factory() as session:
        _seed_post_event_bundle(session)
        recommendation = session.query(EventRecommendation).filter(EventRecommendation.event_id == "POST-001").one()
        recommendation.recommended_total_officers = 18
        recommendation.deployment_plan_json = {
            "recommended_total_officers": 18,
            "deployment_style": "incident_command_posture",
            "officer_gap": 2,
        }
        recommendation.barricade_plan_json = {
            "barricade_level": "extended_buffer_with_slow_speed_channelization"
        }
        recommendation.diversion_plan_json = {"strategy": "weather_buffered_hotspot_bypass"}
        recommendation.recommended_action_summary = (
            "Deploy 18 officers in incident command posture around Central Spine. "
            "Use extended buffer with slow speed channelization and weather buffered hotspot bypass operations."
        )
        session.commit()

        record = generate_post_event_report(session, "POST-001", commit=False)
        session.commit()
        session.refresh(record)

        assert record.recommendation_summary == recommendation.recommended_action_summary
        assert "18 officers" in record.recommendation_summary
        assert "incident command posture" in record.recommendation_summary


def test_post_event_report_route_persists_report_and_audit_log():
    session_factory = _build_session_factory()
    actor_id = uuid4()

    with session_factory() as session:
        _seed_post_event_bundle(session)
        _seed_actor(session, actor_id=actor_id, role="control_room")

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[routes_post_event.require_post_event_access] = lambda: AuthContext(
        firebase_uid="control-room-post-event",
        email="control@example.com",
        role="control_room",
        user_account_id=str(actor_id),
    )

    try:
        with TestClient(app) as client:
            response = client.post("/api/events/POST-001/post-event-report")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["event_id"] == "POST-001"
    assert payload["predicted_impact_score"] == 78.0
    assert payload["simulated_actual_impact_score"] == 94.0
    assert payload["impact_deviation"] == 16.0
    assert payload["report_json"]["report_count"] == 3
    assert "future playbook" in payload["future_recommendations"].casefold() or "future" in payload["future_recommendations"].casefold()

    with session_factory() as session:
        assert session.query(PostEventReport).count() == 1
        assert session.query(SystemAuditLog).filter(SystemAuditLog.action == "post_event_report_generate").count() == 1


def test_post_event_report_route_rejects_unassigned_officer():
    session_factory = _build_session_factory()
    actor_id = uuid4()

    with session_factory() as session:
        _seed_post_event_bundle(session)
        _seed_actor(session, actor_id=actor_id, role="police_officer")

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[routes_post_event.require_post_event_access] = lambda: AuthContext(
        firebase_uid="officer-post-event",
        email="officer@example.com",
        role="police_officer",
        user_account_id=str(actor_id),
        officer_profile_id=str(uuid4()),
        officer_id="BTP-POST-001",
        police_station="Whitefield",
        assigned_corridors=["Outer Ring Road"],
        assigned_zones=["East"],
    )

    try:
        with TestClient(app) as client:
            response = client.post("/api/events/POST-001/post-event-report")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "OFFICER_ASSIGNMENT_REQUIRED"


