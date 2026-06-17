from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import AuthContext, require_role
from app.db.session import get_db
from app.orm.event import Event
from app.orm.event_dna import EventDna
from app.orm.event_feature import EventFeature
from app.orm.hotspot_cluster import HotspotCluster
from app.orm.system_audit_log import SystemAuditLog
from app.services.event_dna_service import (
    EventDnaRebuildReport,
    persist_event_dna,
    rebuild_event_dna_records,
    serialize_event_dna,
)
from app.services.feature_engineering_service import build_features_for_event
from app.services.prediction_service import predict_event, serialize_event_prediction
from app.services.similar_event_service import find_similar_events, serialize_similar_event_match


class EventRecordResponse(BaseModel):
    id: str
    event_type: str | None = None
    event_cause_clean: str | None = None
    priority: str | None = None
    status: str | None = None
    corridor: str | None = None
    police_station: str | None = None
    zone: str | None = None
    junction: str | None = None
    requires_road_closure: bool
    start_datetime: datetime
    end_datetime: datetime | None = None
    description_language: str
    description_normalization_method: str | None = None
    veh_type: str | None = None


class EventFeatureResponse(BaseModel):
    event_hour: int | None = None
    event_day: int | None = None
    event_month: int | None = None
    event_weekday: int | None = None
    is_weekend: bool
    is_peak_hour: bool
    is_night_event: bool
    event_duration_minutes: float | None = None
    closure_duration_minutes: float | None = None
    resolution_duration_minutes: float | None = None
    duration_source: str | None = None
    location_cluster_id: str | None = None
    historical_corridor_risk: float | None = None
    historical_police_station_risk: float | None = None
    historical_cluster_risk: float | None = None
    historical_cause_closure_rate: float | None = None
    historical_corridor_closure_rate: float | None = None
    historical_police_station_closure_rate: float | None = None
    historical_cluster_closure_rate: float | None = None


class EventDnaResponse(BaseModel):
    event_id: str
    dna_summary: str
    time_context: str
    location_context: str
    cause_context: str
    weather_context: str | None = None
    multi_event_context: str | None = None
    historical_pattern: str
    risk_indicators_json: dict[str, object]
    similar_event_ids_json: list[str]


class SimilarEventResponse(BaseModel):
    event_id: str
    similarity: float
    matched_signals: list[str]
    event_cause_clean: str | None = None
    corridor: str | None = None
    police_station: str | None = None
    priority: str | None = None
    event_type: str | None = None
    requires_road_closure: bool
    hotspot_cluster_id: str | None = None
    hotspot_risk_score: float | None = None
    historical_corridor_closure_rate: float | None = None
    historical_cluster_closure_rate: float | None = None


class HotspotOverlayResponse(BaseModel):
    location_cluster_id: str
    centroid_latitude: float
    centroid_longitude: float
    cluster_event_count: int
    cluster_risk_score: float
    cluster_type: str | None = None
    radius_km: float | None = None
    cluster_top_event_cause: str | None = None


class EventPredictionResponse(BaseModel):
    event_id: str
    model_run_id: str | None = None
    predicted_priority: str | None = None
    priority_confidence: float | None = None
    road_closure_probability: float | None = None
    predicted_road_closure: bool | None = None
    estimated_clearance_minutes: float | None = None
    clearance_prediction_method: str | None = None
    clearance_confidence: float | None = None
    clearance_confidence_note: str | None = None
    historical_clearance_range_min: float | None = None
    historical_clearance_range_max: float | None = None
    estimated_impact_score: float | None = None
    impact_category: str | None = None
    impact_radius_km: float | None = None
    vehicle_impact_factor: float | None = None
    vehicle_impact_note: str | None = None
    baseline_risk_score: float | None = None
    additional_event_delta: float | None = None
    weather_adjustment_json: dict[str, object] | None = None
    multi_event_conflict_json: dict[str, object] | None = None
    prediction_explanation_json: dict[str, object] = Field(default_factory=dict)
    model_version: str | None = None


