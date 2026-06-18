from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.officer_access import coerce_uuid, officer_has_event_access
from app.core.security import AuthContext, require_role
from app.db.session import get_db
from app.orm.citizen_report import CitizenReport
from app.orm.event import Event
from app.orm.event_feature import EventFeature
from app.orm.event_prediction import EventPrediction
from app.orm.live_event_update import LiveEventUpdate
from app.orm.system_audit_log import SystemAuditLog
from app.services.feature_engineering_service import build_features_for_event
from app.services.live_escalation_service import (
    LiveUpdateInput,
    apply_live_update,
    normalize_congestion_level,
    serialize_live_update,
)
from app.services.prediction_service import predict_event

router = APIRouter(prefix="/api/events", tags=["live_updates"])

ALLOWED_CONGESTION_LEVELS = {"Info", "Watch", "Stable", "Warning", "Critical"}


class LiveUpdateRequest(BaseModel):
    current_congestion_level: str = Field(min_length=3, max_length=32)
    field_update: str | None = Field(default=None, max_length=500)
    road_closure_active: bool = False
    officer_shortage: bool = False
    crowd_increase: bool = False
    rain_waterlogging: bool = False
    new_nearby_incident: bool = False

    @field_validator("current_congestion_level", mode="before")
    @classmethod
    def _normalize_congestion_level(cls, value: str) -> str:
        normalized = normalize_congestion_level(str(value))
        if normalized not in ALLOWED_CONGESTION_LEVELS:
            raise ValueError("Unsupported congestion level.")
        return normalized

    @field_validator("field_update", mode="before")
    @classmethod
    def _strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None


class LiveUpdateResponse(BaseModel):
    id: str
    event_id: str
    update_source: str
    current_congestion_level: str
    field_update: str | None = None
    road_closure_active: bool
    officer_shortage: bool
    crowd_increase: bool
    rain_waterlogging: bool
    new_nearby_incident: bool
    expected_impact_score: float
    current_impact_score: float
    impact_deviation: float
    alert_level: str | None = None
    adaptive_action: str | None = None
    honesty_note: str
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


def require_live_update_access(
    auth: AuthContext = Depends(require_role("admin", "control_room", "police_officer")),
) -> AuthContext:
    return auth


def _get_primary_feature(db: Session, event_id: str) -> EventFeature | None:
    return db.scalars(
        select(EventFeature)
        .where(EventFeature.event_id == event_id)
        .order_by(EventFeature.created_at.desc(), EventFeature.id.desc())
    ).first()


def _get_primary_prediction(db: Session, event_id: str) -> EventPrediction | None:
    return db.scalars(
        select(EventPrediction)
        .where(EventPrediction.event_id == event_id)
        .order_by(EventPrediction.created_at.desc(), EventPrediction.id.desc())
    ).first()


def _count_recent_reports(db: Session, event_id: str) -> int:
    reports = db.scalars(
        select(CitizenReport)
        .where(CitizenReport.event_id == event_id)
        .order_by(CitizenReport.created_at.desc(), CitizenReport.id.desc())
        .limit(5)
    ).all()
    return len(reports)


def _resolve_expected_impact_score(db: Session, event: Event) -> float:
    prediction = _get_primary_prediction(db, event.id)
    if prediction is None or prediction.estimated_impact_score is None:
        feature = _get_primary_feature(db, event.id)
        if feature is None:
            feature, _feature_created = build_features_for_event(db, event, commit=False)
        prediction, _prediction_created = predict_event(
            db,
            event,
            feature=feature,
            commit=False,
            persist=True,
        )
    if prediction.estimated_impact_score is None:
        return 0.0
    return float(prediction.estimated_impact_score)


def _update_source_for_role(role: str) -> str:
    if role == "police_officer":
        return "field_officer"
    return "control_room"


def _record_live_update_audit_log(
    db: Session,
    auth: AuthContext,
    *,
    event_id: str,
    update_source: str,
    payload: LiveUpdateRequest,
    response_payload: dict[str, object],
    corroborating_reports: int,
) -> None:
    db.add(
        SystemAuditLog(
            actor_user_id=coerce_uuid(auth.user_account_id),
            actor_role=auth.role,
            action="live_update_submit",
            resource_type="live_event_updates",
            resource_id=event_id,
            metadata_json={
                "update_source": update_source,
                "current_congestion_level": payload.current_congestion_level,
                "road_closure_active": payload.road_closure_active,
                "officer_shortage": payload.officer_shortage,
                "crowd_increase": payload.crowd_increase,
                "rain_waterlogging": payload.rain_waterlogging,
                "new_nearby_incident": payload.new_nearby_incident,
                "impact_deviation": response_payload["impact_deviation"],
                "alert_level": response_payload["alert_level"],
                "corroborating_reports": corroborating_reports,
            },
        )
    )


@router.post("/{event_id}/live-update", response_model=LiveUpdateResponse)
def submit_live_update(
    event_id: str,
    payload: LiveUpdateRequest,
    auth: AuthContext = Depends(require_live_update_access),
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
        expected_impact_score = _resolve_expected_impact_score(db, event)
        corroborating_reports = _count_recent_reports(db, event.id)
        result = apply_live_update(
            LiveUpdateInput(
                current_congestion_level=payload.current_congestion_level,
                field_update=payload.field_update,
                road_closure_active=payload.road_closure_active,
                officer_shortage=payload.officer_shortage,
                crowd_increase=payload.crowd_increase,
                rain_waterlogging=payload.rain_waterlogging,
                new_nearby_incident=payload.new_nearby_incident,
                expected_impact_score=expected_impact_score,
                corroborating_reports=corroborating_reports,
            )
        )
        update_source = _update_source_for_role(auth.role)
        record = LiveEventUpdate(
            event_id=event.id,
            update_source=update_source,
            current_congestion_level=payload.current_congestion_level,
            field_update=payload.field_update,
            road_closure_active=payload.road_closure_active,
            officer_shortage=payload.officer_shortage,
            crowd_increase=payload.crowd_increase,
            rain_waterlogging=payload.rain_waterlogging,
            new_nearby_incident=payload.new_nearby_incident,
            expected_impact_score=float(result["expected_impact_score"]),
            current_impact_score=float(result["current_impact_score"]),
            impact_deviation=float(result["impact_deviation"]),
            alert_level=str(result["alert_level"]),
            adaptive_action=str(result["adaptive_action"]),
        )
        db.add(record)
        db.flush()
        _record_live_update_audit_log(
            db,
            auth,
            event_id=event.id,
            update_source=update_source,
            payload=payload,
            response_payload=result,
            corroborating_reports=corroborating_reports,
        )
        db.commit()
        db.refresh(record)
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for live updates.")

    response_payload = serialize_live_update(record)
    response_payload["honesty_note"] = str(result["honesty_note"])
    return LiveUpdateResponse.model_validate(response_payload)
