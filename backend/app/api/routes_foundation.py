from __future__ import annotations

from datetime import datetime
from math import atan2, cos, radians, sin, sqrt
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.roles import canonical_role
from app.core.security import AuthContext, require_role
from app.db.session import get_db
from app.orm.incident import INCIDENT_STATUSES, Incident
from app.orm.incident_prediction import IncidentPrediction
from app.orm.incident_vote import IncidentVote
from app.orm.system_audit_log import SystemAuditLog
from app.orm.traffic_station import TrafficStation
from app.orm.user_account import UserAccount
from app.services.foundation_seed_service import seed_foundation_data
from app.services.incident_service import apply_incident_vote, transition_incident

router = APIRouter(prefix="/api/foundation", tags=["foundation"])


class StationResponse(BaseModel):
    id: str
    station_code: str
    name: str
    locality: str
    latitude: float
    longitude: float
    contact_number: str | None = None
    active: bool


class PredictionResponse(BaseModel):
    model_name: str
    model_version: str
    predicted_severity: str | None = None
    police_force_required: int | None = None
    barricades_required: int | None = None
    urgency_score: float | None = None
    route_disruption_score: float | None = None
    confidence_score: float | None = None
    station_recommendation: str | None = None
    hotspot_contribution_score: float | None = None
    explanation_text: str | None = None


class IncidentResponse(BaseModel):
    id: str
    incident_type: str
    title: str
    description: str | None = None
    status: str
    severity: str
    location_name: str
    latitude: float
    longitude: float
    locality: str | None = None
    ward: str | None = None
    source_type: str
    true_vote_count: int
    false_vote_count: int
    confidence_score: float
    assigned_station_name: str | None = None
    assigned_station_code: str | None = None
    station_contact_number: str | None = None
    police_force_required: int | None = None
    barricades_required: int | None = None
    route_impact_summary: str | None = None
    resolution_notes: str | None = None
    station_alerted: bool
    created_at: datetime
    updated_at: datetime
    latest_prediction: PredictionResponse | None = None


class HotspotResponse(BaseModel):
    hotspot_id: str
    label: str
    incident_count: int
    severity: str
    latitude: float
    longitude: float
    active_incident_ids: list[str]


class FoundationBrowseResponse(BaseModel):
    incidents: list[IncidentResponse]
    stations: list[StationResponse]
    hotspots: list[HotspotResponse]
    statuses: list[str]


class VoteRequest(BaseModel):
    vote_value: str = Field(pattern="^(true|false)$")


class StatusTransitionRequest(BaseModel):
    status: str = Field(pattern="^(reported|pending_verification|active|escalated|resolved|rejected|archived)$")
    resolution_notes: str | None = Field(default=None, max_length=1000)


class IncidentCreateRequest(BaseModel):
    incident_type: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=4, max_length=255)
    description: str = Field(min_length=10, max_length=1000)
    severity: str = Field(pattern="^(low|medium|high|critical)$")
    location_name: str = Field(min_length=2, max_length=255)
    latitude: float = Field(ge=12.5, le=13.3)
    longitude: float = Field(ge=77.0, le=78.0)
    locality: str | None = Field(default=None, max_length=255)
    ward: str | None = Field(default=None, max_length=128)


class SeedResponse(BaseModel):
    status: str
    stations: int
    users: int
    incidents: int
    votes: int
    predictions: int


class FoundationAdminSummaryResponse(BaseModel):
    incident_count: int
    station_count: int
    vote_count: int
    prediction_count: int
    user_count: int
    audit_log_count: int
    status_counts: dict[str, int]


class UserResponse(BaseModel):
    id: str
    display_name: str | None = None
    role: str
    auth_provider_uid: str
    is_active: bool
    created_at: datetime


class VoteResponse(BaseModel):
    id: str
    incident_id: str
    voter_user_id: str
    vote_value: str
    created_at: datetime


class AuditLogResponse(BaseModel):
    id: str
    actor_role: str
    action: str
    resource_type: str
    resource_id: str | None = None
    metadata_json: dict[str, object]
    created_at: datetime


