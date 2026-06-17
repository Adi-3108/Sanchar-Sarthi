from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass

from sqlalchemy.orm import Session

from app.orm.event import Event
from app.orm.event_feature import EventFeature
from app.orm.hotspot_cluster import HotspotCluster
from app.services.event_dna_service import (
    EventDnaContext,
    build_event_dna_context,
    build_event_fingerprint,
    cosine_similarity,
    load_event_dna_support_maps,
    time_band_label,
)

STRUCTURED_MATCH_WEIGHTS = {
    "cause_match": 0.18,
    "cluster_match": 0.15,
    "corridor_match": 0.12,
    "police_station_match": 0.10,
    "time_band_match": 0.08,
    "event_type_match": 0.05,
    "road_closure_match": 0.04,
    "priority_match": 0.04,
    "zone_match": 0.02,
    "junction_match": 0.02,
}
VECTOR_SIMILARITY_WEIGHT = 0.20


@dataclass(frozen=True)
class SimilarEventMatch:
    event_id: str
    similarity: float
    matched_signals: list[str]
    event_cause_clean: str | None
    corridor: str | None
    police_station: str | None
    priority: str | None
    event_type: str | None
    requires_road_closure: bool
    hotspot_cluster_id: str | None
    hotspot_risk_score: float | None
    historical_corridor_closure_rate: float | None
    historical_cluster_closure_rate: float | None


@dataclass(frozen=True)
class SimilarityIndex:
    contexts_by_event_id: dict[str, EventDnaContext]
    event_ids_by_cause: dict[str, set[str]]
    event_ids_by_corridor: dict[str, set[str]]
    event_ids_by_station: dict[str, set[str]]
    event_ids_by_cluster: dict[str, set[str]]
    event_ids_by_zone: dict[str, set[str]]
    event_ids_by_junction: dict[str, set[str]]
    event_ids_by_time_band: dict[str, set[str]]


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().casefold()
    return normalized or None


