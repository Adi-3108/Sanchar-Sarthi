from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ManpowerInput:
    impact_score: float
    impact_category: str
    road_closure_probability: float
    event_type: str
    impact_radius_km: float
    available_officers: int | None = None
    corridor: str | None = None
    junction: str | None = None
    police_station: str | None = None


def recommend_manpower(data: ManpowerInput) -> dict[str, object]:
    base = {
        "Low": 4,
        "Medium": 6,
        "High": 8,
        "Critical": 12,
    }.get(data.impact_category, 4)

    reason_codes = ["impact_category", "impact_radius_km"]
    if data.event_type == "unplanned":
        base += 2
        reason_codes.append("event_type_unplanned")
    if data.road_closure_probability >= 0.7:
        base += 2
        reason_codes.append("road_closure_probability")
    if data.impact_radius_km >= 2.5:
        base += 2
        reason_codes.append("wide_impact_radius")
    if data.impact_score >= 85:
        base += 2
        reason_codes.append("severe_impact_score")

    recommended_total_officers = min(base, 20)
    reserve_officers = 0
    if recommended_total_officers >= 12:
        reserve_officers = 2
    elif recommended_total_officers >= 8:
        reserve_officers = 1

    if data.impact_score >= 75:
        deployment_style = "incident_command_posture"
    elif data.road_closure_probability >= 0.6 or data.impact_radius_km >= 2.0:
        deployment_style = "corridor_ring_control"
    else:
        deployment_style = "point_control"

    if data.impact_radius_km >= 3.0:
        sector_count = 4
    elif data.impact_radius_km >= 2.0:
        sector_count = 3
    elif data.impact_radius_km >= 1.2:
        sector_count = 2
    else:
        sector_count = 1

    primary_positions = [
        position
        for position in [
            f"primary corridor anchor: {data.corridor}" if data.corridor else None,
            f"junction control: {data.junction}" if data.junction else None,
            f"station coordination: {data.police_station}" if data.police_station else None,
            "upstream queue monitor",
            "downstream clearance team",
        ]
        if position is not None
    ][:4]

    officer_gap = 0
    feasibility_status = "availability_not_provided"
    if data.available_officers is not None:
        officer_gap = max(recommended_total_officers - data.available_officers, 0)
        feasibility_status = "fully_staffable" if officer_gap == 0 else "requires_reallocation"

    return {
        "recommended_total_officers": recommended_total_officers,
        "deployment_style": deployment_style,
        "reserve_officers": reserve_officers,
        "sector_count": sector_count,
        "available_officers": data.available_officers,
        "officer_gap": officer_gap,
        "feasibility_status": feasibility_status,
        "primary_positions": primary_positions,
        "reason_codes": reason_codes,
        "note": "Recommended manpower is dataset-backed operational guidance, not a statutory deployment mandate.",
    }
