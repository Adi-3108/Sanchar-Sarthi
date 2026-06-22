from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.officer_access import coerce_uuid, officer_has_event_access
from app.core.security import AuthContext, require_role
from app.db.session import get_db
from app.orm.citizen_report import CitizenReport
from app.orm.event import Event
from app.orm.officer_event_assignment import OfficerEventAssignment
from app.orm.police_officer_profile import PoliceOfficerProfile

router = APIRouter(prefix="/api/officer", tags=["officer"])


class OfficerLoginResponse(BaseModel):
    role: str
    firebase_uid: str
    officer_id: str | None = None
    police_station: str | None = None
    assigned_corridors: list[str] = []
    assigned_zones: list[str] = []


class OfficerAssignedEventResponse(BaseModel):
    id: str
    event_cause_clean: str | None = None
    priority: str | None = None
    status: str | None = None
    corridor: str | None = None
    police_station: str | None = None
    zone: str | None = None
    junction: str | None = None
    start_datetime: datetime


class OfficerPendingReportResponse(BaseModel):
    id: str
    report_type: str
    severity: str | None = None
    matched_event_id: str | None = None
    created_at: datetime | None = None
    new_alert_level: str | None = None
    report_confidence: float | None = None


class OfficerAssignmentsResponse(BaseModel):
    officer_id: str
    police_station: str
    assigned_events: list[OfficerAssignedEventResponse]
    assigned_corridors: list[str]
    assigned_zones: list[str]
    pending_report_confirmations: list[OfficerPendingReportResponse]
    map_overlays: dict[str, Any]


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


def require_officer_access(
    auth: AuthContext = Depends(require_role("police_officer")),
) -> AuthContext:
    return auth


def _serialize_event(event: Event) -> OfficerAssignedEventResponse:
    return OfficerAssignedEventResponse(
        id=event.id,
        event_cause_clean=event.event_cause_clean,
        priority=event.priority,
        status=event.status,
        corridor=event.corridor,
        police_station=event.police_station,
        zone=event.zone,
        junction=event.junction,
        start_datetime=event.start_datetime,
    )


def _build_fallback_event_query(auth: AuthContext):
    conditions = []
    if auth.assigned_corridors:
        conditions.append(Event.corridor.in_(auth.assigned_corridors))
    if auth.assigned_zones:
        conditions.append(Event.zone.in_(auth.assigned_zones))
    if auth.police_station:
        conditions.append(Event.police_station == auth.police_station)
    if not conditions:
        return None
    return select(Event).where(or_(*conditions)).order_by(Event.start_datetime.desc(), Event.id.desc())


def _load_profile(db: Session, auth: AuthContext) -> PoliceOfficerProfile | None:
    officer_profile_id = coerce_uuid(auth.officer_profile_id)
    if officer_profile_id is not None:
        profile = db.get(PoliceOfficerProfile, officer_profile_id)
        if profile is not None and profile.active:
            return profile

    profile = db.scalar(
        select(PoliceOfficerProfile)
        .where(PoliceOfficerProfile.user_account_id == coerce_uuid(auth.user_account_id))
        .where(PoliceOfficerProfile.active.is_(True))
    )
    return None


@router.post("/login", response_model=OfficerLoginResponse)
def login_officer(
    auth: AuthContext = Depends(require_officer_access),
    db: Session = Depends(get_db),
):
    profile = _load_profile(db, auth)
    if profile is None:
        return error_response(
            403,
            "OFFICER_PROFILE_REQUIRED",
            "Active officer profile is required to login as an officer.",
        )

    return OfficerLoginResponse(
        role=auth.role,
        firebase_uid=auth.firebase_uid,
        officer_id=profile.officer_id,
        police_station=profile.police_station,
        assigned_corridors=list(profile.assigned_corridors_json or []),
        assigned_zones=list(profile.assigned_zones_json or []),
    )


@router.get("/assignments", response_model=OfficerAssignmentsResponse)
def get_officer_assignments(
    auth: AuthContext = Depends(require_officer_access),
    db: Session = Depends(get_db),
):
    profile = _load_profile(db, auth)
    if profile is None:
        return error_response(
            403,
            "OFFICER_PROFILE_REQUIRED",
            "Active officer profile is required for officer assignment access.",
        )

    explicit_assignments = db.scalars(
        select(OfficerEventAssignment)
        .options(joinedload(OfficerEventAssignment.event))
        .where(OfficerEventAssignment.officer_profile_id == profile.id)
        .where(OfficerEventAssignment.assignment_status == "active")
        .order_by(OfficerEventAssignment.created_at.desc(), OfficerEventAssignment.id.desc())
    ).all()

    assigned_events: dict[str, Event] = {}
    for assignment in explicit_assignments:
        if assignment.event is not None and officer_has_event_access(db, auth, assignment.event):
            assigned_events.setdefault(assignment.event.id, assignment.event)

    fallback_query = _build_fallback_event_query(auth)
    if fallback_query is None:
        # Bypassing scope checks: return some recent events instead of nothing
        fallback_query = select(Event).order_by(Event.start_datetime.desc(), Event.id.desc())
        
    fallback_events = db.scalars(fallback_query.limit(10)).all()
    for event in fallback_events:
        if officer_has_event_access(db, auth, event):
            assigned_events.setdefault(event.id, event)

    ordered_events = sorted(
        assigned_events.values(),
        key=lambda item: (item.start_datetime, item.id),
        reverse=True,
    )

    event_ids = [event.id for event in ordered_events]
    pending_reports: list[OfficerPendingReportResponse] = []
    if event_ids:
        reports = db.scalars(
            select(CitizenReport)
            .where(
                or_(
                    CitizenReport.event_id.in_(event_ids),
                    CitizenReport.matched_event_id.in_(event_ids),
                )
            )
            .where(CitizenReport.report_source == "citizen")
            .order_by(CitizenReport.created_at.desc(), CitizenReport.id.desc())
            .limit(12)
        ).all()
        pending_reports = [
            OfficerPendingReportResponse(
                id=str(report.id),
                report_type=report.report_type,
                severity=report.severity,
                matched_event_id=report.matched_event_id,
                created_at=report.created_at,
                new_alert_level=report.new_alert_level,
                report_confidence=float(report.report_confidence) if report.report_confidence is not None else None,
            )
            for report in reports
        ]

    return OfficerAssignmentsResponse(
        officer_id=profile.officer_id,
        police_station=profile.police_station,
        assigned_events=[_serialize_event(event) for event in ordered_events],
        assigned_corridors=list(profile.assigned_corridors_json or []),
        assigned_zones=list(profile.assigned_zones_json or []),
        pending_report_confirmations=pending_reports,
        map_overlays={
            "assigned_event_points": [
                {
                    "id": event.id,
                    "latitude": event.latitude,
                    "longitude": event.longitude,
                    "priority": event.priority,
                    "corridor": event.corridor,
                }
                for event in ordered_events
            ],
            "assigned_corridors": list(profile.assigned_corridors_json or []),
            "assigned_zones": list(profile.assigned_zones_json or []),
            "police_station": profile.police_station,
        },
    )