class EventDossierResponse(BaseModel):
    event: EventRecordResponse
    features: EventFeatureResponse | None = None
    event_dna: EventDnaResponse | None = None
    prediction: EventPredictionResponse | None = None
    recommendation: dict[str, object] | None = None
    similar_events: list[SimilarEventResponse] = Field(default_factory=list)
    citizen_reports: list[dict[str, object]] = Field(default_factory=list)
    live_updates: list[dict[str, object]] = Field(default_factory=list)
    map_overlays: dict[str, object] = Field(default_factory=dict)


class EventDnaRebuildResponse(BaseModel):
    status: str
    events_processed: int
    dna_created: int
    dna_updated: int
    message: str | None = None


router = APIRouter(prefix="/api/events", tags=["events"])


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


def require_internal_event_access(
    auth: AuthContext = Depends(require_role("admin", "control_room", "police_officer")),
) -> AuthContext:
    return auth


def require_event_dna_rebuild_access(
    auth: AuthContext = Depends(require_role("admin", "control_room")),
) -> AuthContext:
    return auth


def _coerce_uuid(value: str | None) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(value)
    except (ValueError, TypeError):
        return None


def _serialize_event(event: Event) -> EventRecordResponse:
    return EventRecordResponse(
        id=event.id,
        event_type=event.event_type,
        event_cause_clean=event.event_cause_clean,
        priority=event.priority,
        status=event.status,
        corridor=event.corridor,
        police_station=event.police_station,
        zone=event.zone,
        junction=event.junction,
        requires_road_closure=event.requires_road_closure,
        start_datetime=event.start_datetime,
        end_datetime=event.end_datetime,
        description_language=event.description_language,
        description_normalization_method=event.description_normalization_method,
        veh_type=event.veh_type,
    )


def _serialize_feature(feature: EventFeature | None) -> EventFeatureResponse | None:
    if feature is None:
        return None
    return EventFeatureResponse(
        event_hour=feature.event_hour,
        event_day=feature.event_day,
        event_month=feature.event_month,
        event_weekday=feature.event_weekday,
        is_weekend=feature.is_weekend,
        is_peak_hour=feature.is_peak_hour,
        is_night_event=feature.is_night_event,
        event_duration_minutes=float(feature.event_duration_minutes) if feature.event_duration_minutes is not None else None,
        closure_duration_minutes=float(feature.closure_duration_minutes) if feature.closure_duration_minutes is not None else None,
        resolution_duration_minutes=float(feature.resolution_duration_minutes) if feature.resolution_duration_minutes is not None else None,
        duration_source=feature.duration_source,
        location_cluster_id=feature.location_cluster_id,
        historical_corridor_risk=float(feature.historical_corridor_risk) if feature.historical_corridor_risk is not None else None,
        historical_police_station_risk=float(feature.historical_police_station_risk) if feature.historical_police_station_risk is not None else None,
        historical_cluster_risk=float(feature.historical_cluster_risk) if feature.historical_cluster_risk is not None else None,
        historical_cause_closure_rate=float(feature.historical_cause_closure_rate) if feature.historical_cause_closure_rate is not None else None,
        historical_corridor_closure_rate=float(feature.historical_corridor_closure_rate) if feature.historical_corridor_closure_rate is not None else None,
        historical_police_station_closure_rate=float(feature.historical_police_station_closure_rate) if feature.historical_police_station_closure_rate is not None else None,
        historical_cluster_closure_rate=float(feature.historical_cluster_closure_rate) if feature.historical_cluster_closure_rate is not None else None,
    )


def _serialize_hotspot_overlay(hotspot: HotspotCluster | None) -> HotspotOverlayResponse | None:
    if hotspot is None:
        return None
    return HotspotOverlayResponse(
        location_cluster_id=hotspot.location_cluster_id,
        centroid_latitude=float(hotspot.centroid_latitude),
        centroid_longitude=float(hotspot.centroid_longitude),
        cluster_event_count=hotspot.cluster_event_count,
        cluster_risk_score=float(hotspot.cluster_risk_score),
        cluster_type=hotspot.cluster_profile_json.get("cluster_type"),
        radius_km=hotspot.cluster_profile_json.get("radius_km"),
        cluster_top_event_cause=hotspot.cluster_top_event_cause,
    )


