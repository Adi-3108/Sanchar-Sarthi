from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from math import asin, cos, radians, sin, sqrt
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.orm.citizen_report import CitizenReport
from app.orm.event import Event
from app.schemas.reports import CitizenReportCreate
from app.services.text_normalization_service import NormalizedDescription, normalize_description
from app.services.translation_service import TranslationService

EARTH_RADIUS_KM = 6371.0088
EVENT_MATCH_RADIUS_KM = 2.0
DUPLICATE_RADIUS_KM = 0.3
MAX_DUPLICATE_SAMPLE = 100

SOURCE_CONFIDENCE_WEIGHT = {
    "citizen": 0.35,
    "demo": 0.45,
    "field_officer": 0.78,
    "control_room": 0.88,
}

SEVERITY_SIGNAL = {
    "low": 0.25,
    "minor": 0.25,
    "medium": 0.5,
    "moderate": 0.5,
    "high": 0.8,
    "severe": 0.9,
    "critical": 1.0,
}


@dataclass(frozen=True)
class EventMatch:
    event: Event | None
    distance_km: float | None
    location_match_confidence: float
    match_method: str


@dataclass(frozen=True)
class TranslationBookkeeping:
    language: str
    source_language: str
    translated_description: str | None
    translation_provider: str
    translation_status: str
    translation_character_count: int
    normalization: NormalizedDescription


