from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DiversionInput:
    impact_score: float
    impact_category: str
    road_closure_probability: float
    impact_radius_km: float
    corridor: str | None = None
    junction: str | None = None
    zone: str | None = None


def recommend_diversion(data: DiversionInput) -> dict[str, object]:
    strategy = "monitor_only"
    diversion_scope = "advisory watch within 0.8 km"
    reason_codes = ["impact_category"]

    if data.impact_score >= 35 or data.road_closure_probability >= 0.35:
        strategy = "protect_mainline_flow"
        diversion_scope = "soft upstream filtering within 1.2 km"
        reason_codes.append("moderate_disruption")
    if data.road_closure_probability >= 0.6 or data.impact_category in {"High", "Critical"}:
        strategy = "hotspot_bypass"
        diversion_scope = f"avoid hotspot radius within {round(max(data.impact_radius_km, 1.5), 1)} km"
        reason_codes.append("high_closure_risk")

    upstream_focus_points = [
        point
        for point in [
            f"corridor inflow: {data.corridor}" if data.corridor else None,
            f"junction feeder: {data.junction}" if data.junction else None,
            f"zone boundary: {data.zone}" if data.zone else None,
            "freight-heavy feeder road",
        ]
        if point is not None
    ][:4]

    heavy_vehicle_advisory = (
        "Move heavy vehicles to alternate feeder roads before they enter the hotspot radius."
        if strategy != "monitor_only"
        else "Heavy-vehicle rerouting is not required yet; keep advisory monitoring active."
    )

    return {
        "strategy": strategy,
        "corridor_to_protect": data.corridor,
        "diversion_scope": diversion_scope,
        "upstream_focus_points": upstream_focus_points,
        "heavy_vehicle_advisory": heavy_vehicle_advisory,
        "reason_codes": reason_codes,
        "note": "Diversion guidance is simplified MVP routing support, not a city-scale navigation guarantee.",
    }
