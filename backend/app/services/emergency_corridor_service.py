from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EmergencyCorridorInput:
    impact_score: float
    impact_category: str
    road_closure_probability: float
    corridor: str | None = None
    police_station: str | None = None


def recommend_emergency_corridor(data: EmergencyCorridorInput) -> dict[str, object]:
    if data.impact_category == "Critical" or data.road_closure_probability >= 0.75:
        priority = "strict_keep_one_lane_clear"
        lane_policy = "reserve one continuous response lane with controlled entry/exit"
        activation_trigger = "activate immediately with upstream officer signaling"
    elif data.impact_category == "High" or data.road_closure_probability >= 0.5:
        priority = "protected_lane"
        lane_policy = "keep one curbside or median-adjacent lane clear wherever feasible"
        activation_trigger = "activate when queues begin affecting emergency response time"
    else:
        priority = "advisory_ready"
        lane_policy = "maintain advisory corridor awareness without hard lane takeover"
        activation_trigger = "activate only if congestion escalates beyond the forecast"

    protected_corridor = data.corridor or data.police_station

    return {
        "priority": priority,
        "lane_policy": lane_policy,
        "protected_corridor": protected_corridor,
        "activation_trigger": activation_trigger,
        "authentication_note": "Ambulance verification and live dispatch integration remain future scope; MVP protects corridor advisory only.",
        "reason_codes": ["impact_category", "road_closure_probability"],
    }
