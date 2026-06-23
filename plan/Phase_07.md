# PHASE 7 â€” AI ML Prediction Models

## Phase Overview

Train and serve urgency and road-closure likelihood models.

This phase is part of EventFlow AI, a predictive traffic command twin for Bengaluru event-driven congestion. The project uses ASTraM historical event data, FastAPI, Next.js, Supabase PostgreSQL free tier, explainable AI/rule-based planning, MapmyIndia/Mappls primary integration using available 1000 INR credits, Mappls-only map policy, and only free/open-source APIs or services.

---

## Why This Phase Exists

- **Problem being solved:** Train and serve urgency and road-closure likelihood models.
- **User need addressed:** Traffic operators, planners, field officers, citizens, delivery stakeholders, and judges need a reliable implementation step that advances the Predict -> Plan -> Monitor -> Adapt -> Learn workflow.
- **Business requirement satisfied:** This phase supports a complete Flipkart Gridlock 2.0 prototype that demonstrates feasibility, innovation, scalability, security, user experience, and real-world impact.
- **Why now:** This phase depends on Phase 04 and must exist before Impact score and recommendations.
- **How it contributes:** It strengthens EventFlow AI as an operational command system rather than a generic dashboard.

---

## Original Intent Preservation

### Original Problem

Bengaluru event-driven congestion needs data-backed planning for impact, manpower, barricading, diversions, live escalation, and post-event learning.

### User Pain Point

Traffic response is often reactive, delayed, and experience-driven. Users need explainable, map-first, action-oriented intelligence.

### Product Goal

Deliver this capability: Train and serve urgency and road-closure likelihood models.

### Architecture Goal

Maintain backend-owned business logic, frontend-only rendering/API consumption, database persistence through Supabase PostgreSQL, and map provider independence.

### Security Goal

Protect sensitive ASTraM fields, avoid frontend database credentials, enforce three-level access, validate all inputs, rate-limit risky endpoints, and prevent untrusted reports from becoming official automatically.

### Scalability Goal

Keep this phase modular so future phases and production integrations can extend it without breaking contracts.

### Performance Goal

Support MVP targets: dashboard under 5 seconds, simulation under 3 seconds, event-plan generation under 5 seconds, map layer toggles under 2 seconds, and CSV processing under 30 seconds where applicable.

---

## Expected Outcome

After completion:

- **New functionality:** Train and serve urgency and road-closure likelihood models.
- **New APIs:** Predictions included in simulation/detail responses
- **New workflows:** The product moves forward in the end-to-end traffic command workflow.
- **New capabilities:** Impact score and recommendations
- **New infrastructure:** backend/app/ml/feature_pipeline.py; backend/app/ml/train_priority_model.py; backend/app/ml/train_road_closure_model.py; backend/app/ml/train_resolution_time_model.py; backend/app/ml/inference_resolution_time.py; backend/app/services/road_closure_scoring_service.py; backend/app/services/prediction_service.py; backend/app/services/resolution_time_service.py; frontend/app/model-insights/page.tsx
- **New data models:** model_runs, event_predictions

---

## Full Implementation Requirements

Implementation agents must create executable production-ready source files for every path listed in this phase.

Required implementation standards:

- Complete imports, classes, interfaces, functions, DTOs, models, controllers, services, repositories, middleware, tests, and configuration must be written by the implementation agent.
- No paid APIs may be introduced.
- No placeholder or TODO code may be committed.
- All code must be directly executable in the repository.
- All outputs must preserve EventFlow AI's dataset-honest wording: Dataset-backed, Predicted, Estimated, Recommended, Simulated, or Future integration.

### Exact Repository Paths For This Phase

- backend/app/ml/feature_pipeline.py
- backend/app/ml/train_priority_model.py
- backend/app/ml/train_road_closure_model.py
- backend/app/ml/train_resolution_time_model.py
- backend/app/ml/inference_resolution_time.py
- backend/app/services/road_closure_scoring_service.py
- backend/app/services/prediction_service.py
- backend/app/services/resolution_time_service.py
- frontend/app/model-insights/page.tsx


## Implementation Code Snippets

### Dataset-Specific Road-Closure Decision

The uploaded ASTraM CSV has `676 / 8173` road-closure TRUE rows, about `8.27%`. Because the positive class is sparse, the MVP must not present a standalone road-closure classifier as the primary source of truth.

