from __future__ import annotations

from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.orm.event import Event
from app.orm.event_feature import EventFeature
from app.orm.hotspot_cluster import HotspotCluster
from app.services.feature_engineering_service import PEAK_HOURS, rebuild_event_features

EARTH_RADIUS_KM = 6371.0088
HIGH_PRIORITY_VALUES = frozenset({"high", "critical"})
CLUSTER_TYPE_BANDS: tuple[tuple[float, Literal["critical", "high", "medium", "low"]], ...] = (
    (0.75, "critical"),
    (0.5, "high"),
    (0.25, "medium"),
    (0.0, "low"),
)


@dataclass(frozen=True)
class HotspotPoint:
    event_id: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class HotspotRebuildReport:
    clusters_created: int
    clustered_events: int
    noise_events: int
    event_features_updated: int


@dataclass(frozen=True)
class HotspotFilters:
    event_cause: str | None = None
    priority: str | None = None
    requires_road_closure: bool | None = None
    cluster_type: Literal["low", "medium", "high", "critical"] | None = None


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().casefold()
    return normalized or None


def _normalize_priority(value: str | None) -> str | None:
    return _normalize_text(value)


def _is_high_priority(value: str | None) -> bool:
    return (_normalize_priority(value) or "") in HIGH_PRIORITY_VALUES


def _cluster_type_for_score(score: float) -> Literal["low", "medium", "high", "critical"]:
    for minimum, label in CLUSTER_TYPE_BANDS:
        if score >= minimum:
            return label
    return "low"


