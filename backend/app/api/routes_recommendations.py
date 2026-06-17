from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.recommendation_contracts import EventPlanRequest, RecommendationPlanResponse
from app.core.officer_access import coerce_uuid, officer_has_event_access
from app.core.security import AuthContext, require_role
from app.db.session import get_db
from app.orm.event import Event
from app.orm.event_feature import EventFeature
from app.orm.event_prediction import EventPrediction
from app.orm.system_audit_log import SystemAuditLog
from app.services.feature_engineering_service import build_features_for_event
from app.services.prediction_service import predict_event
from app.services.recommendation_orchestrator import (
    build_recommendation_input,
    generate_recommendation_plan,
    persist_recommendation_plan,
)
from app.services.weather_service import resolve_weather_adjustment

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


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


def require_recommendation_access(
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


def _record_recommendation_audit_log(
    db: Session,
    auth: AuthContext,
    *,
    event_id: str,
    available_officers: int | None,
    include_logistics_impact: bool,
    include_emergency_corridor: bool,
    weather_adjustment: dict[str, object] | None = None,
) -> None:
    db.add(
        SystemAuditLog(
            actor_user_id=coerce_uuid(auth.user_account_id),
            actor_role=auth.role,
            action="recommendation_plan_generate",
            resource_type="event_recommendations",
            resource_id=event_id,
            metadata_json={
                "available_officers": available_officers,
                "include_logistics_impact": include_logistics_impact,
                "include_emergency_corridor": include_emergency_corridor,
                "weather_source": (
                    str(weather_adjustment.get("source"))
                    if weather_adjustment is not None and weather_adjustment.get("source") is not None
                    else None
                ),
                "weather_reason_codes": list(weather_adjustment.get("reason_codes", [])) if weather_adjustment else [],
            },
        )
    )


@router.post("/event-plan", response_model=RecommendationPlanResponse)
def generate_event_plan(
    payload: EventPlanRequest,
    auth: AuthContext = Depends(require_recommendation_access),
    db: Session = Depends(get_db),
):
    event = db.get(Event, payload.event_id)
    if event is None:
        return error_response(404, "EVENT_NOT_FOUND", "Requested event was not found.", {"event_id": payload.event_id})
    if not officer_has_event_access(db, auth, event):
        return error_response(
            403,
            "OFFICER_ASSIGNMENT_REQUIRED",
            "Officer is not assigned to the requested event, corridor, station, or zone.",
            {"event_id": payload.event_id},
        )

    try:
        feature = _get_primary_feature(db, event.id)
        if feature is None:
            feature, _feature_created = build_features_for_event(db, event, commit=False)

        weather_requested = (
            payload.weather_condition is not None
            or payload.rain_mm is not None
            or payload.visibility_m is not None
            or payload.use_live_weather
        )
        persisted_prediction = _get_primary_prediction(db, event.id)
        if persisted_prediction is None:
            persisted_prediction, _prediction_created = predict_event(
                db,
                event,
                feature=feature,
                commit=False,
                persist=True,
            )

        weather_adjustment = (
            resolve_weather_adjustment(
                float(event.latitude),
                float(event.longitude),
                weather_condition=payload.weather_condition,
                rain_mm=payload.rain_mm,
                visibility_m=payload.visibility_m,
                use_live_weather=payload.use_live_weather,
                source_context="event_plan",
            )
            if weather_requested
            else None
        )
        prediction_for_plan = persisted_prediction
        if weather_requested:
            prediction_for_plan, _transient_prediction_created = predict_event(
                db,
                event,
                feature=feature,
                weather_condition=payload.weather_condition,
                weather_adjustment_override=weather_adjustment,
                commit=False,
                persist=False,
            )

        recommendation_input = build_recommendation_input(
            event,
            prediction_for_plan,
            available_officers=payload.available_officers,
            include_logistics_impact=payload.include_logistics_impact,
            include_emergency_corridor=payload.include_emergency_corridor,
        )
        plan = generate_recommendation_plan(recommendation_input)
        persist_recommendation_plan(
            db,
            plan,
            commit=False,
            persist=True,
        )
        _record_recommendation_audit_log(
            db,
            auth,
            event_id=event.id,
            available_officers=payload.available_officers,
            include_logistics_impact=payload.include_logistics_impact,
            include_emergency_corridor=payload.include_emergency_corridor,
            weather_adjustment=weather_adjustment or dict(persisted_prediction.weather_adjustment_json or {}),
        )
        db.commit()
        return RecommendationPlanResponse.model_validate(plan)
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for recommendation generation.")