def _get_primary_feature(db: Session, event_id: str) -> EventFeature | None:
    return db.scalars(
        select(EventFeature)
        .where(EventFeature.event_id == event_id)
        .order_by(EventFeature.created_at, EventFeature.id)
    ).first()


def _get_primary_event_dna(db: Session, event_id: str) -> EventDna | None:
    return db.scalars(
        select(EventDna)
        .where(EventDna.event_id == event_id)
        .order_by(EventDna.created_at, EventDna.id)
    ).first()


def _record_event_dna_rebuild_audit_log(
    db: Session,
    auth: AuthContext,
    report: EventDnaRebuildReport,
    *,
    limit_similar: int,
) -> None:
    db.add(
        SystemAuditLog(
            actor_user_id=_coerce_uuid(auth.user_account_id),
            actor_role=auth.role,
            action="event_dna_rebuild",
            resource_type="event_dna",
            resource_id="all-events",
            metadata_json={
                "events_processed": report.events_processed,
                "dna_created": report.dna_created,
                "dna_updated": report.dna_updated,
                "limit_similar": limit_similar,
            },
        )
    )


@router.get("/{event_id}", response_model=EventDossierResponse)
def get_event_detail(
    event_id: str,
    _auth: AuthContext = Depends(require_internal_event_access),
    db: Session = Depends(get_db),
):
    event = db.get(Event, event_id)
    if event is None:
        return error_response(404, "EVENT_NOT_FOUND", "Requested event was not found.", {"event_id": event_id})

    try:
        feature = _get_primary_feature(db, event_id)
        if feature is None:
            feature, _ = build_features_for_event(db, event, commit=False)

        hotspot = None
        if feature and feature.location_cluster_id:
            hotspot = db.scalars(
                select(HotspotCluster).where(HotspotCluster.location_cluster_id == feature.location_cluster_id)
            ).first()

        similar_events = find_similar_events(db, event_id, limit=5)
        dna_record, _created = persist_event_dna(
            db,
            event,
            feature=feature,
            hotspot=hotspot,
            similar_event_ids=[row.event_id for row in similar_events],
            commit=False,
        )
        prediction_record, _prediction_created = predict_event(
            db,
            event,
            feature=feature,
            commit=False,
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for event detail.")

    hotspot_overlay = _serialize_hotspot_overlay(hotspot)
    serialized_prediction = serialize_event_prediction(prediction_record)
    return EventDossierResponse(
        event=_serialize_event(event),
        features=_serialize_feature(feature),
        event_dna=EventDnaResponse.model_validate(serialize_event_dna(dna_record) or {}),
        prediction=(
            EventPredictionResponse.model_validate(serialized_prediction)
            if serialized_prediction is not None
            else None
        ),
        recommendation=None,
        similar_events=[SimilarEventResponse.model_validate(serialize_similar_event_match(row)) for row in similar_events],
        citizen_reports=[],
        live_updates=[],
        map_overlays={"hotspot": hotspot_overlay.model_dump() if hotspot_overlay else None},
    )


@router.post("/rebuild-dna", response_model=EventDnaRebuildResponse)
def rebuild_event_dna(
    limit_similar: int = Query(default=5, ge=1, le=10),
    auth: AuthContext = Depends(require_event_dna_rebuild_access),
    db: Session = Depends(get_db),
):
    try:
        report = rebuild_event_dna_records(
            db,
            limit_similar=limit_similar,
            refresh_supporting_data=True,
            commit=False,
        )
        _record_event_dna_rebuild_audit_log(
            db,
            auth,
            report,
            limit_similar=limit_similar,
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        return error_response(400, "VALIDATION_ERROR", str(exc))
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for Event DNA rebuild.")

    message = "Dataset-backed Event DNA records rebuilt."
    if report.events_processed == 0:
        message = "No events were available for Event DNA rebuild."

    return EventDnaRebuildResponse(
        status="success",
        events_processed=report.events_processed,
        dna_created=report.dna_created,
        dna_updated=report.dna_updated,
        message=message,
    )
