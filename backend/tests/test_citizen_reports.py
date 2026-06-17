from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import routes_reports
from app.core.security import AuthContext
from app.db.base import Base, import_model_modules
from app.db.session import get_db
from app.main import app
from app.orm.citizen_report import CitizenReport
from app.orm.event import Event
from app.orm.system_audit_log import SystemAuditLog
from app.orm.user_account import UserAccount
from app.schemas.reports import CitizenReportCreate
from app.services.citizen_report_service import create_citizen_report, haversine_km


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


def _seed_report_event(session) -> None:
    session.add(
        Event(
            id="REPORT-001",
            event_type="unplanned",
            latitude=12.9716,
            longitude=77.5946,
            event_cause_clean="vehicle_breakdown",
            requires_road_closure=False,
            start_datetime=datetime(2026, 6, 24, 18, 0, tzinfo=timezone.utc),
            description_language="en",
            priority="High",
            corridor="Central Spine",
            police_station="Ashok Nagar",
            zone="Central",
            junction="MG Road",
        )
    )
    session.commit()


def test_haversine_km_returns_zero_for_same_point():
    assert haversine_km(12.9716, 77.5946, 12.9716, 77.5946) == 0.0


def test_create_citizen_report_matches_nearby_event_and_scores_confidence():
    session_factory = _build_session_factory()

    with session_factory() as session:
        _seed_report_event(session)
        payload = CitizenReportCreate(
            report_source="citizen",
            report_type="road_blockage",
            latitude=12.9717,
            longitude=77.5947,
            severity="High",
            description="ಊರ್ವಶಿ ಜಂಕ್ಷನ್ ಹತ್ತಿರ ಟ್ರಾಫಿಕ್ ಜಾಮ್",
            language="kn",
        )

        report, metadata = create_citizen_report(session, payload)

        assert report.matched_event_id == "REPORT-001"
        assert report.event_id == "REPORT-001"
        assert report.source_language == "kn"
        assert report.translation_status == "static_normalized"
        assert report.translated_description == "junction traffic jam"
        assert float(report.location_match_confidence) > 0.9
        assert float(report.report_confidence) >= 0.5
        assert report.new_alert_level in {"Watch", "Warning"}
        assert "not automatic official events" in metadata["dataset_honesty"]


def test_public_citizen_report_route_persists_report_and_audit_log():
    session_factory = _build_session_factory()
    routes_reports._REPORT_RATE_BUCKETS.clear()

    with session_factory() as session:
        _seed_report_event(session)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/reports/congestion",
                json={
                    "report_source": "citizen",
                    "report_type": "road_blockage",
                    "latitude": 12.9717,
                    "longitude": 77.5947,
                    "severity": "High",
                    "description": "Road blocked near MG Road junction",
                    "language": "en",
                },
            )
    finally:
        app.dependency_overrides.clear()
        routes_reports._REPORT_RATE_BUCKETS.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "accepted"
    assert payload["matched_event_id"] == "REPORT-001"
    assert payload["translation_status"] == "not_required"
    assert payload["report_confidence"] >= 0.5
    assert payload["recommended_action"]

    with session_factory() as session:
        assert session.query(CitizenReport).count() == 1
        assert session.query(SystemAuditLog).filter(SystemAuditLog.action == "citizen_report_submit").count() == 1


def test_field_officer_report_requires_registered_officer_auth():
    session_factory = _build_session_factory()

    with session_factory() as session:
        _seed_report_event(session)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/reports/congestion",
                json={
                    "report_source": "field_officer",
                    "report_type": "road_blockage",
                    "latitude": 12.9717,
                    "longitude": 77.5947,
                    "severity": "High",
                    "description": "Officer reports lane blockage near MG Road junction",
                    "language": "en",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "FIREBASE_AUTH_REQUIRED"


def test_field_officer_report_accepts_verified_officer_context():
    session_factory = _build_session_factory()
    actor_id = uuid4()

    with session_factory() as session:
        _seed_report_event(session)
        session.add(
            UserAccount(
                id=actor_id,
                role="police_officer",
                display_name="Report Officer",
                auth_provider="firebase",
                auth_provider_uid="firebase-report-officer",
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
    app.dependency_overrides[routes_reports.resolve_report_auth_context] = lambda: AuthContext(
        firebase_uid="firebase-report-officer",
        email="officer@example.com",
        role="police_officer",
        user_account_id=str(actor_id),
        officer_profile_id=str(uuid4()),
        officer_id="BTP-REPORT-001",
        police_station="Ashok Nagar",
        assigned_corridors=["Central Spine"],
        assigned_zones=["Central"],
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/reports/congestion",
                json={
                    "report_source": "field_officer",
                    "report_type": "road_blockage",
                    "latitude": 12.9717,
                    "longitude": 77.5947,
                    "severity": "High",
                    "description": "Officer confirms lane blockage near MG Road junction",
                    "language": "en",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["matched_event_id"] == "REPORT-001"
    assert payload["report_confidence"] >= 0.65
    assert payload["new_alert_level"] in {"Warning", "Critical"}

