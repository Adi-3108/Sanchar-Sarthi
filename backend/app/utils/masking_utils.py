from __future__ import annotations

import hashlib
import math
from typing import Any

EMPTY_MARKERS = {"", "NULL", "NAN", "NONE", "<NA>"}
SENSITIVE_COLUMNS = {
    "veh_no",
    "client_id",
    "created_by_id",
    "last_modified_by_id",
    "assigned_to_police_id",
    "kgid",
    "closed_by_id",
    "resolved_by_id",
    "citizen_accident_id",
}


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return str(value).strip().upper() in EMPTY_MARKERS


def sanitize_payload_value(value: Any) -> Any:
    if is_empty(value):
        return None
    if isinstance(value, str):
        return value.strip()
    return value


def strip_sensitive_fields(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: sanitize_payload_value(value)
        for key, value in row.items()
        if key not in SENSITIVE_COLUMNS
    }


def mask_vehicle_number(value: Any, salt: str = "eventflow-demo") -> str | None:
    if is_empty(value):
        return None
    normalized = str(value).strip().upper()
    digest = hashlib.sha256(f"{salt}:{normalized}".encode("utf-8")).hexdigest()
    return digest[:16]
