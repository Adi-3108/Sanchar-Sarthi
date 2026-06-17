from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.orm.event import Event
from app.orm.event_feature import EventFeature
from app.utils.datetime_utils import duration_minutes, first_valid_timestamp
from app.utils.masking_utils import is_empty

PEAK_HOURS = frozenset({8, 9, 10, 17, 18, 19, 20})
NIGHT_HOURS = frozenset({22, 23, 0, 1, 2, 3, 4, 5})
MAX_LOCATION_CLUSTER_ID_LENGTH = 128


@dataclass(frozen=True)
class HistoricalFeatureStats:
    total_events: int
    cause_counts: dict[str, int]
    cause_closures: dict[str, int]
    corridor_counts: dict[str, int]
    corridor_closures: dict[str, int]
    police_station_counts: dict[str, int]
    police_station_closures: dict[str, int]
    cluster_counts: dict[str, int]
    cluster_closures: dict[str, int]


@dataclass(frozen=True)
class FeatureRebuildReport:
    events_processed: int
    features_created: int
    features_updated: int
    duration_unavailable: int


def _normalized_key(value: str | None) -> str | None:
    if is_empty(value):
        return None
    return str(value).strip().casefold()


def _slugify(value: str | None) -> str | None:
    if is_empty(value):
        return None
    normalized = re.sub(r"[^a-z0-9]+", "_", str(value).strip().casefold())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or None


def build_location_cluster_id(event: Event) -> str | None:
    zone = _slugify(event.zone)
    junction = _slugify(event.junction)
    route_path = _slugify(event.route_path)
    corridor = _slugify(event.corridor)
    police_station = _slugify(event.police_station)

    candidates = [
        f"zone:{zone}|junction:{junction}" if zone and junction else None,
        f"route:{route_path}" if route_path else None,
        f"corridor:{corridor}|station:{police_station}" if corridor and police_station else None,
        f"zone:{zone}" if zone else None,
        f"junction:{junction}" if junction else None,
        f"corridor:{corridor}" if corridor else None,
        f"station:{police_station}" if police_station else None,
        f"geo:{event.latitude:.3f}:{event.longitude:.3f}",
    ]

    for candidate in candidates:
        if candidate:
            return candidate[:MAX_LOCATION_CLUSTER_ID_LENGTH]
    return None


def best_duration_timestamp(event: Event) -> tuple[datetime | None, str]:
    return first_valid_timestamp(
        event.start_datetime,
        (
            ("end_datetime", event.end_datetime),
            ("closed_datetime", event.closed_datetime),
            ("resolved_datetime", event.resolved_datetime),
        ),
    )


def build_historical_feature_stats(events: list[Event]) -> HistoricalFeatureStats:
    # These dataset-wide aggregates support the current MVP analytics and prototype ML flows.
    # Before claiming production-grade validation, training/evaluation should switch to time-aware splits.
    cause_counts: Counter[str] = Counter()
    cause_closures: Counter[str] = Counter()
    corridor_counts: Counter[str] = Counter()
    corridor_closures: Counter[str] = Counter()
    police_station_counts: Counter[str] = Counter()
    police_station_closures: Counter[str] = Counter()
    cluster_counts: Counter[str] = Counter()
    cluster_closures: Counter[str] = Counter()

    for event in events:
        is_closed = bool(event.requires_road_closure)

        cause_key = _normalized_key(event.event_cause_clean or event.event_cause)
        if cause_key:
            cause_counts[cause_key] += 1
            if is_closed:
                cause_closures[cause_key] += 1

        corridor_key = _normalized_key(event.corridor)
        if corridor_key:
            corridor_counts[corridor_key] += 1
            if is_closed:
                corridor_closures[corridor_key] += 1

        police_station_key = _normalized_key(event.police_station)
        if police_station_key:
            police_station_counts[police_station_key] += 1
            if is_closed:
                police_station_closures[police_station_key] += 1

        cluster_key = _normalized_key(build_location_cluster_id(event))
        if cluster_key:
            cluster_counts[cluster_key] += 1
            if is_closed:
                cluster_closures[cluster_key] += 1

    return HistoricalFeatureStats(
        total_events=len(events),
        cause_counts=dict(cause_counts),
        cause_closures=dict(cause_closures),
        corridor_counts=dict(corridor_counts),
        corridor_closures=dict(corridor_closures),
        police_station_counts=dict(police_station_counts),
        police_station_closures=dict(police_station_closures),
        cluster_counts=dict(cluster_counts),
        cluster_closures=dict(cluster_closures),
    )


def _historical_risk(total_events: int, counts: dict[str, int], key: str | None) -> float | None:
    normalized = _normalized_key(key)
    if total_events <= 0 or normalized is None:
        return None
    return round(counts.get(normalized, 0) / total_events, 4)


def _historical_closure_rate(
    counts: dict[str, int],
    closures: dict[str, int],
    key: str | None,
) -> float | None:
    normalized = _normalized_key(key)
    if normalized is None:
        return None

    total_count = counts.get(normalized, 0)
    if total_count <= 0:
        return None

    return round(closures.get(normalized, 0) / total_count, 4)


