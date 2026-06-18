from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

import app.api.routes_officer as routes_officer_module
from app.core.database import build_engine
from app.core.security import AuthContext
from app.db.base import Base, import_model_modules
from app.db.session import get_db
from app.main import app
from app.orm.citizen_report import CitizenReport
from app.orm.event import Event
from app.orm.officer_event_assignment import OfficerEventAssignment
from app.orm.police_officer_profile import PoliceOfficerProfile
from app.orm.user_account import UserAccount


def _build_session_factory(tmp_path, name: str):
    engine = build_engine(f"sqlite:///{tmp_path / name}")
    import_model_modules()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def test_get_officer_assignments_returns_profile_scope_events_and_reports(tmp_path):
    session_factory = _build_session_factory(tmp_path, "officer-routes.db")
    account_id = uuid4()
    profile_id = uuid4()

    with session_factory() as session:
        session.add(
            UserAccount(
                id=account_id,
                role="police_officer",
                display_name="Assigned Officer",
                auth_provider="firebase",
                auth_provider_uid="firebase-officer-phase15",
                is_active=True,
            )
        )
        session.add(
            PoliceOfficerProfile(
                id=profile_id,
                user_account_id=account_id,
                officer_id="BTP-HSR-001",
                display_name="Assigned Officer",
                police_station="HSR Layout",
                assigned_corridors_json=["ORR East 1"],
                assigned_zones_json=["East"],
                firebase_email="officer@example.com",
                active=True,
            )
        )
        session.add(
            Event(
                id="OFF-001",
                event_type="unplanned",
                latitude=12.92188,
                longitude=77.64516,
                event_cause_clean="vehicle_breakdown",
                requires_road_closure=False,
                start_datetime=datetime(2026, 6, 18, 10, 30, tzinfo=timezone.utc),
                description_language="en",
                description_for_features="vehicle breakdown near corridor",
                description_normalization_method="raw_ascii",
                priority="High",
                status="open",
                corridor="ORR East 1",
                police_station="HSR Layout",
                zone="East",
                junction="Agara Junction",
            )
        )
        session.add(
            OfficerEventAssignment(
                officer_profile_id=profile_id,
                event_id="OFF-001",
                corridor="ORR East 1",
                police_station="HSR Layout",
                assignment_type="event",
                assignment_status="active",
                assigned_by_user_id=account_id,
            )
        )
        session.add(
            CitizenReport(
                report_source="citizen",
                report_type="congestion",
                latitude=12.9219,
                longitude=77.6452,
                severity="High",
                description="Heavy congestion near Agara Junction",
                language="en",
                event_id="OFF-001",
                matched_event_id="OFF-001",
                new_alert_level="Warning",
                report_confidence=0.81,
                recommended_action="Move reserve officers upstream",
                status="accepted",
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
    app.dependency_overrides[routes_officer_module.require_officer_access] = lambda: AuthContext(
        firebase_uid="firebase-officer-phase15",
        email="officer@example.com",
        role="police_officer",
        user_account_id=str(account_id),
        officer_profile_id=str(profile_id),
        officer_id="BTP-HSR-001",
        police_station="HSR Layout",
        assigned_corridors=["ORR East 1"],
        assigned_zones=["East"],
    )

    try:
        with TestClient(app) as client:
            response = client.get("/api/officer/assignments")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["officer_id"] == "BTP-HSR-001"
    assert payload["police_station"] == "HSR Layout"
    assert payload["assigned_corridors"] == ["ORR East 1"]
    assert payload["assigned_zones"] == ["East"]
    assert len(payload["assigned_events"]) == 1
    assert payload["assigned_events"][0]["id"] == "OFF-001"
    assert len(payload["pending_report_confirmations"]) == 1
    assert payload["pending_report_confirmations"][0]["matched_event_id"] == "OFF-001"
    assert payload["map_overlays"]["assigned_event_points"][0]["id"] == "OFF-001"
