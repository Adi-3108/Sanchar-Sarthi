from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from importlib import util as importlib_util
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import resolve_database_url
from app.core.database import build_engine
from app.db.base import Base, import_model_modules
from app.orm.event import Event
from app.orm.event_feature import EventFeature
from app.orm.model_run import ModelRun

BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_ROOT.parent
ARTIFACTS_ROOT = BACKEND_ROOT / "artifacts"

MODELS_ROOT = BACKEND_ROOT / "app" / "models"

PRIORITY_MODEL_NAME = "xgboost_priority_model"
PRIORITY_MODEL_VERSION = "xgboost_kaggle_v1"
PRIORITY_MODEL_PATH = MODELS_ROOT / "xgboost_priority_model.pkl"
LABEL_ENCODER_PATH = MODELS_ROOT / "label_encoder.pkl"

ROAD_CLOSURE_MODEL_NAME = "road_closure_model"
ROAD_CLOSURE_MODEL_VERSION = "road_closure_support_v1"
ROAD_CLOSURE_MODEL_PATH = ARTIFACTS_ROOT / "road_closure_model.joblib"

RESOLUTION_TIME_MODEL_NAME = "resolution_time_model"
RESOLUTION_TIME_MODEL_VERSION = "resolution_time_gbr_v1"
RESOLUTION_TIME_MODEL_PATH = ARTIFACTS_ROOT / "resolution_time_model.joblib"

PEAK_HOURS = frozenset({8, 9, 10, 17, 18, 19, 20})
DATA_FILTER_APPLIED = "resolved_datetime within 24h, else closed_datetime within 24h"
OPTIONAL_ML_MODULES = ("joblib", "pandas", "sklearn")


@dataclass(frozen=True)
class EventFeatureBundle:
    event: Event
    feature: EventFeature | None


def ensure_artifacts_root() -> Path:
    ARTIFACTS_ROOT.mkdir(parents=True, exist_ok=True)
    return ARTIFACTS_ROOT


def ensure_schema(database_url: str | None = None) -> str:
    resolved_database_url = resolve_database_url(database_url)
    import_model_modules()
    try:
        from alembic import command
        from alembic.config import Config

        config = Config(str(REPO_ROOT / "alembic.ini"))
        config.set_main_option("sqlalchemy.url", resolved_database_url.replace("%", "%%"))
        command.upgrade(config, "head")
    except Exception:
        engine = build_engine(resolved_database_url)
        Base.metadata.create_all(engine)
    return resolved_database_url


def build_session_factory(database_url: str | None = None) -> sessionmaker[Session]:
    resolved_database_url = ensure_schema(database_url)
    engine = build_engine(resolved_database_url)
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().casefold()
    return normalized or None


def normalize_priority_bucket(value: str | None) -> str:
    normalized = normalize_text(value)
    if normalized in {"high", "critical"}:
        return "high"
    return "low"


def peak_hour_flag(hour: int | None) -> bool:
    return hour in PEAK_HOURS if hour is not None else False


