from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import sessionmaker

from app.core.database import build_engine
from app.db.base import Base, import_model_modules
from app.orm.event import Event
from app.services import road_closure_scoring_service
from app.services.feature_engineering_service import rebuild_event_features


def _build_session_factory(tmp_path, name: str):
    engine = build_engine(f"sqlite:///{tmp_path / name}")
    import_model_modules()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def test_estimate_road_closure_likelihood_uses_rule_history_when_model_missing(tmp_path, monkeypatch):
    session_factory = _build_session_factory(tmp_path, "road-closure.db")
    monkeypatch.setattr(
        road_closure_scoring_service,
        "ROAD_CLOSURE_MODEL_PATH",
        tmp_path / "missing-road-closure.joblib",
    )

    with session_factory() as session:
        start = datetime(2026, 6, 20, 9, 15, tzinfo=timezone.utc)
        session.add_all(
            [
                Event(
                    id="RC-001",
                    event_type="planned",
                    latitude=12.9716,
                    longitude=77.5946,
                    event_cause_clean="construction",
                    requires_road_closure=True,
                    start_datetime=start,
                    description_language="en",
                    priority="High",
                    corridor="Outer Ring Road",
                    police_station="Bellandur",
                    zone="South East",
                    junction="Marathahalli",
                ),
                Event(
                    id="RC-002",
                    event_type="planned",
                    latitude=12.9718,
                    longitude=77.5948,
                    event_cause_clean="construction",
                    requires_road_closure=True,
                    start_datetime=start,
                    description_language="en",
                    priority="High",
                    corridor="Outer Ring Road",
                    police_station="Bellandur",
                    zone="South East",
                    junction="Marathahalli",
                ),
                Event(
                    id="RC-003",
                    event_type="unplanned",
                    latitude=12.9730,
                    longitude=77.5960,
                    event_cause_clean="vehicle_breakdown",
                    requires_road_closure=False,
                    start_datetime=start,
                    description_language="en",
                    priority="Low",
                    corridor="Airport Road",
                    police_station="HAL",
                    zone="East",
                    junction="Domlur",
                ),
            ]
        )
        session.commit()
        rebuild_event_features(session)

        event = session.get(Event, "RC-001")
        feature = event.features[0]
        result = road_closure_scoring_service.estimate_road_closure_likelihood(
            session,
            event,
            feature=feature,
        )

        assert result["method"] == "primary_rule_history"
        assert result["predicted_road_closure"] is True
        assert float(result["road_closure_probability"]) > 0.5
        assert "dataset_positive_rate" in " ".join(result["reasons"])
        assert "planned_event" in result["reasons"]
        assert "high_priority" in result["reasons"]
        assert "estimated likelihood" in str(result["dataset_warning"])