class FoundationAdminOverviewResponse(BaseModel):
    summary: FoundationAdminSummaryResponse
    incidents: list[IncidentResponse]
    stations: list[StationResponse]
    users: list[UserResponse]
    votes: list[VoteResponse]
    logs: list[AuditLogResponse]
    hotspots: list[HotspotResponse]
    statuses: list[str]


class IncidentAdminUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=4, max_length=255)
    description: str | None = Field(default=None, min_length=10, max_length=1000)
    status: str | None = Field(default=None, pattern="^(reported|pending_verification|active|escalated|resolved|rejected|archived)$")
    severity: str | None = Field(default=None, pattern="^(low|medium|high|critical)$")
    location_name: str | None = Field(default=None, min_length=2, max_length=255)
    locality: str | None = Field(default=None, max_length=255)
    ward: str | None = Field(default=None, max_length=128)
    police_force_required: int | None = Field(default=None, ge=0, le=500)
    barricades_required: int | None = Field(default=None, ge=0, le=500)
    route_impact_summary: str | None = Field(default=None, max_length=1000)
    resolution_notes: str | None = Field(default=None, max_length=1000)
    visible_to_public: bool | None = None
    station_alerted: bool | None = None


class StationAdminUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    locality: str | None = Field(default=None, min_length=2, max_length=255)
    contact_number: str | None = Field(default=None, max_length=64)
    active: bool | None = None


class UserAdminUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=255)
    role: str | None = Field(default=None, pattern="^(guest|citizen|control_room_officer|admin|control_room|police_officer|public_viewer)$")
    is_active: bool | None = None


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


def _coerce_uuid(value: str | None) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(value)
    except ValueError:
        return None


def _latest_prediction(db: Session, incident_id: str) -> IncidentPrediction | None:
    return db.scalar(
        select(IncidentPrediction)
        .where(IncidentPrediction.incident_id == incident_id)
        .order_by(IncidentPrediction.created_at.desc(), IncidentPrediction.model_version.desc(), IncidentPrediction.model_name.desc(), IncidentPrediction.id.desc())
    )


def _haversine_km(first_lat: float, first_lng: float, second_lat: float, second_lng: float) -> float:
    radius_km = 6371.0
    lat_distance = radians(second_lat - first_lat)
    lng_distance = radians(second_lng - first_lng)
    first_lat_rad = radians(first_lat)
    second_lat_rad = radians(second_lat)
    a = sin(lat_distance / 2) ** 2 + cos(first_lat_rad) * cos(second_lat_rad) * sin(lng_distance / 2) ** 2
    return 2 * radius_km * atan2(sqrt(a), sqrt(1 - a))


def _find_nearest_station(db: Session, latitude: float, longitude: float) -> TrafficStation | None:
    stations = db.scalars(select(TrafficStation).where(TrafficStation.active.is_(True))).all()
    if not stations:
        return None
    return min(
        stations,
        key=lambda station: _haversine_km(latitude, longitude, station.latitude, station.longitude),
    )


def _recommend_force(severity: str, incident_type: str) -> int:
    base = {"low": 2, "medium": 4, "high": 8, "critical": 12}.get(severity, 4)
    if incident_type in {"protest", "vip_movement", "festival_crowd"}:
        base += 2
    return base


def _recommend_barricades(severity: str, incident_type: str) -> int:
    if severity == "low":
        return 0 if incident_type in {"signal_failure", "lane_closure"} else 1
    if severity == "medium":
        return 2
    if severity == "high":
        return 4
    return 6


def _route_impact_summary(location_name: str, severity: str) -> str:
    if severity == "critical":
        return f"Avoid the primary carriageway near {location_name}; use upstream diversion guidance."
    if severity == "high":
        return f"Expect major delay near {location_name}; follow alternate junction bypasses."
    if severity == "medium":
        return f"Moderate slowdown expected near {location_name}; keep a diversion ready."
    return f"Minor impact near {location_name}; local slowdown only."


