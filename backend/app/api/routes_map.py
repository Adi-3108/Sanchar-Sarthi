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
from app.services.map_route_service import (
    GeocodeRequest,
    MapProviderUnavailable,
    RouteRequest,
    geocode_address,
    get_route,
)

router = APIRouter(prefix="/api/map", tags=["map"])

Coordinate = tuple[float, float]


class MapConfigResponse(BaseModel):
    activeProvider: Literal["mapmyindia"]
    primaryProvider: Literal["mapmyindia"]
    mapKeyAvailable: bool
    creditsBudgetInr: int
    budgetGuardEnabled: bool
    defaultCenter: Coordinate
    defaultZoom: int
    providerNote: str


class MapRouteRequest(BaseModel):
    origin: Coordinate
    destination: Coordinate
    mode: Literal["driving"] = "driving"
    purpose: str = Field(default="diversion_plan", min_length=2, max_length=64)
    incidentId: str | None = None
    forceReload: bool = False

    @field_validator("origin", "destination")
    @classmethod
    def _validate_lng_lat(cls, value: Coordinate) -> Coordinate:
        longitude, latitude = value
        if not 76.0 <= longitude <= 78.5 or not 12.0 <= latitude <= 14.0:
            raise ValueError("Coordinates must be [longitude, latitude] inside the Bengaluru demo operating area.")
        return value


class MapRouteResponse(BaseModel):
    provider: Literal["mapmyindia"]
    polyline: list[Coordinate]
    distanceMeters: int
    durationSeconds: int
    confidence: Literal["provider_route"]
    cached: bool
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
    provider: Literal["mapmyindia"]
    status: Literal["success"]
    candidates: list[MapGeocodeCandidateResponse] = Field(default_factory=list)
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


def map_provider_error_response(exc: MapProviderUnavailable) -> JSONResponse:
    return error_response(
        exc.status_code,
        "MAPMYINDIA_UNAVAILABLE",
        exc.message,
        {"reason": exc.reason},
    )


def require_map_route_access(
    auth: AuthContext = Depends(require_role("admin", "control_room", "police_officer")),
) -> AuthContext:
    return auth


@router.get("/config", response_model=MapConfigResponse)
def map_config():
    settings = get_settings()
    return MapConfigResponse(
        activeProvider="mapmyindia",
        primaryProvider="mapmyindia",
        mapKeyAvailable=bool(settings.mapmyindia_api_key or settings.mapmyindia_rest_key),
        creditsBudgetInr=settings.mapmyindia_credit_budget_inr,
        budgetGuardEnabled=True,
        defaultCenter=(77.5946, 12.9716),
        defaultZoom=11,
        providerNote="MapmyIndia / Mappls is the only configured map provider.",
    )


@router.post("/route", response_model=MapRouteResponse)
def map_route(
    payload: MapRouteRequest,
    _auth: AuthContext = Depends(require_map_route_access),
    db: Session = Depends(get_db),
):
    try:
        req = RouteRequest(
            origin=payload.origin,
            destination=payload.destination,
            mode=payload.mode,
            purpose=payload.purpose,
            incident_id=payload.incidentId,
        )
        result = get_route(db, req, force_reload=payload.forceReload)
        db.commit()
    except MapProviderUnavailable as exc:
        db.commit()
        return map_provider_error_response(exc)
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
    except MapProviderUnavailable as exc:
        db.commit()
        return map_provider_error_response(exc)
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for map geocoding.")

    return MapGeocodeResponse.model_validate(result)


class ActiveRoute(BaseModel):
    incidentId: str
    polyline: list[Coordinate]


class MapActiveRoutesResponse(BaseModel):
    routes: list[ActiveRoute]


from app.orm.incident import Incident
from sqlalchemy import select

from app.services.map_route_service import _ROUTE_CACHE, route_cache_key


@router.get("/active-routes", response_model=MapActiveRoutesResponse)
def get_active_routes(
    db: Session = Depends(get_db),
):
    incidents = db.scalars(
        select(Incident).where(Incident.status.in_(["active", "confirmed", "escalated"]))
    ).all()

    active_routes = []
    for incident in incidents:
        if not incident.latitude or not incident.longitude:
            continue
        lng, lat = float(incident.longitude), float(incident.latitude)
        origin = (lng - 0.015, lat + 0.015)
        destination = (lng + 0.015, lat - 0.015)
        req = RouteRequest(origin=origin, destination=destination, incident_id=incident.id)
        c_key = route_cache_key(req)
        cached = _ROUTE_CACHE.get(c_key)
        if cached and "polyline" in cached:
            active_routes.append({"incidentId": incident.id, "polyline": cached["polyline"]})

    return {"routes": active_routes}