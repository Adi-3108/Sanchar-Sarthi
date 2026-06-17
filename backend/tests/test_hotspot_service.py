from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import sessionmaker

from app.api import routes_analytics
from app.core.database import build_engine
from app.core.security import AuthContext
from app.db.base import Base, import_model_modules
from app.db.session import get_db
from app.main import app
from app.orm.event import Event
from app.orm.event_feature import EventFeature
from app.orm.hotspot_cluster import HotspotCluster
from app.orm.system_audit_log import SystemAuditLog
from app.orm.user_account import UserAccount
from app.services.feature_engineering_service import build_location_cluster_id
from app.services.hotspot_service import detect_hotspot_clusters, rebuild_hotspots


def _build_session_factory(tmp_path, name: str):
    engine = build_engine(f"sqlite:///{tmp_path / name}")
    import_model_modules()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _seed_hotspot_events(session) -> None:
    start = datetime(2026, 6, 18, 8, 0, tzinfo=timezone.utc)
    session.add_all(
        [
            Event(
                id="HS-001",
                event_type="unplanned",
                latitude=12.9716,
                longitude=77.5946,
                event_cause_clean="vehicle_breakdown",
                requires_road_closure=True,
                start_datetime=start,
                description_language="en",
                priority="High",
                corridor="Central Spine",
                police_station="Ashok Nagar",
                zone="Central",
                junction="MG Road",
                route_path="MG Road -> Residency Road",
                veh_type="Truck",
            ),
            Event(
                id="HS-002",
                event_type="unplanned",
                latitude=12.9722,
                longitude=77.5951,
                event_cause_clean="vehicle_breakdown",
                requires_road_closure=False,
                start_datetime=start + timedelta(minutes=15),
                description_language="en",
                priority="Critical",
                corridor="Central Spine",
                police_station="Ashok Nagar",
                zone="Central",
                junction="MG Road",
                veh_type="Truck",
            ),
            Event(
                id="HS-003",
                event_type="planned",
                latitude=12.9724,
                longitude=77.5949,
                event_cause_clean="construction",
                requires_road_closure=False,
                start_datetime=start + timedelta(hours=10),
                description_language="en",
                priority="Medium",
                corridor="Central Spine",
                police_station="Ashok Nagar",
                zone="Central",
                junction="MG Road",
            ),
            Event(
                id="HS-004",
                event_type="unplanned",
                latitude=12.9719,
                longitude=77.5954,
                event_cause_clean="vehicle_breakdown",
                requires_road_closure=True,
                start_datetime=start + timedelta(hours=11),
                description_language="en",
                priority="High",
                corridor="Central Spine",
                police_station="Ashok Nagar",
                zone="Central",
                junction="MG Road",
            ),
            Event(
                id="HS-005",
                event_type="planned",
                latitude=13.035,
                longitude=77.702,
                event_cause_clean="construction",
                requires_road_closure=False,
                start_datetime=start + timedelta(hours=3),
                description_language="en",
                priority="Low",
                corridor="Outer Ring",
                police_station="KR Puram",
                zone="East",
                junction="Tin Factory",
            ),
        ]
    )
    session.commit()


def test_detect_hotspot_clusters_groups_nearby_events(tmp_path):
    session_factory = _build_session_factory(tmp_path, "phase5-detect.db")

    with session_factory() as session:
        _seed_hotspot_events(session)
        events = session.query(Event).order_by(Event.id).all()

    clusters, noise_events = detect_hotspot_clusters(events, eps_km=0.7, min_samples=3)

    assert len(clusters) == 1
    assert sorted(event.id for event in clusters[0]) == ["HS-001", "HS-002", "HS-003", "HS-004"]
    assert [event.id for event in noise_events] == ["HS-005"]


