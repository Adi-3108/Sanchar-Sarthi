from __future__ import annotations

from datetime import datetime
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
from app.services.foundation_seed_service import seed_foundation_data
from app.services.incident_service import apply_incident_vote, transition_incident

router = APIRouter(prefix="/api/foundation", tags=["foundation"])


class StationResponse(BaseModel):
    station_code: str
    name: str
    locality: str
    latitude: float
    longitude: float
    contact_number: str | None = None


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
    police_force_required: int | None = None
    barricades_required: int | None = None
    route_impact_summary: str | None = None
    resolution_notes: str | None = None
    station_alerted: bool
    created_at: datetime
    updated_at: datetime
    latest_prediction: PredictionResponse | None = None


class FoundationBrowseResponse(BaseModel):
    incidents: list[IncidentResponse]
    stations: list[StationResponse]
    statuses: list[str]


class VoteRequest(BaseModel):
    vote_value: str = Field(pattern="^(true|false)$")


class StatusTransitionRequest(BaseModel):
    status: str = Field(pattern="^(reported|pending_verification|active|escalated|resolved|rejected|archived)$")
    resolution_notes: str | None = Field(default=None, max_length=1000)


class SeedResponse(BaseModel):
    status: str
    stations: int
    users: int
    incidents: int
    votes: int
    predictions: int


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
        .order_by(IncidentPrediction.created_at.desc(), IncidentPrediction.id.desc())
    )


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


def _serialize_incident(db: Session, incident: Incident) -> IncidentResponse:
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
        assigned_station_name=incident.assigned_station_name,
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
                station_code=station.station_code,
                name=station.name,
                locality=station.locality,
                latitude=station.latitude,
                longitude=station.longitude,
                contact_number=station.contact_number,
            )
            for station in stations
        ],
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
        db.commit()
        db.refresh(incident)
    except IntegrityError:
        db.rollback()
        return error_response(409, "DUPLICATE_VOTE", "Only one vote is allowed per user per incident.")
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for voting.")
    return _serialize_incident(db, incident)


@router.get("/control-room", response_model=FoundationBrowseResponse)
def control_room_foundation(
    _auth: AuthContext = Depends(require_role("control_room_officer", "admin")),
    db: Session = Depends(get_db),
):
    return browse_foundation_incidents(db)


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
