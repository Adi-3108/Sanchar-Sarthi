from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import UUID
from uuid import uuid4

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
from app.orm.event_prediction import EventPrediction
from app.orm.hotspot_cluster import HotspotCluster
from app.orm.system_audit_log import SystemAuditLog
from app.services.data_cleaning_service import clean_event_cause
from app.services.event_dna_service import (
    EventDnaRebuildReport,
    build_event_dna_payload,
    persist_event_dna,
    rebuild_event_dna_records,
    serialize_event_dna,
)
from app.services.feature_engineering_service import (
    build_features_for_event,
    build_historical_feature_stats,
    build_transient_feature,
)
from app.services.prediction_service import predict_event, serialize_event_prediction
from app.services.similar_event_service import find_similar_events, serialize_similar_event_match
from app.services.text_normalization_service import normalize_description


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


class SimilarEventSummaryResponse(BaseModel):
    match_count: int
    top_match_event_id: str | None = None
    average_similarity: float | None = None
    highest_similarity: float | None = None
    top_matched_signals: list[str] = Field(default_factory=list)


class CounterfactualResponse(BaseModel):
    baseline_risk_score: float | None = None
    event_impact_score: float | None = None
    additional_event_delta: float | None = None
    honesty_note: str


class EventSimulationRequest(BaseModel):
    event_type: Literal["planned", "unplanned"] = "planned"
    event_cause: str = Field(min_length=1, max_length=128)
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    corridor: str | None = Field(default=None, max_length=255)
    police_station: str | None = Field(default=None, max_length=255)
    zone: str | None = Field(default=None, max_length=255)
    junction: str | None = Field(default=None, max_length=255)
    start_datetime: datetime
    expected_duration_minutes: int | None = Field(default=None, ge=1, le=1440)
    expected_crowd_size: int | None = Field(default=None, ge=0)
    weather_condition: Literal["clear", "cloudy", "light_rain", "rain", "heavy_rain"] = "clear"
    available_officers: int | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, max_length=2000)
    veh_type: str | None = Field(default=None, max_length=64)


class EventSimulationResponse(BaseModel):
    event_dna: EventDnaResponse
    similar_event_summary: SimilarEventSummaryResponse
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
    counterfactual: CounterfactualResponse
    weather_adjustment: dict[str, object] = Field(default_factory=dict)
    recommendations: dict[str, object] = Field(default_factory=dict)
    map_overlays: dict[str, object] = Field(default_factory=dict)
    prediction_explanation_json: dict[str, object] = Field(default_factory=dict)


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


def _serialize_similar_event_summary(similar_events: list[Any]) -> SimilarEventSummaryResponse:
    if not similar_events:
        return SimilarEventSummaryResponse(match_count=0)

    average_similarity = round(
        sum(float(match.similarity) for match in similar_events) / len(similar_events),
        4,
    )
    top_match = similar_events[0]
    return SimilarEventSummaryResponse(
        match_count=len(similar_events),
        top_match_event_id=top_match.event_id,
        average_similarity=average_similarity,
        highest_similarity=round(float(top_match.similarity), 4),
        top_matched_signals=list(top_match.matched_signals),
    )