Implementation rule:

- Primary output: explainable rule/history road-closure score.
- Supporting output: optional class-weighted ML probability if the model artifact exists and metrics are acceptable.
- UI label: "Estimated road-closure likelihood".
- `predicted_road_closure` is a heuristic operational flag derived from the probability, not the primary truth signal.
- Model Insights must show positive sample count, positive rate, PR-AUC, recall for TRUE, and the fact that rules remain active even when ML is available.
- Model Insights should also make it clear that the current MVP uses dataset-wide historical aggregates, so reported metrics are prototype diagnostics rather than leakage-free production validation.

### Dataset-Specific Priority Contract

The uploaded ASTraM CSV currently has only `High` and `Low` values in `events.priority`.  
For MVP consistency:

- `predicted_priority` remains a dataset-backed two-level output: `High` or `Low`.
- Probability/confidence carries the nuance; do not invent `Medium` for the priority field.
- The four-level `Low` / `Medium` / `High` / `Critical` vocabulary belongs to `impact_category`, not to the raw ASTraM priority label.

### `backend/app/ml/train_priority_model.py`
```python
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sqlalchemy import create_engine, text
from app.core.config import get_settings

MODEL_PATH = 'backend/artifacts/priority_model.joblib'

QUERY = text('''
SELECT e.event_type, e.event_cause_clean, e.corridor, e.police_station, e.priority,
       f.event_hour, f.event_weekday, f.is_peak_hour,
       f.historical_corridor_risk, f.historical_police_station_risk
FROM events e JOIN event_features f ON f.event_id = e.id
WHERE e.priority IS NOT NULL
''')

def train() -> dict[str, float]:
    engine = create_engine(get_settings().database_url)
    frame = pd.read_sql(QUERY, engine)
    if frame.empty:
        raise RuntimeError('No training rows available. Run Phase 03 and Phase 04 first.')

    y = frame['priority'].str.lower().eq('high').astype(int)
    if y.nunique() < 2:
        raise RuntimeError('Priority model needs both high and low examples. Use the rule fallback until data is richer.')
    x = frame.drop(columns=['priority'])
    categorical = ['event_type', 'event_cause_clean', 'corridor', 'police_station']
    numeric = ['event_hour', 'event_weekday', 'historical_corridor_risk', 'historical_police_station_risk']

    pipeline = Pipeline([
        ('features', ColumnTransformer([
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical),
            ('num', StandardScaler(), numeric),
        ], remainder='drop')),
        ('model', RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42)),
    ])
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42, stratify=y)
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    metrics = {'f1': float(f1_score(y_test, predictions, zero_division=0))}
    print(classification_report(y_test, predictions, zero_division=0))
    joblib.dump({'pipeline': pipeline, 'metrics': metrics}, MODEL_PATH)
    return metrics

if __name__ == '__main__':
    print(train())
```

### `backend/app/services/road_closure_scoring_service.py`
```python
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.orm.event import Event

def _rate(db: Session, column_name: str, value: str | None) -> float | None:
    if not value:
        return None
    column = getattr(Event, column_name)
    total = db.scalar(select(func.count()).where(column == value)) or 0
    if total == 0:
        return None
    closed = db.scalar(select(func.count()).where(column == value, Event.requires_road_closure.is_(True))) or 0
    return closed / total

def estimate_road_closure_likelihood(db: Session, event: Event, optional_ml_probability: float | None = None) -> dict[str, object]:
    cause_rate = _rate(db, 'event_cause_clean', event.event_cause_clean)
    corridor_rate = _rate(db, 'corridor', event.corridor)
    station_rate = _rate(db, 'police_station', event.police_station)

    score = 0.08
    reasons = ['dataset_positive_rate:0.0827']
    for label, rate, weight in [
        ('cause_history', cause_rate, 0.35),
        ('corridor_history', corridor_rate, 0.25),
        ('station_history', station_rate, 0.15),
    ]:
        if rate is not None:
            score += rate * weight
            reasons.append(f'{label}:{rate:.3f}')

    if (event.priority or '').lower() == 'high':
        score += 0.12
        reasons.append('high_priority')
    if event.event_type == 'planned':
        score += 0.08
        reasons.append('planned_event')

    if optional_ml_probability is not None:
        score = (0.75 * score) + (0.25 * optional_ml_probability)
        reasons.append(f'ml_supporting_signal:{optional_ml_probability:.3f}')

    return {
        'road_closure_probability': round(min(max(score, 0.0), 1.0), 4),
        'method': 'primary_rule_history_with_optional_ml_support',
        'reasons': reasons,
        'dataset_warning': 'requires_road_closure TRUE is sparse; use as estimated likelihood, not exact prediction',
    }
```

