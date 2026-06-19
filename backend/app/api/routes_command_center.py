"""Command Center summary endpoint.

Provides real-time operational statistics for the command center dashboard
instead of relying on the generic /api/health endpoint.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.orm.citizen_report import CitizenReport
from app.orm.event import Event
from app.orm.event_recommendation import EventRecommendation
from app.orm.hotspot_cluster import HotspotCluster
from app.orm.incident import Incident

router = APIRouter(prefix="/api/command-center", tags=["command-center"])


class CommandSummary(BaseModel):
    activeEvents: int
    criticalEvents: int
    hotspotCount: int
    latestRecommendationCount: int
    pendingReports: int
    resolvedToday: int
    totalEvents: int
    totalIncidents: int
    activeIncidents: int


@router.get("/summary", response_model=CommandSummary)
def command_center_summary(db: Session = Depends(get_db)):
    """Public operational overview for the command center dashboard.

    Returns aggregate counts from the event, hotspot, recommendation,
    citizen report, and incident tables so the frontend can display
    real statistics instead of a generic health check.
    """
    # --- Event-based stats (ASTraM dataset events) ---
    total_events = db.scalar(select(func.count()).select_from(Event)) or 0

    # Active events = events whose status is open/active/ongoing
    active_events = db.scalar(
        select(func.count()).select_from(Event).where(
            Event.status.in_(["open", "active", "ongoing", "simulated"])
        )
    ) or 0

    # Critical events = high-priority events
    critical_events = db.scalar(
        select(func.count()).select_from(Event).where(
            Event.priority.in_(["High", "high", "Critical", "critical"])
        )
    ) or 0

    # Hotspot clusters
    hotspot_count = db.scalar(
        select(func.count()).select_from(HotspotCluster)
    ) or 0

    # Recommendation plans generated
    latest_recommendation_count = db.scalar(
        select(func.count()).select_from(EventRecommendation)
    ) or 0

    # Pending citizen reports (status = 'accepted' but not yet verified)
    pending_reports = db.scalar(
        select(func.count()).select_from(CitizenReport).where(
            CitizenReport.status.in_(["accepted", "pending"])
        )
    ) or 0

    # --- Incident-based stats (foundation incidents) ---
    total_incidents = db.scalar(
        select(func.count()).select_from(Incident)
    ) or 0

    active_incidents = db.scalar(
        select(func.count()).select_from(Incident).where(
            Incident.status.in_(["active", "escalated", "pending_verification"])
        )
    ) or 0

    # Resolved today (incidents resolved in the last 24 hours)
    twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
    resolved_today = db.scalar(
        select(func.count()).select_from(Incident).where(
            Incident.status == "resolved",
            Incident.updated_at >= twenty_four_hours_ago,
        )
    ) or 0

    return CommandSummary(
        activeEvents=active_events,
        criticalEvents=critical_events,
        hotspotCount=hotspot_count,
        latestRecommendationCount=latest_recommendation_count,
        pendingReports=pending_reports,
        resolvedToday=resolved_today,
        totalEvents=total_events,
        totalIncidents=total_incidents,
        activeIncidents=active_incidents,
    )
