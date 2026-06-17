"""Add recommendation risk/weather payloads and event_id uniqueness.

Revision ID: 0003_event_recommendations_weather_and_unique
Revises: 0002_event_predictions_event_id_unique
Create Date: 2026-06-18 00:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0003_event_recommendations_weather_and_unique"
down_revision = "0002_event_predictions_event_id_unique"
branch_labels = None
depends_on = None


def _dialect_name() -> str:
    return op.get_bind().dialect.name


def _json_type() -> sa.types.TypeEngine:
    return postgresql.JSONB(astext_type=sa.Text()) if _dialect_name() == "postgresql" else sa.JSON()


def _json_default(payload: str) -> sa.TextClause:
    if _dialect_name() == "postgresql":
        return sa.text(f"'{payload}'::jsonb")
    return sa.text(f"'{payload}'")


def upgrade() -> None:
    with op.batch_alter_table("event_recommendations") as batch_op:
        batch_op.add_column(
            sa.Column(
                "risk_summary_json",
                _json_type(),
                nullable=False,
                server_default=_json_default("{}"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "weather_risk_json",
                _json_type(),
                nullable=False,
                server_default=_json_default("{}"),
            )
        )

    op.execute(
        """
        DELETE FROM event_recommendations
        WHERE id IN (
            SELECT id
            FROM (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY event_id
                        ORDER BY created_at DESC, id DESC
                    ) AS row_number
                FROM event_recommendations
            ) ranked
            WHERE row_number > 1
        )
        """
    )

    with op.batch_alter_table("event_recommendations") as batch_op:
        batch_op.create_unique_constraint("uq_event_recommendations_event_id", ["event_id"])


def downgrade() -> None:
    with op.batch_alter_table("event_recommendations") as batch_op:
        batch_op.drop_constraint("uq_event_recommendations_event_id", type_="unique")
        batch_op.drop_column("weather_risk_json")
        batch_op.drop_column("risk_summary_json")
