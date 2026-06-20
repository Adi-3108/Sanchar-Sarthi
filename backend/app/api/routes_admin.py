from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import AuthContext, require_role
from app.db.session import get_db
from app.orm.police_officer_profile import PoliceOfficerProfile
from app.orm.system_audit_log import SystemAuditLog
from app.orm.traffic_station import TrafficStation
from app.orm.user_account import UserAccount

try:
    from firebase_admin import auth as firebase_auth
except ModuleNotFoundError:
    firebase_auth = None

router = APIRouter(prefix="/api/admin", tags=["admin"])


class CreateOfficerRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=6, max_length=255)
    officer_id: str = Field(..., min_length=3, max_length=64)
    display_name: str = Field(..., min_length=2, max_length=255)
    rank: str | None = Field(default=None, max_length=128)
    police_station: str = Field(..., min_length=2, max_length=255)
    assigned_corridors: list[str] = Field(default_factory=list)
    assigned_zones: list[str] = Field(default_factory=list)


class CreateOfficerResponse(BaseModel):
    status: str
    officer_id: str
    role: str
    active: bool


class CreateControlRoomRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)
    display_name: str = Field(..., min_length=2, max_length=255)


class CreateControlRoomResponse(BaseModel):
    status: str
    firebase_uid: str
    role: str
    active: bool


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: dict[str, object] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        },
    )


def require_admin_access(
    auth: AuthContext = Depends(require_role("admin", "control_room")),
) -> AuthContext:
    return auth


def _coerce_uuid(value: str | None) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(value)
    except (TypeError, ValueError):
        return None


