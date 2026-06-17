from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.feature_pipeline import reliable_clearance_minutes
from app.orm.event import Event
from app.orm.hotspot_cluster import HotspotCluster
from app.services.similar_event_service import SimilarEventMatch

DEFAULT_VEHICLE_IMPACT_MULTIPLIER: dict[str, float] = {
    "bmtc_bus": 1.42,
    "truck": 1.42,
    "heavy_vehicle": 1.37,
    "private_bus": 1.36,
    "taxi": 1.34,
    "others": 1.22,
    "lcv": 1.20,
    "ksrtc_bus": 1.13,
    "private_car": 1.0,
    "auto": 0.93,
}

VEHICLE_TYPE_ALIASES = {
    "mini truck": "lcv",
    "mini_truck": "lcv",
    "light commercial vehicle": "lcv",
}

VEHICLE_IMPACT_NOTE = "Derived from ASTraM resolution time averages per vehicle type."
COUNTERFACTUAL_HONESTY_NOTE = "Delta is a relative operational estimate, not measured vehicle delay."
MIN_DATASET_VEHICLE_SAMPLES = 3


@dataclass(frozen=True)
class VehicleImpactResult:
    multiplier: float
    note: str
    reason_code: str
    source: str
    normalized_vehicle_type: str | None
    sample_count: int | None = None


@dataclass(frozen=True)
class ImpactInput:
    urgency_score: float
    road_closure_likelihood: float
    hotspot_risk_score: float
    similar_event_risk: float
    veh_type: str | None = None
    weather_factor: float = 1.0
    multi_event_factor: float = 1.0


