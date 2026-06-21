from __future__ import annotations

import asyncio
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.database import build_engine
from app.core.roles import canonical_role
from app.core.config import get_settings
from app.db.base import import_model_modules
from app.orm.citizen_report import CitizenReport
from app.orm.event import Event
from app.orm.event_dna import EventDna
from app.orm.event_feature import EventFeature
from app.orm.event_prediction import EventPrediction
from app.orm.event_recommendation import EventRecommendation
from app.orm.hotspot_cluster import HotspotCluster
from app.orm.incident import Incident
from app.orm.live_event_update import LiveEventUpdate
from app.orm.post_event_report import PostEventReport
from app.orm.rag_chunk import RagChunk
from app.services.rag_embedding_service import embed_text_sync

import_model_modules()


@dataclass(frozen=True)
class ChunkSpec:
    chunk_type: str
    text: str
    visibility: str


@dataclass(frozen=True)
class RagIndexReport:
    records_indexed: int
    chunks_upserted: int
    chunk_types: dict[str, int]


def _serialize_json(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _compact(value: str | None, *, limit: int = 500) -> str:
    if not value:
        return ""
    collapsed = " ".join(str(value).split())
    if len(collapsed) <= limit:
        return collapsed
    return f"{collapsed[: limit - 3].rstrip()}..."


def _float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_identifier(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return UUID(value)
        except ValueError:
            return value
    return value


def _latest_event_prediction(db: Session, event_id: str) -> EventPrediction | None:
    return db.scalars(
        select(EventPrediction)
        .where(EventPrediction.event_id == event_id)
        .order_by(EventPrediction.created_at.desc(), EventPrediction.id.desc())
        .limit(1)
    ).first()


def _latest_event_dna(db: Session, event_id: str) -> EventDna | None:
    return db.scalars(
        select(EventDna)
        .where(EventDna.event_id == event_id)
        .order_by(EventDna.created_at.desc(), EventDna.id.desc())
        .limit(1)
    ).first()


def _latest_event_recommendation(db: Session, event_id: str) -> EventRecommendation | None:
    return db.scalars(
        select(EventRecommendation)
        .where(EventRecommendation.event_id == event_id)
        .order_by(EventRecommendation.created_at.desc(), EventRecommendation.id.desc())
        .limit(1)
    ).first()


def _latest_event_feature(db: Session, event_id: str) -> EventFeature | None:
    return db.scalars(
        select(EventFeature)
        .where(EventFeature.event_id == event_id)
        .order_by(EventFeature.created_at.desc(), EventFeature.id.desc())
        .limit(1)
    ).first()


def _incident_visibility(incident: Incident) -> str:
    return "public" if incident.visible_to_public else "control_room"


def _report_visibility(report: CitizenReport) -> str:
    return "control_room"


def _event_specs(db: Session, event: Event) -> list[ChunkSpec]:
    prediction = _latest_event_prediction(db, event.id)
    feature = _latest_event_feature(db, event.id)

    event_lines = [
        f"Event {event.id}: {event.event_cause_clean or event.event_cause or 'unknown_cause'} in {event.corridor or 'unknown corridor'} near {event.junction or 'unknown junction'}.",
        f"Status {event.status or 'unknown'}, priority {event.priority or 'unknown'}, type {event.event_type or 'unknown'}, police station {event.police_station or 'unknown'}, zone {event.zone or 'unknown'}.",
        f"Road closure {'required' if event.requires_road_closure else 'not required'}; vehicle type {event.veh_type or 'unknown'}.",
    ]
    if event.start_datetime is not None:
        event_lines.append(f"Start time {event.start_datetime.isoformat()}.")
    if prediction is not None:
        probability = _float(prediction.road_closure_probability)
        estimated_impact = _float(prediction.estimated_impact_score)
        radius = _float(prediction.impact_radius_km)
        clearance = _float(prediction.estimated_clearance_minutes)
        event_lines.append(
            "Prediction snapshot: "
            f"priority {prediction.predicted_priority or 'unknown'}, "
            f"impact {estimated_impact if estimated_impact is not None else 'n/a'}, "
            f"road closure probability {round(probability * 100, 1) if probability is not None and probability <= 1 else probability or 'n/a'}, "
            f"clearance minutes {clearance if clearance is not None else 'n/a'}, "
            f"radius km {radius if radius is not None else 'n/a'}."
        )
    if feature is not None:
        event_lines.append(
            "Feature snapshot: "
            f"weekend {feature.is_weekend}, peak hour {feature.is_peak_hour}, night event {feature.is_night_event}, "
            f"historical corridor risk {_float(feature.historical_corridor_risk) if feature.historical_corridor_risk is not None else 'n/a'}, "
            f"location cluster {feature.location_cluster_id or 'n/a'}."
        )
    if event.description:
        event_lines.append(f"Description: {_compact(event.description)}")

    specs = [ChunkSpec("event", " ".join(event_lines), "control_room")]

    dna = _latest_event_dna(db, event.id)
    if dna is not None:
        specs.append(
            ChunkSpec(
                "event_dna",
                " ".join(
                    [
                        f"Event DNA for {event.id}: {_compact(dna.dna_summary)}",
                        f"Time context: {_compact(dna.time_context)}",
                        f"Location context: {_compact(dna.location_context)}",
                        f"Cause context: {_compact(dna.cause_context)}",
                        f"Weather context: {_compact(dna.weather_context)}" if dna.weather_context else "",
                        f"Historical pattern: {_compact(dna.historical_pattern)}",
                        f"Risk indicators: {_serialize_json(dna.risk_indicators_json)}",
                        f"Similar event ids: {_serialize_json(dna.similar_event_ids_json)}",
                    ]
                ).strip(),
                "control_room",
            )
        )

    recommendation = _latest_event_recommendation(db, event.id)
    if recommendation is not None:
        specs.append(
            ChunkSpec(
                "recommendation",
                " ".join(
                    [
                        f"Recommendation plan for {event.id}: {_compact(recommendation.recommended_action_summary)}",
                        f"Recommended officers: {recommendation.recommended_total_officers or 0}.",
                        f"Risk summary: {_serialize_json(recommendation.risk_summary_json)}",
                        f"Weather risk: {_serialize_json(recommendation.weather_risk_json)}",
                        f"Deployment: {_serialize_json(recommendation.deployment_plan_json)}",
                        f"Barricades: {_serialize_json(recommendation.barricade_plan_json)}",
                        f"Diversions: {_serialize_json(recommendation.diversion_plan_json)}",
                        f"Emergency corridor: {_serialize_json(recommendation.emergency_corridor_json)}",
                        f"Logistics impact: {_serialize_json(recommendation.logistics_impact_json)}",
                    ]
                ).strip(),
                "control_room",
            )
        )

    return specs


def _incident_specs(incident: Incident) -> list[ChunkSpec]:
    return [
        ChunkSpec(
            "incident",
            " ".join(
                [
                    f"Incident {incident.id}: {incident.title}.",
                    f"Type {incident.incident_type}, status {incident.status}, severity {incident.severity}, source {incident.source_type}.",
                    f"Location {incident.location_name} near {incident.locality or incident.ward or 'unknown locality'}.",
                    f"Confidence {_float(incident.confidence_score) if incident.confidence_score is not None else 'n/a'}, station {incident.assigned_station_name or 'unassigned'}.",
                    f"Route impact: {_compact(incident.route_impact_summary)}" if incident.route_impact_summary else "",
                    f"Resolution notes: {_compact(incident.resolution_notes)}" if incident.resolution_notes else "",
                    f"Description: {_compact(incident.description)}" if incident.description else "",
                ]
            ).strip(),
            _incident_visibility(incident),
        )
    ]


def _citizen_report_specs(report: CitizenReport) -> list[ChunkSpec]:
    return [
        ChunkSpec(
            "citizen_report",
            " ".join(
                [
                    f"Citizen report {report.id}: source {report.report_source}, type {report.report_type}, severity {report.severity or 'unknown'}.",
                    f"Matched event {report.matched_event_id or report.event_id or 'none'}, alert {report.new_alert_level or 'unknown'}, confidence {_float(report.report_confidence) if report.report_confidence is not None else 'n/a'}.",
                    f"Location {report.latitude:.5f}, {report.longitude:.5f}.",
                    f"Recommended action: {_compact(report.recommended_action)}" if report.recommended_action else "",
                    f"Description: {_compact(report.translated_description or report.description)}" if (report.translated_description or report.description) else "",
                ]
            ).strip(),
            _report_visibility(report),
        )
    ]


def _live_update_specs(update: LiveEventUpdate, event: Event | None) -> list[ChunkSpec]:
    event_context = ""
    if event is not None:
        event_context = (
            f"Related event {event.id} on {event.corridor or 'unknown corridor'} near {event.junction or 'unknown junction'}."
        )
    return [
        ChunkSpec(
            "live_update",
            " ".join(
                [
                    f"Live update {update.id} for event {update.event_id}: {update.current_congestion_level} from {update.update_source}.",
                    event_context,
                    f"Expected impact {_float(update.expected_impact_score) if update.expected_impact_score is not None else 'n/a'}, current impact {_float(update.current_impact_score) if update.current_impact_score is not None else 'n/a'}, deviation {_float(update.impact_deviation) if update.impact_deviation is not None else 'n/a'}.",
                    f"Alert {update.alert_level or 'unknown'}, road closure {update.road_closure_active}, officer shortage {update.officer_shortage}, crowd increase {update.crowd_increase}, rain/waterlogging {update.rain_waterlogging}, new nearby incident {update.new_nearby_incident}.",
                    f"Field update: {_compact(update.field_update)}" if update.field_update else "",
                    f"Adaptive action: {_compact(update.adaptive_action)}" if update.adaptive_action else "",
                ]
            ).strip(),
            "control_room",
        )
    ]


def _post_event_report_specs(report: PostEventReport) -> list[ChunkSpec]:
    return [
        ChunkSpec(
            "post_event_report",
            " ".join(
                [
                    f"Post-event report {report.id} for event {report.event_id}: final status {report.final_status or 'unknown'}.",
                    f"Predicted impact {_float(report.predicted_impact_score) if report.predicted_impact_score is not None else 'n/a'}, observed impact {_float(report.simulated_actual_impact_score) if report.simulated_actual_impact_score is not None else 'n/a'}, deviation {_float(report.impact_deviation) if report.impact_deviation is not None else 'n/a'}.",
                    f"Event summary: {_compact(report.event_summary)}",
                    f"Prediction summary: {_compact(report.prediction_summary)}",
                    f"Recommendation summary: {_compact(report.recommendation_summary)}",
                    f"Citizen report summary: {_compact(report.citizen_report_summary)}" if report.citizen_report_summary else "",
                    f"Live escalation summary: {_compact(report.live_escalation_summary)}" if report.live_escalation_summary else "",
                    f"Lessons learned: {_compact(report.lessons_learned)}",
                    f"Future recommendations: {_compact(report.future_recommendations)}",
                ]
            ).strip(),
            "admin",
        )
    ]


def _hotspot_specs(hotspot: HotspotCluster) -> list[ChunkSpec]:
    return [
        ChunkSpec(
            "hotspot",
            " ".join(
                [
                    f"Hotspot {hotspot.location_cluster_id}: risk score {_float(hotspot.cluster_risk_score) if hotspot.cluster_risk_score is not None else 'n/a'}, event count {hotspot.cluster_event_count}.",
                    f"Top cause {hotspot.cluster_top_event_cause or 'unknown'}, high-priority rate {_float(hotspot.cluster_high_priority_rate) if hotspot.cluster_high_priority_rate is not None else 'n/a'}, road-closure rate {_float(hotspot.cluster_road_closure_rate) if hotspot.cluster_road_closure_rate is not None else 'n/a'}, peak-hour rate {_float(hotspot.cluster_peak_hour_rate) if hotspot.cluster_peak_hour_rate is not None else 'n/a'}.",
                    f"Cluster profile: {_serialize_json(hotspot.cluster_profile_json)}",
                ]
            ).strip(),
            "control_room",
        )
    ]


def _replace_source_chunks(
    db: Session,
    *,
    source_table: str,
    source_id: str,
    chunk_specs: list[ChunkSpec],
) -> int:
    existing_rows = db.scalars(
        select(RagChunk).where(RagChunk.source_table == source_table, RagChunk.source_id == source_id)
    ).all()
    existing_by_type = {row.chunk_type: row for row in existing_rows}
    retained_types: set[str] = set()
    upserted = 0

    for spec in chunk_specs:
        retained_types.add(spec.chunk_type)
        embedding = embed_text_sync(spec.text)
        row = existing_by_type.get(spec.chunk_type)
        if row is None:
            row = RagChunk(
                source_table=source_table,
                source_id=source_id,
                chunk_type=spec.chunk_type,
                chunk_text=spec.text,
                embedding=embedding,
                visibility=spec.visibility,
            )
            db.add(row)
        else:
            row.chunk_text = spec.text
            row.embedding = embedding
            row.visibility = spec.visibility
            row.updated_at = datetime.now(timezone.utc)
        upserted += 1

    for row in existing_rows:
        if row.chunk_type not in retained_types:
            db.delete(row)

    db.flush()
    return upserted


def delete_source_chunks(db: Session, source_table: str, source_id: str, *, commit: bool = False) -> int:
    result = db.execute(
        delete(RagChunk).where(RagChunk.source_table == source_table, RagChunk.source_id == source_id)
    )
    if commit:
        db.commit()
    else:
        db.flush()
    return int(result.rowcount or 0)


def index_event_record(db: Session, event_id: str, *, commit: bool = False) -> RagIndexReport:
    event = db.get(Event, event_id)
    if event is None:
        deleted = 0
        for source_table in ("events", "event_dna", "event_recommendations"):
            deleted += delete_source_chunks(db, source_table, event_id, commit=False)
        if commit:
            db.commit()
        return RagIndexReport(records_indexed=0, chunks_upserted=deleted, chunk_types={})

    counts = Counter()
    upserted = _replace_source_chunks(db, source_table="events", source_id=event.id, chunk_specs=_event_specs(db, event))
    counts.update(spec.chunk_type for spec in _event_specs(db, event))

    if commit:
        db.commit()
    return RagIndexReport(records_indexed=1, chunks_upserted=upserted, chunk_types=dict(counts))


def index_incident_record(db: Session, incident_id: str, *, commit: bool = False) -> RagIndexReport:
    incident = db.get(Incident, incident_id)
    specs = _incident_specs(incident) if incident is not None else []
    upserted = _replace_source_chunks(db, source_table="incidents", source_id=incident_id, chunk_specs=specs) if incident is not None else delete_source_chunks(db, "incidents", incident_id, commit=False)
    if commit:
        db.commit()
    return RagIndexReport(records_indexed=1 if incident is not None else 0, chunks_upserted=upserted, chunk_types={spec.chunk_type: 1 for spec in specs})


def index_citizen_report_record(db: Session, report_id: str, *, commit: bool = False) -> RagIndexReport:
    report = db.get(CitizenReport, _coerce_identifier(report_id))
    specs = _citizen_report_specs(report) if report is not None else []
    source_id = str(report.id) if report is not None else str(report_id)
    upserted = _replace_source_chunks(db, source_table="citizen_reports", source_id=source_id, chunk_specs=specs) if report is not None else delete_source_chunks(db, "citizen_reports", source_id, commit=False)
    if commit:
        db.commit()
    return RagIndexReport(records_indexed=1 if report is not None else 0, chunks_upserted=upserted, chunk_types={spec.chunk_type: 1 for spec in specs})


def index_live_update_record(db: Session, update_id: str, *, commit: bool = False) -> RagIndexReport:
    update = db.get(LiveEventUpdate, _coerce_identifier(update_id))
    event = db.get(Event, update.event_id) if update is not None else None
    specs = _live_update_specs(update, event) if update is not None else []
    source_id = str(update.id) if update is not None else str(update_id)
    upserted = _replace_source_chunks(db, source_table="live_event_updates", source_id=source_id, chunk_specs=specs) if update is not None else delete_source_chunks(db, "live_event_updates", source_id, commit=False)
    if commit:
        db.commit()
    return RagIndexReport(records_indexed=1 if update is not None else 0, chunks_upserted=upserted, chunk_types={spec.chunk_type: 1 for spec in specs})


def index_post_event_report_record(db: Session, report_id: str, *, commit: bool = False) -> RagIndexReport:
    report = db.get(PostEventReport, _coerce_identifier(report_id))
    specs = _post_event_report_specs(report) if report is not None else []
    source_id = str(report.id) if report is not None else str(report_id)
    upserted = _replace_source_chunks(db, source_table="post_event_reports", source_id=source_id, chunk_specs=specs) if report is not None else delete_source_chunks(db, "post_event_reports", source_id, commit=False)
    if commit:
        db.commit()
    return RagIndexReport(records_indexed=1 if report is not None else 0, chunks_upserted=upserted, chunk_types={spec.chunk_type: 1 for spec in specs})


def index_hotspot_record(db: Session, location_cluster_id: str, *, commit: bool = False) -> RagIndexReport:
    hotspot = db.scalars(
        select(HotspotCluster).where(HotspotCluster.location_cluster_id == location_cluster_id).limit(1)
    ).first()
    specs = _hotspot_specs(hotspot) if hotspot is not None else []
    upserted = _replace_source_chunks(db, source_table="hotspot_clusters", source_id=location_cluster_id, chunk_specs=specs) if hotspot is not None else delete_source_chunks(db, "hotspot_clusters", location_cluster_id, commit=False)
    if commit:
        db.commit()
    return RagIndexReport(records_indexed=1 if hotspot is not None else 0, chunks_upserted=upserted, chunk_types={spec.chunk_type: 1 for spec in specs})


def reindex_all_hotspots(db: Session, *, commit: bool = False) -> RagIndexReport:
    db.execute(delete(RagChunk).where(RagChunk.source_table == "hotspot_clusters"))
    records = 0
    chunks = 0
    counts = Counter()
    for hotspot in db.scalars(select(HotspotCluster).order_by(HotspotCluster.location_cluster_id)).all():
        report = index_hotspot_record(db, hotspot.location_cluster_id, commit=False)
        records += report.records_indexed
        chunks += report.chunks_upserted
        counts.update(report.chunk_types)
    if commit:
        db.commit()
    return RagIndexReport(records_indexed=records, chunks_upserted=chunks, chunk_types=dict(counts))


def rebuild_rag_index(db: Session, *, commit: bool = False) -> RagIndexReport:
    db.execute(delete(RagChunk))
    records = 0
    chunks = 0
    counts = Counter()

    for incident in db.scalars(select(Incident).order_by(Incident.updated_at.desc(), Incident.id.desc())).all():
        report = index_incident_record(db, incident.id, commit=False)
        records += report.records_indexed
        chunks += report.chunks_upserted
        counts.update(report.chunk_types)

    for event in db.scalars(select(Event).order_by(Event.updated_at.desc(), Event.id.desc())).all():
        report = index_event_record(db, event.id, commit=False)
        records += report.records_indexed
        chunks += report.chunks_upserted
        counts.update(report.chunk_types)

    for report_row in db.scalars(select(CitizenReport).order_by(CitizenReport.created_at.desc(), CitizenReport.id.desc())).all():
        report = index_citizen_report_record(db, str(report_row.id), commit=False)
        records += report.records_indexed
        chunks += report.chunks_upserted
        counts.update(report.chunk_types)

    for update in db.scalars(select(LiveEventUpdate).order_by(LiveEventUpdate.created_at.desc(), LiveEventUpdate.id.desc())).all():
        report = index_live_update_record(db, str(update.id), commit=False)
        records += report.records_indexed
        chunks += report.chunks_upserted
        counts.update(report.chunk_types)

    for report_row in db.scalars(select(PostEventReport).order_by(PostEventReport.created_at.desc(), PostEventReport.id.desc())).all():
        report = index_post_event_report_record(db, str(report_row.id), commit=False)
        records += report.records_indexed
        chunks += report.chunks_upserted
        counts.update(report.chunk_types)

    hotspot_report = reindex_all_hotspots(db, commit=False)
    records += hotspot_report.records_indexed
    chunks += hotspot_report.chunks_upserted
    counts.update(hotspot_report.chunk_types)

    if commit:
        db.commit()
    else:
        db.flush()

    return RagIndexReport(records_indexed=records, chunks_upserted=chunks, chunk_types=dict(counts))


def get_rag_index_status(db: Session) -> dict[str, Any]:
    total_chunks = int(db.scalar(select(func.count()).select_from(RagChunk)) or 0)
    latest_updated_at = db.scalar(select(func.max(RagChunk.updated_at)).select_from(RagChunk))
    by_visibility_rows = db.execute(
        select(RagChunk.visibility, func.count()).group_by(RagChunk.visibility)
    ).all()
    by_type_rows = db.execute(
        select(RagChunk.chunk_type, func.count()).group_by(RagChunk.chunk_type)
    ).all()
    settings = get_settings()
    return {
        "enabled": settings.rag_enabled,
        "llm_provider": settings.rag_llm_provider,
        "embedding_provider": settings.rag_embedding_provider,
        "chunk_count": total_chunks,
        "by_visibility": {str(key): int(value) for key, value in by_visibility_rows},
        "by_type": {str(key): int(value) for key, value in by_type_rows},
        "latest_updated_at": latest_updated_at.isoformat() if latest_updated_at else None,
    }


def _periodic_refresh_recent_live_updates_sync() -> None:
    engine = build_engine()
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    with SessionLocal() as db:
        recent_updates = db.scalars(
            select(LiveEventUpdate).order_by(LiveEventUpdate.created_at.desc(), LiveEventUpdate.id.desc()).limit(25)
        ).all()
        for update in recent_updates:
            index_live_update_record(db, str(update.id), commit=False)
        db.commit()


async def periodic_live_update_index_loop(interval_seconds: int = 300) -> None:
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            await asyncio.to_thread(_periodic_refresh_recent_live_updates_sync)
        except Exception:
            continue

