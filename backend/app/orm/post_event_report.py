from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import CreatedAtMixin, UUIDPrimaryKeyMixin, Base

if TYPE_CHECKING:
    from app.orm.event import Event


class PostEventReport(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "post_event_reports"
    __table_args__ = (Index("idx_post_event_reports_event", "event_id"),)

    event_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    predicted_impact_score: Mapped[float | None] = mapped_column(Numeric(8, 2))
    simulated_actual_impact_score: Mapped[float | None] = mapped_column(Numeric(8, 2))
    impact_deviation: Mapped[float | None] = mapped_column(Numeric(8, 2))
    final_status: Mapped[str | None] = mapped_column(String(64))
    event_summary: Mapped[str] = mapped_column(Text, nullable=False)
    prediction_summary: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation_summary: Mapped[str] = mapped_column(Text, nullable=False)
    citizen_report_summary: Mapped[str | None] = mapped_column(Text)
    live_escalation_summary: Mapped[str | None] = mapped_column(Text)
    lessons_learned: Mapped[str] = mapped_column(Text, nullable=False)
    future_recommendations: Mapped[str] = mapped_column(Text, nullable=False)
    report_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    event: Mapped[Event] = relationship(back_populates="post_event_reports")
