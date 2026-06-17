"""Add event_predictions event_id uniqueness.

Revision ID: 0002_event_predictions_event_id_unique
Revises: 0001_initial_schema
Create Date: 2026-06-18 00:00:00
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_event_predictions_event_id_unique"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM event_predictions
        WHERE id IN (
            SELECT id
            FROM (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY event_id
                        ORDER BY created_at DESC, id DESC
                    ) AS row_number
                FROM event_predictions
            ) ranked
            WHERE row_number > 1
        )
        """
    )
    with op.batch_alter_table("event_predictions") as batch_op:
        batch_op.create_unique_constraint("uq_event_predictions_event_id", ["event_id"])


def downgrade() -> None:
    with op.batch_alter_table("event_predictions") as batch_op:
        batch_op.drop_constraint("uq_event_predictions_event_id", type_="unique")