### `backend/app/services/prediction_service.py`
```python
import joblib
import pandas as pd
from pathlib import Path
from sqlalchemy.orm import Session
from app.orm.event import Event
from app.orm.event_prediction import EventPrediction
from app.services.road_closure_scoring_service import estimate_road_closure_likelihood

PRIORITY_MODEL_PATH = Path('backend/artifacts/priority_model.joblib')

def _fallback_urgency(event: Event) -> float:
    score = 0.35
    if (event.priority or '').lower() == 'high':
        score += 0.3
    if event.requires_road_closure:
        score += 0.2
    if event.event_type == 'unplanned':
        score += 0.1
    return min(score, 1.0)

def predict_event(db: Session, event: Event) -> EventPrediction:
    ml_urgency_probability = None
    if PRIORITY_MODEL_PATH.exists():
        bundle = joblib.load(PRIORITY_MODEL_PATH)
        feature_row = {
            'event_type': event.event_type,
            'event_cause_clean': event.event_cause_clean,
            'corridor': event.corridor,
            'police_station': event.police_station,
            'event_hour': event.start_datetime.hour,
            'event_weekday': event.start_datetime.weekday(),
            'historical_corridor_risk': 0.0,  # Will be joined from event_features in full implementation
            'historical_police_station_risk': 0.0,  # Will be joined from event_features in full implementation
        }
        urgency = float(bundle['pipeline'].predict_proba(pd.DataFrame([feature_row]))[0][1])
        ml_urgency_probability = urgency
        explanation = {'model': 'priority_model', 'dataset_honesty': 'Predicted urgency, not exact delay'}
    else:
        urgency = _fallback_urgency(event)
        explanation = {'model': 'rule_fallback', 'dataset_honesty': 'Estimated from available ASTraM fields'}

    closure = estimate_road_closure_likelihood(db, event, optional_ml_probability=None)
    predicted_priority = 'High' if urgency >= 0.5 else 'Low'
    road_closure_probability = float(closure['road_closure_probability'])

    record = EventPrediction(
        event_id=event.id,
        predicted_priority=predicted_priority,
        priority_confidence=round(urgency, 4),
        road_closure_probability=round(road_closure_probability, 4),
        predicted_road_closure=road_closure_probability >= 0.5,
        prediction_explanation_json={**explanation, 'road_closure': closure, 'ml_urgency_probability': ml_urgency_probability},
        model_version='priority_v1_rule_or_joblib',
    )
    db.add(record)
    db.commit()
    return record
```

### Dataset-Specific: Resolution Time Predictor

**Why this is a differentiating feature:** The ASTraM dataset contains `start_datetime`, `closed_datetime`, and `resolved_datetime`. After filtering out administrative long-tail closures, these allow estimating *how long* an incident will disrupt traffic â€” a number directly missing from existing traffic systems.

**Critical data quality filter (mandatory):**

Not all rows with `closed_datetime` or `resolved_datetime` reflect actual operational clearance times. Many rows have missing or long-tail administrative close timestamps. Use only timestamps that are after `start_datetime` and within 24 hours. Prefer `resolved_datetime` when valid; otherwise use `closed_datetime` when valid.

```sql
-- Only use these rows for training:
SELECT * FROM events
WHERE (
    resolved_datetime IS NOT NULL
    AND resolved_datetime - start_datetime < INTERVAL '24 hours'
    AND resolved_datetime - start_datetime > INTERVAL '0 minutes'
  )
  OR (
    closed_datetime IS NOT NULL
    AND closed_datetime - start_datetime < INTERVAL '24 hours'
    AND closed_datetime - start_datetime > INTERVAL '0 minutes'
  );
```

Dataset audit on the provided CSV showed only `71` valid `resolved_datetime` rows under 24 hours, but about `2467` valid `closed_datetime` rows under 24 hours. Therefore the model must use the reliable timestamp chain above, not `resolved_datetime` alone. If fewer than 200 rows survive this filter on a future dataset, skip ML training and fall back to rule-based estimates only.

