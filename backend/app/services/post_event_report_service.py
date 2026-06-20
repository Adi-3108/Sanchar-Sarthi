from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.orm.citizen_report import CitizenReport
from app.orm.event import Event
from app.orm.event_prediction import EventPrediction
from app.orm.event_recommendation import EventRecommendation
from app.orm.live_event_update import LiveEventUpdate
from app.orm.post_event_report import PostEventReport


def _safe_float(value: Decimal | float | int | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _format_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{round(value * 100)}%"


def _format_number(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def _format_datetime(value: datetime | None) -> str:
    if value is None:
        return "unknown time"
    normalized = value.astimezone(timezone.utc) if value.tzinfo else value
    return normalized.strftime("%Y-%m-%d %H:%M UTC")


def _get_latest_prediction(db: Session, event_id: str) -> EventPrediction | None:
    return db.scalars(
        select(EventPrediction)
        .where(EventPrediction.event_id == event_id)
        .order_by(EventPrediction.created_at.desc(), EventPrediction.id.desc())
    ).first()


def _get_latest_recommendation(db: Session, event_id: str) -> EventRecommendation | None:
    return db.scalars(
        select(EventRecommendation)
        .where(EventRecommendation.event_id == event_id)
        .order_by(EventRecommendation.created_at.desc(), EventRecommendation.id.desc())
    ).first()


def _list_reports(db: Session, event_id: str) -> list[CitizenReport]:
    return db.scalars(
        select(CitizenReport)
        .where(CitizenReport.event_id == event_id)
        .order_by(CitizenReport.created_at.desc(), CitizenReport.id.desc())
    ).all()


def _list_live_updates(db: Session, event_id: str) -> list[LiveEventUpdate]:
    return db.scalars(
        select(LiveEventUpdate)
        .where(LiveEventUpdate.event_id == event_id)
        .order_by(LiveEventUpdate.created_at.desc(), LiveEventUpdate.id.desc())
    ).all()


def _event_summary(event: Event) -> str:
    return (
        f"{(event.event_type or 'event').replace('_', ' ')} "
        f"{(event.event_cause_clean or 'unknown cause').replace('_', ' ')}"
        f" at {event.corridor or event.zone or 'the active corridor'}"
        f" near {event.police_station or 'the assigned station'},"
        f" started {_format_datetime(event.start_datetime)}."
        f" Final recorded status: {event.status or 'not specified'}."
    )


def _prediction_summary(prediction: EventPrediction | None) -> str:
    if prediction is None:
        return "No persisted prediction snapshot was available for this after-action review."

    return (
        f"Predicted {(prediction.impact_category or 'unknown').replace('_', ' ')} impact"
        f" at score {_format_number(_safe_float(prediction.estimated_impact_score))},"
        f" road-closure likelihood {_format_percent(_safe_float(prediction.road_closure_probability))},"
        f" estimated clearance {_format_number(_safe_float(prediction.estimated_clearance_minutes))} minutes,"
        f" and priority {(prediction.predicted_priority or 'unknown')}."
    )


def _recommendation_summary(recommendation: EventRecommendation | None) -> str:
    if recommendation is None:
        return "No persisted recommendation snapshot was available for this after-action review."

    stored_summary = (recommendation.recommended_action_summary or "").strip()
    if stored_summary:
        return stored_summary

    manpower = dict(recommendation.deployment_plan_json or {})
    barricades = dict(recommendation.barricade_plan_json or {})
    diversions = dict(recommendation.diversion_plan_json or {})

    def humanize(value: object | None, fallback: str) -> str:
        raw = str(value or fallback).replace("_", " ").strip()
        return raw or fallback

    recommended_officers = recommendation.recommended_total_officers
    if recommended_officers is None:
        recommended_officers = int(manpower.get("recommended_total_officers") or 0)

    return (
        f"Stored plan called for {recommended_officers} officers"
        f" in {humanize(manpower.get('deployment_style'), 'operational')} posture,"
        f" with {humanize(barricades.get('barricade_level'), 'baseline')} barricade coverage"
        f" and {humanize(diversions.get('strategy'), 'standard')} diversion guidance."
    )


def _citizen_report_summary(reports: list[CitizenReport]) -> str | None:
    if not reports:
        return "No citizen, field, or control-room reports were attached to this event."

    source_counts = Counter((report.report_source or "unknown").replace("_", " ") for report in reports)
    high_confidence = sum(1 for report in reports if (_safe_float(report.report_confidence) or 0) >= 0.7)
    latest_alert = next((report.new_alert_level for report in reports if report.new_alert_level), "Info")
    top_sources = ", ".join(f"{source}: {count}" for source, count in source_counts.most_common(3))
    return (
        f"{len(reports)} linked reports were considered,"
        f" {high_confidence} of them at high confidence,"
        f" with latest alert level {latest_alert}. Source mix: {top_sources}."
    )


def _live_escalation_summary(updates: list[LiveEventUpdate]) -> str | None:
    if not updates:
        return "No live escalation timeline was recorded for this event."

    latest = updates[0]
    highest_score = max((_safe_float(update.current_impact_score) or 0.0) for update in updates)
    highest_deviation = max((_safe_float(update.impact_deviation) or 0.0) for update in updates)
    critical_count = sum(1 for update in updates if (update.alert_level or "").casefold() == "critical")
    return (
        f"{len(updates)} live updates were recorded,"
        f" latest alert {(latest.alert_level or latest.current_congestion_level or 'Stable').replace('_', ' ')},"
        f" highest current impact {_format_number(highest_score)},"
        f" and peak deviation {_format_number(highest_deviation)}."
        f" Critical updates observed: {critical_count}."
    )


def _build_lessons(
    *,
    prediction: EventPrediction | None,
    recommendation: EventRecommendation | None,
    reports: list[CitizenReport],
    updates: list[LiveEventUpdate],
) -> list[str]:
    lessons: list[str] = []
    predicted_score = _safe_float(prediction.estimated_impact_score) if prediction is not None else None
    latest_actual_score = max((_safe_float(update.current_impact_score) or 0.0) for update in updates) if updates else None

    if len(reports) >= 3:
        lessons.append(
            "Multiple reports reinforced the event pressure signal; similar events should keep report monitoring active earlier in the lifecycle."
        )
    if predicted_score is not None and latest_actual_score is not None and latest_actual_score - predicted_score >= 10:
        lessons.append(
            "Live conditions materially exceeded the predicted impact score; similar events should reserve extra adaptive manpower and diversion capacity."
        )
    if recommendation is not None:
        manpower = dict(recommendation.deployment_plan_json or {})
        if int(manpower.get("officer_gap") or 0) > 0:
            lessons.append(
                "The stored recommendation showed an officer gap; reserve staffing should be committed earlier for comparable corridor events."
            )
        weather_risk = dict(recommendation.weather_risk_json or {})
        if list(weather_risk.get("reason_codes", [])):
            lessons.append(
                "Weather-aware planning changed the operational posture; similar wet-weather events should pre-stage barricade and diversion adjustments sooner."
            )
    if any((update.alert_level or "").casefold() == "critical" for update in updates):
        lessons.append(
            "Critical live escalation was reached during the event; the future playbook should include explicit trigger thresholds for command escalation."
        )

    return lessons or [
        "No strong post-event learning spike was detected; retain the baseline playbook and collect richer field outcomes next time."
    ]


def _future_recommendations(
    *,
    event: Event,
    prediction: EventPrediction | None,
    recommendation: EventRecommendation | None,
    reports: list[CitizenReport],
    updates: list[LiveEventUpdate],
) -> str:
    parts = [
        f"Use this Event DNA profile for similar {(event.corridor or event.zone or 'corridor')} events in future planning."
    ]
    if prediction is not None and _safe_float(prediction.road_closure_probability):
        parts.append(
            f"Treat road-closure likelihood around {_format_percent(_safe_float(prediction.road_closure_probability))} as an early staging threshold for upstream control."
        )
    if recommendation is not None:
        diversions = dict(recommendation.diversion_plan_json or {})
        if diversions.get("strategy") is not None:
            parts.append(
                f"Rehearse the {(str(diversions['strategy']).replace('_', ' '))} diversion pattern before the next comparable activation."
            )
    if reports or updates:
        parts.append(
            "Keep citizen reports and live field updates in the same review loop so the playbook reflects both early warning and escalation reality."
        )
    return " ".join(parts)


def _report_json(
    *,
    event: Event,
    prediction: EventPrediction | None,
    recommendation: EventRecommendation | None,
    reports: list[CitizenReport],
    updates: list[LiveEventUpdate],
    lessons: list[str],
) -> dict[str, object]:
    source_counts = Counter((report.report_source or "unknown") for report in reports)
    return {
        "event_id": event.id,
        "event_status": event.status,
        "event_cause_clean": event.event_cause_clean,
        "corridor": event.corridor,
        "police_station": event.police_station,
        "predicted_impact_score": _safe_float(prediction.estimated_impact_score) if prediction is not None else None,
        "predicted_priority": prediction.predicted_priority if prediction is not None else None,
        "road_closure_probability": _safe_float(prediction.road_closure_probability) if prediction is not None else None,
        "recommended_total_officers": recommendation.recommended_total_officers if recommendation is not None else None,
        "recommendation_weather_source": (
            recommendation.weather_risk_json.get("source")
            if recommendation is not None and isinstance(recommendation.weather_risk_json, dict)
            else None
        ),
        "report_count": len(reports),
        "report_source_mix": dict(source_counts),
        "high_confidence_report_count": sum(
            1 for report in reports if (_safe_float(report.report_confidence) or 0) >= 0.7
        ),
        "live_update_count": len(updates),
        "critical_live_update_count": sum(
            1 for update in updates if (update.alert_level or "").casefold() == "critical"
        ),
        "max_current_impact_score": max(
            (_safe_float(update.current_impact_score) or 0.0) for update in updates
        ) if updates else None,
        "max_impact_deviation": max(
            (_safe_float(update.impact_deviation) or 0.0) for update in updates
        ) if updates else None,
        "lessons": lessons,
    }


def generate_post_event_report(
    db: Session,
    event_id: str,
    *,
    commit: bool = True,
) -> PostEventReport:
    event = db.get(Event, event_id)
    if event is None:
        raise ValueError("Event not found")

    prediction = _get_latest_prediction(db, event_id)
    if prediction is None:
        from app.services.feature_engineering_service import build_features_for_event
        from app.services.prediction_service import predict_event
        from app.orm.hotspot_cluster import HotspotCluster
        
        feature, _ = build_features_for_event(db, event, commit=False)
        hotspot = None
        if feature.location_cluster_id:
            hotspot = db.scalars(
                select(HotspotCluster).where(HotspotCluster.location_cluster_id == feature.location_cluster_id)
            ).first()
            
        prediction, _ = predict_event(
            db,
            event,
            feature=feature,
            hotspot=hotspot,
            commit=False,
            persist=False,
        )

    recommendation = _get_latest_recommendation(db, event_id)
    if recommendation is None and prediction is not None:
        from app.services.recommendation_orchestrator import build_recommendation_input, generate_recommendation_plan
        rec_input = build_recommendation_input(event, prediction)
        plan_dict = generate_recommendation_plan(rec_input)
        recommendation = EventRecommendation(
            event_id=event.id,
            recommended_total_officers=int(dict(plan_dict.get("manpower") or {}).get("recommended_total_officers") or 0),
            deployment_plan_json=plan_dict.get("manpower"),
            barricade_plan_json=plan_dict.get("barricades"),
            diversion_plan_json=plan_dict.get("diversions"),
            emergency_corridor_json=plan_dict.get("emergency_corridor"),
            logistics_impact_json=plan_dict.get("flipkart_logistics_impact"),
            action_confidence_ledger_json=plan_dict.get("action_confidence_ledger"),
            recommended_action_summary=str(plan_dict.get("recommended_action_summary") or ""),
            weather_risk_json=plan_dict.get("weather_risk"),
            risk_summary_json=plan_dict.get("risk_summary")
        )
    reports = _list_reports(db, event_id)
    updates = _list_live_updates(db, event_id)
    lessons = _build_lessons(
        prediction=prediction,
        recommendation=recommendation,
        reports=reports,
        updates=updates,
    )

    predicted_score = _safe_float(prediction.estimated_impact_score) if prediction is not None else None
    actual_score = (
        max((_safe_float(update.current_impact_score) or 0.0) for update in updates)
        if updates
        else predicted_score
    )
    impact_deviation = (
        (actual_score - predicted_score)
        if predicted_score is not None and actual_score is not None
        else None
    )
    final_status = (
        event.status
        or (updates[0].alert_level if updates else None)
        or "review_generated"
    )

    record = PostEventReport(
        event_id=event_id,
        predicted_impact_score=predicted_score,
        simulated_actual_impact_score=actual_score,
        impact_deviation=impact_deviation,
        final_status=final_status,
        event_summary=_event_summary(event),
        prediction_summary=_prediction_summary(prediction),
        recommendation_summary=_recommendation_summary(recommendation),
        citizen_report_summary=_citizen_report_summary(reports),
        live_escalation_summary=_live_escalation_summary(updates),
        lessons_learned=" ".join(lessons),
        future_recommendations=_future_recommendations(
            event=event,
            prediction=prediction,
            recommendation=recommendation,
            reports=reports,
            updates=updates,
        ),
        report_json=_report_json(
            event=event,
            prediction=prediction,
            recommendation=recommendation,
            reports=reports,
            updates=updates,
            lessons=lessons,
        ),
    )
    db.add(record)
    if commit:
        db.commit()
        db.refresh(record)
    else:
        db.flush()
    return record


def serialize_post_event_report(record: PostEventReport) -> dict[str, object]:
    return {
        "event_id": record.event_id,
        "predicted_impact_score": _safe_float(record.predicted_impact_score),
        "simulated_actual_impact_score": _safe_float(record.simulated_actual_impact_score),
        "impact_deviation": _safe_float(record.impact_deviation),
        "final_status": record.final_status,
        "event_summary": record.event_summary,
        "prediction_summary": record.prediction_summary,
        "recommendation_summary": record.recommendation_summary,
        "citizen_report_summary": record.citizen_report_summary,
        "live_escalation_summary": record.live_escalation_summary,
        "lessons_learned": record.lessons_learned,
        "future_recommendations": record.future_recommendations,
        "report_json": dict(record.report_json or {}),
        "created_at": (
            record.created_at.astimezone(timezone.utc).isoformat()
            if isinstance(record.created_at, datetime) and record.created_at.tzinfo
            else record.created_at.isoformat()
            if isinstance(record.created_at, datetime)
            else None
        ),
    }

