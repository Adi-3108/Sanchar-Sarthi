from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, Index, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampMixin, Base

if TYPE_CHECKING:
    from app.orm.citizen_report import CitizenReport
    from app.orm.event_dna import EventDna
    from app.orm.event_feature import EventFeature
    from app.orm.event_prediction import EventPrediction
    from app.orm.event_recommendation import EventRecommendation
    from app.orm.live_event_update import LiveEventUpdate
    from app.orm.officer_event_assignment import OfficerEventAssignment
    from app.orm.post_event_report import PostEventReport


class Event(TimestampMixin, Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('planned', 'unplanned')",
            name="ck_events_event_type",
        ),
        Index("idx_events_event_cause_clean", "event_cause_clean"),
        Index("idx_events_priority", "priority"),
        Index("idx_events_status", "status"),
        Index("idx_events_requires_road_closure", "requires_road_closure"),
        Index("idx_events_start_datetime", "start_datetime"),
        Index("idx_events_corridor", "corridor"),
        Index("idx_events_police_station", "police_station"),
        Index("idx_events_zone", "zone"),
        Index("idx_events_junction", "junction"),
        Index("idx_events_lat_lng", "latitude", "longitude"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_type: Mapped[str | None] = mapped_column(String(32))
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    endlatitude: Mapped[float | None] = mapped_column(Float)
    endlongitude: Mapped[float | None] = mapped_column(Float)
    address: Mapped[str | None] = mapped_column(Text)
    end_address: Mapped[str | None] = mapped_column(Text)
    event_cause: Mapped[str | None] = mapped_column(String(128))
    event_cause_clean: Mapped[str | None] = mapped_column(String(128))
    requires_road_closure: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str | None] = mapped_column(String(64))
    authenticated: Mapped[bool | None] = mapped_column(Boolean)
    modified_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    direction: Mapped[str | None] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text)
    description_language: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    description_for_features: Mapped[str | None] = mapped_column(Text)
    description_normalization_method: Mapped[str | None] = mapped_column(String(128))
    veh_type: Mapped[str | None] = mapped_column(String(64))
    veh_no_hash: Mapped[str | None] = mapped_column(String(255))
    veh_no_masked: Mapped[str | None] = mapped_column(String(255))
    corridor: Mapped[str | None] = mapped_column(String(255))
    priority: Mapped[str | None] = mapped_column(String(64))
    cargo_material: Mapped[str | None] = mapped_column(String(255))
    reason_breakdown: Mapped[str | None] = mapped_column(Text)
    reason_breakdown_clean: Mapped[str | None] = mapped_column(String(255))
    age_of_truck: Mapped[float | None] = mapped_column(Numeric(8, 2))
    created_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    route_path: Mapped[str | None] = mapped_column(Text)
    police_station: Mapped[str | None] = mapped_column(String(255))
    resolved_at_address: Mapped[str | None] = mapped_column(Text)
    resolved_at_latitude: Mapped[float | None] = mapped_column(Float)
    resolved_at_longitude: Mapped[float | None] = mapped_column(Float)
    closed_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    zone: Mapped[str | None] = mapped_column(String(255))
    junction: Mapped[str | None] = mapped_column(String(255))
    raw_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)

    features: Mapped[list[EventFeature]] = relationship(back_populates="event")
    dna_records: Mapped[list[EventDna]] = relationship(back_populates="event")
    predictions: Mapped[list[EventPrediction]] = relationship(back_populates="event")
    recommendations: Mapped[list[EventRecommendation]] = relationship(back_populates="event")
    citizen_reports: Mapped[list[CitizenReport]] = relationship(back_populates="event")
    live_updates: Mapped[list[LiveEventUpdate]] = relationship(back_populates="event")
    post_event_reports: Mapped[list[PostEventReport]] = relationship(back_populates="event")
    assignments: Mapped[list[OfficerEventAssignment]] = relationship(back_populates="event")