### `backend/app/ml/train_resolution_time_model.py`
```python
import joblib
import pandas as pd
from pathlib import Path
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sqlalchemy import create_engine, text
from app.core.config import get_settings

MODEL_PATH = Path('backend/artifacts/resolution_time_model.joblib')
MIN_TRAINING_ROWS = 200  # Do not train if fewer rows survive the quality filter

QUERY = text('''
WITH clearance_rows AS (
  SELECT
    e.*,
    CASE
      WHEN e.resolved_datetime IS NOT NULL
       AND e.resolved_datetime - e.start_datetime < INTERVAL '24 hours'
       AND e.resolved_datetime - e.start_datetime > INTERVAL '0 minutes'
      THEN e.resolved_datetime
      WHEN e.closed_datetime IS NOT NULL
       AND e.closed_datetime - e.start_datetime < INTERVAL '24 hours'
       AND e.closed_datetime - e.start_datetime > INTERVAL '0 minutes'
      THEN e.closed_datetime
      ELSE NULL
    END AS reliable_clearance_datetime
  FROM events e
)
SELECT
    c.event_cause_clean,
    c.event_type,
    c.corridor,
    c.police_station,
    c.priority,
    c.veh_type,
    f.event_hour,
    f.event_weekday,
    f.is_peak_hour,
    f.historical_corridor_risk,
    EXTRACT(EPOCH FROM (c.reliable_clearance_datetime - c.start_datetime)) / 60 AS resolution_minutes
FROM clearance_rows c
JOIN event_features f ON f.event_id = c.id
WHERE c.reliable_clearance_datetime IS NOT NULL
''')

def train() -> dict[str, float] | None:
    engine = create_engine(get_settings().database_url)
    frame = pd.read_sql(QUERY, engine)

    if len(frame) < MIN_TRAINING_ROWS:
        print(f'[resolution_time_model] Only {len(frame)} qualifying rows. Skipping ML training. Rule fallback will be used.')
        return None

    y = frame['resolution_minutes']
    x = frame.drop(columns=['resolution_minutes'])

    categorical = ['event_cause_clean', 'event_type', 'corridor', 'police_station', 'priority', 'veh_type']
    numeric = ['event_hour', 'event_weekday', 'historical_corridor_risk']
    binary = ['is_peak_hour']

    pipeline = Pipeline([
        ('features', ColumnTransformer([
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical),
            ('num', StandardScaler(), numeric + binary),
        ], remainder='drop')),
        ('model', GradientBoostingRegressor(n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42)),
    ])

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)

    metrics = {
        'mae_minutes': float(mean_absolute_error(y_test, predictions)),
        'r2_score': float(r2_score(y_test, predictions)),
        'training_rows': len(x_train),
        'test_rows': len(x_test),
        'data_filter': 'resolved_datetime within 24h, else closed_datetime within 24h',
    }
    print(f'[resolution_time_model] MAE: {metrics["mae_minutes"]:.1f} min | R2: {metrics["r2_score"]:.3f} | Rows: {len(frame)}')
    joblib.dump({'pipeline': pipeline, 'metrics': metrics}, MODEL_PATH)
    return metrics

if __name__ == '__main__':
    result = train()
    if result:
        print(result)
    else:
        print('Training skipped: insufficient qualifying rows. Rule fallback active.')
```

### `backend/app/ml/inference_resolution_time.py`
```python
from app.orm.event import Event
from app.services.resolution_time_service import predict_resolution_time


def infer_resolution_time(event: Event) -> dict[str, object]:
    """
    Thin ML-folder inference wrapper used by model_registry/model-insights.
    Service logic remains in resolution_time_service.py so API handlers use one source of truth.
    """
    return predict_resolution_time(event)
```

