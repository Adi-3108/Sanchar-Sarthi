from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LogisticsImpactInput:
    impact_score: float
    impact_category: str
    impact_radius_km: float
    estimated_clearance_minutes: float | None = None
    corridor: str | None = None
    event_type: str = "unplanned"


def assess_logistics_impact(data: LogisticsImpactInput) -> dict[str, object]:
    clearance_minutes = int(round(data.estimated_clearance_minutes or max(data.impact_score * 2, 30.0)))

    if data.impact_category == "Critical":
        impact_level = "dispatch_hold_for_non_essential_shipments"
        dispatch_recommendation = "Pause non-essential dispatches inside the impact radius and release only exception shipments."
    elif data.impact_category == "High":
        impact_level = "stagger_dispatch_and_pre_stage_fleet"
        dispatch_recommendation = "Pre-stage riders outside the impact radius and stagger waves until the corridor stabilizes."
    elif data.impact_category == "Medium":
        impact_level = "soft_delay_and_monitor"
        dispatch_recommendation = "Delay flexible dispatch windows by 30-45 minutes and notify last-mile teams."
    else:
        impact_level = "routine_monitoring"
        dispatch_recommendation = "Keep routine dispatch active with corridor watch only."

    if data.event_type == "planned" and impact_level != "routine_monitoring":
        dispatch_recommendation += " Planned-event timing makes proactive slot shifting preferable to reactive rerouting."

    return {
        "impact_level": impact_level,
        "delivery_risk_window_minutes": clearance_minutes,
        "affected_radius_km": round(data.impact_radius_km, 2),
        "dispatch_recommendation": dispatch_recommendation,
        "warehouse_note": (
            f"Use {data.corridor} as the primary watch corridor for last-mile coordination."
            if data.corridor
            else "Use the impact radius as the primary watch zone for last-mile coordination."
        ),
        "reason_codes": ["impact_category", "estimated_clearance_minutes", "impact_radius_km"],
    }