def _safe_float(value: Decimal | float | int | None, *, default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return min(max(value, minimum), maximum)


def haversine_km(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    lat_a = radians(latitude_a)
    lat_b = radians(latitude_b)
    delta_lat = radians(latitude_b - latitude_a)
    delta_lng = radians(longitude_b - longitude_a)

    value = sin(delta_lat / 2) ** 2 + cos(lat_a) * cos(lat_b) * sin(delta_lng / 2) ** 2
    return round(2 * EARTH_RADIUS_KM * asin(sqrt(value)), 4)


def sanitize_report_description(description: str) -> str:
    without_tags = re.sub(r"<[^>]*>", " ", description)
    without_control_chars = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", without_tags)
    return re.sub(r"\s+", " ", without_control_chars).strip()


def _normalized_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().casefold()
    return normalized or None


def _location_confidence(distance_km: float, *, explicit: bool = False) -> float:
    if explicit:
        return round(_clamp(0.95 - min(distance_km, 5.0) * 0.11, 0.2, 0.95), 4)
    if distance_km > EVENT_MATCH_RADIUS_KM:
        return 0.0
    return round(_clamp(0.95 - (distance_km / EVENT_MATCH_RADIUS_KM) * 0.7, 0.25, 0.95), 4)


def match_nearest_event(
    db: Session,
    *,
    latitude: float,
    longitude: float,
    event_id: str | None = None,
) -> EventMatch:
    if event_id:
        event = db.get(Event, event_id)
        if event is None:
            raise ValueError(f"Event not found: {event_id}")
        distance_km = haversine_km(latitude, longitude, float(event.latitude), float(event.longitude))
        return EventMatch(
            event=event,
            distance_km=distance_km,
            location_match_confidence=_location_confidence(distance_km, explicit=True),
            match_method="explicit_event_id",
        )

    events = db.scalars(select(Event).order_by(Event.start_datetime.desc(), Event.id.desc())).all()
    nearest_event: Event | None = None
    nearest_distance: float | None = None
    for event in events:
        distance_km = haversine_km(latitude, longitude, float(event.latitude), float(event.longitude))
        if nearest_distance is None or distance_km < nearest_distance:
            nearest_event = event
            nearest_distance = distance_km

    if nearest_event is None or nearest_distance is None or nearest_distance > EVENT_MATCH_RADIUS_KM:
        return EventMatch(
            event=None,
            distance_km=nearest_distance,
            location_match_confidence=0.0,
            match_method="no_nearby_event",
        )

    return EventMatch(
        event=nearest_event,
        distance_km=nearest_distance,
        location_match_confidence=_location_confidence(nearest_distance),
        match_method="nearest_event_within_radius",
    )


def count_nearby_duplicate_reports(
    db: Session,
    *,
    latitude: float,
    longitude: float,
    report_type: str,
) -> int:
    report_type_key = report_type.strip().casefold()
    candidates = db.scalars(
        select(CitizenReport)
        .where(CitizenReport.report_type == report_type_key)
        .order_by(CitizenReport.created_at.desc(), CitizenReport.id.desc())
        .limit(MAX_DUPLICATE_SAMPLE)
    ).all()
    return sum(
        1
        for report in candidates
        if haversine_km(latitude, longitude, float(report.latitude), float(report.longitude)) <= DUPLICATE_RADIUS_KM
    )


def normalize_report_description(description: str, language: str | None, translation_service: TranslationService) -> dict[str, object]:
    result = translation_service.normalize(
        text=description,
        source_language=language,
        target_language='en',
    )
    return {
        'description': description,
        'source_language': result.source_language,
        'translated_description': result.translated_text,
        'translation_provider': result.provider,
        'translation_status': result.status,
        'translation_character_count': result.character_count,
    }


def _severity_signal(severity: str | None) -> float:
    return SEVERITY_SIGNAL.get(_normalized_text(severity) or "", 0.4)


def calculate_report_confidence(
    *,
    report_source: str,
    location_match_confidence: float,
    nearby_duplicate_count: int,
    severity: str | None,
    translated_description: str | None,
) -> tuple[float, dict[str, object]]:
    source_weight = SOURCE_CONFIDENCE_WEIGHT.get(report_source, SOURCE_CONFIDENCE_WEIGHT["citizen"])
    duplicate_signal = min(nearby_duplicate_count, 5) / 5
    severity_signal = _severity_signal(severity)
    text_signal = 1.0 if translated_description else 0.35

    confidence = (
        source_weight * 0.45
        + _clamp(location_match_confidence) * 0.25
        + duplicate_signal * 0.15
        + severity_signal * 0.1
        + text_signal * 0.05
    )
    confidence = round(_clamp(confidence, 0.05, 0.95), 4)
    return confidence, {
        "source_weight": round(source_weight, 4),
        "location_match_confidence": round(_clamp(location_match_confidence), 4),
        "nearby_duplicate_count": nearby_duplicate_count,
        "duplicate_signal": round(duplicate_signal, 4),
        "severity_signal": round(severity_signal, 4),
        "text_signal": round(text_signal, 4),
    }


def estimate_impact_score_change(
    *,
    report_confidence: float,
    location_match_confidence: float,
    nearby_duplicate_count: int,
    severity: str | None,
) -> float:
    duplicate_signal = min(nearby_duplicate_count, 5) / 5
    score_change = (
        report_confidence * 8
        + _clamp(location_match_confidence) * 4
        + duplicate_signal * 3
        + _severity_signal(severity) * 5
    )
    return round(min(score_change, 25.0), 2)


def derive_alert_level(
    *,
    report_confidence: float,
    severity: str | None,
    location_match_confidence: float,
) -> str:
    severity_key = _normalized_text(severity)
    if report_confidence >= 0.78 or (severity_key == "critical" and location_match_confidence >= 0.5):
        return "Critical"
    if report_confidence >= 0.58:
        return "Warning"
    if report_confidence >= 0.35:
        return "Watch"
    return "Info"


def build_recommended_action(
    *,
    report_source: str,
    matched_event: Event | None,
    alert_level: str,
    report_confidence: float,
) -> str:
    if matched_event is None:
        return (
            "Show as a public report marker and wait for corroboration before changing official traffic plans."
        )
    location = matched_event.junction or matched_event.corridor or matched_event.police_station or matched_event.id
    if report_source in {"field_officer", "control_room"} or report_confidence >= 0.7:
        return (
            f"Attach report to {location} and ask the assigned traffic unit to verify the "
            f"{alert_level.lower()} alert before adapting manpower or diversions."
        )
    return (
        f"Queue report against {location}; request field confirmation before escalating the recommendation plan."
    )


def build_report_response(record: CitizenReport) -> dict[str, object]:
    return {
        "status": record.status,
        "matched_event_id": record.matched_event_id,
        "source_language": record.source_language,
        "translation_status": record.translation_status,
        "translated_description": record.translated_description,
        "location_match_confidence": _safe_float(record.location_match_confidence)
        if record.location_match_confidence is not None
        else None,
        "report_confidence": _safe_float(record.report_confidence),
        "impact_score_change": _safe_float(record.impact_score_change),
        "new_alert_level": record.new_alert_level or "Info",
        "recommended_action": record.recommended_action or "",
    }


def serialize_citizen_report(record: CitizenReport) -> dict[str, object]:
    return {
        "id": str(record.id),
        "report_source": record.report_source,
        "report_type": record.report_type,
        "latitude": float(record.latitude),
        "longitude": float(record.longitude),
        "severity": record.severity,
        "description": record.description,
        "source_language": record.source_language,
        "translated_description": record.translated_description,
        "translation_status": record.translation_status,
        "matched_event_id": record.matched_event_id,
        "location_match_confidence": _safe_float(record.location_match_confidence)
        if record.location_match_confidence is not None
        else None,
        "report_confidence": _safe_float(record.report_confidence)
        if record.report_confidence is not None
        else None,
        "impact_score_change": _safe_float(record.impact_score_change)
        if record.impact_score_change is not None
        else None,
        "new_alert_level": record.new_alert_level,
        "recommended_action": record.recommended_action,
        "status": record.status,
        "created_at": (
            record.created_at.astimezone(timezone.utc).isoformat()
            if isinstance(record.created_at, datetime) and record.created_at.tzinfo
            else record.created_at.isoformat()
            if isinstance(record.created_at, datetime)
            else None
        ),
    }


def create_citizen_report(
    db: Session,
    payload: CitizenReportCreate,
    translation_service: TranslationService,
    *,
    commit: bool = True,
) -> tuple[CitizenReport, dict[str, object]]:
    report_type = payload.report_type.strip().casefold()
    sanitized_description = sanitize_report_description(payload.description)
    translation = normalize_report_description(
        description=sanitized_description,
        language=payload.language,
        translation_service=translation_service,
    )
    event_match = match_nearest_event(
        db,
        latitude=payload.latitude,
        longitude=payload.longitude,
        event_id=payload.event_id,
    )
    duplicate_count = count_nearby_duplicate_reports(
        db,
        latitude=payload.latitude,
        longitude=payload.longitude,
        report_type=report_type,
    )
    report_confidence, confidence_breakdown = calculate_report_confidence(
        report_source=payload.report_source,
        location_match_confidence=event_match.location_match_confidence,
        nearby_duplicate_count=duplicate_count,
        severity=payload.severity,
        translated_description=translation["translated_description"],
    )
    impact_score_change = estimate_impact_score_change(
        report_confidence=report_confidence,
        location_match_confidence=event_match.location_match_confidence,
        nearby_duplicate_count=duplicate_count,
        severity=payload.severity,
    )
    alert_level = derive_alert_level(
        report_confidence=report_confidence,
        severity=payload.severity,
        location_match_confidence=event_match.location_match_confidence,
    )
    recommended_action = build_recommended_action(
        report_source=payload.report_source,
        matched_event=event_match.event,
        alert_level=alert_level,
        report_confidence=report_confidence,
    )
    matched_event_id = event_match.event.id if event_match.event is not None else None

    record = CitizenReport(
        report_source=payload.report_source,
        report_type=report_type,
        latitude=payload.latitude,
        longitude=payload.longitude,
        severity=payload.severity.strip() if payload.severity else None,
        description=sanitized_description,
        language=payload.language or "en",
        source_language=translation["source_language"],
        translated_description=translation["translated_description"],
        translation_provider=translation["translation_provider"],
        translation_status=translation["translation_status"],
        translation_character_count=translation["translation_character_count"],
        event_id=matched_event_id,
        matched_event_id=matched_event_id,
        location_match_confidence=event_match.location_match_confidence,
        report_confidence=report_confidence,
        impact_score_change=impact_score_change,
        new_alert_level=alert_level,
        recommended_action=recommended_action,
        status="accepted",
    )
    db.add(record)
    if commit:
        db.commit()
        db.refresh(record)
    else:
        db.flush()

    metadata: dict[str, Any] = {
        "match_method": event_match.match_method,
        "distance_km": event_match.distance_km,
        "nearby_duplicate_count": duplicate_count,
        "confidence_breakdown": confidence_breakdown,
        "dataset_honesty": (
            "Citizen and field reports are confidence-scored signals, not automatic official events."
        ),
    }
    return record, metadata

