from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import CreatedAtMixin, UUIDPrimaryKeyMixin, Base

if TYPE_CHECKING:
    from app.orm.event import Event


class LiveEventUpdate(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "live_event_updates"
    __table_args__ = (
        Index("idx_live_event_updates_event_created", "event_id", "created_at"),
        Index("idx_live_event_updates_alert_level", "alert_level"),
    )

    event_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    update_source: Mapped[str] = mapped_column(String(32), nullable=False)
    current_congestion_level: Mapped[str] = mapped_column(String(32), nullable=False)
    field_update: Mapped[str | None] = mapped_column(Text)
    road_closure_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    officer_shortage: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    crowd_increase: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rain_waterlogging: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    new_nearby_incident: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expected_impact_score: Mapped[float | None] = mapped_column(Numeric(8, 2))
    current_impact_score: Mapped[float | None] = mapped_column(Numeric(8, 2))
    impact_deviation: Mapped[float | None] = mapped_column(Numeric(8, 2))
    alert_level: Mapped[str | None] = mapped_column(String(32))
    adaptive_action: Mapped[str | None] = mapped_column(Text)

    event: Mapped[Event] = relationship(back_populates="live_updates")
