from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import combinations

from app.services.citizen_report_service import haversine_km

DEFAULT_EVENT_DURATION = timedelta(hours=2)

REASON_LABELS = {
    "time_overlap": "time overlap",
    "impact_radius_overlap": "impact radius overlap",
    "nearby_event_radius": "nearby event radius",
    "shared_corridor": "shared corridor",
    "shared_police_station": "shared police station",
    "diversion_route_conflict": "diversion route conflict",
    "manpower_gap": "officer gap",
}


@dataclass(frozen=True)
class EventCoordinationInput:
    event_id: str
    latitude: float
    longitude: float
    start_datetime: datetime
    end_datetime: datetime | None
    corridor: str | None
    police_station: str | None
    zone: str | None
    junction: str | None
    estimated_impact_score: float
    impact_radius_km: float
    recommended_personnel: int
    diversion_strategy: str | None = None
    diversion_corridor: str | None = None
    upstream_focus_points: tuple[str, ...] = ()


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().casefold()
    return normalized or None


def _normalized_set(values: tuple[str, ...]) -> set[str]:
    return {value.strip().casefold() for value in values if value and value.strip()}


def _event_end(data: EventCoordinationInput) -> datetime:
    return data.end_datetime or (data.start_datetime + DEFAULT_EVENT_DURATION)


def time_overlap_minutes(left: EventCoordinationInput, right: EventCoordinationInput) -> float:
    overlap_start = max(left.start_datetime, right.start_datetime)
    overlap_end = min(_event_end(left), _event_end(right))
    return max((overlap_end - overlap_start).total_seconds() / 60.0, 0.0)


def _impact_radii_overlap(left: EventCoordinationInput, right: EventCoordinationInput, distance_km: float) -> bool:
    combined_radius = max(left.impact_radius_km, 0.5) + max(right.impact_radius_km, 0.5)
    return distance_km <= combined_radius


def _diversion_conflict(left: EventCoordinationInput, right: EventCoordinationInput) -> bool:
    left_corridor = _normalize_text(left.diversion_corridor or left.corridor)
    right_corridor = _normalize_text(right.diversion_corridor or right.corridor)
    if left_corridor and right_corridor and left_corridor == right_corridor:
        return True

    left_focus = _normalized_set(left.upstream_focus_points)
    right_focus = _normalized_set(right.upstream_focus_points)
    return bool(left_focus and right_focus and left_focus.intersection(right_focus))


def _conflict_level(score: float) -> str:
    if score >= 75:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


def detect_pair_conflict(
    left: EventCoordinationInput,
    right: EventCoordinationInput,
    available_personnel: int,
) -> dict[str, object]:
    overlap = time_overlap_minutes(left, right)
    distance = haversine_km(left.latitude, left.longitude, right.latitude, right.longitude)
    same_corridor = bool(_normalize_text(left.corridor) and _normalize_text(left.corridor) == _normalize_text(right.corridor))
    same_station = bool(
        _normalize_text(left.police_station)
        and _normalize_text(left.police_station) == _normalize_text(right.police_station)
    )
    radii_overlap = _impact_radii_overlap(left, right, distance)
    diversion_conflict = _diversion_conflict(left, right)
    manpower_gap = max(left.recommended_personnel + right.recommended_personnel - available_personnel, 0)

    score = 0.0
    reasons: list[str] = []
    if overlap > 0:
        score += min(30.0, 12.0 + overlap / 8.0)
        reasons.append("time_overlap")
    if radii_overlap:
        score += 18.0
        reasons.append("impact_radius_overlap")
    if distance <= 3.0:
        score += 15.0
        reasons.append("nearby_event_radius")
    if same_corridor:
        score += 20.0
        reasons.append("shared_corridor")
    if same_station:
        score += 10.0
        reasons.append("shared_police_station")
    if diversion_conflict:
        score += 15.0
        reasons.append("diversion_route_conflict")
    if manpower_gap > 0:
        score += min(20.0, 8.0 + manpower_gap * 2.0)
        reasons.append("manpower_gap")

    average_impact = (left.estimated_impact_score + right.estimated_impact_score) / 2.0
    if average_impact >= 75 and reasons:
        score += 8.0
    elif average_impact >= 50 and reasons:
        score += 4.0

    score = min(round(score, 2), 100.0)
    return {
        "event_ids": [left.event_id, right.event_id],
        "conflict_score": score,
        "conflict_level": _conflict_level(score),
        "distance_km": round(distance, 2),
        "overlap_minutes": round(overlap, 1),
        "manpower_gap": manpower_gap,
        "reason_codes": reasons,
        "reason_labels": [REASON_LABELS[reason] for reason in reasons],
    }


