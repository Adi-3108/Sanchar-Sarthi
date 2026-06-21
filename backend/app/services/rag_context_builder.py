from __future__ import annotations

import asyncio
import json
import math
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from sqlalchemy import case, desc, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.roles import canonical_role
from app.orm.citizen_report import CitizenReport
from app.orm.event import Event
from app.orm.event_dna import EventDna
from app.orm.event_prediction import EventPrediction
from app.orm.event_recommendation import EventRecommendation
from app.orm.hotspot_cluster import HotspotCluster
from app.orm.incident import Incident
from app.orm.live_event_update import LiveEventUpdate
from app.orm.map_api_usage_log import MapApiUsageLog
from app.orm.model_run import ModelRun
from app.orm.post_event_report import PostEventReport
from app.orm.rag_chunk import RagChunk
from app.orm.system_audit_log import SystemAuditLog
from app.services.rag_embedding_service import embed_text

STOP_WORDS = {
    "about",
    "active",
    "after",
    "alert",
    "alerts",
    "along",
    "around",
    "before",
    "between",
    "build",
    "current",
    "events",
    "event",
    "have",
    "history",
    "incident",
    "incidents",
    "latest",
    "near",
    "need",
    "open",
    "plan",
    "reports",
    "show",
    "status",
    "there",
    "today",
    "traffic",
    "what",
    "which",
}
TOKEN_PATTERN = re.compile(r"[a-z0-9_:-]+", re.IGNORECASE)


class Intent(Enum):
    CURRENT_STATUS = "current_status"
    HISTORICAL = "historical"
    OPERATIONAL = "operational"
    INCIDENT = "incident"
    ANALYTICS = "analytics"
    GENERAL = "general"


@dataclass(frozen=True)
class ContextSource:
    chunk_type: str
    source_id: str
    similarity: float


@dataclass(frozen=True)
class ContextChunk:
    text: str
    source: ContextSource


def classify_intent(question: str) -> Intent:
    q = question.lower()
    if any(word in q for word in ["right now", "active", "current", "today", "open", "how many", "count"]):
        return Intent.CURRENT_STATUS
    if any(word in q for word in ["last time", "similar", "pattern", "what happened", "past", "history", "before"]):
        return Intent.HISTORICAL
    if any(word in q for word in ["officer", "barricade", "diversion", "deployment", "plan", "recommend"]):
        return Intent.OPERATIONAL
    if any(word in q for word in ["incident", "report", "complaint", "near me", "nearby"]):
        return Intent.INCIDENT
    if any(word in q for word in ["most", "highest", "corridor", "zone", "risk", "rate", "audit", "log"]):
        return Intent.ANALYTICS
    return Intent.GENERAL


def _allowed_visibilities(role: str) -> tuple[str, ...]:
    normalized_role = canonical_role(role)
    if normalized_role == "admin":
        return ("public", "control_room", "admin")
    if normalized_role == "control_room_officer":
        return ("public", "control_room")
    return ("public",)


def _extract_focus_terms(question: str) -> set[str]:
    return {
        token.lower()
        for token in TOKEN_PATTERN.findall(question)
        if len(token) > 2 and token.lower() not in STOP_WORDS
    }


def _matches_focus(texts: list[str | None], terms: set[str]) -> bool:
    if not terms:
        return True
    blob = " ".join(part for part in texts if part).lower()
    return any(term in blob for term in terms)


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    length = min(len(left), len(right))
    numerator = sum(float(left[index]) * float(right[index]) for index in range(length))
    left_norm = math.sqrt(sum(float(value) * float(value) for value in left[:length])) or 1.0
    right_norm = math.sqrt(sum(float(value) * float(value) for value in right[:length])) or 1.0
    return numerator / (left_norm * right_norm)


def _serialize_json(value: Any) -> str:
    if not value:
        return "n/a"
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _clean_text(value: str | None, *, limit: int = 420) -> str:
    if not value:
        return ""
    collapsed = " ".join(value.split())
    if len(collapsed) <= limit:
        return collapsed
    return f"{collapsed[: limit - 3]}..."