def _normalize_scope(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        if not normalized:
            continue
        key = normalized.casefold()
        if key in seen:
            continue
        deduped.append(normalized)
        seen.add(key)
    return deduped

class StationResponse(BaseModel):
    id: str
    station_code: str
    name: str

@router.get("/stations", response_model=list[StationResponse])
def get_stations(
    auth: AuthContext = Depends(require_admin_access),
    db: Session = Depends(get_db)
):
    stations = db.scalars(select(TrafficStation).where(TrafficStation.active.is_(True)).order_by(TrafficStation.name)).all()
    return [
        StationResponse(
            id=str(station.id),
            station_code=station.station_code,
            name=station.name
        ) for station in stations
    ]

@router.post("/officers", response_model=CreateOfficerResponse)
def create_officer(
    payload: CreateOfficerRequest,
    auth: AuthContext = Depends(require_admin_access),
    db: Session = Depends(get_db),
):
    if "@" not in payload.email:
        return error_response(
            400,
            "VALIDATION_ERROR",
            "Officer email must be a valid email address.",
            {"field": "email"},
        )

    email = payload.email.strip()
    officer_id = payload.officer_id.strip()
    display_name = payload.display_name.strip()
    police_station = payload.police_station.strip()

    if not email or not officer_id or not display_name or not police_station:
        return error_response(
            400,
            "VALIDATION_ERROR",
            "Officer creation fields cannot be blank.",
        )

    if firebase_auth is None:
        return error_response(503, "FIREBASE_NOT_CONFIGURED", "Firebase Admin SDK is missing.")

    try:
        user_record = firebase_auth.create_user(
            email=email,
            password=payload.password,
            display_name=display_name,
            email_verified=True
        )
        firebase_uid = user_record.uid
    except firebase_auth.EmailAlreadyExistsError:
        try:
            user_record = firebase_auth.get_user_by_email(email)
            firebase_uid = user_record.uid
        except Exception as e:
            return error_response(500, "FIREBASE_ERROR", str(e))
    except Exception as e:
        return error_response(500, "FIREBASE_ERROR", str(e))

    existing_account = db.scalar(
        select(UserAccount).where(UserAccount.auth_provider_uid == firebase_uid)
    )
    if existing_account is not None:
        return error_response(
            409,
            "DUPLICATE_FIREBASE_UID",
            "A user account already exists for this Firebase UID.",
            {"firebase_uid": firebase_uid},
        )

    existing_profile = db.scalar(
        select(PoliceOfficerProfile).where(PoliceOfficerProfile.officer_id == officer_id)
    )
    if existing_profile is not None:
        return error_response(
            409,
            "DUPLICATE_OFFICER_ID",
            "A police officer profile already exists for this officer ID.",
            {"officer_id": officer_id},
        )

    assigned_corridors = _normalize_scope(payload.assigned_corridors)
    assigned_zones = _normalize_scope(payload.assigned_zones)

    try:
        user_account = UserAccount(
            role="police_officer",
            display_name=display_name,
            auth_provider="firebase",
            auth_provider_uid=firebase_uid,
            is_active=True,
        )
        db.add(user_account)
        db.flush()

        officer_profile = PoliceOfficerProfile(
            user_account_id=user_account.id,
            officer_id=officer_id,
            display_name=display_name,
            rank=payload.rank.strip() if isinstance(payload.rank, str) and payload.rank.strip() else None,
            police_station=police_station,
            assigned_corridors_json=assigned_corridors,
            assigned_zones_json=assigned_zones,
            firebase_email=payload.email.strip(),
            active=True,
        )
        db.add(officer_profile)
        db.flush()

        db.add(
            SystemAuditLog(
                actor_user_id=_coerce_uuid(auth.user_account_id),
                actor_role=auth.role,
                action="admin_create_officer",
                resource_type="police_officer_profiles",
                resource_id=str(officer_profile.id),
                metadata_json={
                    "officer_id": officer_profile.officer_id,
                    "firebase_uid": firebase_uid,
                    "email": officer_profile.firebase_email,
                    "police_station": officer_profile.police_station,
                    "assigned_corridors": assigned_corridors,
                    "assigned_zones": assigned_zones,
                },
            )
        )
        db.commit()
        db.refresh(user_account)
        db.refresh(officer_profile)
    except SQLAlchemyError:
        db.rollback()
        return error_response(
            503,
            "DATABASE_UNAVAILABLE",
            "Database is unavailable for officer creation.",
        )

    return CreateOfficerResponse(
        status="created",
        officer_id=officer_profile.officer_id,
        role=user_account.role,
        active=officer_profile.active,
    )

@router.post("/control-room-users", response_model=CreateControlRoomResponse)
def create_control_room_user(
    payload: CreateControlRoomRequest,
    auth: AuthContext = Depends(require_admin_access),
    db: Session = Depends(get_db),
):
    if "@" not in payload.email:
        return error_response(400, "VALIDATION_ERROR", "Email must be valid.", {"field": "email"})
        
    if firebase_auth is None:
        return error_response(503, "FIREBASE_NOT_CONFIGURED", "Firebase Admin SDK is missing.")

    email = payload.email.strip()
    display_name = payload.display_name.strip()
    
    try:
        user_record = firebase_auth.create_user(
            email=email,
            password=payload.password,
            display_name=display_name,
            email_verified=True
        )
        firebase_uid = user_record.uid
    except firebase_auth.EmailAlreadyExistsError:
        try:
            user_record = firebase_auth.get_user_by_email(email)
            firebase_uid = user_record.uid
        except Exception as e:
            return error_response(500, "FIREBASE_ERROR", str(e))
    except Exception as e:
        return error_response(500, "FIREBASE_ERROR", str(e))

    existing_account = db.scalar(
        select(UserAccount).where(UserAccount.auth_provider_uid == firebase_uid)
    )
    if existing_account is not None:
        existing_account.role = "control_room"
        db.commit()
        return CreateControlRoomResponse(
            status="updated",
            firebase_uid=firebase_uid,
            role="control_room",
            active=existing_account.is_active
        )
        
    try:
        user_account = UserAccount(
            role="control_room",
            display_name=display_name,
            auth_provider="firebase",
            auth_provider_uid=firebase_uid,
            is_active=True,
        )
        db.add(user_account)
        
        log = SystemAuditLog(
            actor_user_id=_coerce_uuid(auth.user_account_id),
            actor_role="admin",
            action="create_control_room_user",
            resource_type="user_account",
            resource_id=firebase_uid,
            metadata_json={"email": email},
        )
        db.add(log)
        
        db.commit()
        
        return CreateControlRoomResponse(
            status="created",
            firebase_uid=firebase_uid,
            role="control_room",
            active=True
        )
    except SQLAlchemyError as e:
        db.rollback()
        return error_response(500, "DATABASE_ERROR", str(e))
