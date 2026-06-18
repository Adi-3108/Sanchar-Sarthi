from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import AuthContext, require_role
from app.db.session import get_db
from app.orm.system_audit_log import SystemAuditLog
from app.services.demo_scenario_service import (
    build_demo_status,
    seed_demo_scenarios,
    serialize_demo_seed_report,
)

router = APIRouter(prefix="/api/demo", tags=["demo"])


class DemoSummaryResponse(BaseModel):
    demo_scenarios: int
    demo_events: int
    demo_users: int
    demo_officers: int
    officer_assignments: int
    demo_features: int
    demo_dna_records: int
    demo_predictions: int
    demo_recommendations: int
    demo_hotspot_clusters: int
    demo_reports: int
    demo_live_updates: int
    demo_post_event_reports: int


class DemoCheckResponse(BaseModel):
    key: str
    label: str
    ready: bool
    detail: str


class DemoScenarioCardResponse(BaseModel):
    scenario_name: str
    scenario_type: str
    description: str
    route: str
    primary_event_id: str | None = None
    event_ids: list[str] = Field(default_factory=list)
    walkthrough_steps: list[str] = Field(default_factory=list)
    expected_highlights: list[str] = Field(default_factory=list)


class DemoStatusResponse(BaseModel):
    status: str
    generated_at: str
    summary: DemoSummaryResponse
    checks: list[DemoCheckResponse] = Field(default_factory=list)
    scenario_cards: list[DemoScenarioCardResponse] = Field(default_factory=list)
    demo_event_ids: list[str] = Field(default_factory=list)
    sample_event_ids: dict[str, object] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


class DemoSeedResponse(BaseModel):
    status: str
    message: str
    generated_at: str
    summary: DemoSummaryResponse
    scenario_names: list[str] = Field(default_factory=list)
    demo_event_ids: list[str] = Field(default_factory=list)


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


def require_demo_seed_access(
    auth: AuthContext = Depends(require_role("admin", "control_room")),
) -> AuthContext:
    return auth


def _coerce_uuid(value: str | None) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(value)
    except (TypeError, ValueError):
        return None


@router.get("/status", response_model=DemoStatusResponse)
def get_demo_status(db: Session = Depends(get_db)):
    try:
        return DemoStatusResponse.model_validate(build_demo_status(db))
    except SQLAlchemyError:
        db.rollback()
        return error_response(
            503,
            "DATABASE_UNAVAILABLE",
            "Database is unavailable for demo readiness status.",
        )


@router.post("/seed", response_model=DemoSeedResponse)
def seed_demo(
    auth: AuthContext = Depends(require_demo_seed_access),
    db: Session = Depends(get_db),
):
    try:
        report = seed_demo_scenarios(db, commit=False)
        payload = serialize_demo_seed_report(report)
        db.add(
            SystemAuditLog(
                actor_user_id=_coerce_uuid(auth.user_account_id),
                actor_role=auth.role,
                action="demo_seed",
                resource_type="demo_scenarios",
                resource_id="phase17",
                metadata_json={
                    "demo_events": payload["summary"]["demo_events"],
                    "demo_scenarios": payload["summary"]["demo_scenarios"],
                    "demo_reports": payload["summary"]["demo_reports"],
                    "demo_live_updates": payload["summary"]["demo_live_updates"],
                    "demo_post_event_reports": payload["summary"]["demo_post_event_reports"],
                },
            )
        )
        db.commit()
        return DemoSeedResponse.model_validate(payload)
    except SQLAlchemyError:
        db.rollback()
        return error_response(
            503,
            "DATABASE_UNAVAILABLE",
            "Database is unavailable for demo seeding.",
        )
