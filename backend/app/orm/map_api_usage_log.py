from __future__ import annotations

from sqlalchemy import Boolean, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import CreatedAtMixin, UUIDPrimaryKeyMixin, Base


class MapApiUsageLog(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "map_api_usage_logs"
    __table_args__ = (
        Index("idx_map_api_usage_provider_created", "provider", "created_at"),
        Index("idx_map_api_usage_api_name", "api_name"),
        Index("idx_map_api_usage_request_hash", "request_hash"),
    )

    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    api_name: Mapped[str] = mapped_column(String(64), nullable=False)
    cache_hit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    estimated_cost_inr: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    request_hash: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    fallback_reason: Mapped[str | None] = mapped_column(String(128))