def _safe_float(value: Decimal | float | int | None, *, default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return min(max(value, minimum), maximum)


def normalize_vehicle_type(veh_type: str | None) -> str | None:
    if veh_type is None:
        return None
    normalized = veh_type.strip().casefold()
    if not normalized:
        return None
    return VEHICLE_TYPE_ALIASES.get(normalized, normalized)


def derive_vehicle_multiplier_profile(
    db: Session,
) -> dict[str, dict[str, float | int]]:
    events = db.scalars(select(Event).order_by(Event.start_datetime, Event.id)).all()
    stats: dict[str, dict[str, float | int]] = {}
    for event in events:
        vehicle_key = normalize_vehicle_type(event.veh_type)
        if vehicle_key is None:
            continue
        clearance_minutes = reliable_clearance_minutes(event)
        if clearance_minutes is None:
            continue
        entry = stats.setdefault(vehicle_key, {"sample_count": 0, "total_clearance_minutes": 0.0})
        entry["sample_count"] = int(entry["sample_count"]) + 1
        entry["total_clearance_minutes"] = float(entry["total_clearance_minutes"]) + clearance_minutes

    baseline = stats.get("private_car")
    if not baseline or int(baseline["sample_count"]) <= 0:
        return {}

    baseline_average = float(baseline["total_clearance_minutes"]) / int(baseline["sample_count"])
    if baseline_average <= 0:
        return {}

    profile: dict[str, dict[str, float | int]] = {}
    for vehicle_key, entry in stats.items():
        sample_count = int(entry["sample_count"])
        average_clearance = float(entry["total_clearance_minutes"]) / sample_count
        multiplier = min(average_clearance / baseline_average, 1.5)
        profile[vehicle_key] = {
            "sample_count": sample_count,
            "avg_clearance_minutes": round(average_clearance, 2),
            "multiplier": round(multiplier, 2),
        }
    return profile


def resolve_vehicle_impact(
    veh_type: str | None,
    *,
    db: Session | None = None,
    profile: dict[str, dict[str, float | int]] | None = None,
) -> VehicleImpactResult:
    normalized_vehicle = normalize_vehicle_type(veh_type)
    if normalized_vehicle is None:
        return VehicleImpactResult(
            multiplier=1.0,
            note=VEHICLE_IMPACT_NOTE,
            reason_code="veh_type:unknown_no_adjustment",
            source="no_adjustment",
            normalized_vehicle_type=None,
            sample_count=None,
        )

    active_profile = profile
    if active_profile is None and db is not None:
        active_profile = derive_vehicle_multiplier_profile(db)

    if active_profile:
        derived = active_profile.get(normalized_vehicle)
        if derived is not None and int(derived["sample_count"]) >= MIN_DATASET_VEHICLE_SAMPLES:
            multiplier = round(float(derived["multiplier"]), 2)
            return VehicleImpactResult(
                multiplier=multiplier,
                note=VEHICLE_IMPACT_NOTE,
                reason_code=f"veh_type:{normalized_vehicle}:dataset_multiplier:{multiplier}",
                source="dataset_derived",
                normalized_vehicle_type=normalized_vehicle,
                sample_count=int(derived["sample_count"]),
            )

    multiplier = min(DEFAULT_VEHICLE_IMPACT_MULTIPLIER.get(normalized_vehicle, 1.0), 1.5)
    return VehicleImpactResult(
        multiplier=round(multiplier, 2),
        note=VEHICLE_IMPACT_NOTE,
        reason_code=f"veh_type:{normalized_vehicle}:fallback_multiplier:{round(multiplier, 2)}",
        source="default_fallback",
        normalized_vehicle_type=normalized_vehicle,
        sample_count=None,
    )


def impact_category(score: float) -> str:
    if score >= 75:
        return "Critical"
    if score >= 50:
        return "High"
    if score >= 30:
        return "Medium"
    return "Low"


def derive_hotspot_risk(hotspot: HotspotCluster | None) -> float:
    return _clamp(_safe_float(hotspot.cluster_risk_score if hotspot is not None else None))


def derive_similar_event_risk(
    similar_events: Sequence[SimilarEventMatch],
) -> tuple[float, dict[str, object]]:
    if not similar_events:
        return 0.0, {
            "method": "no_similarity_matches",
            "top_match_event_id": None,
            "top_match_similarity": 0.0,
            "sampled_matches": 0,
        }

    scored_matches: list[dict[str, object]] = []
    for match in list(similar_events)[:3]:
        corridor_rate = _safe_float(match.historical_corridor_closure_rate)
        cluster_rate = _safe_float(match.historical_cluster_closure_rate)
        hotspot_risk = _safe_float(match.hotspot_risk_score)
        score = _clamp(
            match.similarity * 0.55
            + corridor_rate * 0.2
            + cluster_rate * 0.15
            + hotspot_risk * 0.1
        )
        scored_matches.append(
            {
                "event_id": match.event_id,
                "similarity": round(match.similarity, 4),
                "score": round(score, 4),
                "matched_signals": list(match.matched_signals),
            }
        )

    derived_score = round(
        sum(float(item["score"]) for item in scored_matches) / len(scored_matches),
        4,
    )
    top_match = scored_matches[0]
    return derived_score, {
        "method": "top_similarity_with_closure_context",
        "top_match_event_id": top_match["event_id"],
        "top_match_similarity": top_match["similarity"],
        "sampled_matches": len(scored_matches),
        "sample_matches": scored_matches,
    }


def estimate_impact(
    input_data: ImpactInput,
    *,
    vehicle_impact: VehicleImpactResult,
) -> dict[str, float | str | list[str] | dict[str, object]]:
    raw_score = (
        _clamp(input_data.urgency_score) * 35
        + _clamp(input_data.road_closure_likelihood) * 25
        + _clamp(input_data.hotspot_risk_score) * 20
        + _clamp(input_data.similar_event_risk) * 20
    )
    weather_adjusted = min(raw_score * max(input_data.weather_factor, 0.1), 100.0)
    multi_event_adjusted = min(weather_adjusted * max(input_data.multi_event_factor, 0.1), 100.0)
    adjusted_score = min(
        multi_event_adjusted + ((vehicle_impact.multiplier - 1.0) * 12.0),
        100.0,
    )
    radius_km = round(0.5 + (adjusted_score / 100.0) * 3.5, 2)
    return {
        "estimated_impact_score": round(adjusted_score, 2),
        "impact_category": impact_category(adjusted_score),
        "impact_radius_km": radius_km,
        "vehicle_impact_factor": vehicle_impact.multiplier,
        "vehicle_impact_note": vehicle_impact.note,
        "score_reason_codes": [
            "urgency_score",
            "road_closure_likelihood",
            "hotspot_risk_score",
            "similar_event_risk",
            vehicle_impact.reason_code,
        ],
        "score_components": {
            "raw_score": round(raw_score, 2),
            "weather_adjusted_score": round(weather_adjusted, 2),
            "multi_event_adjusted_score": round(multi_event_adjusted, 2),
        },
    }


def counterfactual_delta(
    current: ImpactInput,
    *,
    vehicle_impact: VehicleImpactResult,
) -> dict[str, float | str]:
    baseline_input = ImpactInput(
        urgency_score=max(current.urgency_score - 0.2, 0.0),
        road_closure_likelihood=max(current.road_closure_likelihood - 0.2, 0.0),
        hotspot_risk_score=current.hotspot_risk_score,
        similar_event_risk=current.similar_event_risk,
        veh_type=None,
        weather_factor=current.weather_factor,
        multi_event_factor=current.multi_event_factor,
    )
    with_event = estimate_impact(current, vehicle_impact=vehicle_impact)
    without_event = estimate_impact(
        baseline_input,
        vehicle_impact=VehicleImpactResult(
            multiplier=1.0,
            note=VEHICLE_IMPACT_NOTE,
            reason_code="counterfactual_baseline_no_vehicle_adjustment",
            source="counterfactual_baseline",
            normalized_vehicle_type=None,
        ),
    )
    baseline_score = float(without_event["estimated_impact_score"])
    event_score = float(with_event["estimated_impact_score"])
    return {
        "baseline_risk_score": round(baseline_score, 2),
        "event_impact_score": round(event_score, 2),
        "additional_event_delta": round(event_score - baseline_score, 2),
        "honesty_note": COUNTERFACTUAL_HONESTY_NOTE,
    }


def build_weather_adjustment(weather_condition: str | None = None) -> dict[str, object]:
    normalized = (weather_condition or "clear").strip().casefold()
    factor_map = {
        "clear": 1.0,
        "cloudy": 1.01,
        "light_rain": 1.05,
        "rain": 1.08,
        "heavy_rain": 1.15,
    }
    factor = factor_map.get(normalized, 1.0)
    source = "manual_simulation_selector" if normalized in factor_map and normalized != "clear" else "phase8_default"
    return {
        "weather_condition": normalized,
        "factor": factor,
        "source": source,
        "note": "Weather modifier is a manual MVP adjustment until dedicated weather risk integration is active.",
    }


def build_multi_event_adjustment() -> dict[str, object]:
    return {
        "factor": 1.0,
        "status": "future_integration_not_active",
        "note": "Multi-event coordination modifier remains neutral until the dedicated coordination phase is implemented.",
    }


def build_impact_assessment(
    db: Session,
    *,
    event: Event,
    urgency_score: float,
    road_closure_likelihood: float,
    hotspot: HotspotCluster | None = None,
    similar_events: Sequence[SimilarEventMatch] = (),
    weather_condition: str | None = None,
) -> dict[str, object]:
    weather_adjustment = build_weather_adjustment(weather_condition)
    multi_event_adjustment = build_multi_event_adjustment()
    similar_event_risk, similar_event_meta = derive_similar_event_risk(similar_events)
    vehicle_impact = resolve_vehicle_impact(event.veh_type, db=db)
    impact_input = ImpactInput(
        urgency_score=urgency_score,
        road_closure_likelihood=road_closure_likelihood,
        hotspot_risk_score=derive_hotspot_risk(hotspot),
        similar_event_risk=similar_event_risk,
        veh_type=event.veh_type,
        weather_factor=float(weather_adjustment["factor"]),
        multi_event_factor=float(multi_event_adjustment["factor"]),
    )
    impact = estimate_impact(impact_input, vehicle_impact=vehicle_impact)
    counterfactual = counterfactual_delta(impact_input, vehicle_impact=vehicle_impact)
    return {
        "impact": impact,
        "counterfactual": counterfactual,
        "weather_adjustment": weather_adjustment,
        "multi_event_conflict": multi_event_adjustment,
        "input_summary": {
            "urgency_score": round(_clamp(urgency_score), 4),
            "road_closure_likelihood": round(_clamp(road_closure_likelihood), 4),
            "hotspot_risk_score": round(derive_hotspot_risk(hotspot), 4),
            "similar_event_risk": round(similar_event_risk, 4),
        },
        "similar_event_summary": similar_event_meta,
        "vehicle_impact": {
            "multiplier": vehicle_impact.multiplier,
            "source": vehicle_impact.source,
            "sample_count": vehicle_impact.sample_count,
            "normalized_vehicle_type": vehicle_impact.normalized_vehicle_type,
            "note": vehicle_impact.note,
        },
    }
