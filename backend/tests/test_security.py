import pytest
from fastapi import HTTPException

import app.core.security as security
from app.core.security import AuthContext, get_auth_context, require_role, verify_firebase_token
from app.orm.police_officer_profile import PoliceOfficerProfile
from app.orm.user_account import UserAccount


class FakeQuery:
    def __init__(self, result):
        self._result = result

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self._result


class FakeSession:
    def __init__(self, mapping):
        self.mapping = mapping

    def query(self, model):
        return FakeQuery(self.mapping.get(model))


def test_verify_firebase_token_requires_bearer_header():
    with pytest.raises(HTTPException) as exc_info:
        verify_firebase_token()

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "MISSING_FIREBASE_TOKEN"


def test_verify_firebase_token_requires_initialized_firebase(monkeypatch):
    if security.firebase_admin is not None:
        monkeypatch.setattr(security.firebase_admin, "_apps", [])

    with pytest.raises(HTTPException) as exc_info:
        verify_firebase_token("Bearer demo-token")

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail["code"] == "FIREBASE_NOT_CONFIGURED"


def test_get_auth_context_returns_admin_context():
    db = FakeSession(
        {
            UserAccount: UserAccount(
                id="user-1",
                role="admin",
                is_active=True,
                auth_provider_uid="firebase-user-1",
            )
        }
    )

    context = get_auth_context(
        token_payload={"uid": "firebase-user-1", "email": "admin@example.com"},
        db=db,
    )

    assert context == AuthContext(
        firebase_uid="firebase-user-1",
        email="admin@example.com",
        role="admin",
        user_account_id="user-1",
        officer_profile_id=None,
        officer_id=None,
        police_station=None,
        assigned_corridors=None,
        assigned_zones=None,
    )


def test_get_auth_context_returns_officer_assignment_context():
    db = FakeSession(
        {
            UserAccount: UserAccount(
                id="user-2",
                role="police_officer",
                is_active=True,
                auth_provider_uid="firebase-user-2",
            ),
            PoliceOfficerProfile: PoliceOfficerProfile(
                id="officer-profile-2",
                user_account_id="user-2",
                officer_id="BTP-HSR-001",
                display_name="Officer Demo",
                police_station="HSR Layout",
                assigned_corridors_json=["ORR East 1"],
                assigned_zones_json=["East"],
                active=True,
            ),
        }
    )

    context = get_auth_context(
        token_payload={"uid": "firebase-user-2", "email": "officer@example.com"},
        db=db,
    )

    assert context == AuthContext(
        firebase_uid="firebase-user-2",
        email="officer@example.com",
        role="police_officer",
        user_account_id="user-2",
        officer_profile_id="officer-profile-2",
        officer_id="BTP-HSR-001",
        police_station="HSR Layout",
        assigned_corridors=["ORR East 1"],
        assigned_zones=["East"],
    )


def test_get_auth_context_requires_active_officer_profile():
    db = FakeSession(
        {
            UserAccount: UserAccount(
                id="user-2",
                role="police_officer",
                is_active=True,
                auth_provider_uid="firebase-user-2",
            ),
            PoliceOfficerProfile: None,
        }
    )

    with pytest.raises(HTTPException) as exc_info:
        get_auth_context(
            token_payload={"uid": "firebase-user-2", "email": "officer@example.com"},
            db=db,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "OFFICER_PROFILE_REQUIRED"


def test_require_role_rejects_non_matching_role():
    dependency = require_role("admin", "control_room")
    db = FakeSession(
        {
            UserAccount: UserAccount(
                id="user-3",
                role="public_viewer",
                is_active=True,
                auth_provider_uid="firebase-user-3",
            )
        }
    )

    with pytest.raises(HTTPException) as exc_info:
        dependency(
            token_payload={"uid": "firebase-user-3", "email": "viewer@example.com"},
            db=db,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "FORBIDDEN_ROLE"