def test_rebuild_hotspots_persists_clusters_and_updates_event_features(tmp_path):
    session_factory = _build_session_factory(tmp_path, "phase5-rebuild.db")

    with session_factory() as session:
        _seed_hotspot_events(session)

        report = rebuild_hotspots(session, eps_km=0.7, min_samples=3)

        assert report.clusters_created == 1
        assert report.clustered_events == 4
        assert report.noise_events == 1
        assert report.event_features_updated == 5

        hotspot = session.query(HotspotCluster).one()
        assert hotspot.location_cluster_id == "CL-001"
        assert hotspot.cluster_event_count == 4
        assert float(hotspot.cluster_high_priority_rate) == pytest.approx(0.75, abs=1e-4)
        assert float(hotspot.cluster_road_closure_rate) == pytest.approx(0.5, abs=1e-4)
        assert float(hotspot.cluster_peak_hour_rate) == pytest.approx(1.0, abs=1e-4)
        assert float(hotspot.cluster_risk_score) == pytest.approx(0.8375, abs=1e-4)
        assert hotspot.cluster_profile_json["cluster_type"] == "critical"
        assert sorted(hotspot.cluster_profile_json["member_event_ids"]) == [
            "HS-001",
            "HS-002",
            "HS-003",
            "HS-004",
        ]

        clustered_feature = (
            session.query(EventFeature)
            .filter(EventFeature.event_id == "HS-001")
            .one()
        )
        noise_feature = (
            session.query(EventFeature)
            .filter(EventFeature.event_id == "HS-005")
            .one()
        )

        assert clustered_feature.location_cluster_id == "CL-001"
        assert float(clustered_feature.historical_cluster_risk) == pytest.approx(0.8, abs=1e-4)
        assert float(clustered_feature.historical_cluster_closure_rate) == pytest.approx(0.5, abs=1e-4)
        assert noise_feature.location_cluster_id == build_location_cluster_id(session.get(Event, "HS-005"))
        assert float(noise_feature.historical_cluster_risk) == pytest.approx(0.2, abs=1e-4)
        assert float(noise_feature.historical_cluster_closure_rate) == pytest.approx(0.0, abs=1e-4)


def test_analytics_routes_return_summary_hotspots_and_rebuild(tmp_path):
    session_factory = _build_session_factory(tmp_path, "phase5-routes.db")
    actor_id = uuid4()

    with session_factory() as session:
        _seed_hotspot_events(session)
        session.add(
            UserAccount(
                id=actor_id,
                role="admin",
                display_name="Hotspot Admin",
                auth_provider="firebase",
                auth_provider_uid="firebase-admin-hotspot",
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
    app.dependency_overrides[routes_analytics.require_internal_analytics_access] = lambda: AuthContext(
        firebase_uid="firebase-admin-hotspot",
        email="admin@example.com",
        role="admin",
        user_account_id=str(actor_id),
    )
    app.dependency_overrides[routes_analytics.require_hotspot_rebuild_access] = lambda: AuthContext(
        firebase_uid="firebase-admin-hotspot",
        email="admin@example.com",
        role="admin",
        user_account_id=str(actor_id),
    )

    try:
        with TestClient(app) as client:
            rebuild_response = client.post("/api/analytics/hotspots/rebuild")
            hotspots_response = client.get("/api/analytics/hotspots?cluster_type=critical")
            summary_response = client.get("/api/analytics/summary")
    finally:
        app.dependency_overrides.clear()

    assert rebuild_response.status_code == 200
    assert rebuild_response.json() == {
        "status": "success",
        "clusters_created": 1,
        "clustered_events": 4,
        "noise_events": 1,
        "event_features_updated": 5,
        "message": "Dataset-backed hotspot clusters rebuilt.",
    }

    assert hotspots_response.status_code == 200
    hotspots_payload = hotspots_response.json()
    assert hotspots_payload["filters_applied"]["cluster_type"] == "critical"
    assert len(hotspots_payload["hotspots"]) == 1
    assert hotspots_payload["hotspots"][0]["location_cluster_id"] == "CL-001"
    assert hotspots_payload["geojson"]["type"] == "FeatureCollection"
    assert len(hotspots_payload["geojson"]["features"]) == 1

    assert summary_response.status_code == 200
    summary_payload = summary_response.json()
    assert summary_payload["total_events"] == 5
    assert summary_payload["planned_events"] == 2
    assert summary_payload["unplanned_events"] == 3
    assert summary_payload["high_priority_events"] == 3
    assert summary_payload["road_closure_required"] == 2
    assert summary_payload["hotspot_count"] == 1
    assert summary_payload["top_causes"][0]["label"] == "vehicle_breakdown"
    assert summary_payload["top_corridors"][0]["label"] == "Central Spine"

    with session_factory() as session:
        audit_log = session.query(SystemAuditLog).one()
        assert audit_log.action == "hotspot_rebuild"
        assert audit_log.resource_type == "hotspot_clusters"
