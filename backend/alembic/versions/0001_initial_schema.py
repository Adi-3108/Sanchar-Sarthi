"""Initial EventFlow schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-17 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
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
    if _dialect_name() == "postgresql":
        return sa.text("gen_random_uuid()")
    return None


def upgrade() -> None:
    if _dialect_name() == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "user_accounts",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False, server_default=_uuid_default()),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("display_name", sa.String(length=255)),
        sa.Column("auth_provider", sa.String(length=32), nullable=False, server_default=sa.text("'firebase'")),
        sa.Column("auth_provider_uid", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("role IN ('admin', 'control_room', 'police_officer', 'public_viewer')", name="ck_user_accounts_role"),
        sa.CheckConstraint("auth_provider = 'firebase'", name="ck_user_accounts_auth_provider"),
        sa.UniqueConstraint("auth_provider_uid", name="uq_user_accounts_auth_provider_uid"),
    )
    op.create_index("idx_user_accounts_role", "user_accounts", ["role"])

    op.create_table(
        "police_officer_profiles",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False, server_default=_uuid_default()),
        sa.Column("user_account_id", _uuid_type(), sa.ForeignKey("user_accounts.id", ondelete="SET NULL")),
        sa.Column("officer_id", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("rank", sa.String(length=128)),
        sa.Column("police_station", sa.String(length=255), nullable=False),
        sa.Column("assigned_corridors_json", _json_type(), nullable=False, server_default=_json_default("[]")),
        sa.Column("assigned_zones_json", _json_type(), nullable=False, server_default=_json_default("[]")),
        sa.Column("firebase_email", sa.String(length=255)),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("officer_id", name="uq_police_officer_profiles_officer_id"),
    )
    op.create_index("idx_officer_profiles_station", "police_officer_profiles", ["police_station"])
    op.create_index("idx_officer_profiles_officer_id", "police_officer_profiles", ["officer_id"])

    op.create_table(
        "events",
        sa.Column("id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("event_type", sa.String(length=32)),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("endlatitude", sa.Float()),
        sa.Column("endlongitude", sa.Float()),
        sa.Column("address", sa.Text()),
        sa.Column("end_address", sa.Text()),
        sa.Column("event_cause", sa.String(length=128)),
        sa.Column("event_cause_clean", sa.String(length=128)),
        sa.Column("requires_road_closure", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("start_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_datetime", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(length=64)),
        sa.Column("authenticated", sa.Boolean()),
        sa.Column("modified_datetime", sa.DateTime(timezone=True)),
        sa.Column("direction", sa.String(length=128)),
        sa.Column("description", sa.Text()),
        sa.Column("description_language", sa.String(length=32), nullable=False, server_default=sa.text("'unknown'")),
        sa.Column("description_for_features", sa.Text()),
        sa.Column("description_normalization_method", sa.String(length=128)),
        sa.Column("veh_type", sa.String(length=64)),
        sa.Column("veh_no_hash", sa.String(length=255)),
        sa.Column("veh_no_masked", sa.String(length=255)),
        sa.Column("corridor", sa.String(length=255)),
        sa.Column("priority", sa.String(length=64)),
        sa.Column("cargo_material", sa.String(length=255)),
        sa.Column("reason_breakdown", sa.Text()),
        sa.Column("reason_breakdown_clean", sa.String(length=255)),
        sa.Column("age_of_truck", sa.Numeric(8, 2)),
        sa.Column("created_date", sa.DateTime(timezone=True)),
        sa.Column("route_path", sa.Text()),
        sa.Column("police_station", sa.String(length=255)),
        sa.Column("resolved_at_address", sa.Text()),
        sa.Column("resolved_at_latitude", sa.Float()),
        sa.Column("resolved_at_longitude", sa.Float()),
        sa.Column("closed_datetime", sa.DateTime(timezone=True)),
        sa.Column("resolved_datetime", sa.DateTime(timezone=True)),
        sa.Column("zone", sa.String(length=255)),
        sa.Column("junction", sa.String(length=255)),
        sa.Column("raw_payload", _json_type(), nullable=False, server_default=_json_default("{}")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("event_type IN ('planned', 'unplanned')", name="ck_events_event_type"),
    )
    op.create_index("idx_events_event_cause_clean", "events", ["event_cause_clean"])
    op.create_index("idx_events_priority", "events", ["priority"])
    op.create_index("idx_events_status", "events", ["status"])
    op.create_index("idx_events_requires_road_closure", "events", ["requires_road_closure"])
    op.create_index("idx_events_start_datetime", "events", ["start_datetime"])
    op.create_index("idx_events_corridor", "events", ["corridor"])
    op.create_index("idx_events_police_station", "events", ["police_station"])
    op.create_index("idx_events_zone", "events", ["zone"])
    op.create_index("idx_events_junction", "events", ["junction"])
    op.create_index("idx_events_lat_lng", "events", ["latitude", "longitude"])

    op.create_table(
        "event_features",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False, server_default=_uuid_default()),
        sa.Column("event_id", sa.String(length=64), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_hour", sa.Integer()),
        sa.Column("event_day", sa.Integer()),
        sa.Column("event_month", sa.Integer()),
        sa.Column("event_weekday", sa.Integer()),
        sa.Column("is_weekend", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_peak_hour", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_night_event", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("event_duration_minutes", sa.Numeric(10, 2)),
        sa.Column("closure_duration_minutes", sa.Numeric(10, 2)),
        sa.Column("resolution_duration_minutes", sa.Numeric(10, 2)),
        sa.Column("duration_source", sa.String(length=32)),
        sa.Column("has_zone", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_junction", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_route_path", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_vehicle_type", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("location_cluster_id", sa.String(length=128)),
        sa.Column("historical_corridor_risk", sa.Numeric(6, 4)),
        sa.Column("historical_police_station_risk", sa.Numeric(6, 4)),
        sa.Column("historical_cluster_risk", sa.Numeric(6, 4)),
        sa.Column("historical_cause_closure_rate", sa.Numeric(6, 4)),
        sa.Column("historical_corridor_closure_rate", sa.Numeric(6, 4)),
        sa.Column("historical_police_station_closure_rate", sa.Numeric(6, 4)),
        sa.Column("historical_cluster_closure_rate", sa.Numeric(6, 4)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint(
            "duration_source IN ('end_datetime', 'closed_datetime', 'resolved_datetime', 'unavailable')",
            name="ck_event_features_duration_source",
        ),
        sa.UniqueConstraint("event_id", name="uq_event_features_event_id"),
    )
    op.create_index("idx_event_features_event_id", "event_features", ["event_id"])
    op.create_index("idx_event_features_location_cluster_id", "event_features", ["location_cluster_id"])

    op.create_table(
        "hotspot_clusters",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False, server_default=_uuid_default()),
        sa.Column("location_cluster_id", sa.String(length=128), nullable=False),
        sa.Column("centroid_latitude", sa.Float(), nullable=False),
        sa.Column("centroid_longitude", sa.Float(), nullable=False),
        sa.Column("cluster_event_count", sa.Integer(), nullable=False),
        sa.Column("cluster_high_priority_rate", sa.Numeric(6, 4)),
        sa.Column("cluster_road_closure_rate", sa.Numeric(6, 4)),
        sa.Column("cluster_peak_hour_rate", sa.Numeric(6, 4)),
        sa.Column("cluster_top_event_cause", sa.String(length=128)),
        sa.Column("cluster_risk_score", sa.Numeric(6, 4), nullable=False),
        sa.Column("cluster_profile_json", _json_type(), nullable=False, server_default=_json_default("{}")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("location_cluster_id", name="uq_hotspot_clusters_location_cluster_id"),
    )
    op.create_index("idx_hotspot_clusters_location_cluster_id", "hotspot_clusters", ["location_cluster_id"])
    op.create_index("idx_hotspot_clusters_centroid", "hotspot_clusters", ["centroid_latitude", "centroid_longitude"])
    op.create_index("idx_hotspot_clusters_risk_score", "hotspot_clusters", ["cluster_risk_score"])

    op.create_table(
        "event_dna",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False, server_default=_uuid_default()),
        sa.Column("event_id", sa.String(length=64), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dna_summary", sa.Text(), nullable=False),
        sa.Column("time_context", sa.Text(), nullable=False),
        sa.Column("location_context", sa.Text(), nullable=False),
        sa.Column("cause_context", sa.Text(), nullable=False),
        sa.Column("weather_context", sa.Text()),
        sa.Column("multi_event_context", sa.Text()),
        sa.Column("historical_pattern", sa.Text(), nullable=False),
        sa.Column("risk_indicators_json", _json_type(), nullable=False, server_default=_json_default("{}")),
        sa.Column("similar_event_ids_json", _json_type(), nullable=False, server_default=_json_default("[]")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("event_id", name="uq_event_dna_event_id"),
    )
    op.create_index("idx_event_dna_event_id", "event_dna", ["event_id"])

    op.create_table(
        "model_runs",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False, server_default=_uuid_default()),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("model_version", sa.String(length=128), nullable=False),
        sa.Column("target_variable", sa.String(length=128), nullable=False),
        sa.Column("training_rows", sa.Integer(), nullable=False),
        sa.Column("test_rows", sa.Integer(), nullable=False),
        sa.Column("metrics_json", _json_type(), nullable=False, server_default=_json_default("{}")),
        sa.Column("feature_list_json", _json_type(), nullable=False, server_default=_json_default("[]")),
        sa.Column("artifact_path", sa.String(length=512)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("model_name", "model_version", name="uq_model_runs_name_version"),
    )
    op.create_index("idx_model_runs_model_name", "model_runs", ["model_name"])
    op.create_index("idx_model_runs_created_at", "model_runs", ["created_at"])

    op.create_table(
        "event_predictions",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False, server_default=_uuid_default()),
        sa.Column("event_id", sa.String(length=64), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_run_id", _uuid_type(), sa.ForeignKey("model_runs.id", ondelete="SET NULL")),
        sa.Column("predicted_priority", sa.String(length=64)),
        sa.Column("priority_confidence", sa.Numeric(6, 4)),
        sa.Column("road_closure_probability", sa.Numeric(6, 4)),
        sa.Column("predicted_road_closure", sa.Boolean()),
        sa.Column("estimated_clearance_minutes", sa.Numeric(8, 2)),
        sa.Column("clearance_prediction_method", sa.String(length=64)),
        sa.Column("clearance_confidence", sa.Numeric(6, 4)),
        sa.Column("clearance_confidence_note", sa.Text()),
        sa.Column("historical_clearance_range_min", sa.Numeric(8, 2)),
        sa.Column("historical_clearance_range_max", sa.Numeric(8, 2)),
        sa.Column("estimated_impact_score", sa.Numeric(8, 2)),
        sa.Column("impact_category", sa.String(length=64)),
        sa.Column("impact_radius_km", sa.Numeric(8, 2)),
        sa.Column("vehicle_impact_factor", sa.Numeric(5, 2)),
        sa.Column("vehicle_impact_note", sa.Text()),
        sa.Column("baseline_risk_score", sa.Numeric(8, 2)),
        sa.Column("additional_event_delta", sa.Numeric(8, 2)),
        sa.Column("weather_adjustment_json", _json_type()),
        sa.Column("multi_event_conflict_json", _json_type()),
        sa.Column("prediction_explanation_json", _json_type(), nullable=False, server_default=_json_default("{}")),
        sa.Column("model_version", sa.String(length=128)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_predictions_event", "event_predictions", ["event_id"])
    op.create_index("idx_event_predictions_predicted_road_closure", "event_predictions", ["predicted_road_closure"])
    op.create_index("idx_event_predictions_impact_category", "event_predictions", ["impact_category"])

    op.create_table(
        "event_recommendations",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False, server_default=_uuid_default()),
        sa.Column("event_id", sa.String(length=64), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recommended_total_officers", sa.Integer()),
        sa.Column("deployment_plan_json", _json_type(), nullable=False, server_default=_json_default("{}")),
        sa.Column("barricade_plan_json", _json_type(), nullable=False, server_default=_json_default("{}")),
        sa.Column("diversion_plan_json", _json_type(), nullable=False, server_default=_json_default("{}")),
        sa.Column("emergency_corridor_json", _json_type()),
        sa.Column("logistics_impact_json", _json_type()),
        sa.Column("action_confidence_ledger_json", _json_type(), nullable=False, server_default=_json_default("[]")),
        sa.Column("recommended_action_summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_event_recommendations_event_id", "event_recommendations", ["event_id"])

    op.create_table(
        "citizen_reports",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False, server_default=_uuid_default()),
        sa.Column("report_source", sa.String(length=32), nullable=False),
        sa.Column("report_type", sa.String(length=80), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("severity", sa.String(length=32)),
        sa.Column("description", sa.Text()),
        sa.Column("language", sa.String(length=16), nullable=False, server_default=sa.text("'en'")),
        sa.Column("source_language", sa.String(length=16)),
        sa.Column("translated_description", sa.Text()),
        sa.Column("translation_provider", sa.String(length=32), nullable=False, server_default=sa.text("'disabled'")),
        sa.Column("translation_status", sa.String(length=32), nullable=False, server_default=sa.text("'disabled'")),
        sa.Column("translation_character_count", sa.Integer()),
        sa.Column("event_id", sa.String(length=64), sa.ForeignKey("events.id", ondelete="SET NULL")),
        sa.Column("matched_event_id", sa.String(length=64)),
        sa.Column("location_match_confidence", sa.Numeric(6, 4)),
        sa.Column("report_confidence", sa.Numeric(6, 4)),
        sa.Column("impact_score_change", sa.Numeric(8, 2)),
        sa.Column("new_alert_level", sa.String(length=32)),
        sa.Column("recommended_action", sa.Text()),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'accepted'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_citizen_reports_report_source", "citizen_reports", ["report_source"])
    op.create_index("idx_citizen_reports_report_type", "citizen_reports", ["report_type"])
    op.create_index("idx_citizen_reports_severity", "citizen_reports", ["severity"])
    op.create_index("idx_citizen_reports_event_created", "citizen_reports", ["event_id", "created_at"])
    op.create_index("idx_citizen_reports_lat_lng", "citizen_reports", ["latitude", "longitude"])

    op.create_table(
        "live_event_updates",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False, server_default=_uuid_default()),
        sa.Column("event_id", sa.String(length=64), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("update_source", sa.String(length=32), nullable=False),
        sa.Column("current_congestion_level", sa.String(length=32), nullable=False),
        sa.Column("field_update", sa.Text()),
        sa.Column("road_closure_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("officer_shortage", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("crowd_increase", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("rain_waterlogging", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("new_nearby_incident", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("expected_impact_score", sa.Numeric(8, 2)),
        sa.Column("current_impact_score", sa.Numeric(8, 2)),
        sa.Column("impact_deviation", sa.Numeric(8, 2)),
        sa.Column("alert_level", sa.String(length=32)),
        sa.Column("adaptive_action", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_live_event_updates_event_created", "live_event_updates", ["event_id", "created_at"])
    op.create_index("idx_live_event_updates_alert_level", "live_event_updates", ["alert_level"])

    op.create_table(
        "post_event_reports",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False, server_default=_uuid_default()),
        sa.Column("event_id", sa.String(length=64), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("predicted_impact_score", sa.Numeric(8, 2)),
        sa.Column("simulated_actual_impact_score", sa.Numeric(8, 2)),
        sa.Column("impact_deviation", sa.Numeric(8, 2)),
        sa.Column("final_status", sa.String(length=64)),
        sa.Column("event_summary", sa.Text(), nullable=False),
        sa.Column("prediction_summary", sa.Text(), nullable=False),
        sa.Column("recommendation_summary", sa.Text(), nullable=False),
        sa.Column("citizen_report_summary", sa.Text()),
        sa.Column("live_escalation_summary", sa.Text()),
        sa.Column("lessons_learned", sa.Text(), nullable=False),
        sa.Column("future_recommendations", sa.Text(), nullable=False),
        sa.Column("report_json", _json_type(), nullable=False, server_default=_json_default("{}")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_post_event_reports_event", "post_event_reports", ["event_id"])

    op.create_table(
        "demo_scenarios",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False, server_default=_uuid_default()),
        sa.Column("scenario_name", sa.String(length=255), nullable=False),
        sa.Column("scenario_type", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("input_payload_json", _json_type(), nullable=False, server_default=_json_default("{}")),
        sa.Column("expected_output_json", _json_type(), nullable=False, server_default=_json_default("{}")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "system_audit_logs",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False, server_default=_uuid_default()),
        sa.Column("actor_user_id", _uuid_type(), sa.ForeignKey("user_accounts.id", ondelete="SET NULL")),
        sa.Column("actor_role", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("resource_type", sa.String(length=128), nullable=False),
        sa.Column("resource_id", sa.String(length=128)),
        sa.Column("metadata_json", _json_type(), nullable=False, server_default=_json_default("{}")),
        sa.Column("request_id", sa.String(length=128)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_system_audit_logs_actor_role", "system_audit_logs", ["actor_role"])
    op.create_index("idx_system_audit_logs_action_created", "system_audit_logs", ["action", "created_at"])
    op.create_index("idx_system_audit_logs_resource_type", "system_audit_logs", ["resource_type"])

    op.create_table(
        "map_api_usage_logs",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False, server_default=_uuid_default()),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("api_name", sa.String(length=64), nullable=False),
        sa.Column("cache_hit", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("estimated_cost_inr", sa.Numeric(10, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("request_hash", sa.String(length=255)),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("fallback_reason", sa.String(length=128)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_map_api_usage_provider_created", "map_api_usage_logs", ["provider", "created_at"])
    op.create_index("idx_map_api_usage_api_name", "map_api_usage_logs", ["api_name"])
    op.create_index("idx_map_api_usage_request_hash", "map_api_usage_logs", ["request_hash"])

    op.create_table(
        "officer_event_assignments",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False, server_default=_uuid_default()),
        sa.Column("officer_profile_id", _uuid_type(), sa.ForeignKey("police_officer_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_id", sa.String(length=64), sa.ForeignKey("events.id", ondelete="CASCADE")),
        sa.Column("corridor", sa.String(length=255)),
        sa.Column("police_station", sa.String(length=255)),
        sa.Column("assignment_type", sa.String(length=32), nullable=False),
        sa.Column("assignment_status", sa.String(length=32), nullable=False, server_default=sa.text("'active'")),
        sa.Column("assigned_by_user_id", _uuid_type(), sa.ForeignKey("user_accounts.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("assignment_type IN ('event', 'corridor', 'station', 'reserve')", name="ck_officer_assignments_type"),
        sa.CheckConstraint("assignment_status IN ('active', 'completed', 'cancelled')", name="ck_officer_assignments_status"),
    )
    op.create_index("idx_officer_assignments_event", "officer_event_assignments", ["event_id"])
    op.create_index("idx_officer_assignments_station", "officer_event_assignments", ["police_station"])
    op.create_index("idx_officer_assignments_corridor", "officer_event_assignments", ["corridor"])


def downgrade() -> None:
    op.drop_index("idx_officer_assignments_corridor", table_name="officer_event_assignments")
    op.drop_index("idx_officer_assignments_station", table_name="officer_event_assignments")
    op.drop_index("idx_officer_assignments_event", table_name="officer_event_assignments")
    op.drop_table("officer_event_assignments")

    op.drop_index("idx_map_api_usage_request_hash", table_name="map_api_usage_logs")
    op.drop_index("idx_map_api_usage_api_name", table_name="map_api_usage_logs")
    op.drop_index("idx_map_api_usage_provider_created", table_name="map_api_usage_logs")
    op.drop_table("map_api_usage_logs")

    op.drop_index("idx_system_audit_logs_resource_type", table_name="system_audit_logs")
    op.drop_index("idx_system_audit_logs_action_created", table_name="system_audit_logs")
    op.drop_index("idx_system_audit_logs_actor_role", table_name="system_audit_logs")
    op.drop_table("system_audit_logs")

    op.drop_table("demo_scenarios")

    op.drop_index("idx_post_event_reports_event", table_name="post_event_reports")
    op.drop_table("post_event_reports")

    op.drop_index("idx_live_event_updates_alert_level", table_name="live_event_updates")
    op.drop_index("idx_live_event_updates_event_created", table_name="live_event_updates")
    op.drop_table("live_event_updates")

    op.drop_index("idx_citizen_reports_lat_lng", table_name="citizen_reports")
    op.drop_index("idx_citizen_reports_event_created", table_name="citizen_reports")
    op.drop_index("idx_citizen_reports_severity", table_name="citizen_reports")
    op.drop_index("idx_citizen_reports_report_type", table_name="citizen_reports")
    op.drop_index("idx_citizen_reports_report_source", table_name="citizen_reports")
    op.drop_table("citizen_reports")

    op.drop_index("idx_event_recommendations_event_id", table_name="event_recommendations")
    op.drop_table("event_recommendations")

    op.drop_index("idx_event_predictions_impact_category", table_name="event_predictions")
    op.drop_index("idx_event_predictions_predicted_road_closure", table_name="event_predictions")
    op.drop_index("idx_predictions_event", table_name="event_predictions")
    op.drop_table("event_predictions")

    op.drop_index("idx_model_runs_created_at", table_name="model_runs")
    op.drop_index("idx_model_runs_model_name", table_name="model_runs")
    op.drop_table("model_runs")

    op.drop_index("idx_event_dna_event_id", table_name="event_dna")
    op.drop_table("event_dna")

    op.drop_index("idx_hotspot_clusters_risk_score", table_name="hotspot_clusters")
    op.drop_index("idx_hotspot_clusters_centroid", table_name="hotspot_clusters")
    op.drop_index("idx_hotspot_clusters_location_cluster_id", table_name="hotspot_clusters")
    op.drop_table("hotspot_clusters")

    op.drop_index("idx_event_features_location_cluster_id", table_name="event_features")
    op.drop_index("idx_event_features_event_id", table_name="event_features")
    op.drop_table("event_features")

    op.drop_index("idx_events_lat_lng", table_name="events")
    op.drop_index("idx_events_junction", table_name="events")
    op.drop_index("idx_events_zone", table_name="events")
    op.drop_index("idx_events_police_station", table_name="events")
    op.drop_index("idx_events_corridor", table_name="events")
    op.drop_index("idx_events_start_datetime", table_name="events")
    op.drop_index("idx_events_requires_road_closure", table_name="events")
    op.drop_index("idx_events_status", table_name="events")
    op.drop_index("idx_events_priority", table_name="events")
    op.drop_index("idx_events_event_cause_clean", table_name="events")
    op.drop_table("events")

    op.drop_index("idx_officer_profiles_officer_id", table_name="police_officer_profiles")
    op.drop_index("idx_officer_profiles_station", table_name="police_officer_profiles")
    op.drop_table("police_officer_profiles")

    op.drop_index("idx_user_accounts_role", table_name="user_accounts")
    op.drop_table("user_accounts")
