from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.roles import canonical_role
from app.core.security import AuthContext
from app.orm.event import Event
from app.orm.officer_event_assignment import OfficerEventAssignment
from app.orm.police_officer_profile import PoliceOfficerProfile


def coerce_uuid(value: str | None) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(value)
    except (ValueError, TypeError):
        return None


def officer_has_event_access(
    db: Session,
    auth: AuthContext,
    event: Event,
) -> bool:
    role = canonical_role(auth.role)
    if role in {"admin", "control_room_officer"}:
        return True

    if auth.police_station and getattr(event, "police_station", None) == auth.police_station:
        return True

    if auth.assigned_corridors and getattr(event, "corridor", None) in auth.assigned_corridors:
        return True

    if auth.assigned_zones and getattr(event, "zone", None) in auth.assigned_zones:
        return True

    user_id = coerce_uuid(auth.user_account_id)
    if not user_id:
        return False

    stmt = (
        select(OfficerEventAssignment.id)
        .join(OfficerEventAssignment.officer_profile)
        .where(
            OfficerEventAssignment.event_id == event.id,
            OfficerEventAssignment.assignment_status == "active",
            PoliceOfficerProfile.user_account_id == user_id,
        )
    )
    return db.scalar(stmt) is not None
