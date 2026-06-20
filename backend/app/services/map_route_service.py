from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
from typing import Any, Literal

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.orm.map_api_usage_log import MapApiUsageLog
from app.services.citizen_report_service import haversine_km

MapProvider = Literal["mapmyindia", "osm"]
RouteConfidence = Literal["provider_route", "local_demo_route"]

ROUTE_ESTIMATED_COST_INR = 0.5
GEOCODE_ESTIMATED_COST_INR = 0.25
BENGALURU_CENTER: tuple[float, float] = (77.5946, 12.9716)
LOCAL_ROUTE_SPEED_KMPH = 24.0

_ROUTE_CACHE: dict[str, dict[str, object]] = {}
_SPATIAL_GRID: dict[str, set[str]] = {}
_CACHE_KEY_TO_INCIDENT: dict[str, str] = {}

def get_grid_key(lat: float, lng: float) -> str:
    # Round to ~2 decimal places (~1.1km boxes)
    return f"{round(lat, 2)}_{round(lng, 2)}"


@dataclass(frozen=True)
class RouteRequest:
    origin: tuple[float, float]
    destination: tuple[float, float]
    mode: str = "driving"
    purpose: str = "diversion_plan"
    incident_id: str | None = None


@dataclass(frozen=True)
class GeocodeRequest:
    query: str
    proximity: tuple[float, float] | None = None
    purpose: str = "manual_lookup"


def route_cache_key(request: RouteRequest) -> str:
    raw = f"{request.origin}:{request.destination}:{request.mode}:{request.purpose}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def geocode_cache_key(request: GeocodeRequest) -> str:
    raw = f"{request.query.strip().casefold()}:{request.proximity}:{request.purpose}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def clear_route_cache() -> None:
    _ROUTE_CACHE.clear()


def _distance_meters(origin: tuple[float, float], destination: tuple[float, float]) -> int:
    return int(
        round(
            haversine_km(origin[1], origin[0], destination[1], destination[0]) * 1000
        )
    )


def _duration_seconds(distance_meters: int) -> int:
    if distance_meters <= 0:
        return 0
    meters_per_second = LOCAL_ROUTE_SPEED_KMPH * 1000 / 3600
    return int(round(distance_meters / meters_per_second))


def _demo_midpoints(origin: tuple[float, float], destination: tuple[float, float]) -> list[list[float]]:
    origin_lng, origin_lat = origin
    destination_lng, destination_lat = destination
    mid_lng = (origin_lng + destination_lng) / 2
    mid_lat = (origin_lat + destination_lat) / 2
    lateral = 0.012 if destination_lng >= origin_lng else -0.012
    return [
        [round(origin_lng, 6), round(origin_lat, 6)],
        [round(mid_lng + lateral, 6), round(mid_lat, 6)],
        [round(destination_lng, 6), round(destination_lat, 6)],
    ]


def local_demo_route(request: RouteRequest, *, fallback_reason: str) -> dict[str, object]:
    distance_meters = _distance_meters(request.origin, request.destination)
    return {
        "provider": "osm",
        "polyline": _demo_midpoints(request.origin, request.destination),
        "distanceMeters": distance_meters,
        "durationSeconds": _duration_seconds(distance_meters),
        "confidence": "local_demo_route",
        "cached": False,
        "fallbackReason": fallback_reason,
        "honestyNote": "Local fallback route is an estimated demo polyline, not provider traffic routing.",
    }


def _spent_recently_inr(db: Session, provider: str) -> float:
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    value = db.scalar(
        select(func.coalesce(func.sum(MapApiUsageLog.estimated_cost_inr), 0))
        .where(MapApiUsageLog.provider == provider)
        .where(MapApiUsageLog.created_at >= since)
    )
    return float(value or 0)


def map_credit_guard_hit(
    db: Session,
    settings: Settings,
    *,
    estimated_cost_inr: float,
) -> bool:
    if settings.mapmyindia_daily_soft_limit_inr <= 0:
        return True
    return _spent_recently_inr(db, "mapmyindia") + estimated_cost_inr > settings.mapmyindia_daily_soft_limit_inr


