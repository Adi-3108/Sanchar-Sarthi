from __future__ import annotations

import httpx

from app.core.config import Settings
from app.services import weather_service


def test_build_manual_weather_adjustment_marks_waterlogging_and_low_visibility():
    payload = weather_service.build_manual_weather_adjustment(
        weather_condition="heavy_rain",
        visibility_m=700,
    )

    assert payload["weather_condition"] == "heavy_rain"
    assert payload["weather_factor"] > 1.0
    assert payload["waterlogging_risk"] == "elevated"
    assert payload["low_visibility"] is True
    assert "heavy_rain_waterlogging_risk" in payload["reason_codes"]
    assert "low_visibility" in payload["reason_codes"]
    assert payload["provider_status"] == "manual_override"


def test_resolve_weather_adjustment_uses_live_provider_when_requested(monkeypatch):
    expected = weather_service.build_weather_adjustment(
        weather_code=63,
        rain_mm=6.0,
        visibility_m=1400.0,
        weather_condition="rain",
        source="open_meteo_live",
        provider="open_meteo",
        provider_status="used",
    )

    monkeypatch.setattr(weather_service, "fetch_open_meteo_adjustment", lambda latitude, longitude: expected)

    payload = weather_service.resolve_weather_adjustment(
        12.9716,
        77.5946,
        use_live_weather=True,
        settings=Settings(OPEN_METEO_ENABLED=True),
    )

    assert payload == expected


def test_resolve_weather_adjustment_falls_back_when_live_provider_fails(monkeypatch):
    def raise_error(latitude: float, longitude: float):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(weather_service, "fetch_open_meteo_adjustment", raise_error)

    payload = weather_service.resolve_weather_adjustment(
        12.9716,
        77.5946,
        use_live_weather=True,
        settings=Settings(OPEN_METEO_ENABLED=True),
    )

    assert payload["source"] == "open_meteo_failed_fallback"
    assert payload["provider"] == "open_meteo"
    assert payload["provider_status"] == "failed_fallback"
    assert payload["weather_factor"] == 1.0
