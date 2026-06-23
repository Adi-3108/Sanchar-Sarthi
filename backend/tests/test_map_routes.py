from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import routes_map
from app.services import map_route_service
from app.core.config import Settings
from app.core.security import AuthContext
from app.db.base import Base, import_model_modules
from app.db.session import get_db
from app.main import app
from app.orm.map_api_usage_log import MapApiUsageLog
from app.services.map_route_service import clear_route_cache


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


def _settings_without_provider_key() -> Settings:
    return Settings(
        _env_file=None,
        map_provider="mapmyindia",
        mapmyindia_api_key=None,
        mapmyindia_rest_key=None,
        mapmyindia_credit_budget_inr=1000,
        mapmyindia_daily_soft_limit_inr=150,
        mapmyindia_enable_routing=True,
        mapmyindia_enable_geocoding=True,
    )


def _settings_with_provider_key() -> Settings:
    return Settings(
        _env_file=None,
        map_provider="mapmyindia",
        mapmyindia_api_key="browser-key-for-test",
        mapmyindia_rest_key="rest-key-for-test",
        mapmyindia_credit_budget_inr=1000,
        mapmyindia_daily_soft_limit_inr=150,
        mapmyindia_enable_routing=True,
        mapmyindia_enable_geocoding=True,
    )


def _admin_auth_context() -> AuthContext:
    return AuthContext(
        firebase_uid="firebase-map-admin",
        email="map-admin@example.com",
        role="admin",
        user_account_id="00000000-0000-0000-0000-000000000001",
    )


def _override_get_db(session_factory):
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    return override_get_db


def test_map_config_is_public_safe_and_reports_missing_key(monkeypatch):
    monkeypatch.setattr(routes_map, "get_settings", _settings_without_provider_key)

    with TestClient(app) as client:
        response = client.get("/api/map/config")

    assert response.status_code == 200
    payload = response.json()
    assert payload["activeProvider"] == "mapmyindia"
    assert payload["primaryProvider"] == "mapmyindia"
    assert payload["mapKeyAvailable"] is False
    assert payload["creditsBudgetInr"] == 1000
    assert "MapmyIndia" in payload["providerNote"]
    removed_provider_key = "fallback" + "Provider"
    assert removed_provider_key not in payload
    removed_reason_key = "fallback" + "Reason"
    assert removed_reason_key not in payload
    assert "REST" not in response.text.upper()
    assert "replace_with_key" not in response.text


def test_map_route_requires_internal_authentication():
    with TestClient(app) as client:
        response = client.post(
            "/api/map/route",
            json={
                "origin": [77.5946, 12.9716],
                "destination": [77.685, 12.9308],
                "mode": "driving",
                "purpose": "diversion_plan",
            },
        )

    assert response.status_code == 401


def test_map_route_returns_provider_unavailable_when_key_missing_and_logs_usage(monkeypatch):
    session_factory = _build_session_factory()
    clear_route_cache()
    monkeypatch.setattr(routes_map, "get_settings", _settings_without_provider_key)
    monkeypatch.setattr(map_route_service, "get_settings", _settings_without_provider_key)

    app.dependency_overrides[get_db] = _override_get_db(session_factory)
    app.dependency_overrides[routes_map.require_map_route_access] = _admin_auth_context

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/map/route",
                json={
                    "origin": [77.5946, 12.9716],
                    "destination": [77.685, 12.9308],
                    "mode": "driving",
                    "purpose": "diversion_plan",
                },
            )
    finally:
        app.dependency_overrides.clear()
        clear_route_cache()

    assert response.status_code == 503
    payload = response.json()
    assert payload["error"]["code"] == "MAPMYINDIA_UNAVAILABLE"
    assert payload["error"]["details"]["reason"] == "missing_key"

    with session_factory() as session:
        log = session.query(MapApiUsageLog).one()
        assert log.api_name == "route"
        assert log.status == "unavailable"
        assert log.provider == "mapmyindia"
        assert log.fallback_reason == "missing_key"


def test_map_route_uses_mapmyindia_provider_when_key_is_available(monkeypatch):
    session_factory = _build_session_factory()
    clear_route_cache()
    monkeypatch.setattr(routes_map, "get_settings", _settings_with_provider_key)
    monkeypatch.setattr(map_route_service, "get_settings", _settings_with_provider_key)

    def fake_route_provider(request, settings, avoid_incidents=None):
        return {
            "provider": "mapmyindia",
            "polyline": [[77.5946, 12.9716], [77.63, 12.96], [77.685, 12.9308]],
            "distanceMeters": 12000,
            "durationSeconds": 1800,
            "confidence": "provider_route",
            "cached": False,
            "honestyNote": "Provider route returned by MapmyIndia/Mappls routing.",
        }

    monkeypatch.setattr(map_route_service, "_call_mapmyindia_route_api", fake_route_provider)

    app.dependency_overrides[get_db] = _override_get_db(session_factory)
    app.dependency_overrides[routes_map.require_map_route_access] = _admin_auth_context

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/map/route",
                json={
                    "origin": [77.5946, 12.9716],
                    "destination": [77.685, 12.9308],
                    "mode": "driving",
                    "purpose": "diversion_plan",
                },
            )
    finally:
        app.dependency_overrides.clear()
        clear_route_cache()

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "mapmyindia"
    assert payload["confidence"] == "provider_route"
    assert payload["cached"] is False
    assert payload["distanceMeters"] == 12000

    with session_factory() as session:
        log = session.query(MapApiUsageLog).one()
        assert log.api_name == "route"
        assert log.status == "success"
        assert log.provider == "mapmyindia"

def test_map_geocode_returns_provider_unavailable_when_key_missing_and_logs_usage(monkeypatch):
    session_factory = _build_session_factory()
    monkeypatch.setattr(routes_map, "get_settings", _settings_without_provider_key)
    monkeypatch.setattr(map_route_service, "get_settings", _settings_without_provider_key)

    app.dependency_overrides[get_db] = _override_get_db(session_factory)
    app.dependency_overrides[routes_map.require_map_route_access] = _admin_auth_context

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/map/geocode",
                json={
                    "query": "MG Road Bengaluru",
                    "proximity": [77.5946, 12.9716],
                    "purpose": "manual_lookup",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    payload = response.json()
    assert payload["error"]["code"] == "MAPMYINDIA_UNAVAILABLE"
    assert payload["error"]["details"]["reason"] == "missing_key"

    with session_factory() as session:
        log = session.query(MapApiUsageLog).one()
        assert log.api_name == "geocode"
        assert log.status == "unavailable"
        assert log.provider == "mapmyindia"
        assert log.fallback_reason == "missing_key"
