"""Add foundation incident workflow tables.

Revision ID: 0004_foundation_incidents
Revises: 0003_event_recommendations_weather_and_unique
Create Date: 2026-06-19 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_foundation_incidents"
down_revision = "0003_event_recommendations_weather_and_unique"
branch_labels = None
depends_on = None


def _dialect_name() -> str:
    return op.get_bind().dialect.name


def _uuid_type() -> sa.types.TypeEngine:
    return postgresql.UUID(as_uuid=True) if _dialect_name() == "postgresql" else sa.String(length=36)


def _json_type() -> sa.types.TypeEngine:
    return postgresql.JSONB(astext_type=sa.Text()) if _dialect_name() == "postgresql" else sa.JSON()


def _json_default(payload: str) -> sa.TextClause:
    if _dialect_name() == "postgresql":
        return sa.text(f"'{payload}'::jsonb")
    return sa.text(f"'{payload}'")


def _uuid_default() -> sa.TextClause | None:
    return sa.text("gen_random_uuid()") if _dialect_name() == "postgresql" else None


def upgrade() -> None:
    if _dialect_name() == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    with op.batch_alter_table("user_accounts") as batch_op:
        batch_op.drop_constraint("ck_user_accounts_role", type_="check")
        batch_op.create_check_constraint(
            "ck_user_accounts_role",
            "role IN ('guest', 'citizen', 'control_room_officer', 'admin', 'control_room', 'police_officer', 'public_viewer')",
        )

    op.create_table(
        "traffic_stations",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False, server_default=_uuid_default()),
        sa.Column("station_code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("locality", sa.String(length=255), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("contact_number", sa.String(length=64)),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("station_code", name="uq_traffic_stations_station_code"),
    )
    op.create_index("idx_traffic_stations_code", "traffic_stations", ["station_code"])
    op.create_index("idx_traffic_stations_locality", "traffic_stations", ["locality"])

    op.create_table(
        "incidents",
        sa.Column("id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("incident_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'pending_verification'")),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default=sa.text("'medium'")),
        sa.Column("location_name", sa.String(length=255), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("locality", sa.String(length=255)),
        sa.Column("ward", sa.String(length=128)),
        sa.Column("created_by_user_id", _uuid_type(), sa.ForeignKey("user_accounts.id", ondelete="SET NULL")),
        sa.Column("source_type", sa.String(length=32), nullable=False, server_default=sa.text("'user'")),
        sa.Column("true_vote_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("false_vote_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("confidence_score", sa.Numeric(6, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("assigned_station_id", _uuid_type(), sa.ForeignKey("traffic_stations.id", ondelete="SET NULL")),
        sa.Column("assigned_station_name", sa.String(length=255)),
        sa.Column("police_force_required", sa.Integer()),
        sa.Column("barricades_required", sa.Integer()),
        sa.Column("route_impact_summary", sa.Text()),
        sa.Column("resolution_notes", sa.Text()),
        sa.Column("visible_to_public", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("station_alerted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("status IN ('reported', 'pending_verification', 'active', 'escalated', 'resolved', 'rejected', 'archived')", name="ck_incidents_status"),
        sa.CheckConstraint("source_type IN ('user', 'control_room', 'admin', 'system_seed')", name="ck_incidents_source_type"),
        sa.CheckConstraint("severity IN ('low', 'medium', 'high', 'critical')", name="ck_incidents_severity"),
    )
    op.create_index("idx_incidents_status", "incidents", ["status"])
    op.create_index("idx_incidents_source_type", "incidents", ["source_type"])
    op.create_index("idx_incidents_location", "incidents", ["latitude", "longitude"])
    op.create_index("idx_incidents_created_at", "incidents", ["created_at"])

    op.create_table(
        "incident_votes",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False, server_default=_uuid_default()),
        sa.Column("incident_id", sa.String(length=64), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("voter_user_id", _uuid_type(), sa.ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vote_value", sa.String(length=8), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("vote_value IN ('true', 'false')", name="ck_incident_votes_value"),
        sa.UniqueConstraint("incident_id", "voter_user_id", name="uq_incident_votes_one_per_user"),
    )
    op.create_index("idx_incident_votes_incident", "incident_votes", ["incident_id"])

    op.create_table(
        "incident_predictions",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False, server_default=_uuid_default()),
        sa.Column("incident_id", sa.String(length=64), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("predicted_severity", sa.String(length=32)),
        sa.Column("police_force_required", sa.Integer()),
        sa.Column("barricades_required", sa.Integer()),
        sa.Column("urgency_score", sa.Numeric(6, 4)),
        sa.Column("route_disruption_score", sa.Numeric(6, 4)),
        sa.Column("confidence_score", sa.Numeric(6, 4)),
        sa.Column("station_recommendation", sa.String(length=255)),
        sa.Column("hotspot_contribution_score", sa.Numeric(6, 4)),
        sa.Column("output_json", _json_type(), nullable=False, server_default=_json_default("{}")),
        sa.Column("explanation_text", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_incident_predictions_incident", "incident_predictions", ["incident_id"])
    op.create_index("idx_incident_predictions_model", "incident_predictions", ["model_name", "model_version"])


def downgrade() -> None:
    op.drop_index("idx_incident_predictions_model", table_name="incident_predictions")
    op.drop_index("idx_incident_predictions_incident", table_name="incident_predictions")
    op.drop_table("incident_predictions")
    op.drop_index("idx_incident_votes_incident", table_name="incident_votes")
    op.drop_table("incident_votes")
    op.drop_index("idx_incidents_created_at", table_name="incidents")
    op.drop_index("idx_incidents_location", table_name="incidents")
    op.drop_index("idx_incidents_source_type", table_name="incidents")
    op.drop_index("idx_incidents_status", table_name="incidents")
    op.drop_table("incidents")
    op.drop_index("idx_traffic_stations_locality", table_name="traffic_stations")
    op.drop_index("idx_traffic_stations_code", table_name="traffic_stations")
    op.drop_table("traffic_stations")
    with op.batch_alter_table("user_accounts") as batch_op:
        batch_op.drop_constraint("ck_user_accounts_role", type_="check")
        batch_op.create_check_constraint(
            "ck_user_accounts_role",
            "role IN ('admin', 'control_room', 'police_officer', 'public_viewer')",
        )