def _haversine_km(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    delta_lat = radians(lat_b - lat_a)
    delta_lon = radians(lon_b - lon_a)
    lat_a_rad = radians(lat_a)
    lat_b_rad = radians(lat_b)

    haversine = (
        sin(delta_lat / 2) ** 2
        + cos(lat_a_rad) * cos(lat_b_rad) * sin(delta_lon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * asin(sqrt(haversine))


def _spatial_bucket_key(latitude: float, longitude: float, cell_size_deg: float) -> tuple[int, int]:
    return int(latitude / cell_size_deg), int(longitude / cell_size_deg)


def _build_spatial_index(
    points: list[HotspotPoint],
    cell_size_deg: float,
) -> dict[tuple[int, int], list[int]]:
    index: dict[tuple[int, int], list[int]] = defaultdict(list)
    for point_index, point in enumerate(points):
        index[_spatial_bucket_key(point.latitude, point.longitude, cell_size_deg)].append(point_index)
    return index


def _neighbor_candidates(
    point: HotspotPoint,
    spatial_index: dict[tuple[int, int], list[int]],
    cell_size_deg: float,
) -> list[int]:
    lat_bucket, lon_bucket = _spatial_bucket_key(point.latitude, point.longitude, cell_size_deg)
    candidates: list[int] = []
    for lat_delta in (-1, 0, 1):
        for lon_delta in (-1, 0, 1):
            candidates.extend(spatial_index.get((lat_bucket + lat_delta, lon_bucket + lon_delta), []))
    return candidates


def _region_query(
    point_index: int,
    points: list[HotspotPoint],
    spatial_index: dict[tuple[int, int], list[int]],
    cell_size_deg: float,
    eps_km: float,
    cache: list[list[int] | None],
) -> list[int]:
    cached = cache[point_index]
    if cached is not None:
        return cached

    point = points[point_index]
    neighbors = [
        candidate_index
        for candidate_index in _neighbor_candidates(point, spatial_index, cell_size_deg)
        if _haversine_km(
            point.latitude,
            point.longitude,
            points[candidate_index].latitude,
            points[candidate_index].longitude,
        )
        <= eps_km
    ]
    cache[point_index] = neighbors
    return neighbors


def detect_hotspot_clusters(
    events: list[Event],
    *,
    eps_km: float = 0.7,
    min_samples: int = 3,
) -> tuple[list[list[Event]], list[Event]]:
    if eps_km <= 0:
        raise ValueError("eps_km must be greater than zero")
    if min_samples < 2:
        raise ValueError("min_samples must be at least 2")

    points = [
        HotspotPoint(
            event_id=event.id,
            latitude=float(event.latitude),
            longitude=float(event.longitude),
        )
        for event in events
        if event.latitude is not None and event.longitude is not None
    ]
    if not points:
        return [], []

    event_by_id = {event.id: event for event in events}
    cell_size_deg = max(eps_km / 111.32, 0.0001)
    spatial_index = _build_spatial_index(points, cell_size_deg)
    region_cache: list[list[int] | None] = [None] * len(points)

    labels: list[int | None] = [None] * len(points)
    visited = [False] * len(points)
    cluster_id = 0

    for point_index in range(len(points)):
        if visited[point_index]:
            continue

        visited[point_index] = True
        neighbors = _region_query(
            point_index,
            points,
            spatial_index,
            cell_size_deg,
            eps_km,
            region_cache,
        )
        if len(neighbors) < min_samples:
            labels[point_index] = -1
            continue

        labels[point_index] = cluster_id
        expansion_queue = deque(neighbors)
        queued = set(neighbors)

        while expansion_queue:
            neighbor_index = expansion_queue.popleft()

            if not visited[neighbor_index]:
                visited[neighbor_index] = True
                secondary_neighbors = _region_query(
                    neighbor_index,
                    points,
                    spatial_index,
                    cell_size_deg,
                    eps_km,
                    region_cache,
                )
                if len(secondary_neighbors) >= min_samples:
                    for secondary_neighbor in secondary_neighbors:
                        if secondary_neighbor not in queued:
                            expansion_queue.append(secondary_neighbor)
                            queued.add(secondary_neighbor)

            if labels[neighbor_index] in (None, -1):
                labels[neighbor_index] = cluster_id

        cluster_id += 1

    clustered_indexes: dict[int, list[int]] = defaultdict(list)
    noise_events: list[Event] = []
    for point_index, label in enumerate(labels):
        if label is None or label == -1:
            noise_events.append(event_by_id[points[point_index].event_id])
            continue
        clustered_indexes[label].append(point_index)

    clusters = [
        [event_by_id[points[point_index].event_id] for point_index in member_indexes]
        for _label, member_indexes in sorted(
            clustered_indexes.items(),
            key=lambda item: (
                -len(item[1]),
                min(points[point_index].event_id for point_index in item[1]),
            ),
        )
    ]
    return clusters, noise_events


def _safe_divide(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 4)


def _top_counts(values: list[str | None], *, limit: int = 5) -> list[dict[str, int]]:
    counts = Counter(value for value in values if value)
    return [
        {"label": label, "count": count}
        for label, count in counts.most_common(limit)
    ]


def _priority_mix(members: list[Event]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for member in members:
        normalized = _normalize_priority(member.priority)
        if normalized:
            counts[normalized] += 1
    return dict(counts)


def _calculate_cluster_risk_score(
    *,
    member_count: int,
    max_member_count: int,
    high_priority_rate: float,
    road_closure_rate: float,
    peak_hour_rate: float,
) -> float:
    size_factor = 1.0 if max_member_count <= 0 else min(member_count / max_member_count, 1.0)
    score = (
        size_factor * 0.4
        + high_priority_rate * 0.25
        + road_closure_rate * 0.2
        + peak_hour_rate * 0.15
    )
    return round(min(score, 1.0), 4)


def _centroid(members: list[Event]) -> tuple[float, float]:
    center_latitude = sum(float(member.latitude) for member in members) / len(members)
    center_longitude = sum(float(member.longitude) for member in members) / len(members)
    return round(center_latitude, 6), round(center_longitude, 6)


def _cluster_radius_km(members: list[Event], centroid_latitude: float, centroid_longitude: float) -> float:
    if not members:
        return 0.0
    return round(
        max(
            _haversine_km(
                centroid_latitude,
                centroid_longitude,
                float(member.latitude),
                float(member.longitude),
            )
            for member in members
        ),
        4,
    )


def _build_cluster_profile(
    *,
    members: list[Event],
    cluster_type: str,
    centroid_latitude: float,
    centroid_longitude: float,
    cluster_radius_km: float,
    high_priority_rate: float,
    road_closure_rate: float,
    peak_hour_rate: float,
) -> dict[str, object]:
    causes = Counter(
        _normalize_text(member.event_cause_clean or member.event_cause) or "unknown"
        for member in members
    )
    road_closure_events = sum(1 for member in members if member.requires_road_closure)
    return {
        "source": "dataset_backed_dbscan",
        "cluster_type": cluster_type,
        "member_event_ids": [member.id for member in members],
        "priority_mix": _priority_mix(members),
        "event_causes": dict(causes),
        "top_corridors": _top_counts([member.corridor for member in members]),
        "top_police_stations": _top_counts([member.police_station for member in members]),
        "centroid_latitude": centroid_latitude,
        "centroid_longitude": centroid_longitude,
        "radius_km": cluster_radius_km,
        "high_priority_rate": high_priority_rate,
        "road_closure_rate": road_closure_rate,
        "peak_hour_rate": peak_hour_rate,
        "road_closure_events": road_closure_events,
        "non_closure_events": len(members) - road_closure_events,
    }


def _update_feature_cluster_metrics(
    features: list[EventFeature],
    event_by_id: dict[str, Event],
) -> int:
    cluster_counts: Counter[str] = Counter()
    cluster_closures: Counter[str] = Counter()

    for feature in features:
        cluster_id = feature.location_cluster_id
        if not cluster_id:
            continue
        cluster_counts[cluster_id] += 1
        if event_by_id[feature.event_id].requires_road_closure:
            cluster_closures[cluster_id] += 1

    total_features = len(features)
    for feature in features:
        cluster_id = feature.location_cluster_id
        if not cluster_id:
            feature.historical_cluster_risk = None
            feature.historical_cluster_closure_rate = None
            continue
        feature.historical_cluster_risk = _safe_divide(cluster_counts[cluster_id], total_features)
        feature.historical_cluster_closure_rate = _safe_divide(
            cluster_closures[cluster_id],
            cluster_counts[cluster_id],
        )

    return len(features)


def rebuild_hotspots(
    db: Session,
    *,
    eps_km: float = 0.7,
    min_samples: int = 3,
    commit: bool = True,
) -> HotspotRebuildReport:
    rebuild_event_features(db, commit=False)

    all_events = db.scalars(select(Event).order_by(Event.start_datetime, Event.id)).all()
    events = [
        event
        for event in all_events
        if event.latitude is not None and event.longitude is not None
    ]
    if not all_events:
        existing_clusters = db.scalars(select(HotspotCluster)).all()
        for cluster in existing_clusters:
            db.delete(cluster)
        if commit:
            db.commit()
        else:
            db.flush()
        return HotspotRebuildReport(
            clusters_created=0,
            clustered_events=0,
            noise_events=0,
            event_features_updated=0,
        )

    if not events:
        existing_clusters = db.scalars(select(HotspotCluster)).all()
        for cluster in existing_clusters:
            db.delete(cluster)
        if commit:
            db.commit()
        else:
            db.flush()
        return HotspotRebuildReport(
            clusters_created=0,
            clustered_events=0,
            noise_events=len(all_events),
            event_features_updated=0,
        )

    features = db.scalars(select(EventFeature).order_by(EventFeature.created_at, EventFeature.id)).all()
    feature_by_event_id = {feature.event_id: feature for feature in features}
    event_by_id = {event.id: event for event in all_events}

    clusters, noise_events = detect_hotspot_clusters(
        events,
        eps_km=eps_km,
        min_samples=min_samples,
    )
    max_member_count = max((len(cluster_members) for cluster_members in clusters), default=0)

    for cluster in db.scalars(select(HotspotCluster)).all():
        db.delete(cluster)

    clustered_event_total = 0
    for cluster_index, members in enumerate(clusters, start=1):
        location_cluster_id = f"CL-{cluster_index:03d}"
        clustered_event_total += len(members)

        centroid_latitude, centroid_longitude = _centroid(members)
        cluster_radius_km = _cluster_radius_km(members, centroid_latitude, centroid_longitude)
        high_priority_rate = _safe_divide(
            sum(1 for member in members if _is_high_priority(member.priority)),
            len(members),
        ) or 0.0
        road_closure_rate = _safe_divide(
            sum(1 for member in members if member.requires_road_closure),
            len(members),
        ) or 0.0
        peak_hour_rate = _safe_divide(
            sum(1 for member in members if member.start_datetime.hour in PEAK_HOURS),
            len(members),
        ) or 0.0
        top_cause = (
            Counter(
                _normalize_text(member.event_cause_clean or member.event_cause) or "unknown"
                for member in members
            ).most_common(1)[0][0]
        )
        risk_score = _calculate_cluster_risk_score(
            member_count=len(members),
            max_member_count=max_member_count,
            high_priority_rate=high_priority_rate,
            road_closure_rate=road_closure_rate,
            peak_hour_rate=peak_hour_rate,
        )
        cluster_type = _cluster_type_for_score(risk_score)

        db.add(
            HotspotCluster(
                location_cluster_id=location_cluster_id,
                centroid_latitude=centroid_latitude,
                centroid_longitude=centroid_longitude,
                cluster_event_count=len(members),
                cluster_high_priority_rate=high_priority_rate,
                cluster_road_closure_rate=road_closure_rate,
                cluster_peak_hour_rate=peak_hour_rate,
                cluster_top_event_cause=top_cause,
                cluster_risk_score=risk_score,
                cluster_profile_json=_build_cluster_profile(
                    members=members,
                    cluster_type=cluster_type,
                    centroid_latitude=centroid_latitude,
                    centroid_longitude=centroid_longitude,
                    cluster_radius_km=cluster_radius_km,
                    high_priority_rate=high_priority_rate,
                    road_closure_rate=road_closure_rate,
                    peak_hour_rate=peak_hour_rate,
                ),
            )
        )

        for member in members:
            feature = feature_by_event_id.get(member.id)
            if feature is not None:
                feature.location_cluster_id = location_cluster_id

    features_updated = _update_feature_cluster_metrics(features, event_by_id)

    if commit:
        db.commit()
    else:
        db.flush()

    return HotspotRebuildReport(
        clusters_created=len(clusters),
        clustered_events=clustered_event_total,
        noise_events=len(noise_events),
        event_features_updated=features_updated,
    )


def _hotspot_matches_filters(cluster: HotspotCluster, filters: HotspotFilters) -> bool:
    profile = cluster.cluster_profile_json or {}

    if filters.cluster_type and profile.get("cluster_type") != filters.cluster_type:
        return False

    if filters.event_cause:
        event_causes = profile.get("event_causes", {})
        if not isinstance(event_causes, dict):
            return False
        if _normalize_text(filters.event_cause) not in event_causes:
            return False

    if filters.priority:
        priority_mix = profile.get("priority_mix", {})
        if not isinstance(priority_mix, dict):
            return False
        if _normalize_priority(filters.priority) not in priority_mix:
            return False

    if filters.requires_road_closure is not None:
        road_closure_events = int(profile.get("road_closure_events", 0))
        non_closure_events = int(profile.get("non_closure_events", 0))
        if filters.requires_road_closure and road_closure_events <= 0:
            return False
        if not filters.requires_road_closure and non_closure_events <= 0:
            return False

    return True


def list_hotspots(
    db: Session,
    *,
    filters: HotspotFilters | None = None,
) -> list[HotspotCluster]:
    active_filters = filters or HotspotFilters()
    hotspots = db.scalars(select(HotspotCluster).order_by(HotspotCluster.cluster_risk_score.desc())).all()
    return [hotspot for hotspot in hotspots if _hotspot_matches_filters(hotspot, active_filters)]


def build_hotspot_geojson(hotspots: list[HotspotCluster]) -> dict[str, object]:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(hotspot.centroid_longitude), float(hotspot.centroid_latitude)],
                },
                "properties": {
                    "location_cluster_id": hotspot.location_cluster_id,
                    "cluster_event_count": hotspot.cluster_event_count,
                    "cluster_risk_score": float(hotspot.cluster_risk_score),
                    "cluster_top_event_cause": hotspot.cluster_top_event_cause,
                    "cluster_type": hotspot.cluster_profile_json.get("cluster_type"),
                    "radius_km": hotspot.cluster_profile_json.get("radius_km"),
                },
            }
            for hotspot in hotspots
        ],
    }


