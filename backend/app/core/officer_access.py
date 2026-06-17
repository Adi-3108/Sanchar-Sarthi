from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.security import AuthContext
from app.orm.event import Event
from app.orm.officer_event_assignment import OfficerEventAssignment


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
    if auth.role in {"admin", "control_room"}:
        return True
    if auth.role != "police_officer":
        return False

    officer_profile_id = coerce_uuid(auth.officer_profile_id)
    if officer_profile_id is not None:
        conditions = [OfficerEventAssignment.event_id == event.id]
        if event.corridor:
            conditions.append(OfficerEventAssignment.corridor == event.corridor)
        if event.police_station:
            conditions.append(OfficerEventAssignment.police_station == event.police_station)
        explicit_assignment = db.scalars(
            select(OfficerEventAssignment)
            .where(
                OfficerEventAssignment.officer_profile_id == officer_profile_id,
                OfficerEventAssignment.assignment_status == "active",
                or_(*conditions),
            )
            .order_by(OfficerEventAssignment.created_at.desc(), OfficerEventAssignment.id.desc())
        ).first()
        if explicit_assignment is not None:
            return True

    assigned_corridors = {value.strip().casefold() for value in (auth.assigned_corridors or []) if value}
    assigned_zones = {value.strip().casefold() for value in (auth.assigned_zones or []) if value}
    if event.corridor and event.corridor.strip().casefold() in assigned_corridors:
        return True
    if event.zone and event.zone.strip().casefold() in assigned_zones:
        return True
    if (
        auth.police_station
        and event.police_station
        and auth.police_station.strip().casefold() == event.police_station.strip().casefold()
    ):
        return True
    return False
