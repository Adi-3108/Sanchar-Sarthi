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
                role="admin",
                display_name="Foundation Admin",
                auth_provider="firebase",
                auth_provider_uid="foundation-admin-001",
                is_active=True,
            )
        )
        session.commit()
    return TestClient(app), session_factory


def test_admin_overview_returns_management_entities():
    client, _session_factory = _client()
    app.dependency_overrides[verify_firebase_token] = lambda: {"uid": "foundation-admin-001", "email": "admin@example.com"}
    try:
        response = client.get("/api/foundation/admin/overview")
        assert response.status_code == 200
        payload = response.json()
        assert payload["summary"]["incident_count"] >= 4
        assert payload["users"]
        assert payload["votes"]
        assert payload["logs"]
    finally:
        app.dependency_overrides.clear()


def test_admin_can_update_incident_and_persist_override_prediction():
    client, _session_factory = _client()
    app.dependency_overrides[verify_firebase_token] = lambda: {"uid": "foundation-admin-001", "email": "admin@example.com"}
    try:
        response = client.patch(
            "/api/foundation/admin/incidents/SS-INC-002",
            json={
                "status": "active",
                "severity": "high",
                "police_force_required": 9,
                "barricades_required": 4,
                "route_impact_summary": "Divert traffic through HSR 14th Main until water clears.",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "active"
        assert payload["severity"] == "high"
        assert payload["latest_prediction"]["model_name"] == "foundation_admin_override"
    finally:
        app.dependency_overrides.clear()


def test_admin_can_delete_vote_and_vote_totals_refresh():
    client, _session_factory = _client()
    app.dependency_overrides[verify_firebase_token] = lambda: {"uid": "foundation-admin-001", "email": "admin@example.com"}
    try:
        overview = client.get("/api/foundation/admin/overview")
        vote_id = overview.json()["votes"][0]["id"]
        delete_response = client.delete(f"/api/foundation/admin/votes/{vote_id}")
        assert delete_response.status_code == 200
        refresh = client.get("/api/foundation/admin/overview")
        assert all(vote["id"] != vote_id for vote in refresh.json()["votes"])
    finally:
        app.dependency_overrides.clear()
