from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import AuthContext, require_role
from app.db.session import get_db
from app.orm.hotspot_cluster import HotspotCluster
from app.orm.model_run import ModelRun
from app.orm.system_audit_log import SystemAuditLog
from app.ml.feature_pipeline import serialize_model_run
from app.services.hotspot_service import (
    HotspotFilters,
    HotspotRebuildReport,
    build_analytics_summary,
    build_hotspot_geojson,
    list_hotspots,
    rebuild_hotspots,
)
from app.services.rag_indexer_service import reindex_all_hotspots


class AnalyticsBreakdownItem(BaseModel):
    label: str
    count: int
    share: float


class AnalyticsSummaryResponse(BaseModel):
    total_events: int
    planned_events: int
    unplanned_events: int
    high_priority_events: int
    road_closure_required: int
    hotspot_count: int
    top_causes: list[AnalyticsBreakdownItem]
    top_corridors: list[AnalyticsBreakdownItem]
    top_police_stations: list[AnalyticsBreakdownItem]


class HotspotItemResponse(BaseModel):
    location_cluster_id: str
    centroid_latitude: float
    centroid_longitude: float
    cluster_event_count: int
    cluster_risk_score: float
    cluster_top_event_cause: str | None = None
    cluster_high_priority_rate: float | None = None
    cluster_road_closure_rate: float | None = None
    cluster_peak_hour_rate: float | None = None
    cluster_type: str | None = None
    cluster_profile: dict[str, object] = Field(default_factory=dict)


class HotspotListResponse(BaseModel):
    hotspots: list[HotspotItemResponse]
    geojson: dict[str, object]
    filters_applied: dict[str, object]


class HotspotRebuildResponse(BaseModel):
    status: str
    clusters_created: int
    clustered_events: int
    noise_events: int
    event_features_updated: int
    message: str | None = None


class ModelRunItemResponse(BaseModel):
    id: str
    model_name: str
    model_version: str
    target_variable: str
    training_rows: int
    test_rows: int
    metrics_json: dict[str, object] = Field(default_factory=dict)
    feature_list_json: list[str] = Field(default_factory=list)
    artifact_path: str | None = None
    artifact_available: bool
    artifact_status: str
    created_at: datetime


class ModelRunListResponse(BaseModel):
    model_runs: list[ModelRunItemResponse]


router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: dict[str, object] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        },
    )


def require_internal_analytics_access(
    auth: AuthContext = Depends(require_role("admin", "control_room", "police_officer")),
) -> AuthContext:
    return auth


def require_hotspot_rebuild_access(
    auth: AuthContext = Depends(require_role("admin", "control_room")),
) -> AuthContext:
    return auth


def _record_hotspot_rebuild_audit_log(
    db: Session,
    auth: AuthContext,
    report: HotspotRebuildReport,
    *,
    eps_km: float,
    min_samples: int,
) -> None:
    actor_user_id = None
    try:
        from uuid import UUID

        actor_user_id = UUID(auth.user_account_id)
    except (ValueError, TypeError):
        actor_user_id = None

    db.add(
        SystemAuditLog(
            actor_user_id=actor_user_id,
            actor_role=auth.role,
            action="hotspot_rebuild",
            resource_type="hotspot_clusters",
            resource_id="all-clusters",
            metadata_json={
                "clusters_created": report.clusters_created,
                "clustered_events": report.clustered_events,
                "noise_events": report.noise_events,
                "event_features_updated": report.event_features_updated,
                "eps_km": eps_km,
                "min_samples": min_samples,
            },
        )
    )


def _serialize_hotspot(hotspot: HotspotCluster) -> HotspotItemResponse:
    cluster_profile = dict(hotspot.cluster_profile_json or {})
    return HotspotItemResponse(
        location_cluster_id=hotspot.location_cluster_id,
        centroid_latitude=float(hotspot.centroid_latitude),
        centroid_longitude=float(hotspot.centroid_longitude),
        cluster_event_count=hotspot.cluster_event_count,
        cluster_risk_score=float(hotspot.cluster_risk_score),
        cluster_top_event_cause=hotspot.cluster_top_event_cause,
        cluster_high_priority_rate=(
            float(hotspot.cluster_high_priority_rate)
            if hotspot.cluster_high_priority_rate is not None
            else None
        ),
        cluster_road_closure_rate=(
            float(hotspot.cluster_road_closure_rate)
            if hotspot.cluster_road_closure_rate is not None
            else None
        ),
        cluster_peak_hour_rate=(
            float(hotspot.cluster_peak_hour_rate)
            if hotspot.cluster_peak_hour_rate is not None
            else None
        ),
        cluster_type=cluster_profile.get("cluster_type") if cluster_profile else None,
        cluster_profile=cluster_profile,
    )