### `backend/app/services/resolution_time_service.py`
```python
import joblib
import pandas as pd
from pathlib import Path
from sqlalchemy.orm import Session
from app.orm.event import Event

MODEL_PATH = Path('backend/artifacts/resolution_time_model.joblib')

# Rule-based fallback estimates (median minutes per cause type from ASTraM patterns).
# Used when ML model artifact is absent or training data was insufficient.
RULE_BASED_ESTIMATES: dict[str, float] = {
    'vehicle_breakdown': 90.0,
    'accident': 110.0,
    'tree_fall': 180.0,
    'water_logging': 240.0,
    'construction': 480.0,
    'public_event': 300.0,
    'congestion': 60.0,
    'pot_holes': 360.0,
    'road_conditions': 240.0,
    'others': 90.0,
    'unknown': 90.0,
}

RULE_BASED_RANGES: dict[str, tuple[float, float]] = {
    'vehicle_breakdown': (45.0, 120.0),
    'accident': (60.0, 150.0),
    'tree_fall': (90.0, 300.0),
    'water_logging': (120.0, 360.0),
    'construction': (180.0, 600.0),
    'public_event': (120.0, 480.0),
    'congestion': (30.0, 120.0),
    'pot_holes': (120.0, 480.0),
    'road_conditions': (90.0, 360.0),
    'others': (45.0, 180.0),
    'unknown': (45.0, 180.0),
}

# Vehicle-type adjustment on top of cause-based estimate.
# Larger vehicles take longer to clear regardless of cause.
VEHICLE_TIME_ADJUSTMENT: dict[str, float] = {
    'bmtc_bus': 1.42,
    'truck': 1.42,
    'heavy_vehicle': 1.37,
    'private_bus': 1.36,
    'ksrtc_bus': 1.13,
    'lcv': 1.20,
    'private_car': 1.0,
    'auto': 0.93,
    'others': 1.22,
}


def _rule_estimate(event: Event) -> tuple[float, str]:
    base = RULE_BASED_ESTIMATES.get(event.event_cause_clean or 'unknown', 90.0)
    vehicle_factor = VEHICLE_TIME_ADJUSTMENT.get((event.veh_type or '').lower(), 1.0)
    estimate = round(base * vehicle_factor, 1)
    return estimate, 'rule_fallback'


def _rule_range(event: Event) -> tuple[float, float]:
    lower, upper = RULE_BASED_RANGES.get(event.event_cause_clean or 'unknown', RULE_BASED_RANGES['unknown'])
    vehicle_factor = VEHICLE_TIME_ADJUSTMENT.get((event.veh_type or '').lower(), 1.0)
    return round(lower * vehicle_factor, 1), round(upper * vehicle_factor, 1)


def predict_resolution_time(event: Event) -> dict[str, object]:
    """
    Returns estimated clearance time in minutes.
    Uses ML model if available; rule-based fallback otherwise.
    Always labels output honestly: 'Estimated clearance time, not guaranteed.'
    """
    if MODEL_PATH.exists():
        bundle = joblib.load(MODEL_PATH)
        feature_row = {
            'event_cause_clean': event.event_cause_clean,
            'event_type': event.event_type,
            'corridor': event.corridor,
            'police_station': event.police_station,
            'priority': event.priority,
            'veh_type': event.veh_type,
            'event_hour': event.start_datetime.hour,
            'event_weekday': event.start_datetime.weekday(),
            'is_peak_hour': event.start_datetime.hour in {8, 9, 10, 17, 18, 19, 20},
            'historical_corridor_risk': 0.0,  # Will be joined from event_features in full implementation
        }
        raw = float(bundle['pipeline'].predict(pd.DataFrame([feature_row]))[0])
        estimated_minutes = max(round(raw, 1), 1.0)
        mae = bundle['metrics'].get('mae_minutes', None)
        training_rows = bundle['metrics'].get('training_rows', 0)
        method = 'ml_gradient_boosting'
        confidence = 0.75 if training_rows >= 1000 else 0.6
        lower_bound = max(round(estimated_minutes - (mae or 30.0), 1), 1.0)
        upper_bound = round(estimated_minutes + (mae or 30.0), 1)
        confidence_note = f'Based on {training_rows} qualifying ASTraM incidents with reliable clearance timestamps'
        if mae:
            confidence_note += f'. Typical error margin: Â±{mae:.0f} min'
    else:
        estimated_minutes, method = _rule_estimate(event)
        confidence = 0.45
        lower_bound, upper_bound = _rule_range(event)
        confidence_note = 'Rule-based estimate from ASTraM cause/vehicle patterns'

    return {
        'estimated_clearance_minutes': estimated_minutes,
        'clearance_prediction_method': method,
        'clearance_confidence': confidence,
        'clearance_confidence_note': confidence_note,
        'historical_clearance_range_min': lower_bound,
        'historical_clearance_range_max': upper_bound,
        'honesty_label': 'Estimated clearance time â€” not a guaranteed operational commitment.',
        'data_filter_applied': 'resolved_datetime within 24h, else closed_datetime within 24h',
    }
```

