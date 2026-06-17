from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampMixin, UUIDPrimaryKeyMixin, Base

if TYPE_CHECKING:
    from app.orm.event import Event
    from app.orm.police_officer_profile import PoliceOfficerProfile
    from app.orm.user_account import UserAccount


class OfficerEventAssignment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "officer_event_assignments"
    __table_args__ = (
        CheckConstraint(
            "assignment_type IN ('event', 'corridor', 'station', 'reserve')",
            name="ck_officer_assignments_type",
        ),
        CheckConstraint(
            "assignment_status IN ('active', 'completed', 'cancelled')",
            name="ck_officer_assignments_status",
        ),
        Index("idx_officer_assignments_event", "event_id"),
        Index("idx_officer_assignments_station", "police_station"),
        Index("idx_officer_assignments_corridor", "corridor"),
    )

    officer_profile_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("police_officer_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("events.id", ondelete="CASCADE"),
    )
    corridor: Mapped[str | None] = mapped_column(String(255))
    police_station: Mapped[str | None] = mapped_column(String(255))
    assignment_type: Mapped[str] = mapped_column(String(32), nullable=False)
    assignment_status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    assigned_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("user_accounts.id", ondelete="SET NULL"),
    )

    officer_profile: Mapped[PoliceOfficerProfile] = relationship(back_populates="assignments")
    event: Mapped[Event | None] = relationship(back_populates="assignments")
    assigned_by_user: Mapped[UserAccount | None] = relationship(back_populates="created_assignments")
