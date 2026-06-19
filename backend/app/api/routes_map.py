from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import AuthContext, require_role
from app.db.session import get_db
from app.services.map_route_service import GeocodeRequest, RouteRequest, geocode_address, get_route

router = APIRouter(prefix="/api/map", tags=["map"])

Coordinate = tuple[float, float]


class MapConfigResponse(BaseModel):
    activeProvider: Literal["mapmyindia", "osm"]
    primaryProvider: Literal["mapmyindia"]
    fallbackProvider: Literal["osm"]
    mapKeyAvailable: bool
    creditsBudgetInr: int
    budgetGuardEnabled: bool
    fallbackReason: Literal["missing_key", "api_error", "credit_guard", "manual_demo"] | None = None
    defaultCenter: Coordinate
    defaultZoom: int
    fallbackNote: str


class MapRouteRequest(BaseModel):
    origin: Coordinate
    destination: Coordinate
    mode: Literal["driving"] = "driving"
    purpose: str = Field(default="diversion_plan", min_length=2, max_length=64)

    @field_validator("origin", "destination")
    @classmethod
    def _validate_lng_lat(cls, value: Coordinate) -> Coordinate:
        longitude, latitude = value
        if not 76.0 <= longitude <= 78.5 or not 12.0 <= latitude <= 14.0:
            raise ValueError("Coordinates must be [longitude, latitude] inside the Bengaluru demo operating area.")
        return value


class MapRouteResponse(BaseModel):
    provider: Literal["mapmyindia", "osm"]
    polyline: list[Coordinate]
    distanceMeters: int
    durationSeconds: int
    confidence: Literal["provider_route", "local_demo_route"]
    cached: bool
    fallbackReason: str | None = None
    honestyNote: str


class MapGeocodeRequest(BaseModel):
    query: str = Field(min_length=3, max_length=255)
    proximity: Coordinate | None = None
    purpose: str = Field(default="manual_lookup", min_length=2, max_length=64)

    @field_validator("query")
    @classmethod
    def _strip_query(cls, value: str) -> str:
        return value.strip()

    @field_validator("proximity")
    @classmethod
    def _validate_proximity(cls, value: Coordinate | None) -> Coordinate | None:
        if value is None:
            return None
        longitude, latitude = value
        if not 76.0 <= longitude <= 78.5 or not 12.0 <= latitude <= 14.0:
            raise ValueError("Proximity must be [longitude, latitude] inside the Bengaluru demo operating area.")
        return value


class MapGeocodeCandidateResponse(BaseModel):
    label: str
    coordinate: Coordinate
    confidence: str


class MapGeocodeResponse(BaseModel):
    provider: Literal["mapmyindia", "osm"]
    status: Literal["success", "manual_required"]
    candidates: list[MapGeocodeCandidateResponse] = Field(default_factory=list)
    fallbackReason: str | None = None
    honestyNote: str


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: dict[str, object] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        },
    )


def require_map_route_access(
    auth: AuthContext = Depends(require_role("admin", "control_room", "police_officer")),
) -> AuthContext:
    return auth


@router.get("/config", response_model=MapConfigResponse)
def map_config():
    settings = get_settings()
    active_provider: Literal["mapmyindia", "osm"] = "mapmyindia"
    fallback_reason = None
    map_key_available = bool(settings.mapmyindia_api_key)
    if settings.map_provider != "mapmyindia" or not map_key_available:
        active_provider = "osm"
        fallback_reason = "missing_key"

    # SECURITY: The actual REST/API key is deliberately omitted from this response.
    # The frontend only receives mapKeyAvailable (boolean) to know if the map is configured.
    # This fulfills the Phase 14 security requirement to prevent API key leaks.
    return MapConfigResponse(
        activeProvider=active_provider,
        primaryProvider="mapmyindia",
        fallbackProvider="osm",
        mapKeyAvailable=map_key_available,
        creditsBudgetInr=settings.mapmyindia_credit_budget_inr,
        budgetGuardEnabled=True,
        fallbackReason=fallback_reason,
        defaultCenter=(77.5946, 12.9716),
        defaultZoom=11,
        fallbackNote=(
            "Primary: MapmyIndia / Mappls using available 1000 INR credits. "
            "Fallback: OSM safety mode with local demo route overlays."
        ),
    )


@router.post("/route", response_model=MapRouteResponse)
def map_route(
    payload: MapRouteRequest,
    _auth: AuthContext = Depends(require_map_route_access),
    db: Session = Depends(get_db),
):
    try:
        result = get_route(
            db,
            RouteRequest(
                origin=payload.origin,
                destination=payload.destination,
                mode=payload.mode,
                purpose=payload.purpose,
            ),
            get_settings(),
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for map route generation.")

    return MapRouteResponse.model_validate(result)


@router.post("/geocode", response_model=MapGeocodeResponse)
def map_geocode(
    payload: MapGeocodeRequest,
    _auth: AuthContext = Depends(require_map_route_access),
    db: Session = Depends(get_db),
):
    try:
        result = geocode_address(
            db,
            GeocodeRequest(
                query=payload.query,
                proximity=payload.proximity,
                purpose=payload.purpose,
            ),
            get_settings(),
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for map geocoding.")

    return MapGeocodeResponse.model_validate(result)