def _vector_chunks_python(
    db: Session,
    question_embedding: list[float],
    visibilities: tuple[str, ...],
    *,
    top_k: int,
    event_id: str | None,
) -> list[ContextChunk]:
    rows = db.scalars(
        select(RagChunk).where(RagChunk.visibility.in_(visibilities))
    ).all()
    scored: list[ContextChunk] = []
    for row in rows:
        similarity = _cosine_similarity(question_embedding, list(row.embedding or []))
        if event_id and row.source_id == event_id:
            similarity = min(similarity + 0.15, 0.9999)
        scored.append(
            ContextChunk(
                text=f"[{row.chunk_type}:{row.source_id}] {row.chunk_text}",
                source=ContextSource(
                    chunk_type=row.chunk_type,
                    source_id=row.source_id,
                    similarity=round(similarity, 4),
                ),
            )
        )
    scored.sort(key=lambda item: item.source.similarity, reverse=True)
    return scored[:top_k]


async def _vector_chunks(
    db: Session,
    question: str,
    role: str,
    *,
    event_id: str | None,
) -> list[ContextChunk]:
    settings = get_settings()
    visibilities = _allowed_visibilities(role)
    question_embedding = await embed_text(question)
    top_k = settings.rag_vector_top_k

    try:
        distance = RagChunk.embedding.cosine_distance(question_embedding)
        ranking = case((RagChunk.source_id == event_id, 0), else_=1) if event_id else None
        query = (
            select(RagChunk, (1 - distance).label("similarity"))
            .where(RagChunk.visibility.in_(visibilities))
        )
        if ranking is not None:
            query = query.order_by(ranking, distance)
        else:
            query = query.order_by(distance)
        rows = db.execute(query.limit(top_k)).all()
        chunks: list[ContextChunk] = []
        for row, similarity in rows:
            similarity_value = float(similarity if similarity is not None else 0.0)
            if event_id and row.source_id == event_id:
                similarity_value = min(similarity_value + 0.15, 0.9999)
            chunks.append(
                ContextChunk(
                    text=f"[{row.chunk_type}:{row.source_id}] {row.chunk_text}",
                    source=ContextSource(
                        chunk_type=row.chunk_type,
                        source_id=row.source_id,
                        similarity=round(similarity_value, 4),
                    ),
                )
            )
        return chunks
    except Exception:
        return _vector_chunks_python(db, question_embedding, visibilities, top_k=top_k, event_id=event_id)


