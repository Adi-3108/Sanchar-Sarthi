from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.ml.feature_pipeline import (
    DATA_FILTER_APPLIED,
    RESOLUTION_TIME_MODEL_PATH,
    build_resolution_time_feature_row,
)
from app.orm.event import Event
from app.orm.event_feature import EventFeature
from app.services.impact_score_service import resolve_vehicle_impact

RULE_BASED_ESTIMATES: dict[str, float] = {
    "vehicle_breakdown": 90.0,
    "accident": 110.0,
    "tree_fall": 180.0,
    "waterlogging": 240.0,
    "construction": 480.0,
    "public_event": 300.0,
    "procession": 240.0,
    "vip_movement": 180.0,
    "protest": 240.0,
    "crowd_buildup": 180.0,
    "congestion": 60.0,
    "pot_holes": 360.0,
    "road_conditions": 240.0,
    "others": 90.0,
    "unknown": 90.0,
}

RULE_BASED_RANGES: dict[str, tuple[float, float]] = {
    "vehicle_breakdown": (45.0, 120.0),
    "accident": (60.0, 150.0),
    "tree_fall": (90.0, 300.0),
    "waterlogging": (120.0, 360.0),
    "construction": (180.0, 600.0),
    "public_event": (120.0, 480.0),
    "procession": (90.0, 360.0),
    "vip_movement": (60.0, 240.0),
    "protest": (90.0, 300.0),
    "crowd_buildup": (90.0, 240.0),
    "congestion": (30.0, 120.0),
    "pot_holes": (120.0, 480.0),
    "road_conditions": (90.0, 360.0),
    "others": (45.0, 180.0),
    "unknown": (45.0, 180.0),
}

CAUSE_ALIASES = {
    "water_logging": "waterlogging",
    "waterlogging": "waterlogging",
    "crowd": "crowd_buildup",
}

VEHICLE_TYPE_ALIASES = {
    "mini truck": "lcv",
    "mini_truck": "lcv",
    "light commercial vehicle": "lcv",
}


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().casefold()
    return normalized or None


def _cause_key(event: Event) -> str:
    normalized = _normalize_text(event.event_cause_clean) or "unknown"
    return CAUSE_ALIASES.get(normalized, normalized)


def _vehicle_key(value: str | None) -> str:
    normalized = _normalize_text(value) or "unknown"
    return VEHICLE_TYPE_ALIASES.get(normalized, normalized)


def _vehicle_multiplier(event: Event, *, db: Session | None = None) -> float:
    return resolve_vehicle_impact(event.veh_type, db=db).multiplier


def _rule_estimate(event: Event, *, db: Session | None = None) -> tuple[float, str]:
    base = RULE_BASED_ESTIMATES.get(_cause_key(event), RULE_BASED_ESTIMATES["unknown"])
    vehicle_factor = _vehicle_multiplier(event, db=db)
    return round(base * vehicle_factor, 1), "rule_fallback"


def _rule_range(event: Event, *, db: Session | None = None) -> tuple[float, float]:
    lower, upper = RULE_BASED_RANGES.get(_cause_key(event), RULE_BASED_RANGES["unknown"])
    vehicle_factor = _vehicle_multiplier(event, db=db)
    return round(lower * vehicle_factor, 1), round(upper * vehicle_factor, 1)


def predict_resolution_time(
    event: Event,
    *,
    feature: EventFeature | None = None,
    db: Session | None = None,
) -> dict[str, object]:
    if RESOLUTION_TIME_MODEL_PATH.exists():
        try:
            import joblib  # type: ignore[import-not-found]
            import pandas as pd  # type: ignore[import-not-found]
        except ModuleNotFoundError:
            estimated_minutes, method = _rule_estimate(event, db=db)
            lower_bound, upper_bound = _rule_range(event, db=db)
            return {
                "estimated_clearance_minutes": estimated_minutes,
                "clearance_prediction_method": method,
                "clearance_confidence": 0.4,
                "clearance_confidence_note": "Rule-based estimate from ASTraM cause/vehicle patterns; ML dependencies are not installed locally.",
                "historical_clearance_range_min": lower_bound,
                "historical_clearance_range_max": upper_bound,
                "honesty_label": "Estimated clearance time, not a guaranteed operational commitment.",
                "data_filter_applied": DATA_FILTER_APPLIED,
            }

        try:
            bundle: dict[str, Any] = joblib.load(RESOLUTION_TIME_MODEL_PATH)
            frame = pd.DataFrame([build_resolution_time_feature_row(event, feature)])
            raw = float(bundle["pipeline"].predict(frame)[0])
            estimated_minutes = max(round(raw, 1), 1.0)
            metrics = dict(bundle.get("metrics", {}))
            mae = metrics.get("mae_minutes")
            training_rows = int(metrics.get("training_rows", 0) or 0)
            lower_bound = max(round(estimated_minutes - float(mae or 30.0), 1), 1.0)
            upper_bound = round(estimated_minutes + float(mae or 30.0), 1)
            confidence = 0.75 if training_rows >= 1000 else 0.6
            note = f"Based on {training_rows} qualifying ASTraM incidents with reliable clearance timestamps"
            if mae is not None:
                note += f". Typical error margin: +/-{float(mae):.0f} min"
            return {
                "estimated_clearance_minutes": estimated_minutes,
                "clearance_prediction_method": "ml_gradient_boosting",
                "clearance_confidence": confidence,
                "clearance_confidence_note": note,
                "historical_clearance_range_min": lower_bound,
                "historical_clearance_range_max": upper_bound,
                "honesty_label": "Estimated clearance time, not a guaranteed operational commitment.",
                "data_filter_applied": metrics.get("data_filter", DATA_FILTER_APPLIED),
            }
        except Exception:
            pass

    estimated_minutes, method = _rule_estimate(event, db=db)
    lower_bound, upper_bound = _rule_range(event, db=db)
    return {
        "estimated_clearance_minutes": estimated_minutes,
        "clearance_prediction_method": method,
        "clearance_confidence": 0.45,
        "clearance_confidence_note": "Rule-based estimate from ASTraM cause/vehicle patterns",
        "historical_clearance_range_min": lower_bound,
        "historical_clearance_range_max": upper_bound,
        "honesty_label": "Estimated clearance time, not a guaranteed operational commitment.",
        "data_filter_applied": DATA_FILTER_APPLIED,
    }
