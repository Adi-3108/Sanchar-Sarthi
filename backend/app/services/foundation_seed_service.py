from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.orm.incident import Incident
from app.orm.incident_prediction import IncidentPrediction
from app.orm.incident_vote import IncidentVote
from app.orm.system_audit_log import SystemAuditLog
from app.orm.traffic_station import TrafficStation
from app.orm.user_account import UserAccount


@dataclass(frozen=True)
class FoundationSeedReport:
    stations: int
    users: int
    incidents: int
    votes: int
    predictions: int


STATIONS = [
    ("BTP-MGROAD", "MG Road Traffic Police Station", "MG Road", 12.9756, 77.6068, "080-2294-2522"),
    ("BTP-SILKBOARD", "Madivala Traffic Police Station", "Silk Board", 12.9177, 77.6234, "080-2294-2533"),
    ("BTP-HEBBAL", "Hebbal Traffic Police Station", "Hebbal", 13.0358, 77.5970, "080-2294-2544"),
    ("BTP-MYSURUROAD", "Byatarayanapura Traffic Police Station", "Mysore Road", 12.9467, 77.5439, "080-2294-2555"),
]

USERS = [
    ("citizen-demo-001", "citizen", "Citizen One"),
    ("citizen-demo-002", "citizen", "Citizen Two"),
    ("citizen-demo-003", "citizen", "Citizen Three"),
]

INCIDENTS = [
    {
        "id": "SS-INC-001",
        "incident_type": "road_accident",
        "title": "Two-wheeler accident near MG Road Metro",
        "description": "Slow movement toward Trinity Circle; lane partially blocked.",
        "status": "active",
        "severity": "high",
        "location_name": "MG Road Metro",
        "latitude": 12.9756,
        "longitude": 77.6068,
        "locality": "MG Road",
        "ward": "Shanthala Nagar",
        "source_type": "system_seed",
        "true_vote_count": 8,
        "false_vote_count": 1,
        "confidence_score": Decimal("0.8800"),
        "assigned_station_code": "BTP-MGROAD",
        "police_force_required": 8,
        "barricades_required": 4,
        "route_impact_summary": "Use Cubbon Road for eastbound diversion.",
    },
    {
        "id": "SS-INC-002",
        "incident_type": "waterlogging",
        "title": "Waterlogging reported at Silk Board",
        "description": "Public reports indicate slow-moving traffic below the flyover.",
        "status": "pending_verification",
        "severity": "medium",
        "location_name": "Central Silk Board Junction",
        "latitude": 12.9177,
        "longitude": 77.6234,
        "locality": "Silk Board",
        "ward": "BTM Layout",
        "source_type": "system_seed",
        "true_vote_count": 3,
        "false_vote_count": 1,
        "confidence_score": Decimal("0.6500"),
        "assigned_station_code": "BTP-SILKBOARD",
        "police_force_required": 5,
        "barricades_required": 2,
        "route_impact_summary": "Prefer HSR 14th Main for local diversion.",
    },
    {
        "id": "SS-INC-003",
        "incident_type": "vip_movement",
        "title": "Temporary lane hold near Hebbal flyover",
        "description": "Control-room seed incident for station mapping and escalation testing.",
        "status": "escalated",
        "severity": "critical",
        "location_name": "Hebbal Flyover",
        "latitude": 13.0358,
        "longitude": 77.5970,
        "locality": "Hebbal",
        "ward": "Hebbal",
        "source_type": "system_seed",
        "true_vote_count": 12,
        "false_vote_count": 0,
        "confidence_score": Decimal("0.9700"),
        "assigned_station_code": "BTP-HEBBAL",
        "police_force_required": 14,
        "barricades_required": 8,
        "route_impact_summary": "Protect airport-bound corridor; divert local traffic through Sanjaynagar.",
    },
    {
        "id": "SS-INC-004",
        "incident_type": "signal_failure",
        "title": "Resolved signal failure on Mysore Road",
        "description": "Resolved seed incident remains visible for lifecycle testing.",
        "status": "resolved",
        "severity": "low",
        "location_name": "Mysore Road Satellite Bus Station",
        "latitude": 12.9467,
        "longitude": 77.5439,
        "locality": "Mysore Road",
        "ward": "Bapujinagar",
        "source_type": "system_seed",
        "true_vote_count": 5,
        "false_vote_count": 2,
        "confidence_score": Decimal("0.7100"),
        "assigned_station_code": "BTP-MYSURUROAD",
        "police_force_required": 2,
        "barricades_required": 0,
        "route_impact_summary": "Normal movement restored.",
        "resolution_notes": "Signal timing restored by field team.",
    },
]


