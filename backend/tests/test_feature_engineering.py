from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.api import routes_datasets
from app.core.database import build_engine
from app.core.security import AuthContext
from app.db.base import Base, import_model_modules
from app.db.session import get_db
from app.main import app
from app.orm.event import Event
from app.orm.event_feature import EventFeature
from app.orm.system_audit_log import SystemAuditLog
from app.orm.user_account import UserAccount
from app.services.feature_engineering_service import (
    best_duration_timestamp,
    build_features_for_event,
    build_location_cluster_id,
    rebuild_event_features,
)
from app.utils.datetime_utils import duration_minutes, first_valid_timestamp


def _build_session_factory(tmp_path, name: str):
    engine = build_engine(f"sqlite:///{tmp_path / name}")
    import_model_modules()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _seed_phase_four_events(session) -> None:
    base_time = datetime(2026, 6, 17, 9, 0, tzinfo=timezone.utc)
    session.add_all(
        [
            Event(
                id="EVT-100",
                event_type="unplanned",
                latitude=12.9716,
                longitude=77.5946,
                event_cause_clean="vehicle_breakdown",
                requires_road_closure=True,
                start_datetime=base_time,
                end_datetime=base_time + timedelta(minutes=60),
                description_language="en",
                corridor="ORR East",
                police_station="HSR Layout",
                zone="East",
                junction="Silk Board",
                route_path="HSR Layout -> Silk Board",
                veh_type="Truck",
            ),
            Event(
                id="EVT-101",
                event_type="unplanned",
                latitude=12.9721,
                longitude=77.5951,
                event_cause_clean="vehicle_breakdown",
                requires_road_closure=False,
                start_datetime=base_time + timedelta(hours=1),
                closed_datetime=base_time + timedelta(hours=3),
                description_language="en",
                corridor="ORR East",
                police_station="HSR Layout",
                zone="East",
                junction="Silk Board",
                veh_type="Mini Truck",
            ),
            Event(
                id="EVT-102",
                event_type="planned",
                latitude=13.0100,
                longitude=77.5200,
                event_cause_clean="construction",
                requires_road_closure=False,
                start_datetime=base_time + timedelta(hours=2),
                description_language="en",
                corridor="Tumakuru Road",
                police_station="Peenya",
                zone="North",
            ),
        ]
    )
    session.commit()


def test_datetime_helpers_use_valid_fallback_order():
    start = datetime(2026, 6, 17, 9, 0, tzinfo=timezone.utc)
    invalid_end = start - timedelta(minutes=10)
    resolved = start + timedelta(minutes=95)

    selected, source = first_valid_timestamp(
        start,
        (
            ("end_datetime", invalid_end),
            ("resolved_datetime", resolved),
        ),
    )

    assert duration_minutes(start, invalid_end) is None
    assert duration_minutes(start, resolved) == 95.0
    assert selected == resolved
    assert source == "resolved_datetime"


def test_build_features_for_event_populates_phase_four_columns(tmp_path):
    session_factory = _build_session_factory(tmp_path, "phase4-build.db")

    with session_factory() as session:
        _seed_phase_four_events(session)
        event = session.get(Event, "EVT-100")

        feature, created = build_features_for_event(session, event)

        assert created is True
        assert feature.event_hour == 9
        assert feature.event_day == 17
        assert feature.event_month == 6
        assert feature.event_weekday == 2
        assert feature.is_peak_hour is True
        assert feature.is_weekend is False
        assert feature.is_night_event is False
        assert float(feature.event_duration_minutes) == 60.0
        assert feature.duration_source == "end_datetime"
        assert feature.has_zone is True
        assert feature.has_junction is True
        assert feature.has_route_path is True
        assert feature.has_vehicle_type is True
        assert feature.location_cluster_id == build_location_cluster_id(event)
        assert float(feature.historical_corridor_risk) == pytest.approx(0.6667, abs=1e-4)
        assert float(feature.historical_police_station_risk) == pytest.approx(0.6667, abs=1e-4)
        assert float(feature.historical_cluster_risk) == pytest.approx(0.6667, abs=1e-4)
        assert float(feature.historical_cause_closure_rate) == pytest.approx(0.5, abs=1e-4)
        assert float(feature.historical_corridor_closure_rate) == pytest.approx(0.5, abs=1e-4)
        assert float(feature.historical_police_station_closure_rate) == pytest.approx(0.5, abs=1e-4)
        assert float(feature.historical_cluster_closure_rate) == pytest.approx(0.5, abs=1e-4)


