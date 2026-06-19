from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.orm.incident_prediction import IncidentPrediction
    from app.orm.incident_vote import IncidentVote
    from app.orm.traffic_station import TrafficStation


INCIDENT_STATUSES = (
    "reported",
    "pending_verification",
    "active",
    "escalated",
    "resolved",
    "rejected",
    "archived",
)

INCIDENT_SOURCES = ("user", "control_room", "admin", "system_seed")
INCIDENT_SEVERITIES = ("low", "medium", "high", "critical")

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "reported": {"pending_verification", "active", "rejected", "archived"},
    "pending_verification": {"active", "rejected", "archived"},
    "active": {"escalated", "resolved", "rejected", "archived"},
    "escalated": {"resolved", "active", "archived"},
    "resolved": {"archived", "active"},
    "rejected": {"archived", "pending_verification"},
    "archived": set(),
}


def can_transition_incident(current_status: str, next_status: str) -> bool:
    return next_status in ALLOWED_TRANSITIONS.get(current_status, set())


class Incident(TimestampMixin, Base):
    __tablename__ = "incidents"
    __table_args__ = (
        CheckConstraint(
            "status IN ('reported', 'pending_verification', 'active', 'escalated', 'resolved', 'rejected', 'archived')",
            name="ck_incidents_status",
        ),
        CheckConstraint(
            "source_type IN ('user', 'control_room', 'admin', 'system_seed')",
            name="ck_incidents_source_type",
        ),
        CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name="ck_incidents_severity",
        ),
        Index("idx_incidents_status", "status"),
        Index("idx_incidents_source_type", "source_type"),
        Index("idx_incidents_location", "latitude", "longitude"),
        Index("idx_incidents_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"INC-{uuid4().hex[:10].upper()}")
    incident_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending_verification")
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="medium")
    location_name: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    locality: Mapped[str | None] = mapped_column(String(255))
    ward: Mapped[str | None] = mapped_column(String(128))
    created_by_user_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("user_accounts.id", ondelete="SET NULL"))
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="user")
    true_vote_count: Mapped[int] = mapped_column(nullable=False, default=0)
    false_vote_count: Mapped[int] = mapped_column(nullable=False, default=0)
    confidence_score: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False, default=0)
    assigned_station_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("traffic_stations.id", ondelete="SET NULL"))
    assigned_station_name: Mapped[str | None] = mapped_column(String(255))
    police_force_required: Mapped[int | None] = mapped_column()
    barricades_required: Mapped[int | None] = mapped_column()
    route_impact_summary: Mapped[str | None] = mapped_column(Text)
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    visible_to_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    station_alerted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    assigned_station: Mapped[TrafficStation | None] = relationship(back_populates="incidents")
    votes: Mapped[list[IncidentVote]] = relationship(back_populates="incident", cascade="all, delete-orphan")
    predictions: Mapped[list[IncidentPrediction]] = relationship(back_populates="incident", cascade="all, delete-orphan")
