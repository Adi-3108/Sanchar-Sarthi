from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BarricadeInput:
    impact_score: float
    impact_category: str
    road_closure_probability: float
    impact_radius_km: float
    corridor: str | None = None
    junction: str | None = None


def recommend_barricades(data: BarricadeInput) -> dict[str, object]:
    level = "soft_channelization"
    estimated_units = 2
    reason_codes = ["impact_category"]

    if data.impact_score >= 40 or data.road_closure_probability >= 0.35:
        level = "partial_lane_guidance"
        estimated_units = 4
        reason_codes.append("moderate_disruption")
    if data.road_closure_probability >= 0.7 or data.impact_score >= 60:
        level = "partial_closure_with_barricades"
        estimated_units = 6
        reason_codes.append("closure_likelihood")
    if data.impact_score >= 80:
        level = "controlled_entry_exit_points"
        estimated_units = 8
        reason_codes.append("critical_impact_score")

    placement_priority = [
        "upstream warning point",
        "incident edge taper",
        "junction mouth control",
        "pedestrian spillover edge",
    ]
    if data.corridor:
        placement_priority.insert(0, f"corridor buffer: {data.corridor}")
    if data.junction:
        placement_priority.insert(1, f"junction gate: {data.junction}")

    return {
        "barricade_level": level,
        "estimated_units": estimated_units,
        "coverage_radius_km": round(data.impact_radius_km, 2),
        "placement_priority": placement_priority[:5],
        "reason_codes": reason_codes,
        "note": "Barricade guidance is an MVP operational template, not a field-surveyed closure layout.",
    }