def _event_focus_chunks(db: Session, role: str, event_id: str | None) -> list[ContextChunk]:
    if not event_id:
        return []
    normalized_role = canonical_role(role)
    if normalized_role not in {"admin", "control_room_officer"}:
        return []

    chunks: list[ContextChunk] = []
    event = db.get(Event, event_id)
    if event is None:
        return chunks

    base_text = (
        f"Focused event {event.id}: {event.event_cause_clean or event.event_cause or 'unknown_cause'} "
        f"on {event.corridor or 'unknown corridor'} near {event.junction or 'unknown junction'}; "
        f"priority {event.priority or 'unknown'}, status {event.status or 'unknown'}, "
        f"road closure {'required' if event.requires_road_closure else 'not required'}."
    )
    chunks.append(
        ContextChunk(
            text=base_text,
            source=ContextSource(chunk_type="event_focus", source_id=event.id, similarity=1.0),
        )
    )

    dna = db.scalar(
        select(EventDna).where(EventDna.event_id == event.id).order_by(desc(EventDna.created_at), desc(EventDna.id))
    )
    if dna is not None:
        chunks.append(
            ContextChunk(
                text=(
                    f"Focused Event DNA for {event.id}: {dna.dna_summary} "
                    f"Time context: {dna.time_context} Location: {dna.location_context} "
                    f"Cause context: {dna.cause_context} Historical pattern: {dna.historical_pattern}"
                ),
                source=ContextSource(chunk_type="event_dna_focus", source_id=event.id, similarity=1.0),
            )
        )

    prediction = db.scalar(
        select(EventPrediction)
        .where(EventPrediction.event_id == event.id)
        .order_by(desc(EventPrediction.created_at), desc(EventPrediction.id))
    )
    if prediction is not None:
        chunks.append(
            ContextChunk(
                text=(
                    f"Focused prediction for {event.id}: priority {prediction.predicted_priority or 'unknown'} "
                    f"with confidence {float(prediction.priority_confidence or 0):.2f}; "
                    f"impact {float(prediction.estimated_impact_score or 0):.2f}; "
                    f"clearance {float(prediction.estimated_clearance_minutes or 0):.1f} minutes; "
                    f"closure probability {float(prediction.road_closure_probability or 0):.2f}."
                ),
                source=ContextSource(chunk_type="prediction_focus", source_id=event.id, similarity=1.0),
            )
        )

    recommendation = db.scalar(
        select(EventRecommendation)
        .where(EventRecommendation.event_id == event.id)
        .order_by(desc(EventRecommendation.created_at), desc(EventRecommendation.id))
    )
    if recommendation is not None:
        chunks.append(
            ContextChunk(
                text=(
                    f"Focused recommendation for {event.id}: {recommendation.recommended_action_summary} "
                    f"Recommended officers {recommendation.recommended_total_officers or 0}. "
                    f"Manpower: {_serialize_json(recommendation.deployment_plan_json)} "
                    f"Barricades: {_serialize_json(recommendation.barricade_plan_json)} "
                    f"Diversions: {_serialize_json(recommendation.diversion_plan_json)}"
                ),
                source=ContextSource(chunk_type="recommendation_focus", source_id=event.id, similarity=1.0),
            )
        )

    live_update = db.scalar(
        select(LiveEventUpdate)
        .where(LiveEventUpdate.event_id == event.id)
        .order_by(desc(LiveEventUpdate.created_at), desc(LiveEventUpdate.id))
    )
    if live_update is not None:
        chunks.append(
            ContextChunk(
                text=(
                    f"Focused live update for {event.id}: level {live_update.current_congestion_level}; "
                    f"impact {float(live_update.current_impact_score or 0):.2f}; "
                    f"deviation {float(live_update.impact_deviation or 0):.2f}; "
                    f"action {_clean_text(live_update.adaptive_action)}."
                ),
                source=ContextSource(chunk_type="live_update_focus", source_id=event.id, similarity=1.0),
            )
        )

    report = db.scalar(
        select(PostEventReport)
        .where(PostEventReport.event_id == event.id)
        .order_by(desc(PostEventReport.created_at), desc(PostEventReport.id))
    )
    if report is not None:
        visibility = "admin" if normalized_role == "admin" else "control_room"
        if visibility in _allowed_visibilities(role):
            chunks.append(
                ContextChunk(
                    text=(
                        f"Focused after-action report for {event.id}: {report.event_summary} "
                        f"Lessons learned: {report.lessons_learned} "
                        f"Future recommendations: {report.future_recommendations}"
                    ),
                    source=ContextSource(chunk_type="post_event_focus", source_id=event.id, similarity=1.0),
                )
            )

    return chunks


def _current_status_chunks(db: Session, role: str, terms: set[str]) -> list[ContextChunk]:
    limit = get_settings().rag_sql_live_limit
    chunks: list[ContextChunk] = []
    for event in db.scalars(select(Event).order_by(desc(Event.updated_at), desc(Event.id)).limit(limit * 2)).all():
        if event.status and str(event.status).casefold() in {"resolved", "archived"}:
            continue
        if not _matches_focus([event.id, event.corridor, event.police_station, event.junction, event.event_cause_clean], terms):
            continue
        chunks.append(
            ContextChunk(
                text=(
                    f"Live event {event.id}: cause {event.event_cause_clean or event.event_cause or 'unknown'}, "
                    f"status {event.status or 'unknown'}, priority {event.priority or 'unknown'}, "
                    f"corridor {event.corridor or 'unknown'}, station {event.police_station or 'unknown'}, "
                    f"junction {event.junction or 'unknown'}."
                ),
                source=ContextSource(chunk_type="live_event", source_id=event.id, similarity=1.0),
            )
        )
        if len(chunks) >= limit:
            break

    incident_query = select(Incident).order_by(desc(Incident.updated_at), desc(Incident.id)).limit(limit * 2)
    if canonical_role(role) not in {"admin", "control_room_officer"}:
        incident_query = incident_query.where(Incident.visible_to_public.is_(True))
    incident_count = 0
    for incident in db.scalars(incident_query).all():
        if incident.status in {"resolved", "rejected", "archived"}:
            continue
        if not _matches_focus([incident.id, incident.title, incident.location_name, incident.locality], terms):
            continue
        chunks.append(
            ContextChunk(
                text=(
                    f"Live incident {incident.id}: {incident.title} at {incident.location_name}; "
                    f"status {incident.status}, severity {incident.severity}, confidence {float(incident.confidence_score or 0):.2f}."
                ),
                source=ContextSource(chunk_type="live_incident", source_id=incident.id, similarity=1.0),
            )
        )
        incident_count += 1
        if incident_count >= limit:
            break

    return chunks[: limit * 2]


