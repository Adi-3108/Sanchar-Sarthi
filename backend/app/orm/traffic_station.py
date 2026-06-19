from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.orm.incident import Incident


class TrafficStation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "traffic_stations"
    __table_args__ = (
        Index("idx_traffic_stations_code", "station_code"),
        Index("idx_traffic_stations_locality", "locality"),
    )

    station_code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    locality: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    contact_number: Mapped[str | None] = mapped_column(String(64))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    incidents: Mapped[list[Incident]] = relationship(back_populates="assigned_station")
