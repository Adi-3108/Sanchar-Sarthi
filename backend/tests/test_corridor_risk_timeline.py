from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base, import_model_modules
from app.db.session import get_db
from app.main import app
from app.orm.event import Event
from app.orm.event_feature import EventFeature


def _build_session_factory():
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    import_model_modules()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _seed_events(session_factory: sessionmaker) -> None:
    with session_factory() as session:
        session.add_all(
            [
                Event(
                    id="EVT-ORR-001",
                    event_type="unplanned",
                    latitude=12.9308,
                    longitude=77.6850,
                    address="HSR Layout",
                    event_cause="vehicle_breakdown",
                    event_cause_clean="vehicle_breakdown",
                    requires_road_closure=False,
                    start_datetime=datetime(2024, 3, 1, 8, 30, tzinfo=timezone.utc),
                    status="resolved",
                    authenticated=True,
                    description="Morning breakdown",
                    description_language="en",
                    corridor="ORR East 1",
                    priority="High",
                    police_station="HSR Layout",
                    raw_payload={},
                ),
                Event(
                    id="EVT-ORR-002",
                    event_type="planned",
                    latitude=12.9275,
                    longitude=77.6762,
                    address="Agara Junction",
                    event_cause="construction_activity",
                    event_cause_clean="construction_activity",
                    requires_road_closure=True,
                    start_datetime=datetime(2024, 3, 6, 18, 15, tzinfo=timezone.utc),
                    status="active",
                    authenticated=True,
                    description="Evening lane restriction",
                    description_language="en",
                    corridor="ORR East 1",
                    priority="Medium",
                    police_station="HSR Layout",
                    raw_payload={},
                ),
                Event(
                    id="EVT-TMK-001",
                    event_type="unplanned",
                    latitude=13.0400,
                    longitude=77.5181,
                    address="Peenya",
                    event_cause="vehicle_breakdown",
                    event_cause_clean="vehicle_breakdown",
                    requires_road_closure=False,
                    start_datetime=datetime(2024, 3, 6, 11, 0, tzinfo=timezone.utc),
                    status="resolved",
                    authenticated=True,
                    description="Control event",
                    description_language="en",
                    corridor="Tumkur Road",
                    priority="Low",
                    police_station="Peenya",
                    raw_payload={},
                ),
            ]
        )
        session.add_all(
            [
                EventFeature(
                    event_id="EVT-ORR-001",
                    is_weekend=False,
                    is_peak_hour=True,
                    is_night_event=False,
                    has_zone=False,
                    has_junction=False,
                    has_route_path=False,
                    has_vehicle_type=False,
                    historical_corridor_risk=0.72,
                ),
                EventFeature(
                    event_id="EVT-ORR-002",
                    is_weekend=False,
                    is_peak_hour=True,
                    is_night_event=False,
                    has_zone=False,
                    has_junction=False,
                    has_route_path=False,
                    has_vehicle_type=False,
                    historical_corridor_risk=0.61,
                ),
            ]
        )
        session.commit()


def test_corridor_timeline_uses_latest_historical_window_and_alias_matching():
    session_factory = _build_session_factory()
    _seed_events(session_factory)

    def override_get_db():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/analytics/corridor-risk-timeline",
                params={"corridor": "Outer Ring Road"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["corridor"] == "Outer Ring Road"
    assert payload["days_analyzed"] == 7
    assert len(payload["hourly_risk_scores"]) == 168
    assert sum(point["event_count"] for point in payload["hourly_risk_scores"]) == 2
    assert payload["average_risk_score"] > 0
    assert 8 in payload["peak_risk_hours"] or 18 in payload["peak_risk_hours"]


def test_corridor_timeline_returns_404_for_unknown_corridor():
    session_factory = _build_session_factory()
    _seed_events(session_factory)

    def override_get_db():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/analytics/corridor-risk-timeline",
                params={"corridor": "Nice Road"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert "No historical event data found" in response.json()["detail"]

