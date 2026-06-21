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
    return True
