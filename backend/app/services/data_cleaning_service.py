from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any, Iterable, TextIO

from sqlalchemy.orm import Session

from app.orm.event import Event
from app.services.text_normalization_service import normalize_description
from app.utils.masking_utils import is_empty, mask_vehicle_number, strip_sensitive_fields

REQUIRED_COLUMNS = {"id", "event_type", "latitude", "longitude", "event_cause", "start_datetime"}
ALLOWED_EVENT_TYPES = {"planned", "unplanned"}
TRUE_VALUES = {"TRUE", "YES", "Y", "1"}
FALSE_VALUES = {"FALSE", "NO", "N", "0"}


@dataclass(frozen=True)
class IngestionReport:
    rows_processed: int
    rows_upserted: int
    invalid_rows: int
    columns_detected: int
    sample_errors: list[str]


def clean_event_cause(value: Any) -> str:
    if is_empty(value):
        return "unknown"
    normalized = str(value).strip().lower()
    for token in (" ", "-", "/", ","):
        normalized = normalized.replace(token, "_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_") or "unknown"


def _clean_string(value: Any) -> str | None:
    if is_empty(value):
        return None
    return str(value).strip()


def parse_datetime(value: Any) -> datetime | None:
    text = _clean_string(value)
    if text is None:
        return None
    normalized = text.replace("Z", "+00:00")
    if " " in normalized and "T" not in normalized:
        date_part, time_part = normalized.split(" ", 1)
        if "-" in date_part and ":" in time_part:
            normalized = f"{date_part}T{time_part}"
    if normalized.endswith("+00"):
        normalized = f"{normalized}:00"
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"invalid datetime value: {text}") from exc


def _parse_float(value: Any, *, field_name: str) -> float:
    text = _clean_string(value)
    if text is None:
        raise ValueError(f"missing required numeric field: {field_name}")
    try:
        return float(text)
    except ValueError as exc:
        raise ValueError(f"invalid numeric field {field_name}: {text}") from exc


def _validate_coordinate(number: float, *, field_name: str, minimum: float, maximum: float) -> float:
    if not minimum <= number <= maximum:
        raise ValueError(f"{field_name} out of range: {number}")
    return number


def parse_optional_coordinate(value: Any) -> float | None:
    if is_empty(value):
        return None
    number = float(str(value).strip())
    return None if number == 0 else number


def parse_required_coordinate(value: Any, *, field_name: str) -> float:
    number = _parse_float(value, field_name=field_name)
    if field_name == "latitude":
        return _validate_coordinate(number, field_name=field_name, minimum=-90, maximum=90)
    return _validate_coordinate(number, field_name=field_name, minimum=-180, maximum=180)


def parse_optional_boolean(value: Any) -> bool | None:
    if is_empty(value):
        return None
    normalized = str(value).strip().upper()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    raise ValueError(f"invalid boolean value: {value}")


def parse_required_boolean(value: Any) -> bool:
    parsed = parse_optional_boolean(value)
    return bool(parsed)


def parse_event_type(value: Any) -> str:
    normalized = (str(value).strip().lower() if not is_empty(value) else "unplanned")
    return normalized if normalized in ALLOWED_EVENT_TYPES else "unplanned"


