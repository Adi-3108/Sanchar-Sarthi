from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.orm.citizen_report import CitizenReport
from app.orm.demo_scenario import DemoScenario
from app.orm.event import Event
from app.orm.event_dna import EventDna
from app.orm.event_feature import EventFeature
from app.orm.event_prediction import EventPrediction
from app.orm.event_recommendation import EventRecommendation
from app.orm.hotspot_cluster import HotspotCluster
from app.orm.live_event_update import LiveEventUpdate
from app.orm.officer_event_assignment import OfficerEventAssignment
from app.orm.police_officer_profile import PoliceOfficerProfile
from app.orm.post_event_report import PostEventReport
from app.orm.user_account import UserAccount
from app.schemas.reports import CitizenReportCreate
from app.services.citizen_report_service import create_citizen_report
from app.services.event_dna_service import rebuild_event_dna_records
from app.services.feature_engineering_service import build_features_for_event
from app.services.hotspot_service import rebuild_hotspots
from app.services.live_escalation_service import LiveUpdateInput, apply_live_update
from app.services.post_event_report_service import generate_post_event_report
from app.services.prediction_service import predict_event, serialize_event_prediction
from app.services.recommendation_orchestrator import (
    build_recommendation_input,
    generate_recommendation_plan,
    persist_recommendation_plan,
)
from app.services.weather_service import resolve_weather_adjustment
from app.core.config import get_settings
from app.core.translation_budget import TranslationBudgetGuard
from app.services.translation_service import TranslationService