`train_resolution_time_model.py` is **non-blocking**. If fewer than 200 qualifying rows exist, training is skipped and the rule-based service handles all requests. MVP completion must not depend on this model being trained.

Model Insights page must show:
- Training row count (after quality filter)
- MAE in minutes
- RÂ² score
- Data filter applied
- Rule fallback status (active or inactive)

---

## Database Requirements

- **Database entities affected:** model_runs, event_predictions
- **Migration requirements:** Create or reuse Alembic migrations when schema changes are required. If this phase only reads existing tables, no new migration is required.
- **SQL statements:** Use SQLAlchemy ORM and parameterized queries. Raw SQL is allowed only for safe analytics/materialized-view style operations.
- **Indexes:** Ensure referenced filters and joins are backed by indexes defined in docs/Database_Design.md.
- **Constraints and foreign keys:** Preserve relationships to events where relevant.
- **Composite indexes:** Add only for high-use filters such as event type + datetime, corridor + priority, report type + created_at.
- **RLS policies:** Not required in MVP because frontend never accesses Supabase directly.
- **Triggers/stored procedures/functions:** Not required in MVP unless explicitly introduced in implementation.
- **Materialized views:** Optional future optimization only.
- **Rollback migrations:** Any schema migration must include a downgrade path or explicit rollback notes.
- **Seed data:** Demo seed data belongs in Phase 17 unless this phase explicitly requires test fixtures.

---

## API Requirements

- **APIs affected:** Predictions included in simulation/detail responses
- **Route definitions:** Register under FastAPI /api routers.
- **Request schemas:** Define Pydantic v2 schemas for every body/query payload.
- **Response schemas:** Define typed response objects matching frontend needs.
- **Validation logic:** Validate coordinates, enums, dates, IDs, filters, pagination, text lengths, and file schemas where applicable.
- **Error handling:** Return structured errors with code, message, and details.
- **Authentication:** Enforce the three-level access model: Level 1 Admin / Control Room and Level 2 Registered Police Officer use Firebase Auth email/password with backend role and assignment checks; Level 3 Public / Citizen uses open rate-limited access.
- **Authorization:** Shape responses by access level: admin full internal view, assigned officer operational view, public-safe advisory/report view. Firebase identity must be verified on protected routes, while EventFlow roles and officer assignments remain enforced by FastAPI/PostgreSQL.
- **Rate limiting:** Apply to upload/report/simulation endpoints where relevant.
- **Audit logging:** Log dataset loads, admin actions, officer management, officer field confirmations, report submissions, simulations, live updates, post-event report generation, and model fallbacks without logging secret values.
- **OpenAPI:** FastAPI must expose OpenAPI definitions automatically from schemas.

---

## Frontend Requirements

- **Frontend scope:** /model-insights
- **Pages/components:** Create exact pages/components listed in repository paths.
- **Hooks:** Use typed API hooks with TanStack Query where remote data is fetched.
- **State management:** Use Zustand for selected event, active map layers, simulation state, filter state, and language where needed.
- **Forms:** Validate required fields before API calls.
- **API integrations:** Use frontend/lib/api.ts; never call Supabase directly.
- **Error states:** Backend unavailable, empty dataset, invalid input, provider failure.
- **Loading states:** Skeletons or progress states for every async panel.
- **Empty states:** No data, no recommendations, no reports, no map layers.
- **Permission handling:** Implement three UI access levels: admin/control-room portal, registered officer portal, and public/citizen portal. Frontend gating is UX only; backend authorization remains mandatory.
- **Routing:** Use Next.js App Router.

---

## Infrastructure Requirements

- **Dockerfiles:** Add or update only when the phase needs runtime packaging.
- **docker-compose:** Use for local development services if needed.
- **Kubernetes/Terraform:** Not required for MVP; document as future production option only.
- **CI/CD:** Add tests/build checks when implementation reaches deployable surfaces.
- **Environment configuration:** Add new environment variables to .env.example immediately.
- **Secrets configuration:** Store secrets only in backend or deployment provider secret stores.
- **Monitoring configuration:** Update health/status checks if this phase adds a critical dependency.
- **Logging configuration:** Structured logs for new backend operations.
- **Alerting configuration:** Free monitoring only, primarily /api/health.

---

## Security Requirements