def clean_astram_row(row: dict[str, Any], *, mask_salt: str = "eventflow-demo") -> dict[str, Any]:
    event_id = _clean_string(row.get("id"))
    if not event_id:
        raise ValueError("missing required field: id")

    start_datetime = parse_datetime(row.get("start_datetime"))
    if start_datetime is None:
        raise ValueError("missing required datetime field: start_datetime")

    description = normalize_description(row.get("description"))
    vehicle_hash = mask_vehicle_number(row.get("veh_no"), salt=mask_salt)
    payload = strip_sensitive_fields(row)

    return {
        "id": event_id,
        "event_type": parse_event_type(row.get("event_type")),
        "latitude": parse_required_coordinate(row.get("latitude"), field_name="latitude"),
        "longitude": parse_required_coordinate(row.get("longitude"), field_name="longitude"),
        "endlatitude": parse_optional_coordinate(row.get("endlatitude")),
        "endlongitude": parse_optional_coordinate(row.get("endlongitude")),
        "address": _clean_string(row.get("address")),
        "end_address": _clean_string(row.get("end_address")),
        "event_cause": _clean_string(row.get("event_cause")),
        "event_cause_clean": clean_event_cause(row.get("event_cause")),
        "requires_road_closure": parse_required_boolean(row.get("requires_road_closure")),
        "start_datetime": start_datetime,
        "end_datetime": parse_datetime(row.get("end_datetime")),
        "status": _clean_string(row.get("status").lower() if isinstance(row.get("status"), str) else row.get("status")),
        "authenticated": parse_optional_boolean(row.get("authenticated")),
        "modified_datetime": parse_datetime(row.get("modified_datetime")),
        "direction": _clean_string(row.get("direction")),
        "description": description.raw,
        "description_language": description.language,
        "description_for_features": description.text_for_features,
        "description_normalization_method": description.method,
        "veh_type": _clean_string(row.get("veh_type")),
        "veh_no_hash": vehicle_hash,
        "veh_no_masked": vehicle_hash,
        "corridor": _clean_string(row.get("corridor")),
        "priority": _clean_string(row.get("priority")),
        "cargo_material": _clean_string(row.get("cargo_material")),
        "reason_breakdown": _clean_string(row.get("reason_breakdown")),
        "reason_breakdown_clean": clean_event_cause(row.get("reason_breakdown")),
        "age_of_truck": _parse_float(row.get("age_of_truck"), field_name="age_of_truck") if not is_empty(row.get("age_of_truck")) else None,
        "created_date": parse_datetime(row.get("created_date")),
        "route_path": _clean_string(row.get("route_path")),
        "police_station": _clean_string(row.get("police_station")),
        "resolved_at_address": _clean_string(row.get("resolved_at_address")),
        "resolved_at_latitude": parse_optional_coordinate(row.get("resolved_at_latitude")),
        "resolved_at_longitude": parse_optional_coordinate(row.get("resolved_at_longitude")),
        "closed_datetime": parse_datetime(row.get("closed_datetime")),
        "resolved_datetime": parse_datetime(row.get("resolved_datetime")),
        "zone": _clean_string(row.get("zone")),
        "junction": _clean_string(row.get("junction")),
        "raw_payload": payload,
    }


def _validate_required_columns(fieldnames: Iterable[str] | None) -> list[str]:
    normalized = {field.strip() for field in fieldnames or []}
    return sorted(REQUIRED_COLUMNS - normalized)


def _ingest_reader(db: Session, reader: csv.DictReader[str], *, mask_salt: str = "eventflow-demo") -> IngestionReport:
    missing_columns = _validate_required_columns(reader.fieldnames)
    if missing_columns:
        raise ValueError(f"Missing ASTraM columns: {missing_columns}")

    rows_processed = 0
    rows_upserted = 0
    invalid_rows = 0
    sample_errors: list[str] = []

    for rows_processed, row in enumerate(reader, start=1):
        try:
            cleaned = clean_astram_row(row, mask_salt=mask_salt)
            db.merge(Event(**cleaned))
            rows_upserted += 1
        except ValueError as exc:
            invalid_rows += 1
            if len(sample_errors) < 5:
                sample_errors.append(f"row {rows_processed}: {exc}")

    db.commit()
    return IngestionReport(
        rows_processed=rows_processed,
        rows_upserted=rows_upserted,
        invalid_rows=invalid_rows,
        columns_detected=len(reader.fieldnames or []),
        sample_errors=sample_errors,
    )


def ingest_astram_csv_text(db: Session, csv_text: str, *, mask_salt: str = "eventflow-demo") -> IngestionReport:
    reader = csv.DictReader(StringIO(csv_text))
    return _ingest_reader(db, reader, mask_salt=mask_salt)


def ingest_astram_csv_bytes(db: Session, content: bytes, *, mask_salt: str = "eventflow-demo") -> IngestionReport:
    return ingest_astram_csv_text(db, content.decode("utf-8-sig"), mask_salt=mask_salt)


def ingest_astram_csv_file(db: Session, csv_path: str | Path, *, mask_salt: str = "eventflow-demo") -> IngestionReport:
    path = Path(csv_path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return _ingest_reader(db, reader, mask_salt=mask_salt)