def _create_prediction_record(db: Session, incident: Incident, station: TrafficStation | None) -> IncidentPrediction:
    confidence = max(float(incident.confidence_score), 0.45 if incident.source_type == "user" else 0.78)
    prediction = IncidentPrediction(
        incident_id=incident.id,
        model_name="foundation_rule_engine",
        model_version="phase-2",
        predicted_severity=incident.severity,
        police_force_required=incident.police_force_required,
        barricades_required=incident.barricades_required,
        urgency_score=round(confidence, 4),
        route_disruption_score=round(min(0.35 + confidence, 0.98), 4),
        confidence_score=round(confidence, 4),
        station_recommendation=station.name if station is not None else incident.assigned_station_name,
        hotspot_contribution_score=round(0.45 + (0.1 * incident.true_vote_count), 4),
        output_json={
            "severity": incident.severity,
            "source_type": incident.source_type,
            "station_alerted": incident.station_alerted,
        },
        explanation_text=(
            f"Rule-based Phase 2 prediction using severity {incident.severity}, source {incident.source_type}, "
            f"and nearest station assignment."
        ),
    )
    db.add(prediction)
    return prediction


def _serialize_hotspots(incidents: list[Incident]) -> list[HotspotResponse]:
    clusters: dict[str, list[Incident]] = {}
    for incident in incidents:
        if incident.status not in {"active", "escalated", "pending_verification"}:
            continue
        cluster_key = (incident.locality or incident.location_name or "unknown").strip().casefold()
        clusters.setdefault(cluster_key, []).append(incident)

    hotspots: list[HotspotResponse] = []
    for cluster_key, cluster_incidents in clusters.items():
        severity_rank = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        dominant_incident = max(cluster_incidents, key=lambda item: severity_rank.get(item.severity, 0))
        average_lat = sum(item.latitude for item in cluster_incidents) / len(cluster_incidents)
        average_lng = sum(item.longitude for item in cluster_incidents) / len(cluster_incidents)
        hotspots.append(
            HotspotResponse(
                hotspot_id=f"HS-{cluster_key[:18].replace(' ', '-').upper()}",
                label=dominant_incident.locality or dominant_incident.location_name,
                incident_count=len(cluster_incidents),
                severity=dominant_incident.severity,
                latitude=average_lat,
                longitude=average_lng,
                active_incident_ids=[item.id for item in cluster_incidents],
            )
        )

    hotspots.sort(key=lambda item: (item.incident_count, item.severity), reverse=True)
    return hotspots



def _serialize_prediction(prediction: IncidentPrediction | None) -> PredictionResponse | None:
    if prediction is None:
        return None
    return PredictionResponse(
        model_name=prediction.model_name,
        model_version=prediction.model_version,
        predicted_severity=prediction.predicted_severity,
        police_force_required=prediction.police_force_required,
        barricades_required=prediction.barricades_required,
        urgency_score=float(prediction.urgency_score) if prediction.urgency_score is not None else None,
        route_disruption_score=float(prediction.route_disruption_score) if prediction.route_disruption_score is not None else None,
        confidence_score=float(prediction.confidence_score) if prediction.confidence_score is not None else None,
        station_recommendation=prediction.station_recommendation,
        hotspot_contribution_score=float(prediction.hotspot_contribution_score) if prediction.hotspot_contribution_score is not None else None,
        explanation_text=prediction.explanation_text,
    )
def _refresh_incident_vote_totals(db: Session, incident: Incident) -> None:
    counts = dict(
        db.execute(
            select(IncidentVote.vote_value, func.count())
            .where(IncidentVote.incident_id == incident.id)
            .group_by(IncidentVote.vote_value)
        ).all()
    )
    incident.true_vote_count = int(counts.get("true", 0))
    incident.false_vote_count = int(counts.get("false", 0))
    total_votes = incident.true_vote_count + incident.false_vote_count
    incident.confidence_score = (incident.true_vote_count / total_votes) if total_votes else 0
    if incident.source_type == "user" and incident.status == "active" and (
        incident.true_vote_count < 5 or float(incident.confidence_score) < 0.7
    ):
        incident.status = "pending_verification"