- **Authentication model:** MVP uses Firebase Auth email/password for Level 1 admin/control-room and Level 2 registered officer login, with public rate-limited access for Level 3 citizens.
- **Authorization model:** Backend route-level guards verify Firebase ID tokens, then enforce Level 1 roles, Level 2 assignment-based access, and Level 3 public-safe responses.
- **Threat model:** Protect against invalid input, report spam, Firebase token misuse, Firebase Admin SDK secret exposure, unauthorized officer access, sensitive-field leakage, and map/API provider failure.
- **Secrets management:** No .env commits; no frontend database secrets.
- **Audit requirements:** Log dataset loads, admin actions, officer management, officer field confirmations, simulations, report submissions, and post-event report generation without logging secret values.
- **Encryption requirements:** HTTPS in deployed environments, SSL database connection.
- **Compliance requirements:** No personal citizen identity collection in MVP; mask ASTraM sensitive fields.
- **Security controls:** Pydantic validation, SQLAlchemy parameterization, rate limits, CORS restrictions, structured error handling.

---

## Testing Requirements

### Unit Tests

Create unit tests for every service/function introduced in this phase.

### Integration Tests

Verify API + database + service integration where this phase touches backend persistence.

### E2E Tests

For frontend phases, verify the user workflow through the relevant page.

### Security Tests

Validate sensitive-field masking, invalid payload rejection, rate limits, and no direct Supabase access.

### Performance Tests

Verify the relevant phase target: simulation under 3 seconds, plan generation under 5 seconds, map toggle under 2 seconds, dashboard under 5 seconds, or ingestion under 30 seconds.

### Load Tests

Use lightweight local load tests only for report/simulation endpoints where relevant.

### Contract Tests

Ensure frontend TypeScript types match backend Pydantic response schemas.

---

## Cross-Phase References & Dependency Tracking

- **Required previous phases:** Phase 04
- **Integration method:** This phase reuses previous contracts and creates outputs consumed by Impact score and recommendations.
- **Compatibility requirements:** Do not break existing API shapes, database schema contracts, environment variables, or frontend route expectations.
- **Required interfaces:** Predictions included in simulation/detail responses
- **Required contracts:** the database entities and file paths listed in this phase plus the shared schema in docs/Database_Design.md.
- **Validation process:** Run this phase's validation commands plus smoke checks for earlier completed phases.

Every dependency is explicit in this file. No previous chat context is required.

## Deliverables

- backend/app/ml/feature_pipeline.py
- backend/app/ml/train_priority_model.py
- backend/app/ml/train_road_closure_model.py
- backend/app/ml/train_resolution_time_model.py
- backend/app/ml/inference_resolution_time.py
- backend/app/services/road_closure_scoring_service.py
- backend/app/services/prediction_service.py
- backend/app/services/resolution_time_service.py
- frontend/app/model-insights/page.tsx

---

## Technical Design Summary

Build this phase as a modular, testable slice of EventFlow AI. Backend code owns data validation, persistence, AI/rule logic, and sensitive handling. Frontend code owns rendering, interaction, and API consumption. Database access is backend-only. MapmyIndia/Mappls is the primary MVP map provider using available 1000 INR credits; MapmyIndia / Mappls must remain the only map provider through the provider adapter.

---

## Validation Checklist

### Automated Verification

Run the commands listed below and all relevant unit/integration tests.

### Manual Verification

Exercise the user workflow affected by this phase in the browser or API client.

### Integration Verification

Confirm previous phase contracts still work and the new outputs feed future phases.

### Security Verification

Check no sensitive fields or secrets are exposed.

### Performance Verification

Measure the relevant endpoint/page timing against MVP targets.

---

## Validation Commands

```bash
python backend/app/ml/train_priority_model.py; python backend/app/ml/train_resolution_time_model.py; pytest backend/tests/test_predictions.py; pytest backend/tests/test_road_closure_scoring.py; pytest backend/tests/test_resolution_time.py
```

`train_road_closure_model.py` and `train_resolution_time_model.py` are optional/supporting. Run them only to populate Model Insights with experimental metrics. Do not block MVP completion on them.

---

## Completion Criteria

Phase is complete only if:

- Code builds successfully.
- Tests pass.
- Security checks pass.
- Performance checks pass for phase-relevant targets.
- Documentation and environment examples are updated.
- Validation checklist passes.
- No paid API dependency is introduced.

---