def _dt(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


DEMO_USER_BLUEPRINTS: tuple[dict[str, str], ...] = (
    {
        "role": "control_room",
        "display_name": "Demo Control Room",
        "auth_provider_uid": "demo-firebase-uid-control-room",
    },
    {
        "role": "police_officer",
        "display_name": "Demo Officer HSR",
        "auth_provider_uid": "demo-firebase-uid-hsr-officer",
    },
    {
        "role": "police_officer",
        "display_name": "Demo Officer Peenya",
        "auth_provider_uid": "demo-firebase-uid-peenya-officer",
    },
)

DEMO_OFFICER_BLUEPRINTS: tuple[dict[str, object], ...] = (
    {
        "officer_id": "BTP-HSR-001",
        "firebase_uid": "demo-firebase-uid-hsr-officer",
        "display_name": "Demo Officer HSR",
        "rank": "Traffic Constable",
        "police_station": "HSR Layout",
        "assigned_corridors_json": ["ORR East 1"],
        "assigned_zones_json": ["East"],
        "firebase_email": "officer.hsr.demo@eventflow.local",
    },
    {
        "officer_id": "BTP-PEENYA-001",
        "firebase_uid": "demo-firebase-uid-peenya-officer",
        "display_name": "Demo Officer Peenya",
        "rank": "Traffic Sub Inspector",
        "police_station": "Peenya",
        "assigned_corridors_json": ["Tumkur Road"],
        "assigned_zones_json": ["North"],
        "firebase_email": "officer.peenya.demo@eventflow.local",
    },
)

INCIDENT_BLUEPRINTS: tuple[dict[str, object], ...] = (
    {
        "id": "INCIDENT_RALLY_ORR",
        "event_type": "planned",
        "latitude": 12.9308,
        "longitude": 77.6850,
        "event_cause": "Procession Movement",
        "event_cause_clean": "procession_movement",
        "requires_road_closure": True,
        "start_datetime": _dt(2026, 7, 20, 12, 30),
        "end_datetime": _dt(2026, 7, 20, 15, 0),
        "status": "scheduled",
        "description": "Planned evening procession near ORR East during peak travel demand.",
        "description_language": "en",
        "description_for_features": "planned evening procession near ORR East during peak travel demand",
        "description_normalization_method": "raw_ascii",
        "veh_type": "mixed",
        "corridor": "ORR East 1",
        "priority": "High",
        "police_station": "HSR Layout",
        "zone": "East",
        "junction": "Agara Junction",
        "raw_payload": {
            "demo": True,
            "scenario": "predict_plan",
            "walkthrough_note": "Primary planned-event storyline for judge walkthroughs.",
        },
    },
    {
        "id": "INCIDENT_CROWD_IBLUR",
        "event_type": "planned",
        "latitude": 12.9327,
        "longitude": 77.6882,
        "event_cause": "Crowd Buildup",
        "event_cause_clean": "crowd_buildup",
        "requires_road_closure": False,
        "start_datetime": _dt(2026, 7, 20, 13, 0),
        "end_datetime": _dt(2026, 7, 20, 16, 0),
        "status": "open",
        "description": "Large spillover crowd expected near the ORR service road junction.",
        "description_language": "en",
        "description_for_features": "large spillover crowd expected near the ORR service road junction",
        "description_normalization_method": "raw_ascii",
        "veh_type": "mixed",
        "corridor": "ORR East 1",
        "priority": "High",
        "police_station": "HSR Layout",
        "zone": "East",
        "junction": "Iblur Junction",
        "raw_payload": {
            "demo": True,
            "scenario": "coordination_support",
            "walkthrough_note": "Secondary ORR event for overlap and hotspot context.",
        },
    },
    {
        "id": "INCIDENT_WATERLOGGING_HSR",
        "event_type": "unplanned",
        "latitude": 12.9296,
        "longitude": 77.6824,
        "event_cause": "Waterlogging",
        "event_cause_clean": "waterlogging",
        "requires_road_closure": True,
        "start_datetime": _dt(2026, 7, 18, 10, 30),
        "end_datetime": _dt(2026, 7, 18, 14, 0),
        "closed_datetime": _dt(2026, 7, 18, 13, 35),
        "resolved_datetime": _dt(2026, 7, 18, 14, 20),
        "status": "resolved",
        "description": "Heavy rain waterlogging forced upstream filtering near the HSR corridor.",
        "description_language": "en",
        "description_for_features": "heavy rain waterlogging forced upstream filtering near the HSR corridor",
        "description_normalization_method": "raw_ascii",
        "veh_type": "mixed",
        "corridor": "ORR East 1",
        "priority": "High",
        "police_station": "HSR Layout",
        "zone": "East",
        "junction": "Silk Board Junction",
        "raw_payload": {
            "demo": True,
            "scenario": "learning_loop",
            "weather_condition": "heavy_rain",
            "walkthrough_note": "Resolved event with seeded reports, live escalation, and learning output.",
        },
    },
    {
        "id": "INCIDENT_BREAKDOWN_TUMKUR",
        "event_type": "unplanned",
        "latitude": 13.0400,
        "longitude": 77.5181,
        "event_cause": "Vehicle Breakdown",
        "event_cause_clean": "vehicle_breakdown",
        "requires_road_closure": False,
        "start_datetime": _dt(2026, 7, 20, 12, 45),
        "end_datetime": None,
        "status": "open",
        "description": "Heavy vehicle breakdown reducing lane availability toward Peenya.",
        "description_language": "en",
        "description_for_features": "heavy vehicle breakdown reducing lane availability toward Peenya",
        "description_normalization_method": "raw_ascii",
        "veh_type": "heavy_goods_vehicle",
        "corridor": "Tumkur Road",
        "priority": "High",
        "police_station": "Peenya",
        "zone": "North",
        "junction": "Goraguntepalya Junction",
        "raw_payload": {
            "demo": True,
            "scenario": "multi_event",
            "walkthrough_note": "Primary unplanned north-corridor event for multi-event coordination.",
        },
    },
    {
        "id": "INCIDENT_CONSTRUCTION_TUMKUR",
        "event_type": "planned",
        "latitude": 13.0418,
        "longitude": 77.5211,
        "event_cause": "Construction",
        "event_cause_clean": "construction",
        "requires_road_closure": True,
        "start_datetime": _dt(2026, 7, 20, 11, 30),
        "end_datetime": _dt(2026, 7, 20, 18, 0),
        "status": "scheduled",
        "description": "Lane-channelization works scheduled along the Peenya stretch.",
        "description_language": "en",
        "description_for_features": "lane channelization works scheduled along the Peenya stretch",
        "description_normalization_method": "raw_ascii",
        "veh_type": "mixed",
        "corridor": "Tumkur Road",
        "priority": "High",
        "police_station": "Peenya",
        "zone": "North",
        "junction": "Jalahalli Cross",
        "raw_payload": {
            "demo": True,
            "scenario": "multi_event",
            "walkthrough_note": "Overlap event that competes for manpower and diversion space.",
        },
    },
    {
        "id": "INCIDENT_ACCIDENT_PEENYA",
        "event_type": "unplanned",
        "latitude": 13.0376,
        "longitude": 77.5160,
        "event_cause": "Accident",
        "event_cause_clean": "accident",
        "requires_road_closure": True,
        "start_datetime": _dt(2026, 7, 19, 8, 45),
        "end_datetime": _dt(2026, 7, 19, 10, 15),
        "closed_datetime": _dt(2026, 7, 19, 9, 50),
        "resolved_datetime": _dt(2026, 7, 19, 10, 20),
        "status": "resolved",
        "description": "Morning accident required a short closure near Peenya flyover access.",
        "description_language": "en",
        "description_for_features": "morning accident required a short closure near Peenya flyover access",
        "description_normalization_method": "raw_ascii",
        "veh_type": "mixed",
        "corridor": "Tumkur Road",
        "priority": "High",
        "police_station": "Peenya",
        "zone": "North",
        "junction": "Peenya Flyover",
        "raw_payload": {
            "demo": True,
            "scenario": "dataset_support",
            "walkthrough_note": "Additional north-corridor history so hotspot clustering is deterministic.",
        },
    },
)

DEMO_REPORT_BLUEPRINTS: tuple[dict[str, object], ...] = (
    {
        "report_source": "demo",
        "report_type": "waterlogging",
        "latitude": 12.9293,
        "longitude": 77.6820,
        "severity": "Critical",
        "description": "Heavy rain has flooded the upstream service road and vehicles are stacking back rapidly.",
        "language": "en",
        "event_id": "INCIDENT_WATERLOGGING_HSR",
    },
    {
        "report_source": "demo",
        "report_type": "road_blockage",
        "latitude": 12.9298,
        "longitude": 77.6827,
        "severity": "High",
        "description": "Barricades and standing water have reduced the corridor to a narrow pass-through lane.",
        "language": "en",
        "event_id": "INCIDENT_WATERLOGGING_HSR",
    },
    {
        "report_source": "demo",
        "report_type": "heavy_congestion",
        "latitude": 12.9302,
        "longitude": 77.6831,
        "severity": "High",
        "description": "Queue spillback is extending into the upstream junction and blocking turn pockets.",
        "language": "en",
        "event_id": "INCIDENT_WATERLOGGING_HSR",
    },
)

DEMO_LIVE_UPDATE_BLUEPRINTS: tuple[dict[str, object], ...] = (
    {
        "event_id": "INCIDENT_WATERLOGGING_HSR",
        "update_source": "field_officer",
        "current_congestion_level": "Warning",
        "field_update": "Water depth rising near the upstream drain and lane discipline is breaking.",
        "road_closure_active": True,
        "officer_shortage": False,
        "crowd_increase": False,
        "rain_waterlogging": True,
        "new_nearby_incident": False,
    },
    {
        "event_id": "INCIDENT_WATERLOGGING_HSR",
        "update_source": "control_room",
        "current_congestion_level": "Critical",
        "field_update": "Spillback has reached the junction mouth and reserve manpower is being requested.",
        "road_closure_active": True,
        "officer_shortage": True,
        "crowd_increase": True,
        "rain_waterlogging": True,
        "new_nearby_incident": False,
    },
)

DEMO_SCENARIO_BLUEPRINTS: tuple[dict[str, object], ...] = (
    {
        "scenario_name": "Judge Walkthrough: Predict And Plan",
        "scenario_type": "simulation",
        "description": "Use the ORR rally storyline to show Event DNA, similar-event memory, impact scoring, and weather-aware planning.",
    },
    {
        "scenario_name": "Judge Walkthrough: Live Escalation",
        "scenario_type": "live_escalation",
        "description": "Use the seeded HSR waterlogging reports and live updates to demonstrate confidence-backed escalation.",
    },
    {
        "scenario_name": "Judge Walkthrough: Multi-Event Coordination",
        "scenario_type": "coordination",
        "description": "Use the Tumkur Road overlap to show conflict overlays, manpower gap, and coordinated response.",
    },
    {
        "scenario_name": "Judge Walkthrough: Post-Event Learning",
        "scenario_type": "learning",
        "description": "Use the resolved HSR waterlogging event to show after-action learning and future playbooks.",
    },
)

INCIDENT_IDS = tuple(str(item["id"]) for item in INCIDENT_BLUEPRINTS)
DEMO_SCENARIO_NAMES = tuple(str(item["scenario_name"]) for item in DEMO_SCENARIO_BLUEPRINTS)
DEMO_FIREBASE_UIDS = tuple(str(item["auth_provider_uid"]) for item in DEMO_USER_BLUEPRINTS)
DEMO_OFFICER_IDS = tuple(str(item["officer_id"]) for item in DEMO_OFFICER_BLUEPRINTS)
LEARNING_EVENT_ID = "INCIDENT_WATERLOGGING_HSR"
COORDINATION_EVENT_IDS = ("INCIDENT_BREAKDOWN_TUMKUR", "INCIDENT_CONSTRUCTION_TUMKUR")


@dataclass(frozen=True)
class DemoSeedReport:
    scenarios_seeded: int
    demo_events_seeded: int
    demo_users_seeded: int
    demo_officers_seeded: int
    officer_assignments_seeded: int
    demo_features_ready: int
    demo_dna_ready: int
    demo_predictions_ready: int
    demo_recommendations_ready: int
    demo_hotspot_clusters_ready: int
    citizen_reports_seeded: int
    live_updates_seeded: int
    post_event_reports_generated: int
    scenario_names: list[str]
    demo_event_ids: list[str]


def _order_lookup(values: tuple[str, ...]) -> dict[str, int]:
    return {value: index for index, value in enumerate(values)}


def _event_order(event_id: str) -> int:
    return _order_lookup(INCIDENT_IDS).get(event_id, len(INCIDENT_IDS))


def _scenario_order(scenario_name: str) -> int:
    return _order_lookup(DEMO_SCENARIO_NAMES).get(scenario_name, len(DEMO_SCENARIO_NAMES))


def _list_demo_events(db: Session) -> list[Event]:
    return sorted(
        db.scalars(select(Event).where(Event.id.in_(INCIDENT_IDS))).all(),
        key=lambda event: _event_order(event.id),
    )


def _list_demo_features(db: Session) -> list[EventFeature]:
    return sorted(
        db.scalars(select(EventFeature).where(EventFeature.event_id.in_(INCIDENT_IDS))).all(),
        key=lambda feature: _event_order(feature.event_id),
    )


def _list_demo_dna_records(db: Session) -> list[EventDna]:
    return sorted(
        db.scalars(select(EventDna).where(EventDna.event_id.in_(INCIDENT_IDS))).all(),
        key=lambda record: _event_order(record.event_id),
    )


def _list_demo_predictions(db: Session) -> list[EventPrediction]:
    return sorted(
        db.scalars(select(EventPrediction).where(EventPrediction.event_id.in_(INCIDENT_IDS))).all(),
        key=lambda record: _event_order(record.event_id),
    )


def _list_demo_recommendations(db: Session) -> list[EventRecommendation]:
    return sorted(
        db.scalars(select(EventRecommendation).where(EventRecommendation.event_id.in_(INCIDENT_IDS))).all(),
        key=lambda record: _event_order(record.event_id),
    )


def _list_demo_reports(db: Session) -> list[CitizenReport]:
    return sorted(
        db.scalars(select(CitizenReport).where(CitizenReport.event_id.in_(INCIDENT_IDS))).all(),
        key=lambda record: (_event_order(record.event_id or ""), str(record.id)),
    )


def _list_demo_live_updates(db: Session) -> list[LiveEventUpdate]:
    return sorted(
        db.scalars(select(LiveEventUpdate).where(LiveEventUpdate.event_id.in_(INCIDENT_IDS))).all(),
        key=lambda record: (_event_order(record.event_id), str(record.id)),
    )


def _list_demo_post_event_reports(db: Session) -> list[PostEventReport]:
    return sorted(
        db.scalars(select(PostEventReport).where(PostEventReport.event_id.in_(INCIDENT_IDS))).all(),
        key=lambda record: (_event_order(record.event_id), str(record.id)),
    )


def _list_demo_scenarios(db: Session) -> list[DemoScenario]:
    return sorted(
        db.scalars(select(DemoScenario).where(DemoScenario.scenario_name.in_(DEMO_SCENARIO_NAMES))).all(),
        key=lambda record: _scenario_order(record.scenario_name),
    )


def _list_demo_users(db: Session) -> list[UserAccount]:
    return sorted(
        db.scalars(select(UserAccount).where(UserAccount.auth_provider_uid.in_(DEMO_FIREBASE_UIDS))).all(),
        key=lambda account: DEMO_FIREBASE_UIDS.index(account.auth_provider_uid),
    )


def _list_demo_officers(db: Session) -> list[PoliceOfficerProfile]:
    return sorted(
        db.scalars(select(PoliceOfficerProfile).where(PoliceOfficerProfile.officer_id.in_(DEMO_OFFICER_IDS))).all(),
        key=lambda officer: DEMO_OFFICER_IDS.index(officer.officer_id),
    )


def _list_demo_assignments(db: Session, officer_profile_ids: list[object]) -> list[OfficerEventAssignment]:
    if not officer_profile_ids:
        return []
    return db.scalars(
        select(OfficerEventAssignment).where(OfficerEventAssignment.officer_profile_id.in_(officer_profile_ids))
    ).all()


def _delete_records(records: list[object], db: Session) -> None:
    for record in records:
        db.delete(record)
    db.flush()


def _cleanup_existing_demo_records(db: Session) -> None:
    _delete_records(_list_demo_post_event_reports(db), db)
    _delete_records(_list_demo_live_updates(db), db)
    _delete_records(_list_demo_reports(db), db)
    _delete_records(_list_demo_recommendations(db), db)
    _delete_records(_list_demo_predictions(db), db)
    _delete_records(_list_demo_dna_records(db), db)
    _delete_records(_list_demo_features(db), db)

    demo_officers = _list_demo_officers(db)
    if demo_officers:
        officer_profile_ids = [officer.id for officer in demo_officers]
        _delete_records(_list_demo_assignments(db, officer_profile_ids), db)

    _delete_records(_list_demo_scenarios(db), db)
    _delete_records(_list_demo_events(db), db)


def _upsert_demo_users(db: Session) -> dict[str, UserAccount]:
    accounts: dict[str, UserAccount] = {}
    for blueprint in DEMO_USER_BLUEPRINTS:
        firebase_uid = str(blueprint["auth_provider_uid"])
        account = db.scalars(
            select(UserAccount).where(UserAccount.auth_provider_uid == firebase_uid)
        ).first()
        if account is None:
            account = UserAccount(
                role=str(blueprint["role"]),
                display_name=str(blueprint["display_name"]),
                auth_provider="firebase",
                auth_provider_uid=firebase_uid,
                is_active=True,
            )
            db.add(account)
        else:
            account.role = str(blueprint["role"])
            account.display_name = str(blueprint["display_name"])
            account.is_active = True
        db.flush()
        accounts[firebase_uid] = account
    return accounts


def _upsert_demo_officers(db: Session, accounts: dict[str, UserAccount]) -> dict[str, PoliceOfficerProfile]:
    officers: dict[str, PoliceOfficerProfile] = {}
    for blueprint in DEMO_OFFICER_BLUEPRINTS:
        officer_id = str(blueprint["officer_id"])
        firebase_uid = str(blueprint["firebase_uid"])
        profile = db.scalars(
            select(PoliceOfficerProfile).where(PoliceOfficerProfile.officer_id == officer_id)
        ).first()
        if profile is None:
            profile = PoliceOfficerProfile(
                officer_id=officer_id,
                display_name=str(blueprint["display_name"]),
                police_station=str(blueprint["police_station"]),
                assigned_corridors_json=list(blueprint["assigned_corridors_json"]),
                assigned_zones_json=list(blueprint["assigned_zones_json"]),
                firebase_email=str(blueprint["firebase_email"]),
                active=True,
            )
            db.add(profile)
        profile.user_account_id = accounts[firebase_uid].id
        profile.display_name = str(blueprint["display_name"])
        profile.rank = str(blueprint["rank"])
        profile.police_station = str(blueprint["police_station"])
        profile.assigned_corridors_json = list(blueprint["assigned_corridors_json"])
        profile.assigned_zones_json = list(blueprint["assigned_zones_json"])
        profile.firebase_email = str(blueprint["firebase_email"])
        profile.active = True
        db.flush()
        officers[officer_id] = profile
    return officers


def _seed_demo_events(db: Session) -> dict[str, Event]:
    seeded: dict[str, Event] = {}
    for blueprint in INCIDENT_BLUEPRINTS:
        event = db.merge(Event(**blueprint))
        db.flush()
        seeded[event.id] = event
    return seeded


def _seed_demo_assignments(
    db: Session,
    *,
    control_room_account: UserAccount,
    officers_by_id: dict[str, PoliceOfficerProfile],
) -> int:
    assignment_blueprints = (
        {
            "officer_profile_id": officers_by_id["BTP-HSR-001"].id,
            "event_id": "INCIDENT_RALLY_ORR",
            "corridor": "ORR East 1",
            "police_station": "HSR Layout",
            "assignment_type": "event",
        },
        {
            "officer_profile_id": officers_by_id["BTP-HSR-001"].id,
            "event_id": "INCIDENT_CROWD_IBLUR",
            "corridor": "ORR East 1",
            "police_station": "HSR Layout",
            "assignment_type": "event",
        },
        {
            "officer_profile_id": officers_by_id["BTP-HSR-001"].id,
            "event_id": "INCIDENT_WATERLOGGING_HSR",
            "corridor": "ORR East 1",
            "police_station": "HSR Layout",
            "assignment_type": "event",
        },
        {
            "officer_profile_id": officers_by_id["BTP-HSR-001"].id,
            "event_id": None,
            "corridor": "ORR East 1",
            "police_station": "HSR Layout",
            "assignment_type": "corridor",
        },
        {
            "officer_profile_id": officers_by_id["BTP-PEENYA-001"].id,
            "event_id": "INCIDENT_BREAKDOWN_TUMKUR",
            "corridor": "Tumkur Road",
            "police_station": "Peenya",
            "assignment_type": "event",
        },
        {
            "officer_profile_id": officers_by_id["BTP-PEENYA-001"].id,
            "event_id": "INCIDENT_CONSTRUCTION_TUMKUR",
            "corridor": "Tumkur Road",
            "police_station": "Peenya",
            "assignment_type": "event",
        },
        {
            "officer_profile_id": officers_by_id["BTP-PEENYA-001"].id,
            "event_id": "INCIDENT_ACCIDENT_PEENYA",
            "corridor": "Tumkur Road",
            "police_station": "Peenya",
            "assignment_type": "event",
        },
        {
            "officer_profile_id": officers_by_id["BTP-PEENYA-001"].id,
            "event_id": None,
            "corridor": "Tumkur Road",
            "police_station": "Peenya",
            "assignment_type": "corridor",
        },
    )
    for blueprint in assignment_blueprints:
        db.add(
            OfficerEventAssignment(
                officer_profile_id=blueprint["officer_profile_id"],
                event_id=blueprint["event_id"],
                corridor=blueprint["corridor"],
                police_station=blueprint["police_station"],
                assignment_type=blueprint["assignment_type"],
                assignment_status="active",
                assigned_by_user_id=control_room_account.id,
            )
        )
    db.flush()
    return len(assignment_blueprints)


def _feature_by_event_id(db: Session) -> dict[str, EventFeature]:
    return {feature.event_id: feature for feature in _list_demo_features(db)}


def _prediction_by_event_id(db: Session) -> dict[str, EventPrediction]:
    return {record.event_id: record for record in _list_demo_predictions(db)}


def _seed_predictions_and_recommendations(
    db: Session,
    events_by_id: dict[str, Event],
) -> tuple[dict[str, EventPrediction], dict[str, EventRecommendation]]:
    features_by_event_id = _feature_by_event_id(db)
    prediction_records: dict[str, EventPrediction] = {}
    recommendation_records: dict[str, EventRecommendation] = {}

    for event_id in INCIDENT_IDS:
        event = events_by_id[event_id]
        feature = features_by_event_id.get(event_id)
        if feature is None:
            feature, _created = build_features_for_event(db, event, commit=False)
            features_by_event_id[event_id] = feature

        prediction_record, _prediction_created = predict_event(
            db,
            event,
            feature=feature,
            commit=False,
            persist=True,
        )
        prediction_records[event_id] = prediction_record

        prediction_for_plan = prediction_record
        raw_payload = dict(event.raw_payload or {})
        if raw_payload.get("weather_condition"):
            prediction_for_plan, _transient_created = predict_event(
                db,
                event,
                feature=feature,
                weather_condition=str(raw_payload.get("weather_condition")),
                weather_adjustment_override=resolve_weather_adjustment(
                    float(event.latitude),
                    float(event.longitude),
                    weather_condition=str(raw_payload.get("weather_condition")),
                    source_context="event_plan",
                ),
                commit=False,
                persist=False,
            )

        recommendation_input = build_recommendation_input(
            event,
            prediction_for_plan,
            available_officers=16 if event.corridor == "ORR East 1" else 14,
            include_logistics_impact=True,
            include_emergency_corridor=True,
        )
        plan = generate_recommendation_plan(recommendation_input)
        recommendation_record, _recommendation_created = persist_recommendation_plan(
            db,
            plan,
            commit=False,
            persist=True,
        )
        recommendation_records[event_id] = recommendation_record

    return prediction_records, recommendation_records


def _seed_demo_reports(db: Session, translation_service: TranslationService) -> int:
    created_count = 0
    for blueprint in DEMO_REPORT_BLUEPRINTS:
        create_citizen_report(
            db,
            CitizenReportCreate.model_validate(blueprint),
            translation_service,
            commit=False,
        )
        created_count += 1
    return created_count


def _seed_demo_live_updates(
    db: Session,
    prediction_by_event_id: dict[str, EventPrediction],
) -> int:
    created_count = 0
    corroborating_reports = len(DEMO_REPORT_BLUEPRINTS)
    for blueprint in DEMO_LIVE_UPDATE_BLUEPRINTS:
        event_id = str(blueprint["event_id"])
        prediction = prediction_by_event_id[event_id]
        expected_impact_score = (
            float(prediction.estimated_impact_score)
            if prediction.estimated_impact_score is not None
            else 0.0
        )
        result = apply_live_update(
            LiveUpdateInput(
                current_congestion_level=str(blueprint["current_congestion_level"]),
                field_update=str(blueprint["field_update"]),
                road_closure_active=bool(blueprint["road_closure_active"]),
                officer_shortage=bool(blueprint["officer_shortage"]),
                crowd_increase=bool(blueprint["crowd_increase"]),
                rain_waterlogging=bool(blueprint["rain_waterlogging"]),
                new_nearby_incident=bool(blueprint["new_nearby_incident"]),
                expected_impact_score=expected_impact_score,
                corroborating_reports=corroborating_reports,
            )
        )
        db.add(
            LiveEventUpdate(
                event_id=event_id,
                update_source=str(blueprint["update_source"]),
                current_congestion_level=str(blueprint["current_congestion_level"]),
                field_update=str(blueprint["field_update"]),
                road_closure_active=bool(blueprint["road_closure_active"]),
                officer_shortage=bool(blueprint["officer_shortage"]),
                crowd_increase=bool(blueprint["crowd_increase"]),
                rain_waterlogging=bool(blueprint["rain_waterlogging"]),
                new_nearby_incident=bool(blueprint["new_nearby_incident"]),
                expected_impact_score=float(result["expected_impact_score"]),
                current_impact_score=float(result["current_impact_score"]),
                impact_deviation=float(result["impact_deviation"]),
                alert_level=str(result["alert_level"]),
                adaptive_action=str(result["adaptive_action"]),
            )
        )
        created_count += 1
    db.flush()
    return created_count


def _build_scenario_payloads(
    prediction_by_event_id: dict[str, EventPrediction],
) -> dict[str, tuple[dict[str, object], dict[str, object]]]:
    rally_prediction = serialize_event_prediction(prediction_by_event_id["INCIDENT_RALLY_ORR"]) or {}
    learning_prediction = serialize_event_prediction(prediction_by_event_id[LEARNING_EVENT_ID]) or {}
    breakdown_prediction = serialize_event_prediction(prediction_by_event_id["INCIDENT_BREAKDOWN_TUMKUR"]) or {}
    construction_prediction = serialize_event_prediction(prediction_by_event_id["INCIDENT_CONSTRUCTION_TUMKUR"]) or {}

    return {
        "Judge Walkthrough: Predict And Plan": (
            {
                "route": "/simulation",
                "primary_event_id": "INCIDENT_RALLY_ORR",
                "event_ids": ["INCIDENT_RALLY_ORR", "INCIDENT_CROWD_IBLUR"],
                "walkthrough_steps": [
                    "Open Simulation Lab and use the seeded ORR rally storyline as the reference case.",
                    "Show Event DNA, similar-event memory, and the estimated impact score before changing weather.",
                    "Toggle heavy rain to show how barricade and diversion posture moves upstream.",
                ],
                "simulation_payload": {
                    "event_type": "planned",
                    "event_cause": "Procession Movement",
                    "latitude": 12.9308,
                    "longitude": 77.6850,
                    "corridor": "ORR East 1",
                    "police_station": "HSR Layout",
                    "zone": "East",
                    "junction": "Agara Junction",
                    "start_datetime": "2026-07-20T18:00:00+05:30",
                    "expected_duration_minutes": 150,
                    "weather_condition": "heavy_rain",
                    "rain_mm": 12,
                    "visibility_m": 800,
                    "available_officers": 16,
                    "description": "Planned evening procession near ORR East during peak travel demand.",
                    "veh_type": "mixed",
                },
            },
            {
                "expected_highlights": [
                    f"Baseline seeded rally impact is {rally_prediction.get('estimated_impact_score', 'n/a')} with {rally_prediction.get('impact_category', 'n/a')} severity.",
                    "Reason codes should mention corridor, peak-hour, and similar-event signals.",
                    "Weather override should widen barricade and diversion posture without claiming exact traffic speed.",
                ]
            },
        ),
        "Judge Walkthrough: Live Escalation": (
            {
                "route": f"/events/{LEARNING_EVENT_ID}",
                "primary_event_id": LEARNING_EVENT_ID,
                "event_ids": [LEARNING_EVENT_ID],
                "walkthrough_steps": [
                    "Open the resolved HSR waterlogging dossier and review the seeded citizen reports.",
                    "Show how corroborating reports feed into the live escalation timeline and adaptive actions.",
                    "Use the ready-made learning route afterward to close the monitor-and-adapt storyline.",
                ],
            },
            {
                "expected_highlights": [
                    f"Seeded learning event baseline impact is {learning_prediction.get('estimated_impact_score', 'n/a')}.",
                    f"{len(DEMO_REPORT_BLUEPRINTS)} corroborating reports and {len(DEMO_LIVE_UPDATE_BLUEPRINTS)} live updates are already linked.",
                    "The latest live update should push the alert state into a high-urgency posture for the learning narrative.",
                ]
            },
        ),
        "Judge Walkthrough: Multi-Event Coordination": (
            {
                "route": "/map-intelligence",
                "primary_event_id": COORDINATION_EVENT_IDS[0],
                "event_ids": list(COORDINATION_EVENT_IDS),
                "walkthrough_steps": [
                    "Open Map Intelligence and run the fixed Tumkur Road overlap event pair.",
                    "Show conflict overlays, manpower gap, and coordinated response notes.",
                    "Use the recommendation panels to explain why the overlap is operationally risky.",
                ],
                "multi_event_payload": {
                    "event_ids": list(COORDINATION_EVENT_IDS),
                    "available_officers": 18,
                },
            },
            {
                "expected_highlights": [
                    f"Tumkur breakdown impact starts near {breakdown_prediction.get('estimated_impact_score', 'n/a')}.",
                    f"Construction overlap adds a second event around {construction_prediction.get('estimated_impact_score', 'n/a')} impact.",
                    "Conflict analysis should surface corridor overlap and manpower competition, not a generic map-only view.",
                ]
            },
        ),
        "Judge Walkthrough: Post-Event Learning": (
            {
                "route": "/post-event-learning",
                "primary_event_id": LEARNING_EVENT_ID,
                "event_ids": [LEARNING_EVENT_ID],
                "walkthrough_steps": [
                    "Open Post-Event Learning with the seeded HSR waterlogging event ID.",
                    "Generate the after-action report and compare predicted versus simulated actual impact.",
                    "Read out lessons learned and the future-playbook recommendation to close the loop.",
                ],
            },
            {
                "expected_highlights": [
                    "Learning output should mention report reinforcement, weather-aware planning, and live escalation drift.",
                    "The post-event report is generated from the same seeded event, reports, live updates, and recommendation snapshot.",
                    "Future recommendations should sound operational and dataset-honest, not like exact outcome guarantees.",
                ]
            },
        ),
    }


def _seed_demo_scenarios(
    db: Session,
    prediction_by_event_id: dict[str, EventPrediction],
) -> int:
    scenario_payloads = _build_scenario_payloads(prediction_by_event_id)
    for blueprint in DEMO_SCENARIO_BLUEPRINTS:
        scenario_name = str(blueprint["scenario_name"])
        input_payload_json, expected_output_json = scenario_payloads[scenario_name]
        db.add(
            DemoScenario(
                scenario_name=scenario_name,
                scenario_type=str(blueprint["scenario_type"]),
                description=str(blueprint["description"]),
                input_payload_json=input_payload_json,
                expected_output_json=expected_output_json,
            )
        )
    db.flush()
    return len(DEMO_SCENARIO_BLUEPRINTS)


def _demo_cluster_count(features: list[EventFeature]) -> int:
    return len(
        {
            feature.location_cluster_id
            for feature in features
            if isinstance(feature.location_cluster_id, str) and feature.location_cluster_id.startswith("CL-")
        }
    )


def seed_demo_scenarios(db: Session, *, commit: bool = True) -> DemoSeedReport:
    _cleanup_existing_demo_records(db)

    accounts = _upsert_demo_users(db)
    officers_by_id = _upsert_demo_officers(db, accounts)
    events_by_id = _seed_demo_events(db)
    assignment_count = _seed_demo_assignments(
        db,
        control_room_account=accounts["demo-firebase-uid-control-room"],
        officers_by_id=officers_by_id,
    )

    settings = get_settings()
    budget_guard = TranslationBudgetGuard(
        daily_limit=settings.google_translate_daily_char_limit,
        monthly_limit=settings.google_translate_monthly_char_limit,
    )
    translation_service = TranslationService(settings, budget_guard)

    # rebuild_hotspots(db, commit=False)
    # rebuild_event_dna_records(db, refresh_supporting_data=False, commit=False)
    prediction_by_event_id, _recommendation_by_event_id = _seed_predictions_and_recommendations(db, events_by_id)
    report_count = _seed_demo_reports(db, translation_service)
    live_update_count = _seed_demo_live_updates(db, prediction_by_event_id)
    generate_post_event_report(db, LEARNING_EVENT_ID, commit=False)
    scenario_count = _seed_demo_scenarios(db, prediction_by_event_id)

    if commit:
        db.commit()
    else:
        db.flush()

    demo_features = _list_demo_features(db)
    return DemoSeedReport(
        scenarios_seeded=scenario_count,
        demo_events_seeded=len(_list_demo_events(db)),
        demo_users_seeded=len(_list_demo_users(db)),
        demo_officers_seeded=len(_list_demo_officers(db)),
        officer_assignments_seeded=assignment_count,
        demo_features_ready=len(demo_features),
        demo_dna_ready=len(_list_demo_dna_records(db)),
        demo_predictions_ready=len(_list_demo_predictions(db)),
        demo_recommendations_ready=len(_list_demo_recommendations(db)),
        demo_hotspot_clusters_ready=_demo_cluster_count(demo_features),
        citizen_reports_seeded=report_count,
        live_updates_seeded=live_update_count,
        post_event_reports_generated=len(_list_demo_post_event_reports(db)),
        scenario_names=list(DEMO_SCENARIO_NAMES),
        demo_event_ids=list(INCIDENT_IDS),
    )


def serialize_demo_seed_report(report: DemoSeedReport) -> dict[str, object]:
    return {
        "status": "success",
        "message": "Deterministic demo scenarios refreshed.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "demo_scenarios": report.scenarios_seeded,
            "demo_events": report.demo_events_seeded,
            "demo_users": report.demo_users_seeded,
            "demo_officers": report.demo_officers_seeded,
            "officer_assignments": report.officer_assignments_seeded,
            "demo_features": report.demo_features_ready,
            "demo_dna_records": report.demo_dna_ready,
            "demo_predictions": report.demo_predictions_ready,
            "demo_recommendations": report.demo_recommendations_ready,
            "demo_hotspot_clusters": report.demo_hotspot_clusters_ready,
            "demo_reports": report.citizen_reports_seeded,
            "demo_live_updates": report.live_updates_seeded,
            "demo_post_event_reports": report.post_event_reports_generated,
        },
        "scenario_names": report.scenario_names,
        "demo_event_ids": report.demo_event_ids,
    }