def _build_admin_summary(db: Session) -> FoundationAdminSummaryResponse:
    status_counts = dict(db.execute(select(Incident.status, func.count()).group_by(Incident.status)).all())
    return FoundationAdminSummaryResponse(
        incident_count=db.scalar(select(func.count()).select_from(Incident)) or 0,
        station_count=db.scalar(select(func.count()).select_from(TrafficStation)) or 0,
        vote_count=db.scalar(select(func.count()).select_from(IncidentVote)) or 0,
        prediction_count=db.scalar(select(func.count()).select_from(IncidentPrediction)) or 0,
        user_count=db.scalar(select(func.count()).select_from(UserAccount)) or 0,
        audit_log_count=db.scalar(select(func.count()).select_from(SystemAuditLog)) or 0,
        status_counts={str(key): int(value) for key, value in status_counts.items()},
    )


def _serialize_user(user: UserAccount) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        display_name=user.display_name,
        role=user.role,
        auth_provider_uid=user.auth_provider_uid,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def _serialize_vote(vote: IncidentVote) -> VoteResponse:
    return VoteResponse(
        id=str(vote.id),
        incident_id=vote.incident_id,
        voter_user_id=str(vote.voter_user_id),
        vote_value=vote.vote_value,
        created_at=vote.created_at,
    )


def _serialize_log(log: SystemAuditLog) -> AuditLogResponse:
    return AuditLogResponse(
        id=str(log.id),
        actor_role=log.actor_role,
        action=log.action,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        metadata_json=log.metadata_json,
        created_at=log.created_at,
    )
def _serialize_incident(db: Session, incident: Incident) -> IncidentResponse:
    station = incident.assigned_station
    return IncidentResponse(
        id=incident.id,
        incident_type=incident.incident_type,
        title=incident.title,
        description=incident.description,
        status=incident.status,
        severity=incident.severity,
        location_name=incident.location_name,
        latitude=incident.latitude,
        longitude=incident.longitude,
        locality=incident.locality,
        ward=incident.ward,
        source_type=incident.source_type,
        true_vote_count=incident.true_vote_count,
        false_vote_count=incident.false_vote_count,
        confidence_score=float(incident.confidence_score),
        assigned_station_name=incident.assigned_station_name or (station.name if station is not None else None),
        assigned_station_code=station.station_code if station is not None else None,
        station_contact_number=station.contact_number if station is not None else None,
        police_force_required=incident.police_force_required,
        barricades_required=incident.barricades_required,
        route_impact_summary=incident.route_impact_summary,
        resolution_notes=incident.resolution_notes,
        station_alerted=incident.station_alerted,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        latest_prediction=_serialize_prediction(_latest_prediction(db, incident.id)),
    )


@router.get("/incidents", response_model=FoundationBrowseResponse)
def browse_foundation_incidents(db: Session = Depends(get_db)):
    incidents = db.scalars(
        select(Incident)
        .where(Incident.visible_to_public.is_(True))
        .order_by(Incident.created_at.desc(), Incident.id)
    ).all()
    stations = db.scalars(select(TrafficStation).where(TrafficStation.active.is_(True)).order_by(TrafficStation.name)).all()
    return FoundationBrowseResponse(
        incidents=[_serialize_incident(db, incident) for incident in incidents],
        stations=[
            StationResponse(
                id=str(station.id),
                station_code=station.station_code,
                name=station.name,
                locality=station.locality,
                latitude=station.latitude,
                longitude=station.longitude,
                contact_number=station.contact_number,
                active=station.active,
            )
            for station in stations
        ],
        hotspots=_serialize_hotspots(incidents),
        statuses=list(INCIDENT_STATUSES),
    )


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
def get_foundation_incident(incident_id: str, db: Session = Depends(get_db)):
    incident = db.get(Incident, incident_id)
    if incident is None or not incident.visible_to_public:
        return error_response(404, "INCIDENT_NOT_FOUND", "Incident was not found.")
    return _serialize_incident(db, incident)


