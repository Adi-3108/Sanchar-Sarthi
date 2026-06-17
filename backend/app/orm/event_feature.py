from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import CreatedAtMixin, UUIDPrimaryKeyMixin, Base

if TYPE_CHECKING:
    from app.orm.event import Event


class EventFeature(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "event_features"
    __table_args__ = (
        CheckConstraint(
            "duration_source IN ('end_datetime', 'closed_datetime', 'resolved_datetime', 'unavailable')",
            name="ck_event_features_duration_source",
        ),
        UniqueConstraint("event_id", name="uq_event_features_event_id"),
        Index("idx_event_features_event_id", "event_id"),
        Index("idx_event_features_location_cluster_id", "location_cluster_id"),
    )

    event_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_hour: Mapped[int | None] = mapped_column()
    event_day: Mapped[int | None] = mapped_column()
    event_month: Mapped[int | None] = mapped_column()
    event_weekday: Mapped[int | None] = mapped_column()
    is_weekend: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_peak_hour: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_night_event: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    event_duration_minutes: Mapped[float | None] = mapped_column(Numeric(10, 2))
    closure_duration_minutes: Mapped[float | None] = mapped_column(Numeric(10, 2))
    resolution_duration_minutes: Mapped[float | None] = mapped_column(Numeric(10, 2))
    duration_source: Mapped[str | None] = mapped_column(String(32))
    has_zone: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_junction: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_route_path: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_vehicle_type: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    location_cluster_id: Mapped[str | None] = mapped_column(String(128))
    historical_corridor_risk: Mapped[float | None] = mapped_column(Numeric(6, 4))
    historical_police_station_risk: Mapped[float | None] = mapped_column(Numeric(6, 4))
    historical_cluster_risk: Mapped[float | None] = mapped_column(Numeric(6, 4))
    historical_cause_closure_rate: Mapped[float | None] = mapped_column(Numeric(6, 4))
    historical_corridor_closure_rate: Mapped[float | None] = mapped_column(Numeric(6, 4))
    historical_police_station_closure_rate: Mapped[float | None] = mapped_column(Numeric(6, 4))
    historical_cluster_closure_rate: Mapped[float | None] = mapped_column(Numeric(6, 4))

    event: Mapped[Event] = relationship(back_populates="features")
