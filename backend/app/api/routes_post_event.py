from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.officer_access import coerce_uuid, officer_has_event_access
from app.core.security import AuthContext, require_role
from app.db.session import get_db
from app.orm.event import Event
from app.orm.system_audit_log import SystemAuditLog
from app.services.post_event_report_service import (
    generate_post_event_report,
    serialize_post_event_report,
)

router = APIRouter(prefix="/api/events", tags=["post_event"])


class PostEventReportResponse(BaseModel):
    event_id: str
    predicted_impact_score: float | None = None
    simulated_actual_impact_score: float | None = None
    impact_deviation: float | None = None
    final_status: str | None = None
    event_summary: str
    prediction_summary: str
    recommendation_summary: str
    citizen_report_summary: str | None = None
    live_escalation_summary: str | None = None
    lessons_learned: str
    future_recommendations: str
    report_json: dict[str, object] = Field(default_factory=dict)
    created_at: str | None = None


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


def require_post_event_access(
    auth: AuthContext = Depends(require_role("admin", "control_room", "police_officer")),
) -> AuthContext:
    return auth


def _record_post_event_audit_log(
    db: Session,
    auth: AuthContext,
    *,
    event_id: str,
    response_payload: dict[str, object],
) -> None:
    db.add(
        SystemAuditLog(
            actor_user_id=coerce_uuid(auth.user_account_id),
            actor_role=auth.role,
            action="post_event_report_generate",
            resource_type="post_event_reports",
            resource_id=event_id,
            metadata_json={
                "predicted_impact_score": response_payload.get("predicted_impact_score"),
                "simulated_actual_impact_score": response_payload.get("simulated_actual_impact_score"),
                "impact_deviation": response_payload.get("impact_deviation"),
                "final_status": response_payload.get("final_status"),
                "report_count": dict(response_payload.get("report_json") or {}).get("report_count"),
                "live_update_count": dict(response_payload.get("report_json") or {}).get("live_update_count"),
            },
        )
    )


@router.post("/{event_id}/post-event-report", response_model=PostEventReportResponse)
def generate_post_event_report_route(
    event_id: str,
    auth: AuthContext = Depends(require_post_event_access),
    db: Session = Depends(get_db),
):
    event = db.get(Event, event_id)
    if event is None:
        return error_response(404, "EVENT_NOT_FOUND", "Requested event was not found.", {"event_id": event_id})
    if not officer_has_event_access(db, auth, event):
        return error_response(
            403,
            "OFFICER_ASSIGNMENT_REQUIRED",
            "Officer is not assigned to the requested event, corridor, station, or zone.",
            {"event_id": event_id},
        )

    try:
        record = generate_post_event_report(db, event_id, commit=False)
        response_payload = serialize_post_event_report(record)
        _record_post_event_audit_log(
            db,
            auth,
            event_id=event_id,
            response_payload=response_payload,
        )
        db.commit()
        db.refresh(record)
    except ValueError as exc:
        db.rollback()
        return error_response(404, "EVENT_NOT_FOUND", str(exc), {"event_id": event_id})
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for post-event learning.")

    return PostEventReportResponse.model_validate(serialize_post_event_report(record))
