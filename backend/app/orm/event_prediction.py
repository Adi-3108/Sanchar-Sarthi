from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, JSON, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import CreatedAtMixin, UUIDPrimaryKeyMixin, Base

if TYPE_CHECKING:
    from app.orm.event import Event
    from app.orm.model_run import ModelRun


class EventPrediction(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "event_predictions"
    __table_args__ = (
        Index("idx_predictions_event", "event_id"),
        Index("idx_event_predictions_predicted_road_closure", "predicted_road_closure"),
        Index("idx_event_predictions_impact_category", "impact_category"),
    )

    event_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    model_run_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("model_runs.id", ondelete="SET NULL"),
    )
    predicted_priority: Mapped[str | None] = mapped_column(String(64))
    priority_confidence: Mapped[float | None] = mapped_column(Numeric(6, 4))
    road_closure_probability: Mapped[float | None] = mapped_column(Numeric(6, 4))
    predicted_road_closure: Mapped[bool | None] = mapped_column(Boolean)
    estimated_clearance_minutes: Mapped[float | None] = mapped_column(Numeric(8, 2))
    clearance_prediction_method: Mapped[str | None] = mapped_column(String(64))
    clearance_confidence: Mapped[float | None] = mapped_column(Numeric(6, 4))
    clearance_confidence_note: Mapped[str | None] = mapped_column(Text)
    historical_clearance_range_min: Mapped[float | None] = mapped_column(Numeric(8, 2))
    historical_clearance_range_max: Mapped[float | None] = mapped_column(Numeric(8, 2))
    estimated_impact_score: Mapped[float | None] = mapped_column(Numeric(8, 2))
    impact_category: Mapped[str | None] = mapped_column(String(64))
    impact_radius_km: Mapped[float | None] = mapped_column(Numeric(8, 2))
    vehicle_impact_factor: Mapped[float | None] = mapped_column(Numeric(5, 2))
    vehicle_impact_note: Mapped[str | None] = mapped_column(Text)
    baseline_risk_score: Mapped[float | None] = mapped_column(Numeric(8, 2))
    additional_event_delta: Mapped[float | None] = mapped_column(Numeric(8, 2))
    weather_adjustment_json: Mapped[dict[str, object] | None] = mapped_column(JSON)
    multi_event_conflict_json: Mapped[dict[str, object] | None] = mapped_column(JSON)
    prediction_explanation_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    model_version: Mapped[str | None] = mapped_column(String(128))

    event: Mapped[Event] = relationship(back_populates="predictions")
    model_run: Mapped[ModelRun | None] = relationship(back_populates="predictions")
