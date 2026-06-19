from dataclasses import dataclass
from typing import Any

from fastapi import Depends, Header, HTTPException, status

from app.db.session import get_db
from app.core.roles import role_allowed
from app.orm.police_officer_profile import PoliceOfficerProfile
from app.orm.user_account import UserAccount

try:
    import firebase_admin
    from firebase_admin import auth as firebase_auth
except ModuleNotFoundError:  # pragma: no cover - exercised before dependency install
    firebase_admin = None
    firebase_auth = None

try:
    from sqlalchemy.orm import Session
except ModuleNotFoundError:  # pragma: no cover - exercised before dependency install
    Session = Any


@dataclass(frozen=True)
class AuthContext:
    firebase_uid: str
    email: str | None
    role: str
    user_account_id: str
    officer_profile_id: str | None = None
    officer_id: str | None = None
    police_station: str | None = None
    assigned_corridors: list[str] | None = None
    assigned_zones: list[str] | None = None


def verify_firebase_token(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict[str, Any]:
    if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "MISSING_FIREBASE_TOKEN"},
        )

    if firebase_admin is None or firebase_auth is None or not firebase_admin._apps:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "FIREBASE_NOT_CONFIGURED"},
        )

    token = authorization.removeprefix("Bearer ").strip()
    try:
        return firebase_auth.verify_id_token(token, check_revoked=True)
    except firebase_auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "REVOKED_FIREBASE_TOKEN"},
        ) from None
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_FIREBASE_TOKEN"},
        ) from None


def load_auth_context(db: Session, token_payload: dict[str, Any]) -> AuthContext:
    account = (
        db.query(UserAccount)
        .filter(UserAccount.auth_provider == "firebase")
        .filter(UserAccount.auth_provider_uid == token_payload["uid"])
        .first()
    )
    if not account or not account.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "INACTIVE_ACCOUNT"},
        )

    officer_profile = None
    if account.role == "police_officer":
        officer_profile = (
            db.query(PoliceOfficerProfile)
            .filter(PoliceOfficerProfile.user_account_id == account.id)
            .filter(PoliceOfficerProfile.active.is_(True))
            .first()
        )
        if not officer_profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "OFFICER_PROFILE_REQUIRED"},
            )

    return AuthContext(
        firebase_uid=token_payload["uid"],
        email=token_payload.get("email"),
        role=account.role,
        user_account_id=str(account.id),
        officer_profile_id=str(officer_profile.id) if officer_profile else None,
        officer_id=officer_profile.officer_id if officer_profile else None,
        police_station=officer_profile.police_station if officer_profile else None,
        assigned_corridors=officer_profile.assigned_corridors_json if officer_profile else None,
        assigned_zones=officer_profile.assigned_zones_json if officer_profile else None,
    )


def get_auth_context(
    token_payload: dict[str, Any] = Depends(verify_firebase_token),
    db: Session = Depends(get_db),
) -> AuthContext:
    return load_auth_context(db, token_payload)


def require_role(*allowed_roles: str):
    def dependency(
        token_payload: dict[str, Any] = Depends(verify_firebase_token),
        db: Session = Depends(get_db),
    ) -> AuthContext:
        auth = load_auth_context(db, token_payload)
        if not role_allowed(auth.role, allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN_ROLE"},
            )
        return auth

    return dependency
