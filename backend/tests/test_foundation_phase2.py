from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import verify_firebase_token
from app.db.base import Base, import_model_modules
from app.db.session import get_db
from app.main import app
from app.orm.user_account import UserAccount
from app.services.foundation_seed_service import seed_foundation_data


def _client():
    import_model_modules()
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_db():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    with session_factory() as session:
        seed_foundation_data(session)
        session.add(
            UserAccount(
                role="control_room_officer",
                display_name="Control Room Demo",
                auth_provider="firebase",
                auth_provider_uid="control-room-demo-001",
                is_active=True,
            )
        )
        session.commit()
    return TestClient(app), session_factory


def test_public_browse_includes_hotspots_and_station_metadata():
    client, _session_factory = _client()
    try:
        response = client.get("/api/foundation/incidents")
        assert response.status_code == 200
        payload = response.json()
        assert payload["hotspots"]
        assert payload["stations"][0]["id"]
        assert payload["incidents"][0]["assigned_station_code"] is not None
    finally:
        app.dependency_overrides.clear()


def test_citizen_can_create_foundation_report():
    client, _session_factory = _client()
    app.dependency_overrides[verify_firebase_token] = lambda: {"uid": "citizen-demo-001", "email": "citizen@example.com"}
    try:
        response = client.post(
            "/api/foundation/incidents/report",
            json={
                "incident_type": "waterlogging",
                "title": "Waterlogging near Richmond Circle",
                "description": "Public movement is slowing near the junction after heavy rain.",
                "severity": "medium",
                "location_name": "Richmond Circle",
                "latitude": 12.9629,
                "longitude": 77.6003,
                "locality": "Richmond Town",
                "ward": "Shantinagar",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "pending_verification"
        assert payload["assigned_station_name"] is not None
        assert payload["latest_prediction"]["model_name"] == "foundation_rule_engine"
    finally:
        app.dependency_overrides.clear()


def test_control_room_can_create_and_resolve_official_incident():
    client, _session_factory = _client()
    app.dependency_overrides[verify_firebase_token] = lambda: {"uid": "control-room-demo-001", "email": "control@example.com"}
    try:
        create_response = client.post(
            "/api/foundation/control-room/incidents",
            json={
                "incident_type": "road_accident",
                "title": "Bus breakdown near Hebbal flyover",
                "description": "A BMTC bus has stalled and is blocking one carriageway.",
                "severity": "high",
                "location_name": "Hebbal Flyover",
                "latitude": 13.0358,
                "longitude": 77.5970,
                "locality": "Hebbal",
                "ward": "Hebbal",
            },
        )
        assert create_response.status_code == 200
        created = create_response.json()
        assert created["status"] == "active"
        assert created["station_alerted"] is True

        transition_response = client.patch(
            f"/api/foundation/control-room/incidents/{created['id']}/status",
            json={"status": "resolved", "resolution_notes": "Traffic normalized and vehicle cleared."},
        )
        assert transition_response.status_code == 200
        updated = transition_response.json()
        assert updated["status"] == "resolved"
        assert updated["resolution_notes"] == "Traffic normalized and vehicle cleared."
    finally:
        app.dependency_overrides.clear()