@router.post("/incidents/{incident_id}/vote", response_model=IncidentResponse)
def vote_incident(
    incident_id: str,
    payload: VoteRequest,
    auth: AuthContext = Depends(require_role("citizen", "admin")),
    db: Session = Depends(get_db),
):
    incident = db.get(Incident, incident_id)
    if incident is None:
        return error_response(404, "INCIDENT_NOT_FOUND", "Incident was not found.")
    user_id = _coerce_uuid(auth.user_account_id)
    if user_id is None:
        return error_response(403, "USER_ACCOUNT_REQUIRED", "Voting requires a registered user account.")
    try:
        db.add(IncidentVote(incident_id=incident.id, voter_user_id=user_id, vote_value=payload.vote_value))
        apply_incident_vote(incident, payload.vote_value)
        db.add(
            SystemAuditLog(
                actor_user_id=user_id,
                actor_role=auth.role,
                action="incident_vote",
                resource_type="incidents",
                resource_id=incident.id,
                metadata_json={"vote_value": payload.vote_value},
            )
        )
        db.commit()
        db.refresh(incident)
    except IntegrityError:
        db.rollback()
        return error_response(409, "DUPLICATE_VOTE", "Only one vote is allowed per user per incident.")
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for voting.")
    return _serialize_incident(db, incident)


@router.post("/incidents/report", response_model=IncidentResponse)
def create_user_incident_report(
    payload: IncidentCreateRequest,
    auth: AuthContext = Depends(require_role("citizen", "admin")),
    db: Session = Depends(get_db),
):
    user_id = _coerce_uuid(auth.user_account_id)
    if user_id is None:
        return error_response(403, "USER_ACCOUNT_REQUIRED", "Reporting requires a registered user account.")

    station = _find_nearest_station(db, payload.latitude, payload.longitude)
    incident = Incident(
        incident_type=payload.incident_type.strip(),
        title=payload.title.strip(),
        description=payload.description.strip(),
        status="pending_verification",
        severity=payload.severity,
        location_name=payload.location_name.strip(),
        latitude=payload.latitude,
        longitude=payload.longitude,
        locality=payload.locality.strip() if payload.locality else None,
        ward=payload.ward.strip() if payload.ward else None,
        created_by_user_id=user_id,
        source_type="user",
        confidence_score=0.35,
        assigned_station_id=station.id if station is not None else None,
        assigned_station_name=station.name if station is not None else None,
        police_force_required=_recommend_force(payload.severity, payload.incident_type),
        barricades_required=_recommend_barricades(payload.severity, payload.incident_type),
        route_impact_summary=_route_impact_summary(payload.location_name, payload.severity),
        station_alerted=False,
        visible_to_public=True,
    )

    try:
        db.add(incident)
        db.flush()
        _create_prediction_record(db, incident, station)
        db.add(
            SystemAuditLog(
                actor_user_id=user_id,
                actor_role=auth.role,
                action="incident_report_create",
                resource_type="incidents",
                resource_id=incident.id,
                metadata_json={"source_type": "user", "status": incident.status},
            )
        )
        db.commit()
        db.refresh(incident)
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for incident reporting.")

    return _serialize_incident(db, incident)


@router.get("/control-room", response_model=FoundationBrowseResponse)
def control_room_foundation(
    _auth: AuthContext = Depends(require_role("control_room_officer", "admin")),
    db: Session = Depends(get_db),
):
    return browse_foundation_incidents(db)


