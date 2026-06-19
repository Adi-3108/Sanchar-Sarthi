from __future__ import annotations

from typing import Any

import httpx

from app.core.config import Settings, get_settings

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
RAIN_CODES = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}
LOW_VISIBILITY_THRESHOLD_M = 1000.0
RAIN_RISK_THRESHOLD_MM = 2.0
HEAVY_RAIN_THRESHOLD_MM = 10.0
MAX_WEATHER_FACTOR = 1.5

MANUAL_WEATHER_PROFILES: dict[str, dict[str, float | int | None]] = {
    "clear": {"weather_code": 0, "rain_mm": 0.0, "visibility_m": 8000.0},
    "cloudy": {"weather_code": 3, "rain_mm": 0.0, "visibility_m": 5000.0},
    "light_rain": {"weather_code": 61, "rain_mm": 2.0, "visibility_m": 2400.0},
    "rain": {"weather_code": 63, "rain_mm": 6.0, "visibility_m": 1600.0},
    "heavy_rain": {"weather_code": 65, "rain_mm": 12.0, "visibility_m": 800.0},
}


def normalize_weather_condition(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().casefold()
    return normalized or None


def infer_weather_condition(
    weather_code: int | None = None,
    rain_mm: float | None = None,
    visibility_m: float | None = None,
) -> str:
    active_rain = float(rain_mm or 0.0)
    active_visibility = float(visibility_m) if visibility_m is not None else None
    if active_rain >= HEAVY_RAIN_THRESHOLD_MM:
        return "heavy_rain"
    if active_rain >= 4.0 or weather_code in {63, 65, 66, 67, 81, 82}:
        return "rain"
    if active_rain >= RAIN_RISK_THRESHOLD_MM or weather_code in RAIN_CODES:
        return "light_rain"
    if active_visibility is not None and active_visibility < 3500.0:
        return "cloudy"
    return "clear"


def classify_waterlogging_risk(rain_mm: float, weather_condition: str) -> str:
    if rain_mm >= HEAVY_RAIN_THRESHOLD_MM or weather_condition == "heavy_rain":
        return "elevated"
    if rain_mm >= RAIN_RISK_THRESHOLD_MM or weather_condition in {"light_rain", "rain"}:
        return "watch"
    return "low"


def build_weather_adjustment(
    *,
    weather_code: int | None = None,
    rain_mm: float = 0.0,
    visibility_m: float | None = None,
    weather_condition: str | None = None,
    source: str = "phase10_default",
    provider: str | None = None,
    provider_status: str = "not_requested",
    note: str | None = None,
) -> dict[str, Any]:
    active_condition = normalize_weather_condition(weather_condition) or infer_weather_condition(
        weather_code=weather_code,
        rain_mm=rain_mm,
        visibility_m=visibility_m,
    )
    active_rain = round(max(float(rain_mm or 0.0), 0.0), 2)
    active_visibility = round(float(visibility_m), 2) if visibility_m is not None else None
    low_visibility = active_visibility is not None and active_visibility < LOW_VISIBILITY_THRESHOLD_M
    waterlogging_risk = classify_waterlogging_risk(active_rain, active_condition)

    factor = 1.0
    reason_codes: list[str] = []
    if weather_code in RAIN_CODES or active_rain >= RAIN_RISK_THRESHOLD_MM or active_condition in {"light_rain", "rain", "heavy_rain"}:
        factor += 0.1
        reason_codes.append("rain_or_wet_roads")
    if waterlogging_risk == "elevated":
        factor += 0.12
        reason_codes.append("heavy_rain_waterlogging_risk")
    elif waterlogging_risk == "watch":
        reason_codes.append("waterlogging_watch")
    if low_visibility:
        factor += 0.08
        reason_codes.append("low_visibility")

    if note is None:
        if source == "open_meteo_live":
            note = "Weather modifier uses current Open-Meteo conditions and remains an operational estimate, not a roadway sensor feed."
        elif source.startswith("manual_"):
            note = "Weather modifier uses a manual scenario override for MVP planning and remains an operational estimate."
        elif provider_status == "failed_fallback":
            note = "Live weather lookup failed, so Sanchar Sarthi used a neutral weather fallback."
        elif provider_status == "disabled":
            note = "Live weather lookup is disabled, so Sanchar Sarthi used a neutral weather fallback."
        else:
            note = "No explicit weather risk was provided, so Sanchar Sarthi used a neutral weather modifier."

    return {
        "weather_condition": active_condition,
        "weather_factor": round(min(factor, MAX_WEATHER_FACTOR), 2),
        "rain_mm": active_rain,
        "visibility_m": active_visibility,
        "low_visibility": low_visibility,
        "waterlogging_risk": waterlogging_risk,
        "reason_codes": reason_codes,
        "source": source,
        "provider": provider,
        "provider_status": provider_status,
        "note": note,
    }


def build_manual_weather_adjustment(
    *,
    weather_condition: str | None = None,
    rain_mm: float | None = None,
    visibility_m: float | None = None,
    source: str = "manual_simulation_selector",
) -> dict[str, Any]:
    active_condition = normalize_weather_condition(weather_condition) or infer_weather_condition(rain_mm=rain_mm, visibility_m=visibility_m)
    defaults = MANUAL_WEATHER_PROFILES.get(active_condition, MANUAL_WEATHER_PROFILES["clear"])
    return build_weather_adjustment(
        weather_code=int(defaults["weather_code"]) if defaults["weather_code"] is not None else None,
        rain_mm=float(rain_mm) if rain_mm is not None else float(defaults["rain_mm"] or 0.0),
        visibility_m=(
            float(visibility_m)
            if visibility_m is not None
            else (
                float(defaults["visibility_m"])
                if defaults["visibility_m"] is not None
                else None
            )
        ),
        weather_condition=active_condition,
        source=source,
        provider=None,
        provider_status="manual_override",
    )


def fetch_open_meteo_adjustment(
    latitude: float,
    longitude: float,
    *,
    timeout_seconds: float = 5.0,
) -> dict[str, Any]:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "weather_code,rain,showers,visibility",
        "timezone": "Asia/Kolkata",
    }
    
    # NOTE ON SYNC I/O: This uses a synchronous httpx.Client which blocks the thread.
    # However, since the FastAPI route handlers calling this service are defined as
    # synchronous functions (`def` instead of `async def`), FastAPI automatically
    # runs them in a separate threadpool. This ensures the main async event loop
    # is NEVER blocked by these external network calls.
    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.get(OPEN_METEO_URL, params=params)
        response.raise_for_status()
        payload = response.json()
    current = dict(payload.get("current", {}) or {})
    rain_mm = float(current.get("rain") or 0.0) + float(current.get("showers") or 0.0)
    visibility_value = current.get("visibility")
    visibility_m = float(visibility_value) if visibility_value is not None else None
    weather_code_value = current.get("weather_code")
    weather_code = int(weather_code_value) if weather_code_value is not None else None
    return build_weather_adjustment(
        weather_code=weather_code,
        rain_mm=rain_mm,
        visibility_m=visibility_m,
        weather_condition=infer_weather_condition(weather_code=weather_code, rain_mm=rain_mm, visibility_m=visibility_m),
        source="open_meteo_live",
        provider="open_meteo",
        provider_status="used",
    )