def safe_float(value: Decimal | float | int | None, *, default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


def safe_bool(value: bool | None) -> bool:
    return bool(value)


def artifact_exists(path_or_value: Path | str | None) -> bool:
    if path_or_value is None:
        return False
    return resolve_artifact_path(path_or_value).exists()


def resolve_artifact_path(path_or_value: Path | str) -> Path:
    path = Path(path_or_value)
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def artifact_status(path: Path, *, required_modules: tuple[str, ...] = OPTIONAL_ML_MODULES) -> str:
    if not path.exists():
        return "not_loaded"
    for module_name in required_modules:
        if importlib_util.find_spec(module_name) is None:
            return "dependency_missing"
    return "loaded"


def missing_optional_modules(
    required_modules: tuple[str, ...] = OPTIONAL_ML_MODULES,
) -> list[str]:
    return [
        module_name
        for module_name in required_modules
        if importlib_util.find_spec(module_name) is None
    ]


def build_feature_map(db: Session) -> dict[str, EventFeature]:
    features = db.scalars(
        select(EventFeature).order_by(EventFeature.created_at.desc(), EventFeature.id.desc())
    ).all()
    feature_map: dict[str, EventFeature] = {}
    for feature in features:
        feature_map.setdefault(feature.event_id, feature)
    return feature_map


def list_event_feature_bundles(db: Session) -> list[EventFeatureBundle]:
    feature_map = build_feature_map(db)
    events = db.scalars(select(Event).order_by(Event.start_datetime, Event.id)).all()
    return [EventFeatureBundle(event=event, feature=feature_map.get(event.id)) for event in events]


def build_priority_feature_row(event: Event, feature: EventFeature | None = None) -> dict[str, object]:
    event_hour = feature.event_hour if feature and feature.event_hour is not None else event.start_datetime.hour
    event_weekday = (
        feature.event_weekday
        if feature and feature.event_weekday is not None
        else event.start_datetime.weekday()
    )
    return {
        "event_type": event.event_type or "unplanned",
        "event_cause_clean": event.event_cause_clean or "unknown",
        "corridor": event.corridor or "unknown",
        "police_station": event.police_station or "unknown",
        "event_hour": event_hour,
        "event_weekday": event_weekday,
        "is_peak_hour": peak_hour_flag(event_hour),
        "historical_corridor_risk": safe_float(feature.historical_corridor_risk if feature else None),
        "historical_police_station_risk": safe_float(feature.historical_police_station_risk if feature else None),
    }


def build_road_closure_feature_row(event: Event, feature: EventFeature | None = None) -> dict[str, object]:
    base = build_priority_feature_row(event, feature)
    base.update(
        {
            "priority": event.priority or "Low",
            "historical_cluster_risk": safe_float(feature.historical_cluster_risk if feature else None),
            "historical_cause_closure_rate": safe_float(
                feature.historical_cause_closure_rate if feature else None
            ),
            "historical_corridor_closure_rate": safe_float(
                feature.historical_corridor_closure_rate if feature else None
            ),
            "historical_police_station_closure_rate": safe_float(
                feature.historical_police_station_closure_rate if feature else None
            ),
            "historical_cluster_closure_rate": safe_float(
                feature.historical_cluster_closure_rate if feature else None
            ),
        }
    )
    return base


def build_resolution_time_feature_row(event: Event, feature: EventFeature | None = None) -> dict[str, object]:
    event_hour = feature.event_hour if feature and feature.event_hour is not None else event.start_datetime.hour
    event_weekday = (
        feature.event_weekday
        if feature and feature.event_weekday is not None
        else event.start_datetime.weekday()
    )
    return {
        "event_cause_clean": event.event_cause_clean or "unknown",
        "event_type": event.event_type or "unplanned",
        "corridor": event.corridor or "unknown",
        "police_station": event.police_station or "unknown",
        "priority": event.priority or "Low",
        "veh_type": event.veh_type or "unknown",
        "event_hour": event_hour,
        "event_weekday": event_weekday,
        "is_peak_hour": peak_hour_flag(event_hour),
        "historical_corridor_risk": safe_float(feature.historical_corridor_risk if feature else None),
    }


def reliable_clearance_timestamp(event: Event) -> datetime | None:
    start = event.start_datetime
    candidates = (event.resolved_datetime, event.closed_datetime)
    for candidate in candidates:
        if candidate is None:
            continue
        if candidate <= start:
            continue
        if candidate - start > timedelta(hours=24):
            continue
        return candidate
    return None


def reliable_clearance_minutes(event: Event) -> float | None:
    clearance_time = reliable_clearance_timestamp(event)
    if clearance_time is None:
        return None
    return round((clearance_time - event.start_datetime).total_seconds() / 60.0, 2)


def upsert_model_run(
    db: Session,
    *,
    model_name: str,
    model_version: str,
    target_variable: str,
    training_rows: int,
    test_rows: int,
    metrics_json: dict[str, object],
    feature_list_json: list[str],
    artifact_path: str | None,
    commit: bool = True,
) -> ModelRun:
    record = db.scalars(
        select(ModelRun)
        .where(ModelRun.model_name == model_name, ModelRun.model_version == model_version)
        .order_by(ModelRun.created_at.desc(), ModelRun.id.desc())
    ).first()
    if record is None:
        record = ModelRun(
            model_name=model_name,
            model_version=model_version,
            target_variable=target_variable,
            training_rows=training_rows,
            test_rows=test_rows,
            metrics_json=metrics_json,
            feature_list_json=feature_list_json,
            artifact_path=artifact_path,
        )
        db.add(record)
    else:
        record.target_variable = target_variable
        record.training_rows = training_rows
        record.test_rows = test_rows
        record.metrics_json = metrics_json
        record.feature_list_json = feature_list_json
        record.artifact_path = artifact_path

    if commit:
        db.commit()
        db.refresh(record)
    else:
        db.flush()
    return record


def latest_model_run(db: Session, model_name: str) -> ModelRun | None:
    return db.scalars(
        select(ModelRun)
        .where(ModelRun.model_name == model_name)
        .order_by(ModelRun.created_at.desc(), ModelRun.id.desc())
    ).first()


def serialize_model_run(record: ModelRun) -> dict[str, object]:
    artifact_path = resolve_artifact_path(record.artifact_path) if record.artifact_path else None
    return {
        "id": str(record.id),
        "model_name": record.model_name,
        "model_version": record.model_version,
        "target_variable": record.target_variable,
        "training_rows": record.training_rows,
        "test_rows": record.test_rows,
        "metrics_json": dict(record.metrics_json or {}),
        "feature_list_json": list(record.feature_list_json or []),
        "artifact_path": record.artifact_path,
        "artifact_available": artifact_exists(record.artifact_path),
        "artifact_status": artifact_status(artifact_path) if artifact_path is not None else "not_loaded",
        "created_at": record.created_at,
    }