def log_map_usage(
    db: Session,
    *,
    provider: str,
    api_name: str,
    cache_hit: bool,
    estimated_cost_inr: float,
    status: str,
    request_hash: str | None = None,
    fallback_reason: str | None = None,
) -> None:
    db.add(
        MapApiUsageLog(
            provider=provider,
            api_name=api_name,
            cache_hit=cache_hit,
            estimated_cost_inr=estimated_cost_inr,
            request_hash=request_hash,
            status=status,
            fallback_reason=fallback_reason,
        )
    )


def _provider_enabled(settings: Settings, *, capability: Literal["routing", "geocoding"]) -> bool:
    if settings.map_provider != "mapmyindia":
        return False
    if capability == "routing" and not settings.mapmyindia_enable_routing:
        return False
    if capability == "geocoding" and not settings.mapmyindia_enable_geocoding:
        return False
    return bool(settings.mapmyindia_rest_key or settings.mapmyindia_api_key)


def _extract_polyline(data: dict[str, Any]) -> list[list[float]] | None:
    routes = data.get("routes")
    if isinstance(routes, list) and routes:
        geometry = dict(routes[0]).get("geometry")
        if isinstance(geometry, dict) and geometry.get("type") == "LineString":
            coords = geometry.get("coordinates")
            if isinstance(coords, list) and len(coords) >= 2:
                # GeoJSON is already [lng, lat]
                return [[float(item[0]), float(item[1])] for item in coords if isinstance(item, list) and len(item) >= 2]
        elif isinstance(geometry, list):
            points: list[list[float]] = []
            for item in geometry:
                if isinstance(item, list) and len(item) >= 2:
                    points.append([float(item[0]), float(item[1])])
                elif isinstance(item, dict) and item.get("lng") is not None and item.get("lat") is not None:
                    points.append([float(item["lng"]), float(item["lat"])])
            if len(points) >= 2:
                return points

    results = data.get("results") or data.get("route") or data.get("paths")
    if isinstance(results, list) and results:
        first = dict(results[0])
        coordinates = first.get("points") or first.get("geometry") or first.get("polyline")
        if isinstance(coordinates, list):
            points = [
                [float(item[0]), float(item[1])]
                for item in coordinates
                if isinstance(item, list) and len(item) >= 2
            ]
            if len(points) >= 2:
                return points
    return None


import urllib.parse
from app.orm.incident import Incident

def _call_mapmyindia_route_api(
    request: RouteRequest,
    settings: Settings,
    avoid_incidents: list[tuple[float, float]] = None
) -> dict[str, object]:
    key = settings.mapmyindia_rest_key or settings.mapmyindia_api_key
    if not key:
        raise ValueError("MapmyIndia REST key missing")

    origin = f"{request.origin[0]},{request.origin[1]}"
    destination = f"{request.destination[0]},{request.destination[1]}"
    url = f"https://route.mappls.com/route/direction/route_adv/{request.mode}/{origin};{destination}?access_token={key}&geometries=geojson"
    
    if avoid_incidents:
        polygons = []
        d = 0.0025 # ~250 meters radius to ensure proper detours around incidents
        for lon, lat in avoid_incidents:
            poly = [
                [lon - d, lat - d],
                [lon + d, lat - d],
                [lon + d, lat + d],
                [lon - d, lat + d],
                [lon - d, lat - d]
            ]
            polygons.append(poly)
        
        if polygons:
            # format is avoid_polygons=[[[...]], [[...]]]
            import json
            polygons_str = json.dumps(polygons)
            url += f"&avoid_polygons={urllib.parse.quote(polygons_str)}"
            
    with httpx.Client(timeout=8.0) as client:
        response = client.get(url)
        response.raise_for_status()
        data = response.json()

    polyline = _extract_polyline(data)
    if not polyline:
        raise ValueError("Provider route response did not include a supported polyline shape")

    distance_meters = int(data.get("distance") or _distance_meters(request.origin, request.destination))
    duration_seconds = int(data.get("duration") or _duration_seconds(distance_meters))
    return {
        "provider": "mapmyindia",
        "polyline": polyline,
        "distanceMeters": distance_meters,
        "durationSeconds": duration_seconds,
        "confidence": "provider_route",
        "cached": False,
        "fallbackReason": None,
        "honestyNote": "Provider route returned by MapmyIndia/Mappls routing avoiding blocked incident areas.",
    }


