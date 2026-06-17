from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UUIDPrimaryKeyMixin:
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class TimestampMixin(CreatedAtMixin):
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


def import_model_modules() -> None:
    from app.orm import (  # noqa: F401
        citizen_report,
        demo_scenario,
        event,
        event_dna,
        event_feature,
        event_prediction,
        event_recommendation,
        hotspot_cluster,
        live_event_update,
        map_api_usage_log,
        model_run,
        officer_event_assignment,
        police_officer_profile,
        post_event_report,
        system_audit_log,
        user_account,
    )
