from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.orm.event import Event
from app.orm.event_dna import EventDna
from app.orm.event_feature import EventFeature
from app.orm.hotspot_cluster import HotspotCluster
from app.services.feature_engineering_service import PEAK_HOURS, build_features_for_event

CAUSE_WEIGHT = {
    "vehicle_breakdown": 0.7,
    "accident": 1.0,
    "road_closure": 0.9,
    "crowd_buildup": 0.8,
    "procession_movement": 0.8,
    "construction": 0.6,
    "waterlogging": 0.85,
    "unknown": 0.4,
}
PRIORITY_WEIGHT = {
    "low": 0.25,
    "medium": 0.5,
    "high": 0.8,
    "critical": 1.0,
}
TEXT_SIGNAL_WEIGHT = {
    "accident": 0.15,
    "junction": 0.08,
    "road": 0.06,
    "rain": 0.08,
    "water": 0.08,
    "traffic": 0.05,
    "vehicle": 0.05,
    "heavy": 0.05,
    "crowd": 0.05,
    "breakdown": 0.05,
}


@dataclass(frozen=True)
class EventDnaContext:
    event: Event
    feature: EventFeature | None
    hotspot: HotspotCluster | None


@dataclass(frozen=True)
class EventDnaRebuildReport:
    events_processed: int
    dna_created: int
    dna_updated: int


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().casefold()
    return normalized or None