def _historical_chunks(db: Session, role: str, terms: set[str]) -> list[ContextChunk]:
    limit = get_settings().rag_sql_live_limit
    normalized_role = canonical_role(role)
    if normalized_role not in {"admin", "control_room_officer"}:
        return []
    chunks: list[ContextChunk] = []
    for report in db.scalars(select(PostEventReport).order_by(desc(PostEventReport.created_at), desc(PostEventReport.id)).limit(limit * 2)).all():
        if not _matches_focus([report.event_id, report.event_summary, report.lessons_learned], terms):
            continue
        chunks.append(
            ContextChunk(
                text=(
                    f"Historical after-action report for {report.event_id}: {report.event_summary} "
                    f"Prediction summary: {report.prediction_summary} "
                    f"Lessons learned: {report.lessons_learned}"
                ),
                source=ContextSource(chunk_type="historical_post_event", source_id=report.event_id, similarity=1.0),
            )
        )
        if len(chunks) >= limit:
            break
    return chunks


def _operational_chunks(db: Session, role: str, terms: set[str]) -> list[ContextChunk]:
    limit = get_settings().rag_sql_live_limit
    normalized_role = canonical_role(role)
    if normalized_role not in {"admin", "control_room_officer"}:
        return []
    chunks: list[ContextChunk] = []
    for recommendation in db.scalars(select(EventRecommendation).order_by(desc(EventRecommendation.created_at), desc(EventRecommendation.id)).limit(limit * 2)).all():
        event = db.get(Event, recommendation.event_id)
        if not _matches_focus([
            recommendation.event_id,
            recommendation.recommended_action_summary,
            event.corridor if event else None,
            event.police_station if event else None,
            event.junction if event else None,
        ], terms):
            continue
        chunks.append(
            ContextChunk(
                text=(
                    f"Operational plan for {recommendation.event_id}: {recommendation.recommended_action_summary} "
                    f"Recommended officers {recommendation.recommended_total_officers or 0}. "
                    f"Deployment {_serialize_json(recommendation.deployment_plan_json)}"
                ),
                source=ContextSource(chunk_type="operational_plan", source_id=recommendation.event_id, similarity=1.0),
            )
        )
        if len(chunks) >= limit:
            break
    return chunks


def _incident_chunks(db: Session, role: str, terms: set[str]) -> list[ContextChunk]:
    limit = get_settings().rag_sql_live_limit
    normalized_role = canonical_role(role)
    chunks: list[ContextChunk] = []
    report_query = select(CitizenReport).order_by(desc(CitizenReport.created_at), desc(CitizenReport.id)).limit(limit * 3)
    if normalized_role not in {"admin", "control_room_officer"}:
        report_query = report_query.where(CitizenReport.report_source == "citizen")
    for report in db.scalars(report_query).all():
        if not _matches_focus([report.report_type, report.description, report.matched_event_id, report.event_id], terms):
            continue
        chunks.append(
            ContextChunk(
                text=(
                    f"Citizen report {report.id}: source {report.report_source}, type {report.report_type}, "
                    f"severity {report.severity or 'unknown'}, matched event {report.matched_event_id or report.event_id or 'none'}, "
                    f"alert {report.new_alert_level or 'unknown'}. Description: {_clean_text(report.translated_description or report.description)}"
                ),
                source=ContextSource(chunk_type="incident_report", source_id=str(report.id), similarity=1.0),
            )
        )
        if len(chunks) >= limit:
            break
    return chunks