def _combined_risk(conflicts: list[dict[str, object]], officer_gap: int) -> str:
    highest_score = max((float(item["conflict_score"]) for item in conflicts), default=0.0)
    if officer_gap > 0:
        highest_score = min(highest_score + min(15.0, officer_gap * 1.5), 100.0)
    if highest_score >= 75:
        return "Critical"
    if highest_score >= 60:
        return "High"
    if highest_score >= 35:
        return "Medium"
    return "Low"


def _coordination_plan(
    *,
    combined_risk: str,
    conflicts: list[dict[str, object]],
    officer_gap: int,
) -> list[str]:
    plan: list[str] = []
    reason_codes = {reason for item in conflicts for reason in list(item.get("reason_codes", []))}
    if combined_risk in {"Critical", "High"}:
        plan.append("Run joint command for the selected events and assign one control-room owner.")
    if "shared_corridor" in reason_codes or "diversion_route_conflict" in reason_codes:
        plan.append("Separate diversion corridors and keep a protected emergency/logistics lane where possible.")
    if "time_overlap" in reason_codes:
        plan.append("Stagger barricade activation and upstream advisories across the overlap window.")
    if officer_gap > 0:
        plan.append(f"Reallocate at least {officer_gap} officers or reduce plan scope before field deployment.")
    if "impact_radius_overlap" in reason_codes or "nearby_event_radius" in reason_codes:
        plan.append("Place mobile units between overlapping impact radii for faster spillover response.")
    if not plan:
        plan.append("Monitor overlaps and keep event plans independent unless field conditions worsen.")
    return plan


def build_conflict_geojson(
    inputs: list[EventCoordinationInput],
    conflicts: list[dict[str, object]],
) -> dict[str, object]:
    by_id = {item.event_id: item for item in inputs}
    features: list[dict[str, object]] = []
    for conflict in conflicts:
        if conflict["conflict_level"] == "low":
            continue
        event_ids = list(conflict["event_ids"])
        left = by_id.get(str(event_ids[0]))
        right = by_id.get(str(event_ids[1]))
        if left is None or right is None:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [left.longitude, left.latitude],
                        [right.longitude, right.latitude],
                    ],
                },
                "properties": {
                    "event_ids": event_ids,
                    "conflict_score": conflict["conflict_score"],
                    "conflict_level": conflict["conflict_level"],
                    "reason_codes": conflict["reason_codes"],
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def analyze_multi_event_conflicts(
    inputs: list[EventCoordinationInput],
    *,
    available_personnel: int,
) -> dict[str, object]:
    conflicts = [
        detect_pair_conflict(left, right, available_personnel)
        for left, right in combinations(inputs, 2)
    ]
    conflicts.sort(key=lambda item: float(item["conflict_score"]), reverse=True)
    total_manpower_demand = sum(item.recommended_personnel for item in inputs)
    officer_gap = max(total_manpower_demand - available_personnel, 0)
    combined_risk = _combined_risk(conflicts, officer_gap)
    conflict_signals = sorted(
        {
            REASON_LABELS.get(reason, reason.replace("_", " "))
            for item in conflicts
            for reason in list(item.get("reason_codes", []))
        }
    )
    high_conflict_count = sum(1 for item in conflicts if item["conflict_level"] in {"high", "critical"})
    coordination_plan = _coordination_plan(
        combined_risk=combined_risk,
        conflicts=conflicts,
        officer_gap=officer_gap,
    )
    return {
        "conflict_detected": any(float(item["conflict_score"]) >= 35 for item in conflicts) or officer_gap > 0,
        "combined_risk": combined_risk,
        "coordination_mode": "joint_command" if combined_risk in {"Critical", "High"} else "normal_monitoring",
        "high_conflict_count": high_conflict_count,
        "conflict_signals": conflict_signals,
        "total_manpower_demand": total_manpower_demand,
        "available_officers": available_personnel,
        "officer_gap": officer_gap,
        "coordination_plan": coordination_plan,
        "conflicts": conflicts,
        "map_overlay": build_conflict_geojson(inputs, conflicts),
        "honesty_note": (
            "Multi-event coordination is dataset-backed operational guidance based on event timing, "
            "location, recommendations, and officer availability; it is not live citywide signal control."
        ),
    }