@router.post("/control-room/incidents", response_model=IncidentResponse)
def create_control_room_incident(
    payload: IncidentCreateRequest,
    auth: AuthContext = Depends(require_role("control_room_officer", "admin")),
    db: Session = Depends(get_db),
):
    actor_user_id = _coerce_uuid(auth.user_account_id)
    station = _find_nearest_station(db, payload.latitude, payload.longitude)
    source_type = "admin" if canonical_role(auth.role) == "admin" else "control_room"
    incident = Incident(
        incident_type=payload.incident_type.strip(),
        title=payload.title.strip(),
        description=payload.description.strip(),
        status="active",
        severity=payload.severity,
        location_name=payload.location_name.strip(),
        latitude=payload.latitude,
        longitude=payload.longitude,
        locality=payload.locality.strip() if payload.locality else None,
        ward=payload.ward.strip() if payload.ward else None,
        created_by_user_id=actor_user_id,
        source_type=source_type,
        confidence_score=0.9,
        assigned_station_id=station.id if station is not None else None,
        assigned_station_name=station.name if station is not None else None,
        police_force_required=_recommend_force(payload.severity, payload.incident_type),
        barricades_required=_recommend_barricades(payload.severity, payload.incident_type),
        route_impact_summary=_route_impact_summary(payload.location_name, payload.severity),
        station_alerted=True,
        visible_to_public=True,
    )
    try:
        db.add(incident)
        db.flush()
        _create_prediction_record(db, incident, station)
        db.add(
            SystemAuditLog(
                actor_user_id=actor_user_id,
                actor_role=auth.role,
                action="control_room_incident_create",
                resource_type="incidents",
                resource_id=incident.id,
                metadata_json={"source_type": source_type, "status": incident.status},
            )
        )
        db.commit()
        db.refresh(incident)
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for official incident creation.")

    return _serialize_incident(db, incident)


@router.patch("/control-room/incidents/{incident_id}/status", response_model=IncidentResponse)
def transition_incident_status(
    incident_id: str,
    payload: StatusTransitionRequest,
    auth: AuthContext = Depends(require_role("control_room_officer", "admin")),
    db: Session = Depends(get_db),
):
    incident = db.get(Incident, incident_id)
    if incident is None:
        return error_response(404, "INCIDENT_NOT_FOUND", "Incident was not found.")
    try:
        transition_incident(
            incident,
            payload.status,
            admin_override=canonical_role(auth.role) == "admin",
            resolution_notes=payload.resolution_notes,
        )
        db.add(
            SystemAuditLog(
                actor_user_id=_coerce_uuid(auth.user_account_id),
                actor_role=auth.role,
                action="incident_status_transition",
                resource_type="incidents",
                resource_id=incident.id,
                metadata_json={"next_status": payload.status},
            )
        )
        db.commit()
        db.refresh(incident)
    except ValueError as exc:
        db.rollback()
        return error_response(400, "INVALID_STATUS_TRANSITION", str(exc))
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for status transition.")
    return _serialize_incident(db, incident)


