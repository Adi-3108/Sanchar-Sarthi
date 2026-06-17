from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.feature_pipeline import (
    PRIORITY_MODEL_NAME,
    PRIORITY_MODEL_PATH,
    ROAD_CLOSURE_MODEL_NAME,
    RESOLUTION_TIME_MODEL_NAME,
    build_priority_feature_row,
    latest_model_run,
)
from app.orm.event import Event
from app.orm.event_feature import EventFeature
from app.orm.hotspot_cluster import HotspotCluster
from app.orm.event_prediction import EventPrediction
from app.services.impact_score_service import build_impact_assessment
from app.services.resolution_time_service import predict_resolution_time
from app.services.road_closure_scoring_service import estimate_road_closure_likelihood
from app.services.similar_event_service import SimilarEventMatch, find_similar_events


def _safe_float(value: Decimal | float | int | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().casefold()
    return normalized or None


def _fallback_urgency(event: Event, feature: EventFeature | None = None) -> float:
    score = 0.25
    priority = _normalize_text(event.priority)
    if priority in {"high", "critical"}:
        score += 0.35
    elif priority == "medium":
        score += 0.12
    if event.requires_road_closure:
        score += 0.2
    if event.event_type == "unplanned":
        score += 0.1
    if feature and feature.is_peak_hour:
        score += 0.05
    return min(score, 1.0)


def _predict_priority_probability(
    event: Event,
    feature: EventFeature | None = None,
) -> tuple[float | None, dict[str, Any] | None, str | None]:
    if not PRIORITY_MODEL_PATH.exists():
        return None, None, None

    try:
        import joblib  # type: ignore[import-not-found]
        import pandas as pd  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        return None, None, "priority_ml_dependency_missing"

    try:
        bundle: dict[str, Any] = joblib.load(PRIORITY_MODEL_PATH)
        frame = pd.DataFrame([build_priority_feature_row(event, feature)])
        probability = float(bundle["pipeline"].predict_proba(frame)[0][1])
        return probability, bundle, None
    except Exception:
        return None, None, "priority_ml_unavailable"


def _get_or_create_prediction_record(db: Session, event_id: str) -> tuple[EventPrediction, bool]:
    existing_records = db.scalars(
        select(EventPrediction)
        .where(EventPrediction.event_id == event_id)
        .order_by(EventPrediction.created_at.desc(), EventPrediction.id.desc())
    ).all()
    if existing_records:
        record = existing_records[0]
        for duplicate in existing_records[1:]:
            db.delete(duplicate)
        return record, False

    record = EventPrediction(event_id=event_id)
    db.add(record)
    return record, True


def _resolve_hotspot(
    db: Session,
    feature: EventFeature | None,
    hotspot: HotspotCluster | None,
) -> HotspotCluster | None:
    if hotspot is not None or feature is None or not feature.location_cluster_id:
        return hotspot
    return db.scalars(
        select(HotspotCluster).where(HotspotCluster.location_cluster_id == feature.location_cluster_id)
    ).first()


def predict_event(
    db: Session,
    event: Event,
    *,
    feature: EventFeature | None = None,
    hotspot: HotspotCluster | None = None,
    similar_events: list[SimilarEventMatch] | None = None,
    weather_condition: str | None = None,
    commit: bool = True,
) -> tuple[EventPrediction, bool]:
    active_similar_events = similar_events if similar_events is not None else find_similar_events(db, event.id, limit=5)
    active_hotspot = _resolve_hotspot(db, feature, hotspot)
    urgency_probability, priority_bundle, priority_warning = _predict_priority_probability(event, feature)
    priority_model_run = latest_model_run(db, PRIORITY_MODEL_NAME)
    resolution_model_run = latest_model_run(db, RESOLUTION_TIME_MODEL_NAME)
    road_closure_model_run = latest_model_run(db, ROAD_CLOSURE_MODEL_NAME)

    if urgency_probability is None:
        urgency_probability = _fallback_urgency(event, feature)
        priority_method = "rule_fallback"
        dataset_honesty = "Estimated from available ASTraM fields"
    else:
        priority_method = "priority_model"
        dataset_honesty = "Predicted urgency, not exact delay"

    closure = estimate_road_closure_likelihood(db, event, feature=feature)
    resolution = predict_resolution_time(event, feature=feature, db=db)
    predicted_priority = "High" if urgency_probability >= 0.5 else "Low"
    road_closure_probability = float(closure["road_closure_probability"])
    impact_assessment = build_impact_assessment(
        db,
        event=event,
        urgency_score=urgency_probability,
        road_closure_likelihood=road_closure_probability,
        hotspot=active_hotspot,
        similar_events=active_similar_events,
        weather_condition=weather_condition,
    )
    impact = dict(impact_assessment["impact"])
    counterfactual = dict(impact_assessment["counterfactual"])
    weather_adjustment = dict(impact_assessment["weather_adjustment"])
    multi_event_conflict = dict(impact_assessment["multi_event_conflict"])
    if priority_method == "priority_model" and priority_model_run is not None:
        primary_model_run_id = priority_model_run.id
    elif closure.get("supporting_ml_probability") is not None and road_closure_model_run is not None:
        primary_model_run_id = road_closure_model_run.id
    elif (
        resolution["clearance_prediction_method"] == "ml_gradient_boosting"
        and resolution_model_run is not None
    ):
        primary_model_run_id = resolution_model_run.id
    else:
        primary_model_run_id = None

    record, created = _get_or_create_prediction_record(db, event.id)
    record.model_run_id = primary_model_run_id
    record.predicted_priority = predicted_priority
    record.priority_confidence = round(urgency_probability, 4)
    record.road_closure_probability = round(road_closure_probability, 4)
    record.predicted_road_closure = bool(closure["predicted_road_closure"])
    record.estimated_clearance_minutes = float(resolution["estimated_clearance_minutes"])
    record.clearance_prediction_method = str(resolution["clearance_prediction_method"])
    record.clearance_confidence = float(resolution["clearance_confidence"])
    record.clearance_confidence_note = str(resolution["clearance_confidence_note"])
    record.historical_clearance_range_min = float(resolution["historical_clearance_range_min"])
    record.historical_clearance_range_max = float(resolution["historical_clearance_range_max"])
    record.estimated_impact_score = float(impact["estimated_impact_score"])
    record.impact_category = str(impact["impact_category"])
    record.impact_radius_km = float(impact["impact_radius_km"])
    record.vehicle_impact_factor = float(impact["vehicle_impact_factor"])
    record.vehicle_impact_note = str(impact["vehicle_impact_note"])
    record.baseline_risk_score = float(counterfactual["baseline_risk_score"])
    record.additional_event_delta = float(counterfactual["additional_event_delta"])
    record.weather_adjustment_json = weather_adjustment
    record.multi_event_conflict_json = multi_event_conflict
    record.prediction_explanation_json = {
        "priority": {
            "method": priority_method,
            "dataset_honesty": dataset_honesty,
            "probability_high": round(urgency_probability, 4),
            "warning": priority_warning,
            "metrics": dict(priority_bundle.get("metrics", {})) if priority_bundle is not None else {},
            "model_run_id": str(priority_model_run.id) if priority_model_run is not None else None,
        },
        "road_closure": {
            **closure,
            "model_run_id": str(road_closure_model_run.id) if road_closure_model_run is not None else None,
        },
        "resolution_time": {
            **resolution,
            "model_run_id": str(resolution_model_run.id) if resolution_model_run is not None else None,
        },
        "impact": {
            **impact_assessment,
            "model_run_id": str(priority_model_run.id) if priority_model_run is not None else None,
            "counterfactual": counterfactual,
        },
    }
    record.model_version = (
        str(priority_bundle.get("model_version"))
        if priority_bundle is not None and priority_bundle.get("model_version")
        else "priority_rule_or_optional_ml_v1"
    )

    if commit:
        db.commit()
        db.refresh(record)
    else:
        db.flush()

    return record, created


def serialize_event_prediction(record: EventPrediction | None) -> dict[str, object] | None:
    if record is None:
        return None
    return {
        "event_id": record.event_id,
        "model_run_id": str(record.model_run_id) if record.model_run_id is not None else None,
        "predicted_priority": record.predicted_priority,
        "priority_confidence": _safe_float(record.priority_confidence),
        "road_closure_probability": _safe_float(record.road_closure_probability),
        "predicted_road_closure": record.predicted_road_closure,
        "estimated_clearance_minutes": _safe_float(record.estimated_clearance_minutes),
        "clearance_prediction_method": record.clearance_prediction_method,
        "clearance_confidence": _safe_float(record.clearance_confidence),
        "clearance_confidence_note": record.clearance_confidence_note,
        "historical_clearance_range_min": _safe_float(record.historical_clearance_range_min),
        "historical_clearance_range_max": _safe_float(record.historical_clearance_range_max),
        "estimated_impact_score": _safe_float(record.estimated_impact_score),
        "impact_category": record.impact_category,
        "impact_radius_km": _safe_float(record.impact_radius_km),
        "vehicle_impact_factor": _safe_float(record.vehicle_impact_factor),
        "vehicle_impact_note": record.vehicle_impact_note,
        "baseline_risk_score": _safe_float(record.baseline_risk_score),
        "additional_event_delta": _safe_float(record.additional_event_delta),
        "weather_adjustment_json": record.weather_adjustment_json,
        "multi_event_conflict_json": record.multi_event_conflict_json,
        "prediction_explanation_json": record.prediction_explanation_json,
        "model_version": record.model_version,
    }
