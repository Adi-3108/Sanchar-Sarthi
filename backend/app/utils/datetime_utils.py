from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone


def normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def duration_minutes(start: datetime | None, end: datetime | None) -> float | None:
    normalized_start = normalize_datetime(start)
    normalized_end = normalize_datetime(end)
    if normalized_start is None or normalized_end is None:
        return None

    delta_seconds = (normalized_end - normalized_start).total_seconds()
    if delta_seconds < 0:
        return None

    return round(delta_seconds / 60, 2)


def first_valid_timestamp(
    start: datetime | None,
    candidates: Iterable[tuple[str, datetime | None]],
) -> tuple[datetime | None, str]:
    for label, candidate in candidates:
        if candidate is None:
            continue
        if duration_minutes(start, candidate) is not None:
            return normalize_datetime(candidate), label
    return None, "unavailable"
