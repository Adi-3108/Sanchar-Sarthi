from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base, import_model_modules
from app.orm.citizen_report import CitizenReport
from app.orm.event import Event
from app.orm.event_dna import EventDna
from app.orm.event_feature import EventFeature
from app.orm.event_prediction import EventPrediction
from app.orm.event_recommendation import EventRecommendation
from app.orm.hotspot_cluster import HotspotCluster
from app.orm.live_event_update import LiveEventUpdate
from app.orm.post_event_report import PostEventReport
from app.orm.rag_chunk import RagChunk
from app.services.rag_indexer_service import (
    index_citizen_report_record,
    index_event_record,
    index_hotspot_record,
    index_live_update_record,
    index_post_event_report_record,
    reindex_all_hotspots,
)


EVENT_ID = "RAG-EVENT-1"
HOTSPOT_ID = "CL-001"


def _build_session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    import_model_modules()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _seed_records(session) -> None:
    session.add(
        Event(
            id=EVENT_ID,
            event_type="unplanned",
            latitude=12.9296,
            longitude=77.6824,
            event_cause="waterlogging",
            event_cause_clean="waterlogging",
            requires_road_closure=True,
            start_datetime=datetime(2026, 7, 18, 10, 30, tzinfo=timezone.utc),
            status="active",
            description_language="en",
            description="Heavy rain waterlogging is building near HSR Layout and spillback is reaching Silk Board Junction.",
            corridor="ORR East 1",
            priority="High",
            police_station="HSR Layout",
            zone="East",
            junction="Silk Board Junction",
            veh_type="mixed",
            raw_payload={},
        )
    )
    session.add(
        EventFeature(
            event_id=EVENT_ID,
            event_hour=10,
            event_day=18,
            event_month=7,
            event_weekday=5,
            is_weekend=True,
            is_peak_hour=True,
            is_night_event=False,
            event_duration_minutes=240,
            closure_duration_minutes=180,
            duration_source="end_datetime",
            location_cluster_id=HOTSPOT_ID,
            historical_corridor_risk=0.62,
            historical_police_station_risk=0.42,
            historical_cluster_risk=0.61,
            historical_cause_closure_rate=0.64,
            historical_corridor_closure_rate=0.08,
            historical_police_station_closure_rate=0.07,
            historical_cluster_closure_rate=0.14,
        )
    )
    session.add(
        EventPrediction(
            event_id=EVENT_ID,
            predicted_priority="High",
            priority_confidence=0.95,
            road_closure_probability=0.64,
            predicted_road_closure=True,
            estimated_clearance_minutes=240,
            clearance_prediction_method="ml",
            clearance_confidence=0.71,
            clearance_confidence_note="Heavy rain scenario.",
            estimated_impact_score=71.11,
            impact_category="High",
            impact_radius_km=2.99,
            vehicle_impact_factor=1.0,
            vehicle_impact_note="Mixed corridor traffic.",
            baseline_risk_score=59.11,
            additional_event_delta=12.0,
            prediction_explanation_json={"summary": "Weather and hotspot risk elevated."},
            model_version="rag-test-v1",
        )
    )
    session.add(
        EventDna(
            event_id=EVENT_ID,
            dna_summary="Waterlogging in ORR East 1 during morning peak with similar-event memory.",
            time_context="Morning peak.",
            location_context="ORR East 1 near Silk Board Junction.",
            cause_context="Waterlogging due to heavy rain.",
            weather_context="Heavy rain with low visibility.",
            historical_pattern="Comparable rain events needed upstream control.",
            risk_indicators_json={"hotspot_risk": 62.2},
            similar_event_ids_json=["FKID006457", "FKID000797"],
        )
    )
    session.add(
        EventRecommendation(
            event_id=EVENT_ID,
            risk_summary_json={"impact_score": 71.11, "impact_category": "High"},
            weather_risk_json={"weather_factor": 1.3, "source": "manual_event_plan_override"},
            recommended_total_officers=12,
            deployment_plan_json={"deployment_style": "corridor_ring_control", "primary_positions": ["Primary corridor anchor"]},
            barricade_plan_json={"barricade_level": "extended_buffer_with_slow_speed_channelization"},
            diversion_plan_json={"strategy": "weather_buffered_hotspot_bypass"},
            emergency_corridor_json={"trigger": "activate when queues begin affecting emergency response time"},
            logistics_impact_json={"strategy": "stagger_dispatch"},
            action_confidence_ledger_json=[{"input": "ASTraM historical events", "confidence": 85}],
            recommended_action_summary="Deploy 12 officers and widen upstream diversion buffers.",
        )
    )
    session.add(
        CitizenReport(
            report_source="citizen",
            report_type="waterlogging",
            latitude=12.9296,
            longitude=77.6824,
            severity="High",
            description="Water is collecting near the service road and traffic is backing up.",
            language="en",
            event_id=EVENT_ID,
            matched_event_id=EVENT_ID,
            report_confidence=0.56,
            new_alert_level="Watch",
            recommended_action="Queue report against ORR East 1.",
        )
    )
    session.add(
        LiveEventUpdate(
            event_id=EVENT_ID,
            update_source="field_officer",
            current_congestion_level="Critical",
            field_update="Water depth rising near service road and queue spillback is reaching junction mouth.",
            road_closure_active=True,
            officer_shortage=True,
            crowd_increase=False,
            rain_waterlogging=True,
            new_nearby_incident=False,
            expected_impact_score=71.11,
            current_impact_score=100.0,
            impact_deviation=28.89,
            alert_level="Critical",
            adaptive_action="Notify control room and widen diversion taper.",
        )
    )
    session.add(
        PostEventReport(
            event_id=EVENT_ID,
            predicted_impact_score=71.11,
            simulated_actual_impact_score=100.0,
            impact_deviation=28.89,
            final_status="resolved",
            event_summary="Resolved waterlogging event on ORR East 1.",
            prediction_summary="High impact with high closure likelihood.",
            recommendation_summary="Twelve officers with corridor ring control.",
            citizen_report_summary="Three linked reports were considered.",
            live_escalation_summary="Three critical live updates were recorded.",
            lessons_learned="Reserve manpower earlier for comparable corridor events.",
            future_recommendations="Keep citizen reports and live updates in the same review loop.",
            report_json={"weather_source": "phase10_default"},
        )
    )
    session.add(
        HotspotCluster(
            location_cluster_id=HOTSPOT_ID,
            centroid_latitude=12.9296,
            centroid_longitude=77.6824,
            cluster_event_count=7391,
            cluster_high_priority_rate=0.57,
            cluster_road_closure_rate=0.08,
            cluster_peak_hour_rate=0.26,
            cluster_top_event_cause="vehicle_breakdown",
            cluster_risk_score=62.2,
            cluster_profile_json={"cluster_type": "high", "member_event_ids": [EVENT_ID]},
        )
    )
    session.commit()