def build_feature_payload(
    event: Event,
    stats: HistoricalFeatureStats,
) -> dict[str, object]:
    duration_end, duration_source = best_duration_timestamp(event)
    location_cluster_id = build_location_cluster_id(event)
    weekday = event.start_datetime.weekday()
    hour = event.start_datetime.hour
    cause_key = event.event_cause_clean or event.event_cause

    return {
        "event_hour": hour,
        "event_day": event.start_datetime.day,
        "event_month": event.start_datetime.month,
        "event_weekday": weekday,
        "is_weekend": weekday >= 5,
        "is_peak_hour": hour in PEAK_HOURS,
        "is_night_event": hour in NIGHT_HOURS,
        "event_duration_minutes": duration_minutes(event.start_datetime, duration_end),
        "closure_duration_minutes": duration_minutes(event.start_datetime, event.closed_datetime),
        "resolution_duration_minutes": duration_minutes(event.start_datetime, event.resolved_datetime),
        "duration_source": duration_source,
        "has_zone": _normalized_key(event.zone) is not None,
        "has_junction": _normalized_key(event.junction) is not None,
        "has_route_path": _normalized_key(event.route_path) is not None,
        "has_vehicle_type": _normalized_key(event.veh_type) is not None,
        "location_cluster_id": location_cluster_id,
        "historical_corridor_risk": _historical_risk(
            stats.total_events,
            stats.corridor_counts,
            event.corridor,
        ),
        "historical_police_station_risk": _historical_risk(
            stats.total_events,
            stats.police_station_counts,
            event.police_station,
        ),
        "historical_cluster_risk": _historical_risk(
            stats.total_events,
            stats.cluster_counts,
            location_cluster_id,
        ),
        "historical_cause_closure_rate": _historical_closure_rate(
            stats.cause_counts,
            stats.cause_closures,
            cause_key,
        ),
        "historical_corridor_closure_rate": _historical_closure_rate(
            stats.corridor_counts,
            stats.corridor_closures,
            event.corridor,
        ),
        "historical_police_station_closure_rate": _historical_closure_rate(
            stats.police_station_counts,
            stats.police_station_closures,
            event.police_station,
        ),
        "historical_cluster_closure_rate": _historical_closure_rate(
            stats.cluster_counts,
            stats.cluster_closures,
            location_cluster_id,
        ),
    }


def build_transient_feature(
    event: Event,
    stats: HistoricalFeatureStats,
) -> EventFeature:
    return EventFeature(
        event_id=event.id,
        **build_feature_payload(event, stats),
    )


def _get_or_create_feature_record(db: Session, event_id: str) -> tuple[EventFeature, bool]:
    existing_records = db.scalars(
        select(EventFeature)
        .where(EventFeature.event_id == event_id)
        .order_by(EventFeature.created_at, EventFeature.id)
    ).all()

    if existing_records:
        feature = existing_records[0]
        for duplicate in existing_records[1:]:
            db.delete(duplicate)
        return feature, False

    feature = EventFeature(event_id=event_id)
    db.add(feature)
    return feature, True


def build_features_for_event(
    db: Session,
    event: Event,
    *,
    stats: HistoricalFeatureStats | None = None,
    commit: bool = True,
) -> tuple[EventFeature, bool]:
    active_stats = stats
    if active_stats is None:
        active_stats = build_historical_feature_stats(db.scalars(select(Event)).all())

    feature_values = build_feature_payload(event, active_stats)
    feature, created = _get_or_create_feature_record(db, event.id)
    for field_name, value in feature_values.items():
        setattr(feature, field_name, value)

    if commit:
        db.commit()
        db.refresh(feature)
    else:
        db.flush()

    return feature, created


def rebuild_event_features(
    db: Session,
    *,
    event_id: str | None = None,
    commit: bool = True,
) -> FeatureRebuildReport:
    all_events = db.scalars(select(Event).order_by(Event.start_datetime, Event.id)).all()
    if not all_events:
        return FeatureRebuildReport(
            events_processed=0,
            features_created=0,
            features_updated=0,
            duration_unavailable=0,
        )

    target_events = all_events
    if event_id is not None:
        target_events = [event for event in all_events if event.id == event_id]
        if not target_events:
            raise ValueError(f"Event not found: {event_id}")

    stats = build_historical_feature_stats(all_events)
    features_created = 0
    features_updated = 0
    duration_unavailable = 0

    for event in target_events:
        feature, created = build_features_for_event(db, event, stats=stats, commit=False)
        if created:
            features_created += 1
        else:
            features_updated += 1
        if feature.duration_source == "unavailable":
            duration_unavailable += 1

    if commit:
        db.commit()
    else:
        db.flush()

    return FeatureRebuildReport(
        events_processed=len(target_events),
        features_created=features_created,
        features_updated=features_updated,
        duration_unavailable=duration_unavailable,
    )
