from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampMixin, UUIDPrimaryKeyMixin, Base

if TYPE_CHECKING:
    from app.orm.officer_event_assignment import OfficerEventAssignment
    from app.orm.user_account import UserAccount


class PoliceOfficerProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "police_officer_profiles"
    __table_args__ = (
        Index("idx_officer_profiles_station", "police_station"),
        Index("idx_officer_profiles_officer_id", "officer_id"),
    )

    user_account_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("user_accounts.id", ondelete="SET NULL"),
    )
    officer_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    rank: Mapped[str | None] = mapped_column(String(128))
    police_station: Mapped[str] = mapped_column(String(255), nullable=False)
    assigned_corridors_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    assigned_zones_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    firebase_email: Mapped[str | None] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user_account: Mapped[UserAccount | None] = relationship(back_populates="officer_profile")
    assignments: Mapped[list[OfficerEventAssignment]] = relationship(back_populates="officer_profile")
