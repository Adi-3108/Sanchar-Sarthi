from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import sessionmaker

from app.core.database import build_engine
from app.db.base import Base, import_model_modules
from app.orm.event import Event
from app.orm.hotspot_cluster import HotspotCluster
from app.services.impact_score_service import (
    build_impact_assessment,
    derive_vehicle_multiplier_profile,
    resolve_vehicle_impact,
)
from app.services.similar_event_service import SimilarEventMatch


def _build_session_factory(tmp_path, name: str):
    engine = build_engine(f"sqlite:///{tmp_path / name}")
    import_model_modules()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def test_derive_vehicle_multiplier_profile_normalizes_against_private_car_and_caps(tmp_path):
    session_factory = _build_session_factory(tmp_path, "impact-score-multipliers.db")
    start = datetime(2026, 6, 22, 8, 0, tzinfo=timezone.utc)

    with session_factory() as session:
        session.add_all(
            [
                Event(
                    id="IMPACT-CAR-001",
                    event_type="unplanned",
                    latitude=12.9716,
                    longitude=77.5946,
                    event_cause_clean="vehicle_breakdown",
                    requires_road_closure=False,
                    start_datetime=start,
                    closed_datetime=start + timedelta(minutes=60),
                    description_language="en",
                    veh_type="private_car",
                ),
                Event(
                    id="IMPACT-CAR-002",
                    event_type="unplanned",
                    latitude=12.9718,
                    longitude=77.5948,
                    event_cause_clean="vehicle_breakdown",
                    requires_road_closure=False,
                    start_datetime=start + timedelta(minutes=5),
                    closed_datetime=start + timedelta(minutes=65),
                    description_language="en",
                    veh_type="private_car",
                ),
                Event(
                    id="IMPACT-TRUCK-001",
                    event_type="unplanned",
                    latitude=12.9720,
                    longitude=77.5950,
                    event_cause_clean="vehicle_breakdown",
                    requires_road_closure=True,
                    start_datetime=start,
                    closed_datetime=start + timedelta(minutes=120),
                    description_language="en",
                    veh_type="truck",
                ),
                Event(
                    id="IMPACT-TRUCK-002",
                    event_type="unplanned",
                    latitude=12.9722,
                    longitude=77.5952,
                    event_cause_clean="vehicle_breakdown",
                    requires_road_closure=True,
                    start_datetime=start + timedelta(minutes=10),
                    closed_datetime=start + timedelta(minutes=130),
                    description_language="en",
                    veh_type="truck",
                ),
                Event(
                    id="IMPACT-TRUCK-003",
                    event_type="unplanned",
                    latitude=12.9724,
                    longitude=77.5954,
                    event_cause_clean="vehicle_breakdown",
                    requires_road_closure=True,
                    start_datetime=start + timedelta(minutes=20),
                    closed_datetime=start + timedelta(minutes=140),
                    description_language="en",
                    veh_type="truck",
                ),
            ]
        )
        session.commit()

        profile = derive_vehicle_multiplier_profile(session)
        truck_impact = resolve_vehicle_impact("truck", db=session, profile=profile)

        assert profile["private_car"]["multiplier"] == 1.0
        assert profile["truck"]["multiplier"] == 1.5
        assert truck_impact.multiplier == 1.5
        assert truck_impact.source == "dataset_derived"


def test_build_impact_assessment_returns_counterfactual_and_vehicle_note(tmp_path):
    session_factory = _build_session_factory(tmp_path, "impact-score-assessment.db")
    start = datetime(2026, 6, 22, 18, 0, tzinfo=timezone.utc)

    with session_factory() as session:
        session.add(
            Event(
                id="IMPACT-EVT-001",
                event_type="planned",
                latitude=12.9716,
                longitude=77.5946,
                event_cause_clean="procession",
                requires_road_closure=False,
                start_datetime=start,
                description_language="en",
                veh_type="truck",
                corridor="MG Road",
                police_station="Ashok Nagar",
            )
        )
        session.commit()
        event = session.get(Event, "IMPACT-EVT-001")
        hotspot = HotspotCluster(
            location_cluster_id="CL-IMPACT-001",
            centroid_latitude=12.9716,
            centroid_longitude=77.5946,
            cluster_event_count=25,
            cluster_high_priority_rate=0.62,
            cluster_road_closure_rate=0.48,
            cluster_peak_hour_rate=0.7,
            cluster_top_event_cause="procession",
            cluster_risk_score=0.74,
            cluster_profile_json={"cluster_type": "high", "radius_km": 1.2},
        )
        similar_events = [
            SimilarEventMatch(
                event_id="SIM-001",
                similarity=0.84,
                matched_signals=["cause", "corridor"],
                event_cause_clean="procession",
                corridor="MG Road",
                police_station="Ashok Nagar",
                priority="High",
                event_type="planned",
                requires_road_closure=True,
                hotspot_cluster_id="CL-001",
                hotspot_risk_score=0.71,
                historical_corridor_closure_rate=0.6,
                historical_cluster_closure_rate=0.5,
            )
        ]

        assessment = build_impact_assessment(
            session,
            event=event,
            urgency_score=0.82,
            road_closure_likelihood=0.68,
            hotspot=hotspot,
            similar_events=similar_events,
            weather_condition="heavy_rain",
        )

        assert float(assessment["impact"]["estimated_impact_score"]) > 0.0
        assert assessment["impact"]["impact_category"] in {"High", "Critical"}
        assert float(assessment["counterfactual"]["additional_event_delta"]) > 0.0
        assert assessment["weather_adjustment"]["weather_condition"] == "heavy_rain"
        assert assessment["vehicle_impact"]["note"] == "Derived from ASTraM resolution time averages per vehicle type."
