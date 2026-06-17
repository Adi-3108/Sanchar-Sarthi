from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.api import routes_events, routes_recommendations
from app.core.database import build_engine
from app.core.security import AuthContext
from app.db.base import Base, import_model_modules
from app.db.session import get_db
from app.main import app
from app.orm.event import Event
from app.orm.event_prediction import EventPrediction
from app.orm.event_recommendation import EventRecommendation
from app.orm.police_officer_profile import PoliceOfficerProfile
from app.orm.system_audit_log import SystemAuditLog
from app.orm.user_account import UserAccount
from app.services import prediction_service, resolution_time_service, road_closure_scoring_service


def _build_session_factory(tmp_path, name: str):
    engine = build_engine(f"sqlite:///{tmp_path / name}")
    import_model_modules()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _seed_recommendation_events(session) -> None:
    start = datetime(2026, 6, 23, 17, 30, tzinfo=timezone.utc)
    session.add_all(
        [
            Event(
                id="REC-001",
                event_type="unplanned",
                latitude=12.9716,
                longitude=77.5946,
                event_cause_clean="vehicle_breakdown",
                requires_road_closure=True,
                start_datetime=start,
                description_language="en",
                description_for_features="heavy vehicle breakdown near major junction",
                description_normalization_method="raw_ascii",
                priority="High",
                corridor="Central Spine",
                police_station="Ashok Nagar",
                zone="Central",
                junction="MG Road",
                veh_type="Truck",
            ),
            Event(
                id="REC-002",
                event_type="planned",
                latitude=12.9722,
                longitude=77.5952,
                event_cause_clean="procession",
                requires_road_closure=False,
                start_datetime=start + timedelta(minutes=20),
                description_language="en",
                description_for_features="planned crowd movement on central spine",
                description_normalization_method="raw_ascii",
                priority="Low",
                corridor="Central Spine",
                police_station="Ashok Nagar",
                zone="Central",
                junction="Brigade Road",
                veh_type="Auto",
            ),
        ]
    )
    session.commit()


