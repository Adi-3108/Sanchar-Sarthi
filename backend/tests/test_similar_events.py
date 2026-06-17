from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import sessionmaker

from app.core.database import build_engine
from app.db.base import Base, import_model_modules
from app.orm.event import Event
from app.orm.event_dna import EventDna
from app.services.event_dna_service import rebuild_event_dna_records
from app.services.hotspot_service import rebuild_hotspots
from app.services.similar_event_service import find_similar_events


def _build_session_factory(tmp_path, name: str):
    engine = build_engine(f"sqlite:///{tmp_path / name}")
    import_model_modules()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _seed_similarity_events(session) -> None:
    start = datetime(2026, 6, 20, 17, 0, tzinfo=timezone.utc)
    session.add_all(
        [
            Event(
                id="SIM-001",
                event_type="unplanned",
                latitude=12.9716,
                longitude=77.5946,
                event_cause_clean="vehicle_breakdown",
                requires_road_closure=True,
                start_datetime=start,
                description_language="en",
                description_for_features="heavy vehicle traffic at junction",
                description_normalization_method="raw_ascii",
                priority="High",
                corridor="Central Spine",
                police_station="Ashok Nagar",
                zone="Central",
                junction="MG Road",
                veh_type="Truck",
            ),
            Event(
                id="SIM-002",
                event_type="unplanned",
                latitude=12.9721,
                longitude=77.5951,
                event_cause_clean="vehicle_breakdown",
                requires_road_closure=True,
                start_datetime=start + timedelta(minutes=10),
                description_language="en",
                description_for_features="vehicle breakdown causing traffic at road junction",
                description_normalization_method="raw_ascii",
                priority="High",
                corridor="Central Spine",
                police_station="Ashok Nagar",
                zone="Central",
                junction="MG Road",
                veh_type="Truck",
            ),
            Event(
                id="SIM-003",
                event_type="unplanned",
                latitude=12.9724,
                longitude=77.5949,
                event_cause_clean="vehicle_breakdown",
                requires_road_closure=False,
                start_datetime=start + timedelta(minutes=25),
                description_language="en",
                description_for_features="vehicle issue with moderate traffic",
                description_normalization_method="raw_ascii",
                priority="Medium",
                corridor="Central Spine",
                police_station="Ashok Nagar",
                zone="Central",
                junction="Brigade Junction",
                veh_type="Truck",
            ),
            Event(
                id="SIM-004",
                event_type="planned",
                latitude=13.0500,
                longitude=77.7200,
                event_cause_clean="construction",
                requires_road_closure=False,
                start_datetime=start + timedelta(hours=6),
                description_language="en",
                description_for_features="construction work on outer road",
                description_normalization_method="raw_ascii",
                priority="Low",
                corridor="Outer Ring",
                police_station="KR Puram",
                zone="East",
                junction="Tin Factory",
            ),
        ]
    )
    session.commit()


def test_find_similar_events_prefers_structural_matches(tmp_path):
    session_factory = _build_session_factory(tmp_path, "phase6-similar.db")

    with session_factory() as session:
        _seed_similarity_events(session)
        rebuild_hotspots(session)

        matches = find_similar_events(session, "SIM-001", limit=3)

        assert [match.event_id for match in matches] == ["SIM-002", "SIM-003", "SIM-004"]
        assert matches[0].similarity > matches[1].similarity > matches[2].similarity
        assert "cause" in matches[0].matched_signals
        assert "corridor" in matches[0].matched_signals
        assert "police station" in matches[0].matched_signals
        assert matches[0].hotspot_cluster_id == "CL-001"
        assert matches[2].event_cause_clean == "construction"


def test_rebuild_event_dna_records_persists_similar_event_ids(tmp_path):
    session_factory = _build_session_factory(tmp_path, "phase6-similar-rebuild.db")

    with session_factory() as session:
        _seed_similarity_events(session)

        first_report = rebuild_event_dna_records(
            session,
            limit_similar=3,
            refresh_supporting_data=True,
        )
        second_report = rebuild_event_dna_records(
            session,
            limit_similar=2,
            refresh_supporting_data=False,
        )

        assert first_report.events_processed == 4
        assert first_report.dna_created == 4
        assert first_report.dna_updated == 0
        assert second_report.dna_created == 0
        assert second_report.dna_updated == 4

        record = session.query(EventDna).filter(EventDna.event_id == "SIM-001").one()
        assert record.similar_event_ids_json[:2] == ["SIM-002", "SIM-003"]
        assert len(record.similar_event_ids_json) == 2
        assert "dataset-backed matches" in record.dna_summary
