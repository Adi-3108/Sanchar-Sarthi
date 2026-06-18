from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from app.orm.live_event_update import LiveEventUpdate

LEVEL_ALIASES = {
    "info": "Info",
    "watch": "Watch",
    "stable": "Stable",
    "warning": "Warning",
    "critical": "Critical",
}

CONGESTION_LEVEL_DELTA = {
    "info": 0.0,
    "watch": 3.0,
    "stable": 0.0,
    "warning": 7.0,
    "critical": 10.0,
}

FLAG_DELTAS = {
    "road_closure_active": 10.0,
    "officer_shortage": 8.0,
    "crowd_increase": 7.0,
    "rain_waterlogging": 10.0,
    "new_nearby_incident": 12.0,
}

MAX_CORROBORATION_DELTA = 6.0


@dataclass(frozen=True)
class LiveUpdateInput:
    current_congestion_level: str
    field_update: str | None
    road_closure_active: bool
    officer_shortage: bool
    crowd_increase: bool
    rain_waterlogging: bool
    new_nearby_incident: bool
    expected_impact_score: float
    corroborating_reports: int = 0


def _safe_float(value: Decimal | float | int | None, *, default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


def _clamp_score(value: float) -> float:
    return round(min(max(value, 0.0), 100.0), 2)


def normalize_congestion_level(value: str) -> str:
    normalized = value.strip().casefold()
    return LEVEL_ALIASES.get(normalized, value.strip().title() or "Stable")


def escalation_level(score: float) -> str:
    if score >= 85:
        return "Critical"
    if score >= 65:
        return "Warning"
    return "Stable"


def _dedupe_actions(actions: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for action in actions:
        key = action.casefold()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(action)
    return ordered


def _build_adaptive_action(
    *,
    level: str,
    road_closure_active: bool,
    officer_shortage: bool,
    crowd_increase: bool,
    rain_waterlogging: bool,
    new_nearby_incident: bool,
    corroborating_reports: int,
) -> str:
    actions: list[str] = []

    if level in {"Warning", "Critical"}:
        actions.append("Notify control room")
    if officer_shortage:
        actions.append("Move 2 reserve officers upstream or request spillover support")
    elif level == "Critical":
        actions.append("Prepare additional manpower")
    if road_closure_active or level == "Critical":
        actions.append("Activate the stored diversion plan")
    if crowd_increase:
        actions.append("Expand crowd-control perimeter near the upstream junction")
    if rain_waterlogging:
        actions.append("Avoid low-lying approaches and widen barricade taper")
    if new_nearby_incident:
        actions.append("Treat the nearby incident as a corridor conflict and coordinate the next sector")
    if corroborating_reports >= 2:
        actions.append(f"Cross-check against {corroborating_reports} recent corroborating reports")

    if not actions:
        return "Monitor situation and keep field confirmations coming."
    return "; ".join(_dedupe_actions(actions))


def apply_live_update(data: LiveUpdateInput) -> dict[str, object]:
    expected_score = _clamp_score(float(data.expected_impact_score))
    normalized_level = normalize_congestion_level(data.current_congestion_level)
    delta = CONGESTION_LEVEL_DELTA.get(normalized_level.casefold(), 0.0)

    for field_name, field_delta in FLAG_DELTAS.items():
        if getattr(data, field_name):
            delta += field_delta

    corroboration_delta = min(max(data.corroborating_reports, 0), 4) * 1.5
    delta += min(corroboration_delta, MAX_CORROBORATION_DELTA)

    current_score = _clamp_score(expected_score + delta)
    alert_level = escalation_level(current_score)
    adaptive_action = _build_adaptive_action(
        level=alert_level,
        road_closure_active=data.road_closure_active,
        officer_shortage=data.officer_shortage,
        crowd_increase=data.crowd_increase,
        rain_waterlogging=data.rain_waterlogging,
        new_nearby_incident=data.new_nearby_incident,
        corroborating_reports=max(data.corroborating_reports, 0),
    )

    return {
        "expected_impact_score": expected_score,
        "current_impact_score": current_score,
        "impact_deviation": round(current_score - expected_score, 2),
        "alert_level": alert_level,
        "adaptive_action": adaptive_action,
        "honesty_note": "Simulated live escalation guidance, not automatic police dispatch.",
    }


def serialize_live_update(record: LiveEventUpdate) -> dict[str, object]:
    created_at = record.created_at
    if isinstance(created_at, datetime) and created_at.tzinfo is not None:
        created_at_value = created_at.astimezone(timezone.utc).isoformat()
    elif isinstance(created_at, datetime):
        created_at_value = created_at.isoformat()
    else:
        created_at_value = None

    return {
        "id": str(record.id),
        "event_id": record.event_id,
        "update_source": record.update_source,
        "current_congestion_level": record.current_congestion_level,
        "field_update": record.field_update,
        "road_closure_active": record.road_closure_active,
        "officer_shortage": record.officer_shortage,
        "crowd_increase": record.crowd_increase,
        "rain_waterlogging": record.rain_waterlogging,
        "new_nearby_incident": record.new_nearby_incident,
        "expected_impact_score": _safe_float(record.expected_impact_score, default=0.0),
        "current_impact_score": _safe_float(record.current_impact_score, default=0.0),
        "impact_deviation": _safe_float(record.impact_deviation, default=0.0),
        "alert_level": record.alert_level,
        "adaptive_action": record.adaptive_action,
        "created_at": created_at_value,
    }