def _build_demo_checks(
    *,
    summary: dict[str, int],
) -> list[dict[str, object]]:
    return [
        {
            "key": "scenario_seed",
            "label": "Scenario records",
            "ready": summary["demo_scenarios"] >= len(DEMO_SCENARIO_BLUEPRINTS),
            "detail": f"{summary['demo_scenarios']} of {len(DEMO_SCENARIO_BLUEPRINTS)} judge walkthrough scenarios are stored.",
        },
        {
            "key": "event_seed",
            "label": "Deterministic events",
            "ready": summary["demo_events"] >= len(INCIDENT_BLUEPRINTS),
            "detail": f"{summary['demo_events']} of {len(INCIDENT_BLUEPRINTS)} fixed demo events are available.",
        },
        {
            "key": "hotspots",
            "label": "Hotspot coverage",
            "ready": summary["demo_hotspot_clusters"] >= 1,
            "detail": f"{summary['demo_hotspot_clusters']} persisted hotspot clusters cover the seeded corridors.",
        },
        {
            "key": "planning_stack",
            "label": "Predict and plan stack",
            "ready": (
                summary["demo_features"] >= len(INCIDENT_BLUEPRINTS)
                and summary["demo_dna_records"] >= len(INCIDENT_BLUEPRINTS)
                and summary["demo_predictions"] >= len(INCIDENT_BLUEPRINTS)
                and summary["demo_recommendations"] >= len(INCIDENT_BLUEPRINTS)
            ),
            "detail": (
                f"{summary['demo_features']} features, {summary['demo_dna_records']} DNA records, "
                f"{summary['demo_predictions']} predictions, and {summary['demo_recommendations']} recommendations are ready."
            ),
        },
        {
            "key": "live_loop",
            "label": "Monitor and adapt loop",
            "ready": summary["demo_reports"] >= 3 and summary["demo_live_updates"] >= 2,
            "detail": f"{summary['demo_reports']} reports and {summary['demo_live_updates']} live updates power the escalation storyline.",
        },
        {
            "key": "learning_loop",
            "label": "Post-event learning",
            "ready": summary["demo_post_event_reports"] >= 1,
            "detail": f"{summary['demo_post_event_reports']} after-action report is ready for the closing learning loop.",
        },
        {
            "key": "officer_access",
            "label": "Officer access mapping",
            "ready": summary["demo_officers"] >= 2 and summary["officer_assignments"] >= 6,
            "detail": f"{summary['demo_officers']} demo officers and {summary['officer_assignments']} assignments are mapped in PostgreSQL.",
        },
    ]


