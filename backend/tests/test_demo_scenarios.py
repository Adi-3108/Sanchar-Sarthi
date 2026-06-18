from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.api.routes_demo as routes_demo_module
from app.core.security import AuthContext
from app.db.base import Base, import_model_modules
from app.db.session import get_db
from app.main import app
from app.orm.citizen_report import CitizenReport
from app.orm.demo_scenario import DemoScenario
from app.orm.event import Event
from app.orm.live_event_update import LiveEventUpdate
from app.orm.post_event_report import PostEventReport
from app.orm.system_audit_log import SystemAuditLog
from app.orm.user_account import UserAccount
from app.services.demo_scenario_service import (
    DEMO_EVENT_IDS,
    DEMO_SCENARIO_NAMES,
    LEARNING_EVENT_ID,
    build_demo_status,
    seed_demo_scenarios,
)


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


def test_seed_demo_scenarios_is_deterministic_and_populates_readiness():
    session_factory = _build_session_factory()

    with session_factory() as session:
        first_report = seed_demo_scenarios(session, commit=True)
        second_report = seed_demo_scenarios(session, commit=True)
        status = build_demo_status(session)

        assert first_report.demo_events_seeded == len(DEMO_EVENT_IDS)
        assert second_report.demo_events_seeded == len(DEMO_EVENT_IDS)
        assert first_report.scenarios_seeded == len(DEMO_SCENARIO_NAMES)
        assert second_report.scenarios_seeded == len(DEMO_SCENARIO_NAMES)

        assert session.query(Event).filter(Event.id.in_(DEMO_EVENT_IDS)).count() == len(DEMO_EVENT_IDS)
        assert session.query(DemoScenario).filter(DemoScenario.scenario_name.in_(DEMO_SCENARIO_NAMES)).count() == len(
            DEMO_SCENARIO_NAMES
        )
        assert session.query(CitizenReport).filter(CitizenReport.event_id == LEARNING_EVENT_ID).count() == 3
        assert session.query(LiveEventUpdate).filter(LiveEventUpdate.event_id == LEARNING_EVENT_ID).count() == 2
        assert session.query(PostEventReport).filter(PostEventReport.event_id == LEARNING_EVENT_ID).count() == 1

        assert status["status"] == "ready"
        assert status["summary"]["demo_events"] == len(DEMO_EVENT_IDS)
        assert status["summary"]["demo_scenarios"] == len(DEMO_SCENARIO_NAMES)
        assert status["summary"]["demo_hotspot_clusters"] >= 1
        assert all(check["ready"] for check in status["checks"])
        assert status["sample_event_ids"]["learning"] == LEARNING_EVENT_ID


def test_demo_seed_route_and_status_route_work_together():
    session_factory = _build_session_factory()
    actor_id = uuid4()

    with session_factory() as session:
        session.add(
            UserAccount(
                id=actor_id,
                role="control_room",
                display_name="Demo Seeder",
                auth_provider="firebase",
                auth_provider_uid="firebase-control-room-demo",
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
    app.dependency_overrides[routes_demo_module.require_demo_seed_access] = lambda: AuthContext(
        firebase_uid="firebase-control-room-demo",
        email="control-room@example.com",
        role="control_room",
        user_account_id=str(actor_id),
    )

    try:
        with TestClient(app) as client:
            pre_seed_status = client.get("/api/demo/status")
            seed_response = client.post("/api/demo/seed")
            post_seed_status = client.get("/api/demo/status")
    finally:
        app.dependency_overrides.clear()

    assert pre_seed_status.status_code == 200
    assert pre_seed_status.json()["status"] == "incomplete"

    assert seed_response.status_code == 200
    seed_payload = seed_response.json()
    assert seed_payload["summary"]["demo_events"] == len(DEMO_EVENT_IDS)
    assert seed_payload["summary"]["demo_scenarios"] == len(DEMO_SCENARIO_NAMES)
    assert seed_payload["summary"]["demo_post_event_reports"] == 1

    assert post_seed_status.status_code == 200
    status_payload = post_seed_status.json()
    assert status_payload["status"] == "ready"
    assert status_payload["summary"]["demo_reports"] == 3
    assert status_payload["summary"]["demo_live_updates"] == 2
    assert status_payload["sample_event_ids"]["coordination_pair"] == [
        "DEMO_EVENT_BREAKDOWN_TUMKUR",
        "DEMO_EVENT_CONSTRUCTION_TUMKUR",
    ]

    with session_factory() as session:
        assert session.query(SystemAuditLog).filter(SystemAuditLog.action == "demo_seed").count() == 1
