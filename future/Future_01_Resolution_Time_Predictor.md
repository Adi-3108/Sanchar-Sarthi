# FUTURE 01 â€” Resolution Time Predictor

## Overview

Expose a dedicated resolution-time prediction endpoint and a judge-friendly UI card by reusing the canonical Phase 07 clearance estimator.

This future enhancement does **not** introduce a second competing model, artifact path, or training pipeline. It wraps the existing Phase 07 resolution-time contract in a standalone API and dashboard component for easier demos and external integrations.

---

## Why This Exists

- Judges and operators naturally ask: "How long will this disruption last?"
- Phase 07 already defines the canonical dataset-backed clearance estimator and optional ML artifact.
- A dedicated endpoint and UI panel make that intelligence easier to consume without fragmenting the model architecture.

---

## Canonical Reuse Rule

Future 01 must reuse the existing Phase 07 resolution-time stack:

- training script: `backend/app/ml/train_resolution_time_model.py`
- inference service: `backend/app/services/resolution_time_service.py`
- thin inference wrapper: `backend/app/ml/inference_resolution_time.py`
- artifact path: `backend/artifacts/resolution_time_model.joblib`
- fallback logic: Phase 07 rule/history estimate when the ML artifact is absent or training is skipped

Do **not** introduce:

- a second artifact such as `backend/models/resolution_time_regressor.pkl`
- a second training script
- alternate feature names such as `breakdown_category`, `location_latitude`, or `location_longitude`
- a different algorithm contract that competes with the existing Phase 07 estimator

---

## Expected Outcome

After completion:

- **New functionality:** dedicated resolution-time prediction API and reusable dashboard card
- **New APIs:** `POST /api/predict/resolution-time`
- **New workflows:** command-center and demo surfaces can ask for a standalone clearance estimate without manually parsing the full event dossier
- **New infrastructure:** `backend/app/api/routes_predict_resolution.py`; `backend/app/schemas/resolution_prediction.py`; `frontend/components/recommendations/ResolutionTimePredictor.tsx`; `frontend/lib/hooks/useResolutionPrediction.ts`
- **New data models:** none required for MVP; optional audit log only if explicitly added later

---

## Request/Response Contract

### Request

Use real schema names consistent with the dataset and Phase 07 service:

```json
{
  "event_type": "unplanned",
  "event_cause_clean": "vehicle_breakdown",
  "corridor": "Tumkur Road",
  "police_station": "Peenya",
  "priority": "High",
  "veh_type": "truck",
  "latitude": 13.0400,
  "longitude": 77.5181,
  "start_datetime": "2026-06-18T18:00:00Z"
}
```

### Response

The endpoint should mirror Phase 07 output fields:

```json
{
  "estimated_clearance_minutes": 94.0,
  "clearance_prediction_method": "ml_gradient_boosting",
  "clearance_confidence": 0.75,
  "clearance_confidence_note": "Based on qualifying ASTraM incidents with reliable clearance timestamps.",
  "historical_clearance_range_min": 66.0,
  "historical_clearance_range_max": 126.0,
  "honesty_label": "Estimated clearance time, not a guaranteed operational commitment."
}
```

---

## Repository Paths

- `backend/app/api/routes_predict_resolution.py`
- `backend/app/schemas/resolution_prediction.py`
- `frontend/components/recommendations/ResolutionTimePredictor.tsx`
- `frontend/lib/hooks/useResolutionPrediction.ts`

---

## Implementation Notes

### `backend/app/schemas/resolution_prediction.py`

```python
from datetime import datetime
from pydantic import BaseModel, Field


class ResolutionPredictionRequest(BaseModel):
    event_type: str | None = None
    event_cause_clean: str | None = None
    corridor: str | None = None
    police_station: str | None = None
    priority: str | None = None
    veh_type: str | None = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    start_datetime: datetime


class ResolutionPredictionResponse(BaseModel):
    estimated_clearance_minutes: float
    clearance_prediction_method: str
    clearance_confidence: float
    clearance_confidence_note: str
    historical_clearance_range_min: float
    historical_clearance_range_max: float
    honesty_label: str
```

### `backend/app/api/routes_predict_resolution.py`

```python
from datetime import timezone

from fastapi import APIRouter

from app.orm.event import Event
from app.schemas.resolution_prediction import (
    ResolutionPredictionRequest,
    ResolutionPredictionResponse,
)
from app.services.resolution_time_service import predict_resolution_time

router = APIRouter(prefix="/api/predict", tags=["prediction"])


@router.post("/resolution-time", response_model=ResolutionPredictionResponse)
def predict_resolution_time_endpoint(payload: ResolutionPredictionRequest) -> ResolutionPredictionResponse:
    transient_event = Event(
        id="TRANSIENT-RESOLUTION-PREDICTION",
        event_type=payload.event_type,
        event_cause_clean=payload.event_cause_clean,
        corridor=payload.corridor,
        police_station=payload.police_station,
        priority=payload.priority,
        veh_type=payload.veh_type,
        latitude=payload.latitude,
        longitude=payload.longitude,
        requires_road_closure=False,
        start_datetime=payload.start_datetime.astimezone(timezone.utc),
        description_language="unknown",
    )
    result = predict_resolution_time(transient_event)
    return ResolutionPredictionResponse(**result)
```

### Frontend Contract

The frontend card should:

- call `POST /api/predict/resolution-time`
- render estimated minutes plus range and confidence
- show the Phase 07 honesty label verbatim
- avoid claiming exact resolution time

---

## Database Requirements

- No new required table.
- Read-only dependency on the existing `events`/`event_features`/`model_runs` ecosystem from Phase 07.
- Optional prediction audit logging is allowed only if it does not create a second model registry.

---

## Dependencies

- Required previous phase: `Phase_07.md`
- Recommended UI integration phase: `Phase_15.md`

---

## Validation

```bash
pytest backend/tests/test_resolution_time.py
npm run build
```

Success criteria:

- the endpoint returns the same contract as Phase 07
- no second model artifact or training script is introduced
- the UI uses dataset-honest wording
