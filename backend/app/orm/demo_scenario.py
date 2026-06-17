from __future__ import annotations

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import CreatedAtMixin, UUIDPrimaryKeyMixin, Base


class DemoScenario(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "demo_scenarios"

    scenario_name: Mapped[str] = mapped_column(String(255), nullable=False)
    scenario_type: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    input_payload_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    expected_output_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