def resolve_weather_adjustment(
    latitude: float,
    longitude: float,
    *,
    weather_condition: str | None = None,
    rain_mm: float | None = None,
    visibility_m: float | None = None,
    use_live_weather: bool = False,
    source_context: str = "simulation",
    settings: Settings | None = None,
) -> dict[str, Any]:
    active_settings = settings or get_settings()
    if weather_condition is not None or rain_mm is not None or visibility_m is not None:
        manual_source = "manual_simulation_selector" if source_context == "simulation" else "manual_event_plan_override"
        return build_manual_weather_adjustment(
            weather_condition=weather_condition,
            rain_mm=rain_mm,
            visibility_m=visibility_m,
            source=manual_source,
        )

    if use_live_weather:
        if active_settings.open_meteo_enabled:
            try:
                return fetch_open_meteo_adjustment(latitude, longitude)
            except (httpx.HTTPError, ValueError):
                return build_weather_adjustment(
                    weather_condition="clear",
                    source="open_meteo_failed_fallback",
                    provider="open_meteo",
                    provider_status="failed_fallback",
                )
        return build_weather_adjustment(
            weather_condition="clear",
            source="open_meteo_disabled_default",
            provider="open_meteo",
            provider_status="disabled",
        )

    return build_weather_adjustment(
        weather_condition="clear",
        source="phase10_default",
        provider_status="not_requested",
    )
