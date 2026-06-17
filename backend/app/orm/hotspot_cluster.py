from __future__ import annotations

from sqlalchemy import Index, JSON, Float, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import CreatedAtMixin, UUIDPrimaryKeyMixin, Base


class HotspotCluster(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "hotspot_clusters"
    __table_args__ = (
        Index("idx_hotspot_clusters_location_cluster_id", "location_cluster_id"),
        Index("idx_hotspot_clusters_centroid", "centroid_latitude", "centroid_longitude"),
        Index("idx_hotspot_clusters_risk_score", "cluster_risk_score"),
    )

    location_cluster_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    centroid_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    centroid_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    cluster_event_count: Mapped[int] = mapped_column(nullable=False)
    cluster_high_priority_rate: Mapped[float | None] = mapped_column(Numeric(6, 4))
    cluster_road_closure_rate: Mapped[float | None] = mapped_column(Numeric(6, 4))
    cluster_peak_hour_rate: Mapped[float | None] = mapped_column(Numeric(6, 4))
    cluster_top_event_cause: Mapped[str | None] = mapped_column(String(128))
    cluster_risk_score: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    cluster_profile_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