def _build_simulated_event(payload: EventSimulationRequest) -> Event:
    normalized_description = normalize_description(payload.description)
    start_datetime = payload.start_datetime
    if start_datetime.tzinfo is None:
        start_datetime = start_datetime.replace(tzinfo=timezone.utc)
    end_datetime = None
    if payload.expected_duration_minutes is not None:
        end_datetime = start_datetime + timedelta(minutes=payload.expected_duration_minutes)

    return Event(
        id=f"SIM-{uuid4().hex[:12].upper()}",
        event_type=payload.event_type,
        latitude=payload.latitude,
        longitude=payload.longitude,
        event_cause=payload.event_cause.strip(),
        event_cause_clean=clean_event_cause(payload.event_cause),
        requires_road_closure=False,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        status="simulated",
        description=normalized_description.raw,
        description_language=normalized_description.language,
        description_for_features=normalized_description.text_for_features,
        description_normalization_method=normalized_description.method,
        veh_type=payload.veh_type.strip() if payload.veh_type and payload.veh_type.strip() else None,
        corridor=payload.corridor.strip() if payload.corridor and payload.corridor.strip() else None,
        police_station=(payload.police_station.strip() if payload.police_station and payload.police_station.strip() else None),
        zone=payload.zone.strip() if payload.zone and payload.zone.strip() else None,
        junction=payload.junction.strip() if payload.junction and payload.junction.strip() else None,
        raw_payload={
            "simulation": True,
            "expected_duration_minutes": payload.expected_duration_minutes,
            "expected_crowd_size": payload.expected_crowd_size,
            "weather_condition": payload.weather_condition,
            "available_officers": payload.available_officers,
        },
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


def _get_primary_prediction(db: Session, event_id: str) -> EventPrediction | None:
    return db.scalars(
        select(EventPrediction)
        .where(EventPrediction.event_id == event_id)
        .order_by(EventPrediction.created_at.desc(), EventPrediction.id.desc())
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
            stats = build_historical_feature_stats(
                db.scalars(select(Event).order_by(Event.start_datetime, Event.id)).all()
            )
            feature = build_transient_feature(event, stats)

        hotspot = None
        if feature and feature.location_cluster_id:
            hotspot = db.scalars(
                select(HotspotCluster).where(HotspotCluster.location_cluster_id == feature.location_cluster_id)
            ).first()

        similar_events = find_similar_events(
            db,
            event_id,
            limit=5,
            feature_override=feature,
            persist_missing_feature=False,
        )
        dna_record = _get_primary_event_dna(db, event_id)
        dna_payload = (
            serialize_event_dna(dna_record)
            if dna_record is not None
            else build_event_dna_payload(
                event,
                feature=feature,
                hotspot=hotspot,
                similar_event_ids=[row.event_id for row in similar_events],
            )
        )
        prediction_record = _get_primary_prediction(db, event_id)
        if prediction_record is not None:
            serialized_prediction = serialize_event_prediction(prediction_record)
        else:
            prediction_record, _prediction_created = predict_event(
                db,
                event,
                feature=feature,
                hotspot=hotspot,
                similar_events=similar_events,
                commit=False,
                persist=False,
            )
            serialized_prediction = serialize_event_prediction(prediction_record)
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for event detail.")

    hotspot_overlay = _serialize_hotspot_overlay(hotspot)
    return EventDossierResponse(
        event=_serialize_event(event),
        features=_serialize_feature(feature),
        event_dna=EventDnaResponse.model_validate(dna_payload),
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


@router.post("/simulate", response_model=EventSimulationResponse)
def simulate_event(
    payload: EventSimulationRequest,
    _auth: AuthContext = Depends(require_internal_event_access),
    db: Session = Depends(get_db),
):
    try:
        simulated_event = _build_simulated_event(payload)
        db.add(simulated_event)
        db.flush()

        feature, _feature_created = build_features_for_event(db, simulated_event, commit=False)
        hotspot = None
        if feature.location_cluster_id:
            hotspot = db.scalars(
                select(HotspotCluster).where(HotspotCluster.location_cluster_id == feature.location_cluster_id)
            ).first()

        similar_events = find_similar_events(db, simulated_event.id, limit=5)
        dna_record, _dna_created = persist_event_dna(
            db,
            simulated_event,
            feature=feature,
            hotspot=hotspot,
            similar_event_ids=[row.event_id for row in similar_events],
            commit=False,
            persist=False,
        )
        prediction_record, _prediction_created = predict_event(
            db,
            simulated_event,
            feature=feature,
            hotspot=hotspot,
            similar_events=similar_events,
            weather_condition=payload.weather_condition,
            commit=False,
            persist=False,
        )
        serialized_prediction = serialize_event_prediction(prediction_record) or {}
        event_dna_payload = serialize_event_dna(dna_record) or {}
        hotspot_overlay = _serialize_hotspot_overlay(hotspot)
        impact_explanation = dict(
            (
                prediction_record.prediction_explanation_json.get("impact", {})
                if prediction_record.prediction_explanation_json
                else {}
            )
            or {}
        )
        counterfactual = dict(impact_explanation.get("counterfactual", {}))
        response = EventSimulationResponse(
            event_dna=EventDnaResponse.model_validate(event_dna_payload),
            similar_event_summary=_serialize_similar_event_summary(similar_events),
            predicted_priority=serialized_prediction.get("predicted_priority"),
            priority_confidence=serialized_prediction.get("priority_confidence"),
            road_closure_probability=serialized_prediction.get("road_closure_probability"),
            predicted_road_closure=serialized_prediction.get("predicted_road_closure"),
            estimated_clearance_minutes=serialized_prediction.get("estimated_clearance_minutes"),
            clearance_prediction_method=serialized_prediction.get("clearance_prediction_method"),
            clearance_confidence=serialized_prediction.get("clearance_confidence"),
            clearance_confidence_note=serialized_prediction.get("clearance_confidence_note"),
            historical_clearance_range_min=serialized_prediction.get("historical_clearance_range_min"),
            historical_clearance_range_max=serialized_prediction.get("historical_clearance_range_max"),
            estimated_impact_score=serialized_prediction.get("estimated_impact_score"),
            impact_category=serialized_prediction.get("impact_category"),
            impact_radius_km=serialized_prediction.get("impact_radius_km"),
            vehicle_impact_factor=serialized_prediction.get("vehicle_impact_factor"),
            vehicle_impact_note=serialized_prediction.get("vehicle_impact_note"),
            counterfactual=CounterfactualResponse(
                baseline_risk_score=serialized_prediction.get("baseline_risk_score"),
                event_impact_score=serialized_prediction.get("estimated_impact_score"),
                additional_event_delta=serialized_prediction.get("additional_event_delta"),
                honesty_note=str(
                    counterfactual.get(
                        "honesty_note",
                        "Delta is a relative operational estimate, not measured vehicle delay.",
                    )
                ),
            ),
            weather_adjustment=dict(serialized_prediction.get("weather_adjustment_json") or {}),
            recommendations={},
            map_overlays={"hotspot": hotspot_overlay.model_dump() if hotspot_overlay else None},
            prediction_explanation_json=dict(serialized_prediction.get("prediction_explanation_json") or {}),
        )
        db.rollback()
        return response
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for event simulation.")


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
