from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Numeric, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import CreatedAtMixin, UUIDPrimaryKeyMixin, Base

if TYPE_CHECKING:
    from app.orm.event import Event


class CitizenReport(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "citizen_reports"
    __table_args__ = (
        Index("idx_citizen_reports_report_source", "report_source"),
        Index("idx_citizen_reports_report_type", "report_type"),
        Index("idx_citizen_reports_severity", "severity"),
        Index("idx_citizen_reports_event_created", "event_id", "created_at"),
        Index("idx_citizen_reports_lat_lng", "latitude", "longitude"),
    )

    report_source: Mapped[str] = mapped_column(String(32), nullable=False)
    report_type: Mapped[str] = mapped_column(String(80), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str | None] = mapped_column(String(32))
    description: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    source_language: Mapped[str | None] = mapped_column(String(16))
    translated_description: Mapped[str | None] = mapped_column(Text)
    translation_provider: Mapped[str] = mapped_column(String(32), nullable=False, default="disabled")
    translation_status: Mapped[str] = mapped_column(String(32), nullable=False, default="disabled")
    translation_character_count: Mapped[int | None] = mapped_column()
    event_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("events.id", ondelete="SET NULL"),
    )
    matched_event_id: Mapped[str | None] = mapped_column(String(64))
    location_match_confidence: Mapped[float | None] = mapped_column(Numeric(6, 4))
    report_confidence: Mapped[float | None] = mapped_column(Numeric(6, 4))
    impact_score_change: Mapped[float | None] = mapped_column(Numeric(8, 2))
    new_alert_level: Mapped[str | None] = mapped_column(String(32))
    recommended_action: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="accepted")

    event: Mapped[Event | None] = relationship(back_populates="citizen_reports")
