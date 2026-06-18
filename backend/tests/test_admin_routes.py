from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

import app.api.routes_admin as routes_admin_module
from app.core.database import build_engine
from app.core.security import AuthContext
from app.db.base import Base, import_model_modules
from app.db.session import get_db
from app.main import app
from app.orm.police_officer_profile import PoliceOfficerProfile
from app.orm.system_audit_log import SystemAuditLog
from app.orm.user_account import UserAccount


def _build_session_factory(tmp_path, name: str):
    engine = build_engine(f"sqlite:///{tmp_path / name}")
    import_model_modules()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def test_create_officer_route_persists_user_profile_and_audit_log(tmp_path):
    session_factory = _build_session_factory(tmp_path, "admin-routes.db")
    actor_id = uuid4()

    with session_factory() as session:
        session.add(
            UserAccount(
                id=actor_id,
                role="admin",
                display_name="Phase 15 Admin",
                auth_provider="firebase",
                auth_provider_uid="firebase-admin-phase15",
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
    app.dependency_overrides[routes_admin_module.require_admin_access] = lambda: AuthContext(
        firebase_uid="firebase-admin-phase15",
        email="admin@example.com",
        role="admin",
        user_account_id=str(actor_id),
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/admin/officers",
                json={
                    "email": "officer.hsr.demo@eventflow.local",
                    "firebase_uid": "firebase-officer-hsr-001",
                    "officer_id": "BTP-HSR-001",
                    "display_name": "Officer Demo",
                    "rank": "Traffic Constable",
                    "police_station": "HSR Layout",
                    "assigned_corridors": ["ORR East 1", "ORR East 1"],
                    "assigned_zones": ["East"],
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "status": "created",
        "officer_id": "BTP-HSR-001",
        "role": "police_officer",
        "active": True,
    }

    with session_factory() as session:
        account = session.query(UserAccount).filter(UserAccount.auth_provider_uid == "firebase-officer-hsr-001").one()
        profile = session.query(PoliceOfficerProfile).filter(PoliceOfficerProfile.user_account_id == account.id).one()
        assert account.role == "police_officer"
        assert profile.officer_id == "BTP-HSR-001"
        assert profile.assigned_corridors_json == ["ORR East 1"]
        assert profile.assigned_zones_json == ["East"]
        assert session.query(SystemAuditLog).filter(SystemAuditLog.action == "admin_create_officer").count() == 1