def test_event_plan_route_generates_and_persists_recommendation_for_admin(tmp_path, monkeypatch):
    session_factory = _build_session_factory(tmp_path, "recommendations-admin.db")
    actor_id = uuid4()
    monkeypatch.setattr(prediction_service, "PRIORITY_MODEL_PATH", tmp_path / "missing-priority.joblib")
    monkeypatch.setattr(
        road_closure_scoring_service,
        "ROAD_CLOSURE_MODEL_PATH",
        tmp_path / "missing-road-closure.joblib",
    )
    monkeypatch.setattr(
        resolution_time_service,
        "RESOLUTION_TIME_MODEL_PATH",
        tmp_path / "missing-resolution.joblib",
    )

    with session_factory() as session:
        _seed_recommendation_events(session)
        session.add(
            UserAccount(
                id=actor_id,
                role="admin",
                display_name="Recommendation Admin",
                auth_provider="firebase",
                auth_provider_uid="firebase-admin-recommendation",
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
    app.dependency_overrides[routes_recommendations.require_recommendation_access] = lambda: AuthContext(
        firebase_uid="firebase-admin-recommendation",
        email="admin@example.com",
        role="admin",
        user_account_id=str(actor_id),
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/recommendations/event-plan",
                json={
                    "event_id": "REC-001",
                    "available_officers": 7,
                    "include_logistics_impact": True,
                    "include_emergency_corridor": True,
                    "weather_condition": "heavy_rain",
                    "visibility_m": 700,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["event_id"] == "REC-001"
    assert payload["risk_summary"]["impact_category"] in {"Low", "Medium", "High", "Critical"}
    assert payload["weather_risk"]["weather_condition"] == "heavy_rain"
    assert payload["weather_risk"]["low_visibility"] is True
    assert payload["manpower"]["recommended_total_officers"] >= 1
    assert payload["barricades"]["estimated_units"] >= 2
    assert payload["barricades"]["field_note"]
    assert payload["diversions"]["strategy"]
    assert payload["diversions"]["field_note"]
    assert payload["emergency_corridor"]["priority"]
    assert payload["flipkart_logistics_impact"]["impact_level"]
    assert len(payload["action_confidence_ledger"]) >= 4
    assert payload["recommended_action_summary"]

    with session_factory() as session:
        assert session.query(EventPrediction).filter(EventPrediction.event_id == "REC-001").count() == 1
        recommendation = session.query(EventRecommendation).filter(EventRecommendation.event_id == "REC-001").one()
        assert recommendation.recommended_total_officers == payload["manpower"]["recommended_total_officers"]
        assert recommendation.deployment_plan_json["feasibility_status"] == "requires_reallocation"
        assert session.query(SystemAuditLog).filter(SystemAuditLog.action == "recommendation_plan_generate").count() == 1


def test_event_plan_route_allows_assigned_officer(tmp_path, monkeypatch):
    session_factory = _build_session_factory(tmp_path, "recommendations-officer.db")
    actor_id = uuid4()
    profile_id = uuid4()
    monkeypatch.setattr(prediction_service, "PRIORITY_MODEL_PATH", tmp_path / "missing-priority.joblib")
    monkeypatch.setattr(
        road_closure_scoring_service,
        "ROAD_CLOSURE_MODEL_PATH",
        tmp_path / "missing-road-closure.joblib",
    )
    monkeypatch.setattr(
        resolution_time_service,
        "RESOLUTION_TIME_MODEL_PATH",
        tmp_path / "missing-resolution.joblib",
    )

    with session_factory() as session:
        _seed_recommendation_events(session)
        session.add(
            UserAccount(
                id=actor_id,
                role="police_officer",
                display_name="Assigned Officer",
                auth_provider="firebase",
                auth_provider_uid="firebase-assigned-officer",
                is_active=True,
            )
        )
        session.add(
            PoliceOfficerProfile(
                id=profile_id,
                user_account_id=actor_id,
                officer_id="BTP-CENTRAL-001",
                display_name="Assigned Officer",
                police_station="Ashok Nagar",
                assigned_corridors_json=["Central Spine"],
                assigned_zones_json=["Central"],
                active=True,
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
    app.dependency_overrides[routes_recommendations.require_recommendation_access] = lambda: AuthContext(
        firebase_uid="firebase-assigned-officer",
        email="officer@example.com",
        role="police_officer",
        user_account_id=str(actor_id),
        officer_profile_id=str(profile_id),
        officer_id="BTP-CENTRAL-001",
        police_station="Ashok Nagar",
        assigned_corridors=["Central Spine"],
        assigned_zones=["Central"],
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/recommendations/event-plan",
                json={"event_id": "REC-001", "available_officers": 12},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["event_id"] == "REC-001"


def test_event_plan_route_rejects_unassigned_officer(tmp_path):
    session_factory = _build_session_factory(tmp_path, "recommendations-officer-reject.db")
    actor_id = uuid4()
    profile_id = uuid4()

    with session_factory() as session:
        _seed_recommendation_events(session)
        session.add(
            UserAccount(
                id=actor_id,
                role="police_officer",
                display_name="Unassigned Officer",
                auth_provider="firebase",
                auth_provider_uid="firebase-unassigned-officer",
                is_active=True,
            )
        )
        session.add(
            PoliceOfficerProfile(
                id=profile_id,
                user_account_id=actor_id,
                officer_id="BTP-EAST-001",
                display_name="Unassigned Officer",
                police_station="KR Puram",
                assigned_corridors_json=["Outer Ring"],
                assigned_zones_json=["East"],
                active=True,
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
    app.dependency_overrides[routes_recommendations.require_recommendation_access] = lambda: AuthContext(
        firebase_uid="firebase-unassigned-officer",
        email="officer@example.com",
        role="police_officer",
        user_account_id=str(actor_id),
        officer_profile_id=str(profile_id),
        officer_id="BTP-EAST-001",
        police_station="KR Puram",
        assigned_corridors=["Outer Ring"],
        assigned_zones=["East"],
    )

    try:
        with TestClient(app) as client:
            response = client.post("/api/recommendations/event-plan", json={"event_id": "REC-001"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "OFFICER_ASSIGNMENT_REQUIRED"


def test_event_detail_and_simulate_include_recommendations(tmp_path, monkeypatch):
    session_factory = _build_session_factory(tmp_path, "recommendations-events.db")
    actor_id = uuid4()
    monkeypatch.setattr(prediction_service, "PRIORITY_MODEL_PATH", tmp_path / "missing-priority.joblib")
    monkeypatch.setattr(
        road_closure_scoring_service,
        "ROAD_CLOSURE_MODEL_PATH",
        tmp_path / "missing-road-closure.joblib",
    )
    monkeypatch.setattr(
        resolution_time_service,
        "RESOLUTION_TIME_MODEL_PATH",
        tmp_path / "missing-resolution.joblib",
    )

    with session_factory() as session:
        _seed_recommendation_events(session)
        session.add(
            UserAccount(
                id=actor_id,
                role="control_room",
                display_name="Control Room",
                auth_provider="firebase",
                auth_provider_uid="firebase-control-room-rec",
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
        firebase_uid="firebase-control-room-rec",
        email="control@example.com",
        role="control_room",
        user_account_id=str(actor_id),
    )
    app.dependency_overrides[routes_recommendations.require_recommendation_access] = lambda: AuthContext(
        firebase_uid="firebase-control-room-rec",
        email="control@example.com",
        role="control_room",
        user_account_id=str(actor_id),
    )

    try:
        with TestClient(app) as client:
            plan_response = client.post(
                "/api/recommendations/event-plan",
                json={"event_id": "REC-001", "available_officers": 10},
            )
            detail_response = client.get("/api/events/REC-001")
            simulate_response = client.post(
                "/api/events/simulate",
                json={
                    "event_type": "planned",
                    "event_cause": "procession",
                    "latitude": 12.9716,
                    "longitude": 77.5946,
                    "corridor": "MG Road",
                    "police_station": "Ashok Nagar",
                    "zone": "Central",
                    "junction": "Brigade Road",
                    "start_datetime": "2026-06-24T18:00:00Z",
                    "expected_duration_minutes": 120,
                    "expected_crowd_size": 5000,
                    "weather_condition": "heavy_rain",
                    "available_officers": 18,
                    "description": "Large procession expected during evening peak",
                    "veh_type": "Truck",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert plan_response.status_code == 200
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["recommendation"]["event_id"] == "REC-001"
    assert detail_payload["recommendation"]["manpower"]["recommended_total_officers"] >= 1
    assert detail_payload["recommendation"]["risk_summary"]["impact_category"] in {
        "Low",
        "Medium",
        "High",
        "Critical",
    }
    assert detail_payload["recommendation"]["weather_risk"]["weather_condition"] == "clear"

    assert simulate_response.status_code == 200
    simulate_payload = simulate_response.json()
    assert simulate_payload["recommendations"]["event_id"].startswith("SIM-")
    assert simulate_payload["recommendations"]["manpower"]["recommended_total_officers"] >= 1
    assert simulate_payload["recommendations"]["weather_risk"]["weather_condition"] == "heavy_rain"
    assert len(simulate_payload["recommendations"]["action_confidence_ledger"]) >= 4


def test_event_detail_rejects_unassigned_officer(tmp_path):
    session_factory = _build_session_factory(tmp_path, "recommendations-detail-reject.db")
    actor_id = uuid4()
    profile_id = uuid4()

    with session_factory() as session:
        _seed_recommendation_events(session)
        session.add(
            UserAccount(
                id=actor_id,
                role="police_officer",
                display_name="Unassigned Detail Officer",
                auth_provider="firebase",
                auth_provider_uid="firebase-unassigned-detail-officer",
                is_active=True,
            )
        )
        session.add(
            PoliceOfficerProfile(
                id=profile_id,
                user_account_id=actor_id,
                officer_id="BTP-WEST-001",
                display_name="Unassigned Detail Officer",
                police_station="Vijayanagar",
                assigned_corridors_json=["West Link"],
                assigned_zones_json=["West"],
                active=True,
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
        firebase_uid="firebase-unassigned-detail-officer",
        email="officer@example.com",
        role="police_officer",
        user_account_id=str(actor_id),
        officer_profile_id=str(profile_id),
        officer_id="BTP-WEST-001",
        police_station="Vijayanagar",
        assigned_corridors=["West Link"],
        assigned_zones=["West"],
    )

    try:
        with TestClient(app) as client:
            response = client.get("/api/events/REC-001")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "OFFICER_ASSIGNMENT_REQUIRED"
