from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ml.feature_pipeline import ROAD_CLOSURE_MODEL_PATH, build_road_closure_feature_row, safe_float
from app.orm.event import Event
from app.orm.event_feature import EventFeature


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().casefold()
    return normalized or None


def _dataset_positive_rate(db: Session) -> float:
    total = db.scalar(select(func.count()).select_from(Event)) or 0
    if total <= 0:
        return 0.0
    positives = db.scalar(
        select(func.count()).select_from(Event).where(Event.requires_road_closure.is_(True))
    ) or 0
    return positives / total


def _historical_rate(
    db: Session,
    feature: EventFeature | None,
    *,
    feature_value: float | None,
    column_name: str,
    event_value: str | None,
) -> float | None:
    if feature_value is not None:
        return float(feature_value)
    if not event_value:
        return None

    column = getattr(Event, column_name)
    total = db.scalar(select(func.count()).where(column == event_value)) or 0
    if total <= 0:
        return None
    positives = db.scalar(
        select(func.count()).where(column == event_value, Event.requires_road_closure.is_(True))
    ) or 0
    return positives / total


def _predict_supporting_ml_probability(
    event: Event,
    feature: EventFeature | None = None,
) -> tuple[float | None, str | None]:
    if not ROAD_CLOSURE_MODEL_PATH.exists():
        return None, None

    try:
        import joblib  # type: ignore[import-not-found]
        import pandas as pd  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        return None, "supporting_ml_dependency_missing"

    try:
        bundle: dict[str, Any] = joblib.load(ROAD_CLOSURE_MODEL_PATH)
        frame = pd.DataFrame([build_road_closure_feature_row(event, feature)])
        probability = float(bundle["pipeline"].predict_proba(frame)[0][1])
        return probability, None
    except Exception:
        return None, "supporting_ml_unavailable"


def estimate_road_closure_likelihood(
    db: Session,
    event: Event,
    *,
    feature: EventFeature | None = None,
) -> dict[str, object]:
    base_rate = _dataset_positive_rate(db)
    score = base_rate
    reasons = [f"dataset_positive_rate:{base_rate:.4f}"]

    cause_rate = _historical_rate(
        db,
        feature,
        feature_value=safe_float(feature.historical_cause_closure_rate) if feature and feature.historical_cause_closure_rate is not None else None,
        column_name="event_cause_clean",
        event_value=event.event_cause_clean,
    )
    corridor_rate = _historical_rate(
        db,
        feature,
        feature_value=safe_float(feature.historical_corridor_closure_rate) if feature and feature.historical_corridor_closure_rate is not None else None,
        column_name="corridor",
        event_value=event.corridor,
    )
    station_rate = _historical_rate(
        db,
        feature,
        feature_value=safe_float(feature.historical_police_station_closure_rate) if feature and feature.historical_police_station_closure_rate is not None else None,
        column_name="police_station",
        event_value=event.police_station,
    )
    cluster_rate = (
        safe_float(feature.historical_cluster_closure_rate)
        if feature and feature.historical_cluster_closure_rate is not None
        else None
    )

    for label, rate, weight in (
        ("cause_history", cause_rate, 0.35),
        ("corridor_history", corridor_rate, 0.2),
        ("station_history", station_rate, 0.15),
        ("cluster_history", cluster_rate, 0.1),
    ):
        if rate is None:
            continue
        score += rate * weight
        reasons.append(f"{label}:{rate:.3f}")

    priority = _normalize_text(event.priority)
    if priority in {"high", "critical"}:
        score += 0.12
        reasons.append("high_priority")
    elif priority == "medium":
        score += 0.05
        reasons.append("medium_priority")

    if event.event_type == "planned":
        score += 0.08
        reasons.append("planned_event")
    else:
        reasons.append("unplanned_event")

    if feature and feature.is_peak_hour:
        score += 0.05
        reasons.append("peak_hour")

    optional_ml_probability, ml_status = _predict_supporting_ml_probability(event, feature)
    method = "primary_rule_history"
    if optional_ml_probability is not None:
        score = (0.75 * score) + (0.25 * optional_ml_probability)
        reasons.append(f"ml_supporting_signal:{optional_ml_probability:.3f}")
        method = "primary_rule_history_with_optional_ml_support"
    elif ml_status is not None:
        reasons.append(ml_status)

    probability = round(min(max(score, 0.0), 1.0), 4)
    return {
        "road_closure_probability": probability,
        "predicted_road_closure": probability >= 0.5,
        "method": method,
        "reasons": reasons,
        "dataset_warning": "requires_road_closure TRUE is sparse; use as estimated likelihood, not exact prediction",
        "supporting_ml_probability": round(optional_ml_probability, 4) if optional_ml_probability is not None else None,
    }
