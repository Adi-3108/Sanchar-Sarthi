from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.database import get_database_status


class ModelHealth(BaseModel):
    priority: str
    road_closure: str
    resolution_time: str


class AuthHealth(BaseModel):
    firebase: Literal["configured", "not_configured"]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    environment: str
    checked_at: datetime
    database: str
    database_detail: str | None = None
    models: ModelHealth
    auth: AuthHealth


router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    database_status, database_detail = get_database_status()
    firebase_status = (
        "configured"
        if settings.firebase_project_id
        and settings.firebase_client_email
        and settings.firebase_private_key
        else "not_configured"
    )
    return HealthResponse(
        status="ok",
        service="eventflow-ai-backend",
        environment=settings.environment,
        checked_at=datetime.now(timezone.utc),
        database=database_status,
        database_detail=database_detail,
        models=ModelHealth(
            priority="not_loaded",
            road_closure="not_loaded",
            resolution_time="not_loaded",
        ),
        auth=AuthHealth(firebase=firebase_status),
    )
