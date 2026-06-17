from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import CreatedAtMixin, UUIDPrimaryKeyMixin, Base

if TYPE_CHECKING:
    from app.orm.event import Event


class EventDna(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "event_dna"
    __table_args__ = (Index("idx_event_dna_event_id", "event_id"),)

    event_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    dna_summary: Mapped[str] = mapped_column(Text, nullable=False)
    time_context: Mapped[str] = mapped_column(Text, nullable=False)
    location_context: Mapped[str] = mapped_column(Text, nullable=False)
    cause_context: Mapped[str] = mapped_column(Text, nullable=False)
    weather_context: Mapped[str | None] = mapped_column(Text)
    multi_event_context: Mapped[str | None] = mapped_column(Text)
    historical_pattern: Mapped[str] = mapped_column(Text, nullable=False)
    risk_indicators_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    similar_event_ids_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    event: Mapped[Event] = relationship(back_populates="dna_records")
