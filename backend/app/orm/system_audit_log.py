from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Index, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import CreatedAtMixin, UUIDPrimaryKeyMixin, Base

if TYPE_CHECKING:
    from app.orm.user_account import UserAccount


class SystemAuditLog(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "system_audit_logs"
    __table_args__ = (
        Index("idx_system_audit_logs_actor_role", "actor_role"),
        Index("idx_system_audit_logs_action_created", "action", "created_at"),
        Index("idx_system_audit_logs_resource_type", "resource_type"),
    )

    actor_user_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("user_accounts.id", ondelete="SET NULL"),
    )
    actor_role: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(128))
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    request_id: Mapped[str | None] = mapped_column(String(128))

    actor_user: Mapped[UserAccount | None] = relationship(back_populates="audit_logs")
