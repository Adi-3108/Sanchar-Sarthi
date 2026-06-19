from __future__ import annotations

from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin


class IncidentVote(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "incident_votes"
    __table_args__ = (
        CheckConstraint("vote_value IN ('true', 'false')", name="ck_incident_votes_value"),
        UniqueConstraint("incident_id", "voter_user_id", name="uq_incident_votes_one_per_user"),
        Index("idx_incident_votes_incident", "incident_id"),
    )

    incident_id: Mapped[str] = mapped_column(String(64), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    voter_user_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False)
    vote_value: Mapped[str] = mapped_column(String(8), nullable=False)

    incident: Mapped["Incident"] = relationship(back_populates="votes")