def build_analytics_summary(db: Session) -> dict[str, object]:
    events = db.scalars(select(Event)).all()
    hotspots = db.scalars(select(HotspotCluster)).all()

    total_events = len(events)
    planned_events = sum(1 for event in events if _normalize_text(event.event_type) == "planned")
    unplanned_events = sum(1 for event in events if _normalize_text(event.event_type) == "unplanned")
    high_priority_events = sum(1 for event in events if _is_high_priority(event.priority))
    road_closure_required = sum(1 for event in events if event.requires_road_closure)

    def top_items(values: list[str | None], *, limit: int = 5) -> list[dict[str, object]]:
        counts = Counter(value for value in values if value)
        return [
            {
                "label": label,
                "count": count,
                "share": round(count / total_events, 4) if total_events else 0.0,
            }
            for label, count in counts.most_common(limit)
        ]

    return {
        "total_events": total_events,
        "planned_events": planned_events,
        "unplanned_events": unplanned_events,
        "high_priority_events": high_priority_events,
        "road_closure_required": road_closure_required,
        "hotspot_count": len(hotspots),
        "top_causes": top_items([event.event_cause_clean or event.event_cause for event in events]),
        "top_corridors": top_items([event.corridor for event in events]),
        "top_police_stations": top_items([event.police_station for event in events]),
    }