def _safe_float(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def _description_signal(event: Event) -> float:
    method = getattr(event, "description_normalization_method", None)
    text = (getattr(event, "description_for_features", None) or "").lower()
    if not text or method == "skipped_low_confidence":
        return 0.0
    return min(sum(weight for token, weight in TEXT_SIGNAL_WEIGHT.items() if token in text), 0.25)


def time_band_label(event: Event, feature: EventFeature | None = None) -> str:
    hour = feature.event_hour if feature and feature.event_hour is not None else event.start_datetime.hour
    weekday = (
        feature.event_weekday
        if feature and feature.event_weekday is not None
        else event.start_datetime.weekday()
    )

    if hour in {8, 9, 10}:
        return "morning_peak"
    if hour in {17, 18, 19, 20}:
        return "evening_peak"
    if hour in {22, 23, 0, 1, 2, 3, 4, 5}:
        return "night"
    if weekday >= 5:
        return "weekend_day"
    return "weekday_day"


def build_event_dna_context(
    event: Event,
    *,
    feature: EventFeature | None = None,
    hotspot: HotspotCluster | None = None,
) -> EventDnaContext:
    return EventDnaContext(
        event=event,
        feature=feature,
        hotspot=hotspot,
    )


def build_event_fingerprint(context: EventDnaContext) -> dict[str, float]:
    event = context.event
    feature = context.feature
    hotspot = context.hotspot
    hour = feature.event_hour if feature and feature.event_hour is not None else event.start_datetime.hour
    return {
        "cause_weight": CAUSE_WEIGHT.get(event.event_cause_clean or "unknown", 0.4),
        "priority_weight": PRIORITY_WEIGHT.get(_normalize_text(event.priority) or "low", 0.25),
        "is_peak_hour": 1.0 if hour in PEAK_HOURS else 0.0,
        "is_weekend": 1.0 if (feature.is_weekend if feature else event.start_datetime.weekday() >= 5) else 0.0,
        "is_night_event": 1.0 if (feature.is_night_event if feature else hour in {22, 23, 0, 1, 2, 3, 4, 5}) else 0.0,
        "closure_flag": 1.0 if event.requires_road_closure else 0.0,
        "unplanned_flag": 1.0 if _normalize_text(event.event_type) == "unplanned" else 0.0,
        "duration_available": 0.0 if feature and feature.duration_source == "unavailable" else 1.0,
        "hotspot_risk": _safe_float(hotspot.cluster_risk_score if hotspot else None),
        "corridor_risk": _safe_float(feature.historical_corridor_risk if feature else None),
        "station_risk": _safe_float(feature.historical_police_station_risk if feature else None),
        "cluster_risk": _safe_float(feature.historical_cluster_risk if feature else None),
        "cause_closure_rate": _safe_float(feature.historical_cause_closure_rate if feature else None),
        "corridor_closure_rate": _safe_float(feature.historical_corridor_closure_rate if feature else None),
        "station_closure_rate": _safe_float(feature.historical_police_station_closure_rate if feature else None),
        "cluster_closure_rate": _safe_float(feature.historical_cluster_closure_rate if feature else None),
        "description_signal": _description_signal(event),
    }


def cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    keys = set(left) | set(right)
    dot = sum(left.get(key, 0.0) * right.get(key, 0.0) for key in keys)
    left_norm = sum(left.get(key, 0.0) ** 2 for key in keys) ** 0.5
    right_norm = sum(right.get(key, 0.0) ** 2 for key in keys) ** 0.5
    return 0.0 if left_norm == 0 or right_norm == 0 else dot / (left_norm * right_norm)


def build_time_context(context: EventDnaContext) -> str:
    event = context.event
    feature = context.feature
    band = time_band_label(event, feature)
    parts = [f"Time band: {band.replace('_', ' ')}."]
    if feature and feature.duration_source:
        if feature.duration_source == "unavailable":
            parts.append("Duration remains dataset-backed as unknown because no reliable end timestamp was available.")
        else:
            parts.append(f"Duration uses {feature.duration_source} fallback from ASTraM timestamps.")
    parts.append(f"Started at hour {event.start_datetime.hour:02d}.")
    return " ".join(parts)


def build_location_context(context: EventDnaContext) -> str:
    event = context.event
    feature = context.feature
    hotspot = context.hotspot
    location_parts = [
        f"Corridor: {event.corridor or 'unknown corridor'}.",
        f"Police station: {event.police_station or 'unknown station'}.",
        f"Zone: {event.zone or 'unknown zone'}.",
        f"Junction: {event.junction or 'unknown junction'}.",
    ]
    if feature and feature.location_cluster_id:
        location_parts.append(f"Location cluster: {feature.location_cluster_id}.")
    if hotspot is not None:
        cluster_type = hotspot.cluster_profile_json.get("cluster_type")
        location_parts.append(
            f"Hotspot profile: {cluster_type or 'dataset-backed'} cluster with risk score {round(float(hotspot.cluster_risk_score) * 100, 1)}."
        )
    return " ".join(location_parts)


def build_cause_context(context: EventDnaContext) -> str:
    event = context.event
    parts = [
        f"Cause: {event.event_cause_clean or event.event_cause or 'unknown'}.",
        f"Event type: {event.event_type or 'unknown'}.",
        f"Priority: {event.priority or 'unknown'}.",
        "Road closure required." if event.requires_road_closure else "No road closure recorded.",
    ]
    if event.description_normalization_method == "skipped_low_confidence":
        parts.append("Description text was preserved for audit but ignored in DNA scoring due to low-confidence normalization.")
    elif event.description_for_features:
        parts.append(f"Description signal used normalized text via {event.description_normalization_method or 'unknown method'}.")
    return " ".join(parts)


def build_historical_pattern(context: EventDnaContext) -> str:
    feature = context.feature
    hotspot = context.hotspot
    if feature is None:
        return "Historical pattern is unavailable until feature engineering has been generated."

    pattern_parts = [
        f"Historical corridor risk: {round(_safe_float(feature.historical_corridor_risk) * 100, 1)}%.",
        f"Historical police-station risk: {round(_safe_float(feature.historical_police_station_risk) * 100, 1)}%.",
        f"Historical cause closure rate: {round(_safe_float(feature.historical_cause_closure_rate) * 100, 1)}%.",
        f"Historical corridor closure rate: {round(_safe_float(feature.historical_corridor_closure_rate) * 100, 1)}%.",
    ]
    if feature.location_cluster_id:
        pattern_parts.append(
            f"Historical cluster closure rate: {round(_safe_float(feature.historical_cluster_closure_rate) * 100, 1)}%."
        )
    if hotspot is not None:
        pattern_parts.append(
            f"Dataset-backed hotspot score: {round(float(hotspot.cluster_risk_score) * 100, 1)} with {hotspot.cluster_event_count} events in the cluster."
        )
    return " ".join(pattern_parts)


def build_risk_indicators_json(context: EventDnaContext) -> dict[str, object]:
    feature = context.feature
    hotspot = context.hotspot
    fingerprint = build_event_fingerprint(context)
    return {
        **fingerprint,
        "time_band": time_band_label(context.event, feature),
        "location_cluster_id": feature.location_cluster_id if feature else None,
        "duration_source": feature.duration_source if feature else None,
        "hotspot_cluster_type": hotspot.cluster_profile_json.get("cluster_type") if hotspot else None,
        "hotspot_radius_km": hotspot.cluster_profile_json.get("radius_km") if hotspot else None,
        "description_normalization_method": context.event.description_normalization_method,
    }


def build_dna_summary(context: EventDnaContext, similar_event_count: int = 0) -> str:
    event = context.event
    hotspot = context.hotspot
    band = time_band_label(event, context.feature).replace("_", " ")
    summary = (
        f"{event.event_cause_clean or event.event_cause or 'unknown event'} "
        f"in {event.corridor or 'unknown corridor'} during {band}."
    )
    if hotspot is not None:
        summary += f" Hotspot risk score is {round(float(hotspot.cluster_risk_score) * 100, 1)}."
    if similar_event_count > 0:
        summary += f" Similar-event memory found {similar_event_count} dataset-backed matches."
    if event.description_normalization_method == "skipped_low_confidence":
        summary += " Description text was ignored for similarity because normalization confidence was low."
    return summary


def _get_or_create_event_dna_record(db: Session, event_id: str) -> tuple[EventDna, bool]:
    existing_records = db.scalars(
        select(EventDna)
        .where(EventDna.event_id == event_id)
        .order_by(EventDna.created_at, EventDna.id)
    ).all()
    if existing_records:
        record = existing_records[0]
        for duplicate in existing_records[1:]:
            db.delete(duplicate)
        return record, False

    record = EventDna(event_id=event_id)
    db.add(record)
    return record, True


def load_event_dna_support_maps(
    db: Session,
    *,
    ensure_feature_for_event: Event | None = None,
) -> tuple[list[Event], dict[str, EventFeature], dict[str, HotspotCluster]]:
    if ensure_feature_for_event is not None:
        feature = db.scalars(
            select(EventFeature)
            .where(EventFeature.event_id == ensure_feature_for_event.id)
            .order_by(EventFeature.created_at, EventFeature.id)
        ).first()
        if feature is None:
            build_features_for_event(db, ensure_feature_for_event, commit=False)

    events = db.scalars(select(Event).order_by(Event.start_datetime, Event.id)).all()
    features = db.scalars(select(EventFeature).order_by(EventFeature.created_at, EventFeature.id)).all()
    hotspots = db.scalars(select(HotspotCluster).order_by(HotspotCluster.cluster_risk_score.desc())).all()
    return (
        events,
        {feature.event_id: feature for feature in features},
        {hotspot.location_cluster_id: hotspot for hotspot in hotspots},
    )


def persist_event_dna(
    db: Session,
    event: Event,
    *,
    feature: EventFeature | None = None,
    hotspot: HotspotCluster | None = None,
    similar_event_ids: list[str] | None = None,
    commit: bool = True,
) -> tuple[EventDna, bool]:
    context = build_event_dna_context(event, feature=feature, hotspot=hotspot)
    record, created = _get_or_create_event_dna_record(db, event.id)
    record.time_context = build_time_context(context)
    record.location_context = build_location_context(context)
    record.cause_context = build_cause_context(context)
    record.weather_context = None
    record.multi_event_context = None
    record.historical_pattern = build_historical_pattern(context)
    record.risk_indicators_json = build_risk_indicators_json(context)
    record.similar_event_ids_json = similar_event_ids or []
    record.dna_summary = build_dna_summary(context, similar_event_count=len(record.similar_event_ids_json))

    if commit:
        db.commit()
        db.refresh(record)
    else:
        db.flush()

    return record, created


def rebuild_event_dna_records(
    db: Session,
    *,
    event_id: str | None = None,
    limit_similar: int = 5,
    refresh_supporting_data: bool = False,
    commit: bool = True,
) -> EventDnaRebuildReport:
    if refresh_supporting_data:
        from app.services.hotspot_service import rebuild_hotspots

        rebuild_hotspots(db, commit=False)

    events, feature_by_event_id, hotspots_by_id = load_event_dna_support_maps(db)
    if not events:
        return EventDnaRebuildReport(events_processed=0, dna_created=0, dna_updated=0)

    target_events = events
    if event_id is not None:
        target_events = [event for event in events if event.id == event_id]
        if not target_events:
            raise ValueError(f"Event not found: {event_id}")

    from app.services.similar_event_service import build_similarity_index, rank_similar_events_for_event

    similarity_index = build_similarity_index(
        events,
        feature_by_event_id=feature_by_event_id,
        hotspots_by_cluster_id=hotspots_by_id,
    )

    dna_created = 0
    dna_updated = 0
    for event in target_events:
        feature = feature_by_event_id.get(event.id)
        hotspot = hotspots_by_id.get(feature.location_cluster_id) if feature and feature.location_cluster_id else None
        matches = rank_similar_events_for_event(event, similarity_index, limit=limit_similar)
        _record, created = persist_event_dna(
            db,
            event,
            feature=feature,
            hotspot=hotspot,
            similar_event_ids=[match.event_id for match in matches],
            commit=False,
        )
        if created:
            dna_created += 1
        else:
            dna_updated += 1

    if commit:
        db.commit()
    else:
        db.flush()

    return EventDnaRebuildReport(
        events_processed=len(target_events),
        dna_created=dna_created,
        dna_updated=dna_updated,
    )


def serialize_event_dna(record: EventDna | None) -> dict[str, Any] | None:
    if record is None:
        return None
    return {
        "event_id": record.event_id,
        "dna_summary": record.dna_summary,
        "time_context": record.time_context,
        "location_context": record.location_context,
        "cause_context": record.cause_context,
        "weather_context": record.weather_context,
        "multi_event_context": record.multi_event_context,
        "historical_pattern": record.historical_pattern,
        "risk_indicators_json": record.risk_indicators_json,
        "similar_event_ids_json": record.similar_event_ids_json,
    }