@router.get("/admin/overview", response_model=FoundationAdminOverviewResponse)
def admin_foundation_overview(
    _auth: AuthContext = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    incidents = db.scalars(select(Incident).order_by(Incident.created_at.desc(), Incident.id)).all()
    stations = db.scalars(select(TrafficStation).order_by(TrafficStation.name)).all()
    users = db.scalars(select(UserAccount).order_by(UserAccount.created_at.desc())).all()
    votes = db.scalars(select(IncidentVote).order_by(IncidentVote.created_at.desc(), IncidentVote.id).limit(200)).all()
    logs = db.scalars(select(SystemAuditLog).order_by(SystemAuditLog.created_at.desc(), SystemAuditLog.id).limit(200)).all()
    return FoundationAdminOverviewResponse(
        summary=_build_admin_summary(db),
        incidents=[_serialize_incident(db, incident) for incident in incidents],
        stations=[
            StationResponse(
                id=str(station.id),
                station_code=station.station_code,
                name=station.name,
                locality=station.locality,
                latitude=station.latitude,
                longitude=station.longitude,
                contact_number=station.contact_number,
                active=station.active,
            )
            for station in stations
        ],
        users=[_serialize_user(user) for user in users],
        votes=[_serialize_vote(vote) for vote in votes],
        logs=[_serialize_log(log) for log in logs],
        hotspots=_serialize_hotspots(incidents),
        statuses=list(INCIDENT_STATUSES),
    )


@router.patch("/admin/incidents/{incident_id}", response_model=IncidentResponse)
def admin_update_incident(
    incident_id: str,
    payload: IncidentAdminUpdateRequest,
    auth: AuthContext = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    incident = db.get(Incident, incident_id)
    if incident is None:
        return error_response(404, "INCIDENT_NOT_FOUND", "Incident was not found.")

    try:
        if payload.title is not None:
            incident.title = payload.title.strip()
        if payload.description is not None:
            incident.description = payload.description.strip()
        if payload.location_name is not None:
            incident.location_name = payload.location_name.strip()
        if payload.locality is not None:
            incident.locality = payload.locality.strip() or None
        if payload.ward is not None:
            incident.ward = payload.ward.strip() or None
        if payload.severity is not None:
            incident.severity = payload.severity
        if payload.police_force_required is not None:
            incident.police_force_required = payload.police_force_required
        if payload.barricades_required is not None:
            incident.barricades_required = payload.barricades_required
        if payload.route_impact_summary is not None:
            incident.route_impact_summary = payload.route_impact_summary.strip() or None
        if payload.resolution_notes is not None:
            incident.resolution_notes = payload.resolution_notes.strip() or None
        if payload.visible_to_public is not None:
            incident.visible_to_public = payload.visible_to_public
        if payload.station_alerted is not None:
            incident.station_alerted = payload.station_alerted
        if payload.status is not None and payload.status != incident.status:
            transition_incident(incident, payload.status, admin_override=True, resolution_notes=payload.resolution_notes)

        db.add(
            SystemAuditLog(
                actor_user_id=_coerce_uuid(auth.user_account_id),
                actor_role=auth.role,
                action="admin_update_incident",
                resource_type="incidents",
                resource_id=incident.id,
                metadata_json={
                    "status": incident.status,
                    "severity": incident.severity,
                    "visible_to_public": incident.visible_to_public,
                },
            )
        )
        db.add(
            IncidentPrediction(
                incident_id=incident.id,
                model_name="foundation_admin_override",
                model_version="phase-3",
                predicted_severity=incident.severity,
                police_force_required=incident.police_force_required,
                barricades_required=incident.barricades_required,
                urgency_score=float(incident.confidence_score),
                route_disruption_score=min(0.98, 0.35 + float(incident.confidence_score)),
                confidence_score=float(incident.confidence_score),
                station_recommendation=incident.assigned_station_name,
                hotspot_contribution_score=0.55,
                output_json={"override": True, "status": incident.status},
                explanation_text="Admin override snapshot persisted for audit and explainability.",
            )
        )
        db.commit()
        db.refresh(incident)
    except ValueError as exc:
        db.rollback()
        return error_response(400, "INVALID_STATUS_TRANSITION", str(exc))
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for incident update.")

    return _serialize_incident(db, incident)


@router.delete("/admin/incidents/{incident_id}")
def admin_delete_incident(
    incident_id: str,
    auth: AuthContext = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    incident = db.get(Incident, incident_id)
    if incident is None:
        return error_response(404, "INCIDENT_NOT_FOUND", "Incident was not found.")

    try:
        db.add(
            SystemAuditLog(
                actor_user_id=_coerce_uuid(auth.user_account_id),
                actor_role=auth.role,
                action="admin_delete_incident",
                resource_type="incidents",
                resource_id=incident.id,
                metadata_json={"title": incident.title, "status": incident.status},
            )
        )
        db.delete(incident)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for incident deletion.")

    return {"status": "deleted", "incident_id": incident_id}


@router.patch("/admin/stations/{station_id}", response_model=StationResponse)
def admin_update_station(
    station_id: str,
    payload: StationAdminUpdateRequest,
    auth: AuthContext = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    station_uuid = _coerce_uuid(station_id)
    if station_uuid is None:
        return error_response(404, "STATION_NOT_FOUND", "Station was not found.")
    station = db.get(TrafficStation, station_uuid)
    if station is None:
        return error_response(404, "STATION_NOT_FOUND", "Station was not found.")

    try:
        if payload.name is not None:
            station.name = payload.name.strip()
        if payload.locality is not None:
            station.locality = payload.locality.strip()
        if payload.contact_number is not None:
            station.contact_number = payload.contact_number.strip() or None
        if payload.active is not None:
            station.active = payload.active
        db.add(
            SystemAuditLog(
                actor_user_id=_coerce_uuid(auth.user_account_id),
                actor_role=auth.role,
                action="admin_update_station",
                resource_type="traffic_stations",
                resource_id=str(station.id),
                metadata_json={"station_code": station.station_code, "active": station.active},
            )
        )
        db.commit()
        db.refresh(station)
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for station update.")

    return StationResponse(
        id=str(station.id),
        station_code=station.station_code,
        name=station.name,
        locality=station.locality,
        latitude=station.latitude,
        longitude=station.longitude,
        contact_number=station.contact_number,
        active=station.active,
    )


@router.patch("/admin/users/{user_id}", response_model=UserResponse)
def admin_update_user(
    user_id: str,
    payload: UserAdminUpdateRequest,
    auth: AuthContext = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    user_uuid = _coerce_uuid(user_id)
    if user_uuid is None:
        return error_response(404, "USER_NOT_FOUND", "User was not found.")
    account = db.get(UserAccount, user_uuid)
    if account is None:
        return error_response(404, "USER_NOT_FOUND", "User was not found.")

    try:
        if payload.display_name is not None:
            account.display_name = payload.display_name.strip()
        if payload.role is not None:
            account.role = payload.role
        if payload.is_active is not None:
            account.is_active = payload.is_active
        db.add(
            SystemAuditLog(
                actor_user_id=_coerce_uuid(auth.user_account_id),
                actor_role=auth.role,
                action="admin_update_user",
                resource_type="user_accounts",
                resource_id=str(account.id),
                metadata_json={"role": account.role, "is_active": account.is_active},
            )
        )
        db.commit()
        db.refresh(account)
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for user update.")

    return _serialize_user(account)


@router.delete("/admin/votes/{vote_id}")
def admin_delete_vote(
    vote_id: str,
    auth: AuthContext = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    vote_uuid = _coerce_uuid(vote_id)
    if vote_uuid is None:
        return error_response(404, "VOTE_NOT_FOUND", "Vote was not found.")
    vote = db.get(IncidentVote, vote_uuid)
    if vote is None:
        return error_response(404, "VOTE_NOT_FOUND", "Vote was not found.")
    incident = db.get(Incident, vote.incident_id)

    try:
        db.add(
            SystemAuditLog(
                actor_user_id=_coerce_uuid(auth.user_account_id),
                actor_role=auth.role,
                action="admin_delete_vote",
                resource_type="incident_votes",
                resource_id=str(vote.id),
                metadata_json={"incident_id": vote.incident_id, "vote_value": vote.vote_value},
            )
        )
        db.delete(vote)
        db.flush()
        if incident is not None:
            _refresh_incident_vote_totals(db, incident)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for vote deletion.")

    return {"status": "deleted", "vote_id": str(vote_uuid)}


@router.get("/admin/summary")
def admin_foundation_summary(
    _auth: AuthContext = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    status_counts = dict(db.execute(select(Incident.status, func.count()).group_by(Incident.status)).all())
    return {
        "incident_count": db.scalar(select(func.count()).select_from(Incident)) or 0,
        "station_count": db.scalar(select(func.count()).select_from(TrafficStation)) or 0,
        "vote_count": db.scalar(select(func.count()).select_from(IncidentVote)) or 0,
        "prediction_count": db.scalar(select(func.count()).select_from(IncidentPrediction)) or 0,
        "status_counts": status_counts,
    }


@router.post("/admin/seed", response_model=SeedResponse)
def seed_foundation(
    _auth: AuthContext = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    report = seed_foundation_data(db)
    return SeedResponse(
        status="seeded",
        stations=report.stations,
        users=report.users,
        incidents=report.incidents,
        votes=report.votes,
        predictions=report.predictions,
    )
