def test_rag_indexer_creates_expected_chunk_types_and_visibilities():
    session_factory = _build_session_factory()

    with session_factory() as session:
        _seed_records(session)
        index_event_record(session, EVENT_ID, commit=False)
        report_id = str(session.scalars(select(CitizenReport.id)).first())
        live_update_id = str(session.scalars(select(LiveEventUpdate.id)).first())
        post_event_report_id = str(session.scalars(select(PostEventReport.id)).first())
        index_citizen_report_record(session, report_id, commit=False)
        index_live_update_record(session, live_update_id, commit=False)
        index_post_event_report_record(session, post_event_report_id, commit=False)
        index_hotspot_record(session, HOTSPOT_ID, commit=False)
        session.commit()

        chunks = session.scalars(select(RagChunk)).all()
        chunk_signatures = {(chunk.chunk_type, chunk.visibility) for chunk in chunks}

        assert ("event", "control_room") in chunk_signatures
        assert ("event_dna", "control_room") in chunk_signatures
        assert ("recommendation", "control_room") in chunk_signatures
        assert ("citizen_report", "control_room") in chunk_signatures
        assert ("live_update", "control_room") in chunk_signatures
        assert ("hotspot", "control_room") in chunk_signatures
        assert ("post_event_report", "admin") in chunk_signatures


def test_reindex_all_hotspots_replaces_stale_hotspot_chunks():
    session_factory = _build_session_factory()

    with session_factory() as session:
        _seed_records(session)
        index_hotspot_record(session, HOTSPOT_ID, commit=True)

        hotspot = session.scalar(select(HotspotCluster).where(HotspotCluster.location_cluster_id == HOTSPOT_ID))
        assert hotspot is not None
        session.delete(hotspot)
        session.commit()

        reindex_all_hotspots(session, commit=True)
        remaining = session.scalars(
            select(RagChunk).where(RagChunk.source_table == "hotspot_clusters", RagChunk.source_id == HOTSPOT_ID)
        ).all()

        assert remaining == []
