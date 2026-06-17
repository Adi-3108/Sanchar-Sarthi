from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.api import routes_events
from app.core.database import build_engine
from app.core.security import AuthContext
from app.db.base import Base, import_model_modules
from app.db.session import get_db
from app.main import app
from app.orm.event import Event
from app.orm.event_prediction import EventPrediction
from app.orm.model_run import ModelRun
from app.orm.user_account import UserAccount
from app.services import prediction_service, resolution_time_service, road_closure_scoring_service
from app.services.feature_engineering_service import build_features_for_event


def _build_session_factory(tmp_path, name: str):
    engine = build_engine(f"sqlite:///{tmp_path / name}")
    import_model_modules()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _seed_prediction_events(session) -> None:
    start = datetime(2026, 6, 21, 8, 0, tzinfo=timezone.utc)
    session.add_all(
        [
            Event(
                id="PRED-001",
                event_type="unplanned",
                latitude=12.9716,
                longitude=77.5946,
                event_cause_clean="vehicle_breakdown",
                requires_road_closure=True,
                start_datetime=start,
                description_language="en",
                description_for_features="vehicle breakdown at major junction",
                description_normalization_method="raw_ascii",
                priority="High",
                corridor="Central Spine",
                police_station="Ashok Nagar",
                zone="Central",
                junction="MG Road",
                veh_type="Truck",
            ),
            Event(
                id="PRED-002",
                event_type="unplanned",
                latitude=12.9720,
                longitude=77.5950,
                event_cause_clean="vehicle_breakdown",
                requires_road_closure=False,
                start_datetime=start + timedelta(minutes=10),
                description_language="en",
                description_for_features="disabled truck near corridor",
                description_normalization_method="raw_ascii",
                priority="Low",
                corridor="Central Spine",
                police_station="Ashok Nagar",
                zone="Central",
                junction="MG Road",
                veh_type="Truck",
            ),
        ]
    )
    session.commit()


def test_predict_event_persists_single_rule_fallback_prediction(tmp_path, monkeypatch):
    session_factory = _build_session_factory(tmp_path, "predictions.db")
    monkeypatch.setattr(prediction_service, "PRIORITY_MODEL_PATH", tmp_path / "missing-priority.joblib")
    monkeypatch.setattr(
        road_closure_scoring_service,
        "ROAD_CLOSURE_MODEL_PATH",
        tmp_path / "missing-road-closure.joblib",
    )
    monkeypatch.setattr(
        resolution_time_service,
        "RESOLUTION_TIME_MODEL_PATH",
        tmp_path / "missing-resolution.joblib",
    )

    with session_factory() as session:
        _seed_prediction_events(session)
        event = session.get(Event, "PRED-001")
        feature, _created = build_features_for_event(session, event)

        record, created = prediction_service.predict_event(session, event, feature=feature)
        assert created is True
        assert record.predicted_priority in {"High", "Low"}
        assert float(record.priority_confidence) > 0.0
        assert record.clearance_prediction_method == "rule_fallback"
        assert record.prediction_explanation_json["priority"]["method"] == "rule_fallback"
        assert record.prediction_explanation_json["road_closure"]["method"] == "primary_rule_history"
        assert record.prediction_explanation_json["resolution_time"]["data_filter_applied"]

        record_again, created_again = prediction_service.predict_event(session, event, feature=feature)
        assert created_again is False
        assert record_again.id == record.id
        assert session.query(EventPrediction).filter(EventPrediction.event_id == "PRED-001").count() == 1


def test_event_detail_route_includes_prediction_payload(tmp_path, monkeypatch):
    session_factory = _build_session_factory(tmp_path, "predictions-route.db")
    actor_id = uuid4()
    monkeypatch.setattr(prediction_service, "PRIORITY_MODEL_PATH", tmp_path / "missing-priority.joblib")
    monkeypatch.setattr(
        road_closure_scoring_service,
        "ROAD_CLOSURE_MODEL_PATH",
        tmp_path / "missing-road-closure.joblib",
    )
    monkeypatch.setattr(
        resolution_time_service,
        "RESOLUTION_TIME_MODEL_PATH",
        tmp_path / "missing-resolution.joblib",
    )

    with session_factory() as session:
        _seed_prediction_events(session)
        session.add(
            UserAccount(
                id=actor_id,
                role="admin",
                display_name="Prediction Admin",
                auth_provider="firebase",
                auth_provider_uid="firebase-admin-prediction",
                is_active=True,
            )
        )
        session.commit()

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[routes_events.require_internal_event_access] = lambda: AuthContext(
        firebase_uid="firebase-admin-prediction",
        email="admin@example.com",
        role="admin",
        user_account_id=str(actor_id),
    )

    try:
        with TestClient(app) as client:
            response = client.get("/api/events/PRED-001")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["prediction"]["event_id"] == "PRED-001"
    assert payload["prediction"]["predicted_priority"] in {"High", "Low"}
    assert payload["prediction"]["clearance_prediction_method"] == "rule_fallback"
    assert payload["prediction"]["prediction_explanation_json"]["road_closure"]["method"] == "primary_rule_history"


def test_model_runs_endpoint_returns_latest_run_per_model(tmp_path):
    session_factory = _build_session_factory(tmp_path, "model-runs-route.db")

    with session_factory() as session:
        session.add_all(
            [
                ModelRun(
                    model_name="priority_model",
                    model_version="priority_rf_v1",
                    target_variable="priority_high",
                    training_rows=100,
                    test_rows=20,
                    metrics_json={"status": "trained", "f1": 0.82},
                    feature_list_json=["event_type", "corridor"],
                    artifact_path="backend/artifacts/priority_model.joblib",
                ),
                ModelRun(
                    model_name="road_closure_model",
                    model_version="road_closure_support_v1",
                    target_variable="requires_road_closure_true",
                    training_rows=120,
                    test_rows=24,
                    metrics_json={"status": "trained", "pr_auc": 0.41},
                    feature_list_json=["event_type", "priority"],
                    artifact_path="backend/artifacts/road_closure_model.joblib",
                ),
            ]
        )
        session.commit()

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            response = client.get("/api/analytics/model-runs")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["model_runs"]) == 2
    assert {row["model_name"] for row in payload["model_runs"]} == {
        "priority_model",
        "road_closure_model",
    }