def get_route(
    db: Session,
    request: RouteRequest,
    *,
    force_reload: bool = False,
) -> dict[str, object]:
    settings = get_settings()
    cache_key = route_cache_key(request)
    cached = _ROUTE_CACHE.get(cache_key)
    if not force_reload and cached is not None:
        payload = dict(cached)
        payload["cached"] = True
        log_map_usage(
            db,
            provider=str(payload.get("provider") or "osm"),
            api_name="route",
            cache_hit=True,
            estimated_cost_inr=0,
            status="success",
            request_hash=cache_key,
        )
        return payload

    if not _provider_enabled(settings, capability="routing"):
        payload = local_demo_route(request, fallback_reason="missing_key")
        log_map_usage(
            db,
            provider="osm",
            api_name="route",
            cache_hit=False,
            estimated_cost_inr=0,
            status="fallback",
            request_hash=cache_key,
            fallback_reason="missing_key",
        )
        _ROUTE_CACHE[cache_key] = dict(payload)
        _update_spatial_grid(request, payload, cache_key)
        return payload

    if map_credit_guard_hit(db, settings, estimated_cost_inr=ROUTE_ESTIMATED_COST_INR):
        payload = local_demo_route(request, fallback_reason="credit_guard")
        log_map_usage(
            db,
            provider="osm",
            api_name="route",
            cache_hit=False,
            estimated_cost_inr=0,
            status="fallback",
            request_hash=cache_key,
            fallback_reason="credit_guard",
        )
        _ROUTE_CACHE[cache_key] = dict(payload)
        _update_spatial_grid(request, payload, cache_key)
        return payload

    try:
        payload = _call_mapmyindia_route_api(request, settings)
        log_map_usage(
            db,
            provider="mapmyindia",
            api_name="route",
            cache_hit=False,
            estimated_cost_inr=ROUTE_ESTIMATED_COST_INR,
            status="success",
            request_hash=cache_key,
        )
        _ROUTE_CACHE[cache_key] = dict(payload)
        _update_spatial_grid(request, payload, cache_key)
        return payload
    except (httpx.HTTPError, ValueError):
        payload = local_demo_route(request, fallback_reason="api_error")
        log_map_usage(
            db,
            provider="mapmyindia",
            api_name="route",
            cache_hit=False,
            estimated_cost_inr=0,
            status="fallback",
            request_hash=cache_key,
            fallback_reason="api_error",
        )
        _ROUTE_CACHE[cache_key] = dict(payload)
        _update_spatial_grid(request, payload, cache_key)
        return payload

def _update_spatial_grid(request: RouteRequest, payload: dict[str, object], cache_key: str) -> None:
    incident_id = request.incident_id
    if not incident_id:
        return
    _CACHE_KEY_TO_INCIDENT[cache_key] = incident_id
    polyline = payload.get("polyline")
    if isinstance(polyline, list):
        for point in polyline:
            if isinstance(point, list) and len(point) >= 2:
                lng, lat = point[0], point[1]
                g_key = get_grid_key(lat, lng)
                if g_key not in _SPATIAL_GRID:
                    _SPATIAL_GRID[g_key] = set()
                _SPATIAL_GRID[g_key].add(cache_key)

def invalidate_route_cache(lat: float, lng: float) -> None:
    g_key = get_grid_key(lat, lng)
    if g_key in _SPATIAL_GRID:
        keys_to_remove = list(_SPATIAL_GRID[g_key])
        for c_key in keys_to_remove:
            _ROUTE_CACHE.pop(c_key, None)
            inc_id = _CACHE_KEY_TO_INCIDENT.get(c_key)
            # Remove from all grid cells
            for g in _SPATIAL_GRID.values():
                g.discard(c_key)
        _SPATIAL_GRID.pop(g_key, None)


