from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.orm.event import Event
from app.orm.event_prediction import EventPrediction
from app.orm.event_recommendation import EventRecommendation
from app.services.barricade_service import BarricadeInput, recommend_barricades
from app.services.diversion_service import DiversionInput, recommend_diversion
from app.services.emergency_corridor_service import (
    EmergencyCorridorInput,
    recommend_emergency_corridor,
)
from app.services.logistics_impact_service import LogisticsImpactInput, assess_logistics_impact
from app.services.manpower_service import ManpowerInput, recommend_manpower

DATASET_HONESTY_NOTE = "Recommended actions are dataset-backed operational guidance, not a live city-control guarantee."


def _safe_float(value: Decimal | float | int | None, *, default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


@dataclass(frozen=True)
class RecommendationInput:
    event_id: str
    event_type: str
    event_cause_clean: str | None
    corridor: str | None
    police_station: str | None
    zone: str | None
    junction: str | None
    requires_road_closure: bool
    predicted_priority: str | None
    impact_score: float
    impact_category: str
    road_closure_probability: float
    predicted_road_closure: bool
    estimated_clearance_minutes: float | None
    estimated_radius_km: float
    vehicle_impact_factor: float | None
    baseline_risk_score: float | None
    additional_event_delta: float | None
    available_officers: int | None = None
    include_logistics_impact: bool = True
    include_emergency_corridor: bool = True
    prediction_explanation_json: dict[str, object] | None = None
    weather_adjustment_json: dict[str, object] | None = None


def build_recommendation_input(
    event: Event,
    prediction: EventPrediction,
    *,
    available_officers: int | None = None,
    include_logistics_impact: bool = True,
    include_emergency_corridor: bool = True,
) -> RecommendationInput:
    return RecommendationInput(
        event_id=event.id,
        event_type=event.event_type or "unplanned",
        event_cause_clean=event.event_cause_clean,
        corridor=event.corridor,
        police_station=event.police_station,
        zone=event.zone,
        junction=event.junction,
        requires_road_closure=event.requires_road_closure,
        predicted_priority=prediction.predicted_priority,
        impact_score=_safe_float(prediction.estimated_impact_score),
        impact_category=prediction.impact_category or "Low",
        road_closure_probability=_safe_float(prediction.road_closure_probability),
        predicted_road_closure=bool(prediction.predicted_road_closure),
        estimated_clearance_minutes=_safe_float(prediction.estimated_clearance_minutes, default=0.0)
        if prediction.estimated_clearance_minutes is not None
        else None,
        estimated_radius_km=_safe_float(prediction.impact_radius_km, default=1.5),
        vehicle_impact_factor=_safe_float(prediction.vehicle_impact_factor, default=1.0)
        if prediction.vehicle_impact_factor is not None
        else None,
        baseline_risk_score=_safe_float(prediction.baseline_risk_score)
        if prediction.baseline_risk_score is not None
        else None,
        additional_event_delta=_safe_float(prediction.additional_event_delta)
        if prediction.additional_event_delta is not None
        else None,
        available_officers=available_officers,
        include_logistics_impact=include_logistics_impact,
        include_emergency_corridor=include_emergency_corridor,
        prediction_explanation_json=dict(prediction.prediction_explanation_json or {}),
        weather_adjustment_json=dict(prediction.weather_adjustment_json or {}),
    )


def _prediction_confidence(input_data: RecommendationInput) -> float:
    priority = dict((input_data.prediction_explanation_json or {}).get("priority", {}) or {})
    method = str(priority.get("method") or "")
    if method == "priority_model":
        return 0.72
    if method == "rule_fallback":
        return 0.58
    return 0.5


def _closure_confidence(input_data: RecommendationInput) -> float:
    if input_data.road_closure_probability >= 0.75:
        return 0.7
    if input_data.road_closure_probability >= 0.45:
        return 0.62
    return 0.54


def _clearance_confidence(input_data: RecommendationInput) -> float:
    resolution = dict((input_data.prediction_explanation_json or {}).get("resolution_time", {}) or {})
    method = str(resolution.get("clearance_prediction_method") or "")
    if method == "ml_gradient_boosting":
        return 0.74
    if method == "rule_fallback":
        return 0.5
    return 0.45


def _weather_confidence(input_data: RecommendationInput) -> float:
    weather = dict(input_data.weather_adjustment_json or {})
    source = str(weather.get("source") or "")
    if source == "open_meteo_live":
        return 0.66
    if source.startswith("manual_"):
        return 0.6
    if source.startswith("open_meteo_"):
        return 0.42
    return 0.38


def build_weather_risk(input_data: RecommendationInput) -> dict[str, object]:
    weather = dict(input_data.weather_adjustment_json or {})
    if not weather:
        return {
            "weather_condition": "clear",
            "weather_factor": 1.0,
            "rain_mm": 0.0,
            "visibility_m": None,
            "low_visibility": False,
            "waterlogging_risk": "low",
            "reason_codes": [],
            "source": "phase10_default",
            "provider": None,
            "provider_status": "not_requested",
            "note": "No explicit weather risk was provided, so EventFlow AI used a neutral weather modifier.",
        }
    return weather


def apply_weather_to_barricades(
    barricade_plan: dict[str, object],
    weather_risk: dict[str, object],
) -> dict[str, object]:
    updated = dict(barricade_plan)
    reason_codes = list(updated.get("reason_codes", []))
    for reason in list(weather_risk.get("reason_codes", [])):
        if reason not in reason_codes:
            reason_codes.append(reason)

    weather_factor = _safe_float(weather_risk.get("weather_factor"))
    waterlogging_risk = str(weather_risk.get("waterlogging_risk") or "low")
    low_visibility = bool(weather_risk.get("low_visibility"))

    if weather_factor >= 1.2 or waterlogging_risk == "elevated":
        updated["barricade_level"] = "extended_buffer_with_slow_speed_channelization"
        updated["estimated_units"] = int(updated.get("estimated_units") or 0) + 2
        updated["field_note"] = "Increase taper distance and avoid pushing traffic through low-lying road segments."
    elif low_visibility:
        updated["field_note"] = "Strengthen reflector visibility and add slower channelization near the incident edge."

    placement_priority = list(updated.get("placement_priority", []))
    if waterlogging_risk in {"watch", "elevated"} and "avoid low-lying diversion entry" not in placement_priority:
        placement_priority.append("avoid low-lying diversion entry")
    updated["placement_priority"] = placement_priority[:6]
    updated["reason_codes"] = reason_codes
    return updated


def apply_weather_to_diversion(
    diversion_plan: dict[str, object],
    weather_risk: dict[str, object],
) -> dict[str, object]:
    updated = dict(diversion_plan)
    reason_codes = list(updated.get("reason_codes", []))
    for reason in list(weather_risk.get("reason_codes", [])):
        if reason not in reason_codes:
            reason_codes.append(reason)

    waterlogging_risk = str(weather_risk.get("waterlogging_risk") or "low")
    low_visibility = bool(weather_risk.get("low_visibility"))
    weather_factor = _safe_float(weather_risk.get("weather_factor"))
    upstream_focus_points = list(updated.get("upstream_focus_points", []))

    if waterlogging_risk == "elevated" or weather_factor >= 1.2:
        updated["strategy"] = "weather_buffered_hotspot_bypass"
        updated["diversion_scope"] = "avoid low-lying approaches and create wider upstream diversion buffers"
        updated["heavy_vehicle_advisory"] = "Move heavy vehicles away from low-lying corridors and flooded underpasses before hotspot entry."
        updated["field_note"] = "Do not route diversions through low-visibility or waterlogging-prone links without field confirmation."
    elif low_visibility:
        updated["field_note"] = "Advance upstream advisories earlier because visibility-related braking waves may widen the spillover radius."

    if waterlogging_risk in {"watch", "elevated"} and "avoid low-lying roads" not in upstream_focus_points:
        upstream_focus_points.append("avoid low-lying roads")
    if low_visibility and "advance warning farther upstream" not in upstream_focus_points:
        upstream_focus_points.append("advance warning farther upstream")

    updated["upstream_focus_points"] = upstream_focus_points[:5]
    updated["reason_codes"] = reason_codes
    return updated


def build_confidence_ledger(
    input_data: RecommendationInput,
    *,
    manpower: dict[str, object],
    diversion: dict[str, object],
) -> list[dict[str, object]]:
    ledger = [
        {
            "input": "ASTraM historical events",
            "confidence": 0.85,
            "note": "Core event patterns, corridors, and closure history come from the loaded ASTraM dataset.",
            "source": "dataset_history",
        },
        {
            "input": "Priority and impact estimate",
            "confidence": _prediction_confidence(input_data),
            "note": "Derived from Phase 7/8 rule-plus-optional-ML prediction layers.",
            "source": "prediction_stack",
        },
        {
            "input": "Road-closure likelihood",
            "confidence": _closure_confidence(input_data),
            "note": "Treat probability as the primary signal; the boolean closure flag is only an operational helper.",
            "source": "road_closure_probability",
        },
    ]
    weather_risk = build_weather_risk(input_data)
    if weather_risk.get("source") != "phase10_default" or weather_risk.get("reason_codes"):
        ledger.append(
            {
                "input": "Weather modifier",
                "confidence": _weather_confidence(input_data),
                "note": f"Weather input source: {weather_risk.get('source', 'unknown')}. This remains an operational adjustment, not a road-sensor ground truth feed.",
                "source": "phase10_weather_adjustment",
            }
        )
    ledger.extend(
        [
        {
            "input": "Manpower and diversion heuristics",
            "confidence": 0.6 if str(manpower.get("deployment_style")) != "point_control" else 0.55,
            "note": f"Uses {diversion.get('strategy', 'operational')} recommendation heuristics rather than live GPS fleet telemetry.",
            "source": "phase9_rule_orchestration",
        },
        {
            "input": "Live traffic speed",
            "confidence": 0.0,
            "note": "Not present in the ASTraM dataset or current MVP integrations.",
            "source": "future_live_integration",
        },
        ]
    )
    return ledger


def build_recommended_action_summary(
    input_data: RecommendationInput,
    *,
    manpower: dict[str, object],
    barricades: dict[str, object],
    diversion: dict[str, object],
) -> str:
    corridor = input_data.corridor or input_data.zone or "the impact zone"
    summary = (
        f"Deploy {manpower['recommended_total_officers']} officers in "
        f"{manpower['deployment_style'].replace('_', ' ')} around {corridor}. "
        f"Use {barricades['barricade_level'].replace('_', ' ')} and "
        f"{diversion['strategy'].replace('_', ' ')} operations."
    )
    weather_risk = build_weather_risk(input_data)
    if list(weather_risk.get("reason_codes", [])):
        summary += " Apply the weather-risk note before final field deployment."
    if int(manpower.get("officer_gap", 0) or 0) > 0:
        summary += f" Reallocate {manpower['officer_gap']} additional officers to reach the recommended posture."
    return summary


def generate_recommendation_plan(input_data: RecommendationInput) -> dict[str, object]:
    weather_risk = build_weather_risk(input_data)
    manpower = recommend_manpower(
        ManpowerInput(
            impact_score=input_data.impact_score,
            impact_category=input_data.impact_category,
            road_closure_probability=input_data.road_closure_probability,
            event_type=input_data.event_type,
            impact_radius_km=input_data.estimated_radius_km,
            available_officers=input_data.available_officers,
            corridor=input_data.corridor,
            junction=input_data.junction,
            police_station=input_data.police_station,
        )
    )
    barricades = recommend_barricades(
        BarricadeInput(
            impact_score=input_data.impact_score,
            impact_category=input_data.impact_category,
            road_closure_probability=input_data.road_closure_probability,
            impact_radius_km=input_data.estimated_radius_km,
            corridor=input_data.corridor,
            junction=input_data.junction,
        )
    )
    barricades = apply_weather_to_barricades(barricades, weather_risk)
    diversion = recommend_diversion(
        DiversionInput(
            impact_score=input_data.impact_score,
            impact_category=input_data.impact_category,
            road_closure_probability=input_data.road_closure_probability,
            impact_radius_km=input_data.estimated_radius_km,
            corridor=input_data.corridor,
            junction=input_data.junction,
            zone=input_data.zone,
        )
    )
    diversion = apply_weather_to_diversion(diversion, weather_risk)
    emergency_corridor = (
        recommend_emergency_corridor(
            EmergencyCorridorInput(
                impact_score=input_data.impact_score,
                impact_category=input_data.impact_category,
                road_closure_probability=input_data.road_closure_probability,
                corridor=input_data.corridor,
                police_station=input_data.police_station,
            )
        )
        if input_data.include_emergency_corridor
        else None
    )
    logistics_impact = (
        assess_logistics_impact(
            LogisticsImpactInput(
                impact_score=input_data.impact_score,
                impact_category=input_data.impact_category,
                impact_radius_km=input_data.estimated_radius_km,
                estimated_clearance_minutes=input_data.estimated_clearance_minutes,
                corridor=input_data.corridor,
                event_type=input_data.event_type,
            )
        )
        if input_data.include_logistics_impact
        else None
    )
    confidence_ledger = build_confidence_ledger(
        input_data,
        manpower=manpower,
        diversion=diversion,
    )
    recommended_action_summary = build_recommended_action_summary(
        input_data,
        manpower=manpower,
        barricades=barricades,
        diversion=diversion,
    )

    return {
        "event_id": input_data.event_id,
        "risk_summary": {
            "impact_score": round(input_data.impact_score, 2),
            "impact_category": input_data.impact_category,
            "road_closure_probability": round(input_data.road_closure_probability, 4),
            "predicted_priority": input_data.predicted_priority,
            "estimated_clearance_minutes": round(input_data.estimated_clearance_minutes, 2)
            if input_data.estimated_clearance_minutes is not None
            else None,
            "estimated_radius_km": round(input_data.estimated_radius_km, 2),
            "baseline_risk_score": round(input_data.baseline_risk_score, 2)
            if input_data.baseline_risk_score is not None
            else None,
            "additional_event_delta": round(input_data.additional_event_delta, 2)
            if input_data.additional_event_delta is not None
            else None,
            "honesty_note": DATASET_HONESTY_NOTE,
        },
        "weather_risk": weather_risk,
        "manpower": manpower,
        "barricades": barricades,
        "diversions": diversion,
        "emergency_corridor": emergency_corridor,
        "flipkart_logistics_impact": logistics_impact,
        "action_confidence_ledger": confidence_ledger,
        "recommended_action_summary": recommended_action_summary,
    }


def _get_or_create_recommendation_record(
    db: Session,
    event_id: str,
) -> tuple[EventRecommendation, bool]:
    existing_records = db.scalars(
        select(EventRecommendation)
        .where(EventRecommendation.event_id == event_id)
        .order_by(EventRecommendation.created_at.desc(), EventRecommendation.id.desc())
    ).all()
    if existing_records:
        record = existing_records[0]
        for duplicate in existing_records[1:]:
            db.delete(duplicate)
        return record, False

    record = EventRecommendation(event_id=event_id)
    db.add(record)
    return record, True


def persist_recommendation_plan(
    db: Session,
    plan: dict[str, object],
    *,
    commit: bool = True,
    persist: bool = True,
) -> tuple[EventRecommendation, bool]:
    event_id = str(plan["event_id"])
    if persist:
        record, created = _get_or_create_recommendation_record(db, event_id)
    else:
        record = EventRecommendation(event_id=event_id)
        created = False

    manpower = dict(plan.get("manpower") or {})
    record.recommended_total_officers = int(manpower.get("recommended_total_officers") or 0)
    record.deployment_plan_json = manpower
    record.barricade_plan_json = dict(plan.get("barricades") or {})
    record.diversion_plan_json = dict(plan.get("diversions") or {})
    record.emergency_corridor_json = (
        dict(plan.get("emergency_corridor") or {})
        if plan.get("emergency_corridor") is not None
        else None
    )
    record.logistics_impact_json = (
        dict(plan.get("flipkart_logistics_impact") or {})
        if plan.get("flipkart_logistics_impact") is not None
        else None
    )
    record.action_confidence_ledger_json = list(plan.get("action_confidence_ledger") or [])
    record.recommended_action_summary = str(plan.get("recommended_action_summary") or "")

    if persist and commit:
        db.commit()
        db.refresh(record)
    elif persist:
        db.flush()

    return record, created


def serialize_recommendation_plan(
    record: EventRecommendation | None,
) -> dict[str, Any] | None:
    if record is None:
        return None
    return {
        "event_id": record.event_id,
        "risk_summary": {},
        "weather_risk": None,
        "manpower": dict(record.deployment_plan_json or {}),
        "barricades": dict(record.barricade_plan_json or {}),
        "diversions": dict(record.diversion_plan_json or {}),
        "emergency_corridor": dict(record.emergency_corridor_json or {})
        if record.emergency_corridor_json is not None
        else None,
        "flipkart_logistics_impact": dict(record.logistics_impact_json or {})
        if record.logistics_impact_json is not None
        else None,
        "action_confidence_ledger": list(record.action_confidence_ledger_json or []),
        "recommended_action_summary": record.recommended_action_summary,
    }


def merge_risk_summary_into_plan(
    plan: dict[str, object],
    prediction: EventPrediction | None,
) -> dict[str, object]:
    if prediction is None:
        return plan
    merged = dict(plan)
    merged["weather_risk"] = dict(prediction.weather_adjustment_json or {})
    merged["risk_summary"] = {
        "impact_score": _safe_float(prediction.estimated_impact_score),
        "impact_category": prediction.impact_category or "Low",
        "road_closure_probability": _safe_float(prediction.road_closure_probability),
        "predicted_priority": prediction.predicted_priority,
        "estimated_clearance_minutes": (
            _safe_float(prediction.estimated_clearance_minutes)
            if prediction.estimated_clearance_minutes is not None
            else None
        ),
        "estimated_radius_km": _safe_float(prediction.impact_radius_km, default=1.5),
        "baseline_risk_score": (
            _safe_float(prediction.baseline_risk_score)
            if prediction.baseline_risk_score is not None
            else None
        ),
        "additional_event_delta": (
            _safe_float(prediction.additional_event_delta)
            if prediction.additional_event_delta is not None
            else None
        ),
        "honesty_note": DATASET_HONESTY_NOTE,
    }
    return merged