def test_rebuild_event_features_is_idempotent_and_uses_duration_fallbacks(tmp_path):
    session_factory = _build_session_factory(tmp_path, "phase4-rebuild.db")

    with session_factory() as session:
        _seed_phase_four_events(session)

        first_report = rebuild_event_features(session)
        second_report = rebuild_event_features(session)

        assert first_report.events_processed == 3
        assert first_report.features_created == 3
        assert first_report.features_updated == 0
        assert first_report.duration_unavailable == 1
        assert second_report.features_created == 0
        assert second_report.features_updated == 3
        assert session.query(EventFeature).count() == 3

        closed_feature = (
            session.query(EventFeature)
            .filter(EventFeature.event_id == "EVT-101")
            .one()
        )
        unavailable_feature = (
            session.query(EventFeature)
            .filter(EventFeature.event_id == "EVT-102")
            .one()
        )

        assert closed_feature.duration_source == "closed_datetime"
        assert float(closed_feature.event_duration_minutes) == 120.0
        assert unavailable_feature.duration_source == "unavailable"
        assert unavailable_feature.event_duration_minutes is None


def test_best_duration_timestamp_prefers_end_then_closed_then_resolved(tmp_path):
    session_factory = _build_session_factory(tmp_path, "phase4-best-end.db")

    with session_factory() as session:
        base_time = datetime(2026, 6, 17, 12, 0, tzinfo=timezone.utc)
        event = Event(
            id="EVT-103",
            event_type="unplanned",
            latitude=12.90,
            longitude=77.60,
            event_cause_clean="crowd_buildup",
            requires_road_closure=False,
            start_datetime=base_time,
            end_datetime=base_time + timedelta(minutes=30),
            closed_datetime=base_time + timedelta(minutes=40),
            resolved_datetime=base_time + timedelta(minutes=50),
            description_language="en",
        )
        session.add(event)
        session.commit()

        selected, source = best_duration_timestamp(event)

        assert selected == event.end_datetime
        assert source == "end_datetime"


def test_generate_features_endpoint_rebuilds_features_and_writes_audit_log(tmp_path):
    session_factory = _build_session_factory(tmp_path, "phase4-route.db")
    actor_id = uuid4()

    with session_factory() as session:
        _seed_phase_four_events(session)
        session.add(
            UserAccount(
                id=actor_id,
                role="admin",
                display_name="Phase Four Admin",
                auth_provider="firebase",
                auth_provider_uid="firebase-admin-1",
                is_active=True,
            )
        )
        session.commit()

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[routes_datasets.require_admin_or_control_room] = lambda: AuthContext(
        firebase_uid="firebase-admin-1",
        email="admin@example.com",
        role="admin",
        user_account_id=str(actor_id),
    )

    try:
        with TestClient(app) as client:
            response = client.post("/api/datasets/generate-features")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "events_processed": 3,
        "features_created": 3,
        "features_updated": 0,
        "duration_unavailable": 1,
        "message": "Event features generated.",
    }

    with session_factory() as session:
        assert session.query(EventFeature).count() == 3
        audit_log = session.query(SystemAuditLog).one()
        assert audit_log.action == "dataset_generate_features"
        assert audit_log.resource_type == "event_features"
        assert audit_log.metadata_json["events_processed"] == 3