def _safe_float(value: object | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _add_index_value(index: dict[str, set[str]], key: str | None, event_id: str) -> None:
    if key is None:
        return
    index[key].add(event_id)


def build_similarity_index(
    events: list[Event],
    *,
    feature_by_event_id: dict[str, EventFeature],
    hotspots_by_cluster_id: dict[str, HotspotCluster],
) -> SimilarityIndex:
    contexts_by_event_id: dict[str, EventDnaContext] = {}
    event_ids_by_cause: dict[str, set[str]] = defaultdict(set)
    event_ids_by_corridor: dict[str, set[str]] = defaultdict(set)
    event_ids_by_station: dict[str, set[str]] = defaultdict(set)
    event_ids_by_cluster: dict[str, set[str]] = defaultdict(set)
    event_ids_by_zone: dict[str, set[str]] = defaultdict(set)
    event_ids_by_junction: dict[str, set[str]] = defaultdict(set)
    event_ids_by_time_band: dict[str, set[str]] = defaultdict(set)

    for event in events:
        feature = feature_by_event_id.get(event.id)
        hotspot = hotspots_by_cluster_id.get(feature.location_cluster_id) if feature and feature.location_cluster_id else None
        context = build_event_dna_context(event, feature=feature, hotspot=hotspot)
        contexts_by_event_id[event.id] = context

        _add_index_value(event_ids_by_cause, _normalize_text(event.event_cause_clean or event.event_cause), event.id)
        _add_index_value(event_ids_by_corridor, _normalize_text(event.corridor), event.id)
        _add_index_value(event_ids_by_station, _normalize_text(event.police_station), event.id)
        _add_index_value(event_ids_by_cluster, _normalize_text(feature.location_cluster_id if feature else None), event.id)
        _add_index_value(event_ids_by_zone, _normalize_text(event.zone), event.id)
        _add_index_value(event_ids_by_junction, _normalize_text(event.junction), event.id)
        event_ids_by_time_band[time_band_label(event, feature)].add(event.id)

    return SimilarityIndex(
        contexts_by_event_id=contexts_by_event_id,
        event_ids_by_cause=dict(event_ids_by_cause),
        event_ids_by_corridor=dict(event_ids_by_corridor),
        event_ids_by_station=dict(event_ids_by_station),
        event_ids_by_cluster=dict(event_ids_by_cluster),
        event_ids_by_zone=dict(event_ids_by_zone),
        event_ids_by_junction=dict(event_ids_by_junction),
        event_ids_by_time_band=dict(event_ids_by_time_band),
    )


def _candidate_event_ids(target_context: EventDnaContext, index: SimilarityIndex) -> set[str]:
    target_event = target_context.event
    target_feature = target_context.feature
    target_candidates: set[str] = set()
    lookups = (
        (index.event_ids_by_cause, _normalize_text(target_event.event_cause_clean or target_event.event_cause)),
        (index.event_ids_by_corridor, _normalize_text(target_event.corridor)),
        (index.event_ids_by_station, _normalize_text(target_event.police_station)),
        (index.event_ids_by_cluster, _normalize_text(target_feature.location_cluster_id if target_feature else None)),
        (index.event_ids_by_zone, _normalize_text(target_event.zone)),
        (index.event_ids_by_junction, _normalize_text(target_event.junction)),
        (index.event_ids_by_time_band, time_band_label(target_event, target_feature)),
    )
    for mapping, key in lookups:
        if key is None:
            continue
        target_candidates.update(mapping.get(key, set()))
    target_candidates.discard(target_event.id)

    if target_candidates:
        return target_candidates

    # Fallback for sparse events so similarity retrieval still returns evidence when available.
    return set(index.contexts_by_event_id) - {target_event.id}


def _match_score(target: EventDnaContext, candidate: EventDnaContext) -> tuple[float, list[str]]:
    target_event = target.event
    candidate_event = candidate.event
    target_feature = target.feature
    candidate_feature = candidate.feature

    signals = {
        "cause_match": _normalize_text(target_event.event_cause_clean or target_event.event_cause)
        == _normalize_text(candidate_event.event_cause_clean or candidate_event.event_cause),
        "cluster_match": _normalize_text(target_feature.location_cluster_id if target_feature else None)
        == _normalize_text(candidate_feature.location_cluster_id if candidate_feature else None),
        "corridor_match": _normalize_text(target_event.corridor) == _normalize_text(candidate_event.corridor),
        "police_station_match": _normalize_text(target_event.police_station) == _normalize_text(candidate_event.police_station),
        "time_band_match": time_band_label(target_event, target_feature) == time_band_label(candidate_event, candidate_feature),
        "event_type_match": _normalize_text(target_event.event_type) == _normalize_text(candidate_event.event_type),
        "road_closure_match": target_event.requires_road_closure == candidate_event.requires_road_closure,
        "priority_match": _normalize_text(target_event.priority) == _normalize_text(candidate_event.priority),
        "zone_match": _normalize_text(target_event.zone) == _normalize_text(candidate_event.zone),
        "junction_match": _normalize_text(target_event.junction) == _normalize_text(candidate_event.junction),
    }

    structured_score = sum(
        STRUCTURED_MATCH_WEIGHTS[key]
        for key, matched in signals.items()
        if matched
    )
    vector_similarity = cosine_similarity(
        build_event_fingerprint(target),
        build_event_fingerprint(candidate),
    )
    similarity = min(structured_score + vector_similarity * VECTOR_SIMILARITY_WEIGHT, 1.0)
    matched_signals = [
        key.removesuffix("_match").replace("_", " ")
        for key, matched in signals.items()
        if matched
    ]
    if vector_similarity >= 0.75:
        matched_signals.append("operational fingerprint")
    return round(similarity, 4), matched_signals


def rank_similar_events_for_event(
    event: Event,
    index: SimilarityIndex,
    *,
    limit: int = 5,
) -> list[SimilarEventMatch]:
    target_context = index.contexts_by_event_id.get(event.id)
    if target_context is None:
        return []

    candidate_ids = _candidate_event_ids(target_context, index)
    if len(candidate_ids) < limit:
        candidate_ids.update(set(index.contexts_by_event_id) - {event.id})

    matches: list[SimilarEventMatch] = []
    for candidate_id in candidate_ids:
        candidate_context = index.contexts_by_event_id[candidate_id]
        similarity, matched_signals = _match_score(target_context, candidate_context)
        candidate_feature = candidate_context.feature
        candidate_hotspot = candidate_context.hotspot
        matches.append(
            SimilarEventMatch(
                event_id=candidate_id,
                similarity=similarity,
                matched_signals=matched_signals,
                event_cause_clean=candidate_context.event.event_cause_clean,
                corridor=candidate_context.event.corridor,
                police_station=candidate_context.event.police_station,
                priority=candidate_context.event.priority,
                event_type=candidate_context.event.event_type,
                requires_road_closure=candidate_context.event.requires_road_closure,
                hotspot_cluster_id=candidate_feature.location_cluster_id if candidate_feature else None,
                hotspot_risk_score=_safe_float(candidate_hotspot.cluster_risk_score if candidate_hotspot else None),
                historical_corridor_closure_rate=_safe_float(
                    candidate_feature.historical_corridor_closure_rate if candidate_feature else None
                ),
                historical_cluster_closure_rate=_safe_float(
                    candidate_feature.historical_cluster_closure_rate if candidate_feature else None
                ),
            )
        )

    return sorted(
        matches,
        key=lambda match: (
            -match.similarity,
            match.event_id,
        ),
    )[:limit]


def _find_similar_events(
    db: Session,
    event: Event,
    *,
    limit: int,
    feature_override: EventFeature | None = None,
    persist_missing_feature: bool = True,
) -> list[SimilarEventMatch]:
    if feature_override is None and persist_missing_feature:
        events, feature_by_event_id, hotspots_by_cluster_id = load_event_dna_support_maps(
            db,
            ensure_feature_for_event=event,
        )
    else:
        events, feature_by_event_id, hotspots_by_cluster_id = load_event_dna_support_maps(db)
        if feature_override is not None:
            feature_by_event_id[event.id] = feature_override

    index = build_similarity_index(
        events,
        feature_by_event_id=feature_by_event_id,
        hotspots_by_cluster_id=hotspots_by_cluster_id,
    )
    return rank_similar_events_for_event(event, index, limit=limit)


def find_similar_events(
    db: Session,
    event_id: str,
    *,
    limit: int = 5,
    feature_override: EventFeature | None = None,
    persist_missing_feature: bool = True,
) -> list[SimilarEventMatch]:
    event = db.get(Event, event_id)
    if event is None:
        return []

    return _find_similar_events(
        db,
        event,
        limit=limit,
        feature_override=feature_override,
        persist_missing_feature=persist_missing_feature,
    )


def serialize_similar_event_match(match: SimilarEventMatch) -> dict[str, object]:
    return asdict(match)
