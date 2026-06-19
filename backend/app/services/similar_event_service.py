from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from heapq import nlargest

from sqlalchemy.orm import Session

from app.orm.event import Event
from app.orm.event_feature import EventFeature
from app.orm.hotspot_cluster import HotspotCluster
from app.services.event_dna_service import (
    EventDnaContext,
    build_event_dna_context,
    build_event_fingerprint,
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
SIMILARITY_PREFILTER_MIN = 300
SIMILARITY_PREFILTER_MULTIPLIER = 60


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
class IndexedEventContext:
    context: EventDnaContext
    cause_key: str | None
    corridor_key: str | None
    station_key: str | None
    cluster_key: str | None
    zone_key: str | None
    junction_key: str | None
    time_band: str
    priority_key: str | None
    event_type_key: str | None
    road_closure_key: str
    fingerprint_vector: tuple[float, ...]
    fingerprint_norm: float


@dataclass(frozen=True)
class SimilarityIndex:
    contexts_by_event_id: dict[str, EventDnaContext]
    indexed_contexts_by_event_id: dict[str, IndexedEventContext]
    event_ids_by_cause: dict[str, set[str]]
    event_ids_by_corridor: dict[str, set[str]]
    event_ids_by_station: dict[str, set[str]]
    event_ids_by_cluster: dict[str, set[str]]
    event_ids_by_zone: dict[str, set[str]]
    event_ids_by_junction: dict[str, set[str]]
    event_ids_by_time_band: dict[str, set[str]]
    event_ids_by_priority: dict[str, set[str]]
    event_ids_by_event_type: dict[str, set[str]]
    event_ids_by_road_closure: dict[str, set[str]]


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().casefold()
    return normalized or None


def _safe_float(value: object | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _road_closure_key(value: bool) -> str:
    return "true" if value else "false"


def _add_index_value(index: dict[str, set[str]], key: str | None, event_id: str) -> None:
    if key is None:
        return
    index[key].add(event_id)


def _build_indexed_context(
    event: Event,
    feature: EventFeature | None,
    hotspot: HotspotCluster | None,
) -> IndexedEventContext:
    context = build_event_dna_context(event, feature=feature, hotspot=hotspot)
    fingerprint = build_event_fingerprint(context)
    fingerprint_vector = tuple(float(value) for value in fingerprint.values())
    fingerprint_norm = sum(value * value for value in fingerprint_vector) ** 0.5
    return IndexedEventContext(
        context=context,
        cause_key=_normalize_text(event.event_cause_clean or event.event_cause),
        corridor_key=_normalize_text(event.corridor),
        station_key=_normalize_text(event.police_station),
        cluster_key=_normalize_text(feature.location_cluster_id if feature else None),
        zone_key=_normalize_text(event.zone),
        junction_key=_normalize_text(event.junction),
        time_band=time_band_label(event, feature),
        priority_key=_normalize_text(event.priority),
        event_type_key=_normalize_text(event.event_type),
        road_closure_key=_road_closure_key(event.requires_road_closure),
        fingerprint_vector=fingerprint_vector,
        fingerprint_norm=fingerprint_norm,
    )


def build_similarity_index(
    events: list[Event],
    *,
    feature_by_event_id: dict[str, EventFeature],
    hotspots_by_cluster_id: dict[str, HotspotCluster],
) -> SimilarityIndex:
    contexts_by_event_id: dict[str, EventDnaContext] = {}
    indexed_contexts_by_event_id: dict[str, IndexedEventContext] = {}
    event_ids_by_cause: dict[str, set[str]] = defaultdict(set)
    event_ids_by_corridor: dict[str, set[str]] = defaultdict(set)
    event_ids_by_station: dict[str, set[str]] = defaultdict(set)
    event_ids_by_cluster: dict[str, set[str]] = defaultdict(set)
    event_ids_by_zone: dict[str, set[str]] = defaultdict(set)
    event_ids_by_junction: dict[str, set[str]] = defaultdict(set)
    event_ids_by_time_band: dict[str, set[str]] = defaultdict(set)
    event_ids_by_priority: dict[str, set[str]] = defaultdict(set)
    event_ids_by_event_type: dict[str, set[str]] = defaultdict(set)
    event_ids_by_road_closure: dict[str, set[str]] = defaultdict(set)

    for event in events:
        feature = feature_by_event_id.get(event.id)
        hotspot = hotspots_by_cluster_id.get(feature.location_cluster_id) if feature and feature.location_cluster_id else None
        indexed_context = _build_indexed_context(event, feature, hotspot)
        contexts_by_event_id[event.id] = indexed_context.context
        indexed_contexts_by_event_id[event.id] = indexed_context

        _add_index_value(event_ids_by_cause, indexed_context.cause_key, event.id)
        _add_index_value(event_ids_by_corridor, indexed_context.corridor_key, event.id)
        _add_index_value(event_ids_by_station, indexed_context.station_key, event.id)
        _add_index_value(event_ids_by_cluster, indexed_context.cluster_key, event.id)
        _add_index_value(event_ids_by_zone, indexed_context.zone_key, event.id)
        _add_index_value(event_ids_by_junction, indexed_context.junction_key, event.id)
        event_ids_by_time_band[indexed_context.time_band].add(event.id)
        _add_index_value(event_ids_by_priority, indexed_context.priority_key, event.id)
        _add_index_value(event_ids_by_event_type, indexed_context.event_type_key, event.id)
        event_ids_by_road_closure[indexed_context.road_closure_key].add(event.id)

    return SimilarityIndex(
        contexts_by_event_id=contexts_by_event_id,
        indexed_contexts_by_event_id=indexed_contexts_by_event_id,
        event_ids_by_cause=dict(event_ids_by_cause),
        event_ids_by_corridor=dict(event_ids_by_corridor),
        event_ids_by_station=dict(event_ids_by_station),
        event_ids_by_cluster=dict(event_ids_by_cluster),
        event_ids_by_zone=dict(event_ids_by_zone),
        event_ids_by_junction=dict(event_ids_by_junction),
        event_ids_by_time_band=dict(event_ids_by_time_band),
        event_ids_by_priority=dict(event_ids_by_priority),
        event_ids_by_event_type=dict(event_ids_by_event_type),
        event_ids_by_road_closure=dict(event_ids_by_road_closure),
    )


def _candidate_event_ids(target_context: EventDnaContext, index: SimilarityIndex) -> set[str]:
    target_item = index.indexed_contexts_by_event_id[target_context.event.id]
    target_candidates: set[str] = set()
    lookups = (
        (index.event_ids_by_cause, target_item.cause_key),
        (index.event_ids_by_corridor, target_item.corridor_key),
        (index.event_ids_by_station, target_item.station_key),
        (index.event_ids_by_cluster, target_item.cluster_key),
        (index.event_ids_by_zone, target_item.zone_key),
        (index.event_ids_by_junction, target_item.junction_key),
        (index.event_ids_by_time_band, target_item.time_band),
        (index.event_ids_by_priority, target_item.priority_key),
        (index.event_ids_by_event_type, target_item.event_type_key),
        (index.event_ids_by_road_closure, target_item.road_closure_key),
    )
    for mapping, key in lookups:
        if key is None:
            continue
        target_candidates.update(mapping.get(key, set()))
    target_candidates.discard(target_context.event.id)

    if target_candidates:
        return target_candidates

    return set(index.contexts_by_event_id) - {target_context.event.id}


def _add_candidate_scores(
    scores: dict[str, float],
    candidate_ids: set[str],
    *,
    weight: float,
    target_event_id: str,
) -> None:
    for candidate_id in candidate_ids:
        if candidate_id == target_event_id:
            continue
        scores[candidate_id] = scores.get(candidate_id, 0.0) + weight


def _candidate_structured_scores(target_item: IndexedEventContext, index: SimilarityIndex) -> dict[str, float]:
    scores: dict[str, float] = {}
    lookups = (
        (index.event_ids_by_cause, target_item.cause_key, STRUCTURED_MATCH_WEIGHTS["cause_match"]),
        (index.event_ids_by_cluster, target_item.cluster_key, STRUCTURED_MATCH_WEIGHTS["cluster_match"]),
        (index.event_ids_by_corridor, target_item.corridor_key, STRUCTURED_MATCH_WEIGHTS["corridor_match"]),
        (index.event_ids_by_station, target_item.station_key, STRUCTURED_MATCH_WEIGHTS["police_station_match"]),
        (index.event_ids_by_time_band, target_item.time_band, STRUCTURED_MATCH_WEIGHTS["time_band_match"]),
        (index.event_ids_by_event_type, target_item.event_type_key, STRUCTURED_MATCH_WEIGHTS["event_type_match"]),
        (index.event_ids_by_road_closure, target_item.road_closure_key, STRUCTURED_MATCH_WEIGHTS["road_closure_match"]),
        (index.event_ids_by_priority, target_item.priority_key, STRUCTURED_MATCH_WEIGHTS["priority_match"]),
        (index.event_ids_by_zone, target_item.zone_key, STRUCTURED_MATCH_WEIGHTS["zone_match"]),
        (index.event_ids_by_junction, target_item.junction_key, STRUCTURED_MATCH_WEIGHTS["junction_match"]),
    )
    for mapping, key, weight in lookups:
        if key is None:
            continue
        _add_candidate_scores(
            scores,
            mapping.get(key, set()),
            weight=weight,
            target_event_id=target_item.context.event.id,
        )

    if scores:
        return scores

    return {
        candidate_id: 0.0
        for candidate_id in index.contexts_by_event_id
        if candidate_id != target_item.context.event.id
    }


def _cosine_similarity_from_vectors(
    left_vector: tuple[float, ...],
    left_norm: float,
    right_vector: tuple[float, ...],
    right_norm: float,
) -> float:
    if left_norm == 0 or right_norm == 0:
        return 0.0
    dot = sum(left * right for left, right in zip(left_vector, right_vector))
    return dot / (left_norm * right_norm)


def _match_score(target: IndexedEventContext, candidate: IndexedEventContext) -> tuple[float, list[str]]:
    target_event = target.context.event
    candidate_event = candidate.context.event

    signals = {
        "cause_match": target.cause_key == candidate.cause_key,
        "cluster_match": target.cluster_key == candidate.cluster_key,
        "corridor_match": target.corridor_key == candidate.corridor_key,
        "police_station_match": target.station_key == candidate.station_key,
        "time_band_match": target.time_band == candidate.time_band,
        "event_type_match": target.event_type_key == candidate.event_type_key,
        "road_closure_match": target_event.requires_road_closure == candidate_event.requires_road_closure,
        "priority_match": target.priority_key == candidate.priority_key,
        "zone_match": target.zone_key == candidate.zone_key,
        "junction_match": target.junction_key == candidate.junction_key,
    }

    structured_score = sum(
        STRUCTURED_MATCH_WEIGHTS[key]
        for key, matched in signals.items()
        if matched
    )
    vector_similarity = _cosine_similarity_from_vectors(
        target.fingerprint_vector,
        target.fingerprint_norm,
        candidate.fingerprint_vector,
        candidate.fingerprint_norm,
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
    target_item = index.indexed_contexts_by_event_id.get(event.id)
    if target_item is None:
        return []

    candidate_scores = _candidate_structured_scores(target_item, index)
    candidate_ids = list(candidate_scores)
    prefilter_limit = max(limit * SIMILARITY_PREFILTER_MULTIPLIER, SIMILARITY_PREFILTER_MIN)
    if len(candidate_ids) > prefilter_limit:
        candidate_ids = [
            candidate_id
            for candidate_id, _score in nlargest(
                prefilter_limit,
                candidate_scores.items(),
                key=lambda item: (item[1], item[0]),
            )
        ]
    elif len(candidate_ids) < limit:
        for candidate_id in index.contexts_by_event_id:
            if candidate_id != event.id and candidate_id not in candidate_scores:
                candidate_ids.append(candidate_id)

    matches: list[SimilarEventMatch] = []
    for candidate_id in candidate_ids:
        candidate_item = index.indexed_contexts_by_event_id[candidate_id]
        similarity, matched_signals = _match_score(target_item, candidate_item)
        candidate_context = candidate_item.context
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