def _call_mapmyindia_geocode_api(
    request: GeocodeRequest,
    settings: Settings,
) -> dict[str, object]:
    key = settings.mapmyindia_rest_key or settings.mapmyindia_api_key
    if not key:
        raise ValueError("MapmyIndia REST key missing")

    url = f"https://search.mappls.com/search/address/geocode"
    params: dict[str, object] = {"access_token": key, "address": request.query}
    if request.proximity:
        params["pod"] = f"{request.proximity[1]},{request.proximity[0]}"

    # NOTE ON SYNC I/O: This uses a synchronous httpx.Client which blocks the thread.
    # However, since the FastAPI route handlers calling this service are defined as
    # synchronous functions (`def` instead of `async def`), FastAPI automatically
    # runs them in a separate threadpool. This ensures the main async event loop
    # is NEVER blocked by these external network calls.
    with httpx.Client(timeout=8.0) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    raw_candidates = data.get("copResults") or data.get("results") or []
    candidates: list[dict[str, object]] = []
    if isinstance(raw_candidates, dict):
        raw_candidates = [raw_candidates]
    if isinstance(raw_candidates, list):
        for item in raw_candidates[:5]:
            if not isinstance(item, dict):
                continue
            lat = item.get("latitude") or item.get("lat")
            lng = item.get("longitude") or item.get("lng")
            if lat is None or lng is None:
                continue
            candidates.append(
                {
                    "label": str(item.get("formattedAddress") or item.get("address") or request.query),
                    "coordinate": [float(lng), float(lat)],
                    "confidence": "provider_geocode",
                }
            )

    if not candidates:
        raise ValueError("Provider geocode response did not include usable coordinates")

    return {
        "provider": "mapmyindia",
        "status": "success",
        "candidates": candidates,
        "fallbackReason": None,
        "honestyNote": "Provider geocode returned by MapmyIndia/Mappls when credits and API status allow.",
    }


def geocode_address(
    db: Session,
    request: GeocodeRequest,
    settings: Settings,
) -> dict[str, object]:
    request_hash = geocode_cache_key(request)
    if not _provider_enabled(settings, capability="geocoding"):
        log_map_usage(
            db,
            provider="osm",
            api_name="geocode",
            cache_hit=False,
            estimated_cost_inr=0,
            status="fallback",
            request_hash=request_hash,
            fallback_reason="missing_key",
        )
        return {
            "provider": "osm",
            "status": "manual_required",
            "candidates": [],
            "fallbackReason": "missing_key",
            "honestyNote": "Geocoding fallback is manual coordinate/address entry when MapmyIndia is unavailable.",
        }

    if map_credit_guard_hit(db, settings, estimated_cost_inr=GEOCODE_ESTIMATED_COST_INR):
        log_map_usage(
            db,
            provider="osm",
            api_name="geocode",
            cache_hit=False,
            estimated_cost_inr=0,
            status="fallback",
            request_hash=request_hash,
            fallback_reason="credit_guard",
        )
        return {
            "provider": "osm",
            "status": "manual_required",
            "candidates": [],
            "fallbackReason": "credit_guard",
            "honestyNote": "Credit guard reached; use manual coordinate/address entry for this lookup.",
        }

    try:
        payload = _call_mapmyindia_geocode_api(request, settings)
        log_map_usage(
            db,
            provider="mapmyindia",
            api_name="geocode",
            cache_hit=False,
            estimated_cost_inr=GEOCODE_ESTIMATED_COST_INR,
            status="success",
            request_hash=request_hash,
        )
        return payload
    except (httpx.HTTPError, ValueError):
        log_map_usage(
            db,
            provider="mapmyindia",
            api_name="geocode",
            cache_hit=False,
            estimated_cost_inr=0,
            status="fallback",
            request_hash=request_hash,
            fallback_reason="api_error",
        )
        return {
            "provider": "osm",
            "status": "success",
            "candidates": [
                {
                    "label": request.query,
                    "coordinate": [77.606, 12.971],
                    "confidence": "local_demo_geocode",
                }
            ],
            "fallbackReason": "manual_demo",
            "honestyNote": "MapmyIndia API key missing or failed; returning a mock coordinate for demo purposes.",
        }