def seed_foundation_data(db: Session, *, commit: bool = True) -> FoundationSeedReport:
    station_count = user_count = incident_count = vote_count = prediction_count = 0
    station_by_code: dict[str, TrafficStation] = {}

    for station_code, name, locality, latitude, longitude, contact_number in STATIONS:
        station = db.scalar(select(TrafficStation).where(TrafficStation.station_code == station_code))
        if station is None:
            station = TrafficStation(
                station_code=station_code,
                name=name,
                locality=locality,
                latitude=latitude,
                longitude=longitude,
                contact_number=contact_number,
            )
            db.add(station)
            station_count += 1
        station_by_code[station_code] = station

    users: list[UserAccount] = []
    for firebase_uid, role, display_name in USERS:
        user = db.scalar(select(UserAccount).where(UserAccount.auth_provider_uid == firebase_uid))
        if user is None:
            user = UserAccount(
                role=role,
                display_name=display_name,
                auth_provider="firebase",
                auth_provider_uid=firebase_uid,
                is_active=True,
            )
            db.add(user)
            user_count += 1
        users.append(user)

    db.flush()

    for item in INCIDENTS:
        incident = db.get(Incident, item["id"])
        station = station_by_code[item["assigned_station_code"]]
        if incident is None:
            incident = Incident(
                id=item["id"],
                incident_type=item["incident_type"],
                title=item["title"],
                description=item["description"],
                status=item["status"],
                severity=item["severity"],
                location_name=item["location_name"],
                latitude=item["latitude"],
                longitude=item["longitude"],
                locality=item["locality"],
                ward=item["ward"],
                source_type=item["source_type"],
                true_vote_count=item["true_vote_count"],
                false_vote_count=item["false_vote_count"],
                confidence_score=item["confidence_score"],
                assigned_station_id=station.id,
                assigned_station_name=station.name,
                police_force_required=item["police_force_required"],
                barricades_required=item["barricades_required"],
                route_impact_summary=item["route_impact_summary"],
                resolution_notes=item.get("resolution_notes"),
                visible_to_public=True,
                station_alerted=item["status"] in {"active", "escalated"},
            )
            db.add(incident)
            incident_count += 1

        existing_prediction = db.scalar(
            select(IncidentPrediction).where(IncidentPrediction.incident_id == item["id"])
        )
        if existing_prediction is None:
            db.add(
                IncidentPrediction(
                    incident_id=item["id"],
                    model_name="foundation_rule_engine",
                    model_version="phase-1",
                    predicted_severity=item["severity"],
                    police_force_required=item["police_force_required"],
                    barricades_required=item["barricades_required"],
                    urgency_score=item["confidence_score"],
                    route_disruption_score=Decimal("0.8000") if item["status"] in {"active", "escalated"} else Decimal("0.3500"),
                    confidence_score=item["confidence_score"],
                    station_recommendation=station.name,
                    hotspot_contribution_score=Decimal("0.6000"),
                    output_json={"source": "seeded_rule_engine", "phase": "foundation"},
                    explanation_text="Seeded Phase 1 rule output for auditable UI and workflow testing.",
                )
            )
            prediction_count += 1

        for user, vote_value in zip(users, ("true", "true", "false"), strict=False):
            existing_vote = db.scalar(
                select(IncidentVote)
                .where(IncidentVote.incident_id == item["id"])
                .where(IncidentVote.voter_user_id == user.id)
            )
            if existing_vote is None:
                db.add(IncidentVote(incident_id=item["id"], voter_user_id=user.id, vote_value=vote_value))
                vote_count += 1

    db.add(
        SystemAuditLog(
            actor_role="system",
            action="foundation_seed_data",
            resource_type="foundation",
            resource_id="phase-1",
            metadata_json={
                "stations_created": station_count,
                "users_created": user_count,
                "incidents_created": incident_count,
                "votes_created": vote_count,
                "predictions_created": prediction_count,
            },
        )
    )

    if commit:
        db.commit()

    return FoundationSeedReport(
        stations=station_count,
        users=user_count,
        incidents=incident_count,
        votes=vote_count,
        predictions=prediction_count,
    )
