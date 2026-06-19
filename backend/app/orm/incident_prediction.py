from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class IncidentPrediction(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "incident_predictions"
    __table_args__ = (
        Index("idx_incident_predictions_incident", "incident_id"),
        Index("idx_incident_predictions_model", "model_name", "model_version"),
    )

    incident_id: Mapped[str] = mapped_column(String(64), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    predicted_severity: Mapped[str | None] = mapped_column(String(32))
    police_force_required: Mapped[int | None] = mapped_column()
    barricades_required: Mapped[int | None] = mapped_column()
    urgency_score: Mapped[float | None] = mapped_column(Numeric(6, 4))
    route_disruption_score: Mapped[float | None] = mapped_column(Numeric(6, 4))
    confidence_score: Mapped[float | None] = mapped_column(Numeric(6, 4))
    station_recommendation: Mapped[str | None] = mapped_column(String(255))
    hotspot_contribution_score: Mapped[float | None] = mapped_column(Numeric(6, 4))
    output_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    explanation_text: Mapped[str | None] = mapped_column(Text)

    incident: Mapped["Incident"] = relationship(back_populates="predictions")
