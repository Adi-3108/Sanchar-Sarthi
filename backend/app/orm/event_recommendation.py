from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import CreatedAtMixin, UUIDPrimaryKeyMixin, Base

if TYPE_CHECKING:
    from app.orm.event import Event


class EventRecommendation(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "event_recommendations"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_event_recommendations_event_id"),
        Index("idx_event_recommendations_event_id", "event_id"),
    )

    event_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    risk_summary_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    weather_risk_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    recommended_total_officers: Mapped[int | None] = mapped_column()
    deployment_plan_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    barricade_plan_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    diversion_plan_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    emergency_corridor_json: Mapped[dict[str, object] | None] = mapped_column(JSON)
    logistics_impact_json: Mapped[dict[str, object] | None] = mapped_column(JSON)
    action_confidence_ledger_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False, default=list)
    recommended_action_summary: Mapped[str] = mapped_column(Text, nullable=False)

    event: Mapped[Event] = relationship(back_populates="recommendations")