def _scenario_card(record: DemoScenario) -> dict[str, object]:
    input_payload = dict(record.input_payload_json or {})
    expected_output = dict(record.expected_output_json or {})
    return {
        "scenario_name": record.scenario_name,
        "scenario_type": record.scenario_type,
        "description": record.description,
        "route": str(input_payload.get("route") or "/settings"),
        "primary_event_id": input_payload.get("primary_event_id"),
        "event_ids": list(input_payload.get("event_ids") or []),
        "walkthrough_steps": [str(item) for item in list(input_payload.get("walkthrough_steps") or [])],
        "expected_highlights": [str(item) for item in list(expected_output.get("expected_highlights") or [])],
    }


def build_demo_status(db: Session) -> dict[str, object]:
    demo_features = _list_demo_features(db)
    summary = {
        "demo_scenarios": len(_list_demo_scenarios(db)),
        "demo_events": len(_list_demo_events(db)),
        "demo_users": len(_list_demo_users(db)),
        "demo_officers": len(_list_demo_officers(db)),
        "officer_assignments": len(_list_demo_assignments(db, [item.id for item in _list_demo_officers(db)])),
        "demo_features": len(demo_features),
        "demo_dna_records": len(_list_demo_dna_records(db)),
        "demo_predictions": len(_list_demo_predictions(db)),
        "demo_recommendations": len(_list_demo_recommendations(db)),
        "demo_hotspot_clusters": _demo_cluster_count(demo_features),
        "demo_reports": len(_list_demo_reports(db)),
        "demo_live_updates": len(_list_demo_live_updates(db)),
        "demo_post_event_reports": len(_list_demo_post_event_reports(db)),
    }
    checks = _build_demo_checks(summary=summary)
    status = "ready" if all(bool(item["ready"]) for item in checks) else "incomplete"

    return {
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "checks": checks,
        "scenario_cards": [_scenario_card(record) for record in _list_demo_scenarios(db)],
        "demo_event_ids": list(INCIDENT_IDS),
        "sample_event_ids": {
            "predict_plan": "INCIDENT_RALLY_ORR",
            "learning": LEARNING_EVENT_ID,
            "coordination_pair": list(COORDINATION_EVENT_IDS),
        },
        "notes": [
            "Phase 17 refreshes only records with fixed DEMO_ identifiers; non-demo records remain untouched.",
            "Seeded Firebase identities create backend authorization mappings only. Real sign-in users still need to exist in your Firebase project.",
            "The learning scenario stores a weather-aware recommendation snapshot while preserving a canonical seeded prediction row for consistency with earlier phases.",
        ],
    }
