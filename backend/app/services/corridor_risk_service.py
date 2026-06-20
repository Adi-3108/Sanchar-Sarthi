from __future__ import annotations

from datetime import datetime, time, timedelta

from sqlalchemy import Integer, case, cast, func, or_
from sqlalchemy.orm import Session

from app.orm.event import Event
from app.orm.event_feature import EventFeature
from app.schemas.corridor_analytics import CorridorRiskTimelineResponse, HourlyRiskPoint

_CORRIDOR_ALIAS_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"orr", "outer ring road", "outer ring rd"}),
    frozenset({"omr", "old madras road", "old madras rd"}),
    frozenset({"bannerghatta road", "bannerghata road", "bannerghatta rd"}),
    frozenset({"bellary road", "bellary rd", "ballari road", "airport road"}),
    frozenset({"tumkur road", "tumakuru road"}),
    frozenset({"hosur road", "hosur rd"}),
)


def _normalize_corridor(value: str) -> str:
    return " ".join(value.casefold().replace("-", " ").split())


def _expand_corridor_aliases(corridor: str) -> set[str]:
    normalized = _normalize_corridor(corridor)
    aliases = {normalized}
    for alias_group in _CORRIDOR_ALIAS_GROUPS:
        if normalized in alias_group:
            aliases.update(alias_group)
    return aliases


def _corridor_matchers(corridor: str) -> list[object]:
    aliases = sorted(_expand_corridor_aliases(corridor))
    return [Event.corridor.ilike(f"%{alias}%") for alias in aliases if alias]


def _reference_week_start(latest_event_at: datetime) -> datetime:
    days_since_sunday = (latest_event_at.weekday() + 1) % 7
    reference_date = (latest_event_at - timedelta(days=days_since_sunday)).date()
    reference = datetime.combine(reference_date, time.min)
    if latest_event_at.tzinfo is not None:
        reference = reference.replace(tzinfo=latest_event_at.tzinfo)
    return reference


class CorridorRiskService:
    def __init__(self, db: Session):
        self.db = db

    def get_risk_timeline(self, corridor: str, days: int) -> CorridorRiskTimelineResponse:
        corridor_name = corridor.strip()
        corridor_filters = _corridor_matchers(corridor_name)
        if not corridor_filters:
            raise LookupError("Corridor name is required.")

        latest_event_at = (
            self.db.query(func.max(Event.start_datetime))
            .filter(Event.start_datetime.is_not(None))
            .filter(or_(*corridor_filters))
            .scalar()
        )
        if latest_event_at is None:
            raise LookupError(f"No historical event data found for corridor '{corridor_name}'.")

        end_date = latest_event_at
        start_date = end_date - timedelta(days=days)

        priority_score = case(
            (func.lower(func.coalesce(Event.priority, "")) == "high", 82.0),
            (func.lower(func.coalesce(Event.priority, "")) == "medium", 58.0),
            (func.lower(func.coalesce(Event.priority, "")) == "low", 34.0),
            else_=24.0,
        )
        historical_component = func.coalesce(EventFeature.historical_corridor_risk * 100.0, priority_score)
        closure_bonus = case((Event.requires_road_closure.is_(True), 12.0), else_=0.0)
        peak_bonus = case((EventFeature.is_peak_hour.is_(True), 8.0), else_=0.0)
        risk_expression = (priority_score * 0.55) + (historical_component * 0.35) + closure_bonus + peak_bonus

        hour_expression = cast(func.extract("hour", Event.start_datetime), Integer)
        day_expression = cast(func.extract("dow", Event.start_datetime), Integer)

        rows = (
            self.db.query(
                hour_expression.label("hour"),
                day_expression.label("day_of_week"),
                func.avg(risk_expression).label("avg_risk"),
                func.count(Event.id).label("event_count"),
            )
            .outerjoin(EventFeature, EventFeature.event_id == Event.id)
            .filter(or_(*corridor_filters))
            .filter(Event.start_datetime >= start_date)
            .filter(Event.start_datetime <= end_date)
            .group_by(hour_expression, day_expression)
            .order_by(day_expression, hour_expression)
            .all()
        )

        if not rows:
            raise LookupError(f"No usable historical timestamps found for corridor '{corridor_name}'.")

        bucket_lookup: dict[tuple[int, int], tuple[float, int]] = {}
        hour_risk_totals: dict[int, float] = {}
        hour_event_totals: dict[int, int] = {}
        total_weighted_risk = 0.0
        total_events = 0

        for row in rows:
            hour = int(row.hour)
            day_of_week = int(row.day_of_week)
            risk_score = round(float(row.avg_risk), 2)
            event_count = int(row.event_count)

            bucket_lookup[(day_of_week, hour)] = (risk_score, event_count)
            hour_risk_totals[hour] = hour_risk_totals.get(hour, 0.0) + (risk_score * event_count)
            hour_event_totals[hour] = hour_event_totals.get(hour, 0) + event_count
            total_weighted_risk += risk_score * event_count
            total_events += event_count

        reference_week_start = _reference_week_start(end_date)
        hourly_scores: list[HourlyRiskPoint] = []
        for day_of_week in range(7):
            for hour in range(24):
                risk_score, event_count = bucket_lookup.get((day_of_week, hour), (0.0, 0))
                timestamp = (reference_week_start + timedelta(days=day_of_week, hours=hour)).isoformat()
                hourly_scores.append(
                    HourlyRiskPoint(
                        timestamp=timestamp,
                        hour=hour,
                        day_of_week=day_of_week,
                        risk_score=risk_score,
                        event_count=event_count,
                    )
                )

        peak_hours = sorted(
            hour_risk_totals,
            key=lambda hour: (
                -(hour_risk_totals[hour] / max(hour_event_totals[hour], 1)),
                -hour_event_totals[hour],
                hour,
            ),
        )[:3]

        average_risk_score = round(total_weighted_risk / total_events, 2) if total_events else 0.0

        return CorridorRiskTimelineResponse(
            corridor=corridor_name,
            days_analyzed=days,
            hourly_risk_scores=hourly_scores,
            peak_risk_hours=peak_hours,
            average_risk_score=average_risk_score,
        )