def _analytics_chunks(db: Session, role: str, terms: set[str]) -> list[ContextChunk]:
    limit = get_settings().rag_sql_live_limit
    normalized_role = canonical_role(role)
    chunks: list[ContextChunk] = []

    for hotspot in db.scalars(select(HotspotCluster).order_by(desc(HotspotCluster.cluster_risk_score), desc(HotspotCluster.cluster_event_count)).limit(limit)).all():
        if not _matches_focus([hotspot.location_cluster_id, hotspot.cluster_top_event_cause, _serialize_json(hotspot.cluster_profile_json)], terms):
            continue
        chunks.append(
            ContextChunk(
                text=(
                    f"Hotspot {hotspot.location_cluster_id}: risk score {float(hotspot.cluster_risk_score):.2f}, "
                    f"events {hotspot.cluster_event_count}, top cause {hotspot.cluster_top_event_cause or 'unknown'}, "
                    f"peak-hour rate {float(hotspot.cluster_peak_hour_rate or 0):.2f}."
                ),
                source=ContextSource(chunk_type="hotspot_analytics", source_id=hotspot.location_cluster_id, similarity=1.0),
            )
        )

    if normalized_role == "admin":
        for model_run in db.scalars(select(ModelRun).order_by(desc(ModelRun.created_at), desc(ModelRun.id)).limit(3)).all():
            chunks.append(
                ContextChunk(
                    text=(
                        f"Model run {model_run.model_name} {model_run.model_version}: training rows {model_run.training_rows}, "
                        f"test rows {model_run.test_rows}, metrics {_serialize_json(model_run.metrics_json)}."
                    ),
                    source=ContextSource(chunk_type="model_run", source_id=str(model_run.id), similarity=1.0),
                )
            )
        for log in db.scalars(select(SystemAuditLog).order_by(desc(SystemAuditLog.created_at), desc(SystemAuditLog.id)).limit(5)).all():
            if not _matches_focus([log.action, log.resource_type, log.resource_id], terms):
                continue
            chunks.append(
                ContextChunk(
                    text=(
                        f"Audit log {log.action} on {log.resource_type} {log.resource_id or 'n/a'} by {log.actor_role}; "
                        f"metadata {_serialize_json(log.metadata_json)}."
                    ),
                    source=ContextSource(chunk_type="audit_log", source_id=str(log.id), similarity=1.0),
                )
            )
        for usage in db.scalars(select(MapApiUsageLog).order_by(desc(MapApiUsageLog.created_at), desc(MapApiUsageLog.id)).limit(3)).all():
            chunks.append(
                ContextChunk(
                    text=(
                        f"Map API usage {usage.provider}/{usage.api_name}: status {usage.status}, "
                        f"cost INR {float(usage.estimated_cost_inr):.2f}, cache hit {usage.cache_hit}."
                    ),
                    source=ContextSource(chunk_type="map_usage", source_id=str(usage.id), similarity=1.0),
                )
            )
    return chunks[: limit * 2]


def _general_chunks(db: Session, role: str, terms: set[str]) -> list[ContextChunk]:
    chunks = _current_status_chunks(db, role, terms)
    chunks.extend(_analytics_chunks(db, role, terms)[:3])
    return chunks


async def _live_sql_chunks(
    db: Session,
    question: str,
    role: str,
    *,
    event_id: str | None,
) -> list[ContextChunk]:
    intent = classify_intent(question)
    terms = _extract_focus_terms(question)
    focused = _event_focus_chunks(db, role, event_id)
    if intent == Intent.CURRENT_STATUS:
        return focused + _current_status_chunks(db, role, terms)
    if intent == Intent.HISTORICAL:
        return focused + _historical_chunks(db, role, terms)
    if intent == Intent.OPERATIONAL:
        return focused + _operational_chunks(db, role, terms)
    if intent == Intent.INCIDENT:
        return focused + _incident_chunks(db, role, terms)
    if intent == Intent.ANALYTICS:
        return focused + _analytics_chunks(db, role, terms)
    return focused + _general_chunks(db, role, terms)


def _deduplicate_sources(sources: list[ContextSource]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str], ContextSource] = {}
    for source in sources:
        key = (source.chunk_type, source.source_id)
        existing = by_key.get(key)
        if existing is None or source.similarity > existing.similarity:
            by_key[key] = source
    ordered = sorted(by_key.values(), key=lambda source: source.similarity, reverse=True)
    return [
        {
            "chunk_type": source.chunk_type,
            "source_id": source.source_id,
            "similarity": round(source.similarity, 4),
        }
        for source in ordered
    ]


async def build_context(
    db: Session,
    question: str,
    role: str,
    event_id: str | None = None,
) -> tuple[list[str], list[dict[str, Any]]]:
    vector_task = _vector_chunks(db, question, role, event_id=event_id)
    live_task = _live_sql_chunks(db, question, role, event_id=event_id)
    vector_chunks, live_chunks = await asyncio.gather(vector_task, live_task)

    merged: list[ContextChunk] = []
    seen_texts: set[str] = set()
    for item in [*live_chunks, *vector_chunks]:
        if item.text in seen_texts:
            continue
        seen_texts.add(item.text)
        merged.append(item)

    return [item.text for item in merged], _deduplicate_sources([item.source for item in merged])
