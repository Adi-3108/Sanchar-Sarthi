from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampMixin, UUIDPrimaryKeyMixin, Base

if TYPE_CHECKING:
    from app.orm.officer_event_assignment import OfficerEventAssignment
    from app.orm.police_officer_profile import PoliceOfficerProfile
    from app.orm.system_audit_log import SystemAuditLog


class UserAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_accounts"
    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'control_room', 'police_officer', 'public_viewer')",
            name="ck_user_accounts_role",
        ),
        CheckConstraint(
            "auth_provider = 'firebase'",
            name="ck_user_accounts_auth_provider",
        ),
        Index("idx_user_accounts_role", "role"),
    )

    role: Mapped[str] = mapped_column(String(32), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255))
    auth_provider: Mapped[str] = mapped_column(String(32), nullable=False, default="firebase")
    auth_provider_uid: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    officer_profile: Mapped[PoliceOfficerProfile | None] = relationship(
        back_populates="user_account",
        uselist=False,
    )
    created_assignments: Mapped[list[OfficerEventAssignment]] = relationship(
        back_populates="assigned_by_user",
    )
    audit_logs: Mapped[list[SystemAuditLog]] = relationship(back_populates="actor_user")
