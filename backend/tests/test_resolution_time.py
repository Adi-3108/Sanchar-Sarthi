from __future__ import annotations

from datetime import datetime, timezone

from app.orm.event import Event
from app.services import resolution_time_service


def test_predict_resolution_time_uses_rule_fallback_with_vehicle_alias(tmp_path, monkeypatch):
    monkeypatch.setattr(
        resolution_time_service,
        "RESOLUTION_TIME_MODEL_PATH",
        tmp_path / "missing-resolution-time.joblib",
    )
    event = Event(
        id="RT-001",
        event_type="unplanned",
        latitude=12.9716,
        longitude=77.5946,
        event_cause_clean="vehicle_breakdown",
        requires_road_closure=False,
        start_datetime=datetime(2026, 6, 20, 8, 30, tzinfo=timezone.utc),
        description_language="en",
        veh_type="Mini Truck",
        priority="High",
    )

    result = resolution_time_service.predict_resolution_time(event)

    assert result["clearance_prediction_method"] == "rule_fallback"
    assert float(result["estimated_clearance_minutes"]) == 108.0
    assert float(result["historical_clearance_range_min"]) == 54.0
    assert float(result["historical_clearance_range_max"]) == 144.0
    assert float(result["clearance_confidence"]) == 0.45
    assert "Rule-based estimate" in str(result["clearance_confidence_note"])
    assert result["data_filter_applied"] == "resolved_datetime within 24h, else closed_datetime within 24h"
