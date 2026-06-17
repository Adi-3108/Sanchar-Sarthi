from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CitizenReportCreate(BaseModel):
    report_source: Literal["citizen", "field_officer", "control_room", "demo"] = "citizen"
    report_type: str = Field(min_length=2, max_length=80)
    latitude: float = Field(ge=12.0, le=14.0)
    longitude: float = Field(ge=76.0, le=78.5)
    severity: str | None = Field(default=None, max_length=32)
    description: str = Field(min_length=10, max_length=500)
    language: str = Field(default="auto", min_length=2, max_length=16)
    event_id: str | None = Field(default=None, max_length=64)

    @field_validator("report_type", "description", "language", mode="before")
    @classmethod
    def _strip_required_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return str(value).strip()

    @field_validator("severity", "event_id", mode="before")
    @classmethod
    def _strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class CitizenReportResponse(BaseModel):
    status: str
    matched_event_id: str | None = None
    source_language: str | None = None
    translation_status: str
    translated_description: str | None = None
    location_match_confidence: float | None = None
    report_confidence: float
    impact_score_change: float
    new_alert_level: str
    recommended_action: str