def _list_latest_model_runs(db: Session) -> list[ModelRun]:
    rows = db.scalars(
        select(ModelRun).order_by(ModelRun.created_at.desc(), ModelRun.id.desc())
    ).all()
    latest_by_model_name: dict[str, ModelRun] = {}
    for row in rows:
        latest_by_model_name.setdefault(row.model_name, row)
    return sorted(
        latest_by_model_name.values(),
        key=lambda row: (row.created_at, row.model_name),
        reverse=True,
    )


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_summary(
    _auth: AuthContext = Depends(require_internal_analytics_access),
    db: Session = Depends(get_db),
):
    try:
        summary = build_analytics_summary(db)
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for analytics summary.")
    return AnalyticsSummaryResponse.model_validate(summary)


@router.get("/hotspots", response_model=HotspotListResponse)
def get_hotspots(
    event_cause: str | None = Query(default=None, max_length=128),
    priority: str | None = Query(default=None, max_length=64),
    requires_road_closure: bool | None = Query(default=None),
    cluster_type: Literal["low", "medium", "high", "critical"] | None = Query(default=None),
    _auth: AuthContext = Depends(require_internal_analytics_access),
    db: Session = Depends(get_db),
):
    try:
        filters = HotspotFilters(
            event_cause=event_cause,
            priority=priority,
            requires_road_closure=requires_road_closure,
            cluster_type=cluster_type,
        )
        hotspots = list_hotspots(db, filters=filters)
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for hotspot analytics.")

    return HotspotListResponse(
        hotspots=[_serialize_hotspot(hotspot) for hotspot in hotspots],
        geojson=build_hotspot_geojson(hotspots),
        filters_applied={
            "event_cause": event_cause,
            "priority": priority,
            "requires_road_closure": requires_road_closure,
            "cluster_type": cluster_type,
        },
    )


@router.get("/model-runs", response_model=ModelRunListResponse)
def get_model_runs(
    _auth: AuthContext = Depends(require_internal_analytics_access),
    db: Session = Depends(get_db),
):
    try:
        model_runs = _list_latest_model_runs(db)
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for model insights.")

    return ModelRunListResponse(
        model_runs=[ModelRunItemResponse.model_validate(serialize_model_run(row)) for row in model_runs]
    )


@router.post("/hotspots/rebuild", response_model=HotspotRebuildResponse)
def rebuild_hotspot_clusters(
    eps_km: float = Query(default=0.7, ge=0.1, le=5.0),
    min_samples: int = Query(default=3, ge=2, le=50),
    auth: AuthContext = Depends(require_hotspot_rebuild_access),
    db: Session = Depends(get_db),
):
    try:
        report = rebuild_hotspots(db, eps_km=eps_km, min_samples=min_samples, commit=False)
        _record_hotspot_rebuild_audit_log(
            db,
            auth,
            report,
            eps_km=eps_km,
            min_samples=min_samples,
        )
        db.commit()
        try:
            reindex_all_hotspots(db, commit=True)
        except Exception:
            db.rollback()
    except ValueError as exc:
        db.rollback()
        return error_response(400, "VALIDATION_ERROR", str(exc))
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for hotspot rebuild.")

    message = "Dataset-backed hotspot clusters rebuilt."
    if report.clusters_created == 0:
        message = "No hotspot clusters were created from the current dataset."

    return HotspotRebuildResponse(
        status="success",
        clusters_created=report.clusters_created,
        clustered_events=report.clustered_events,
        noise_events=report.noise_events,
        event_features_updated=report.event_features_updated,
        message=message,
    )
