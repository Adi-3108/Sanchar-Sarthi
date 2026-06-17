from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Index, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import CreatedAtMixin, UUIDPrimaryKeyMixin, Base

if TYPE_CHECKING:
    from app.orm.event_prediction import EventPrediction


class ModelRun(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "model_runs"
    __table_args__ = (
        UniqueConstraint("model_name", "model_version", name="uq_model_runs_name_version"),
        Index("idx_model_runs_model_name", "model_name"),
        Index("idx_model_runs_created_at", "created_at"),
    )

    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[str] = mapped_column(String(128), nullable=False)
    target_variable: Mapped[str] = mapped_column(String(128), nullable=False)
    training_rows: Mapped[int] = mapped_column(nullable=False)
    test_rows: Mapped[int] = mapped_column(nullable=False)
    metrics_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    feature_list_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    artifact_path: Mapped[str | None] = mapped_column(String(512))

    predictions: Mapped[list[EventPrediction]] = relationship(back_populates="model_run")
