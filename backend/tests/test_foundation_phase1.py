from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import AuthContext
from app.db.base import Base, import_model_modules
from app.db.session import get_db
from app.main import app
from app.orm.incident import can_transition_incident
from app.services.foundation_seed_service import seed_foundation_data
from app.services.incident_service import apply_incident_vote


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
    return TestClient(app), session_factory


def test_foundation_public_browse_and_seed_data():
    client, _session_factory = _client()
    try:
        response = client.get("/api/foundation/incidents")
        assert response.status_code == 200
        payload = response.json()
        assert len(payload["incidents"]) == 4
        assert len(payload["stations"]) == 4
        assert "pending_verification" in payload["statuses"]
    finally:
        app.dependency_overrides.clear()


def test_control_room_route_requires_authentication():
    client, _session_factory = _client()
    try:
        response = client.get("/api/foundation/control-room")
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "MISSING_FIREBASE_TOKEN"
    finally:
        app.dependency_overrides.clear()


def test_incident_lifecycle_rules():
    assert can_transition_incident("pending_verification", "active")
    assert can_transition_incident("active", "resolved")
    assert not can_transition_incident("resolved", "pending_verification")


def test_vote_threshold_promotes_pending_incident():
    from app.orm.incident import Incident

    incident = Incident(
        id="TEST-INCIDENT",
        incident_type="roadblock",
        title="Test incident",
        status="pending_verification",
        severity="medium",
        location_name="Test location",
        latitude=12.97,
        longitude=77.59,
        source_type="user",
        true_vote_count=4,
        false_vote_count=0,
        confidence_score=0.8,
    )
    apply_incident_vote(incident, "true")
    assert incident.status == "active"
