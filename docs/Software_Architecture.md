# EventFlow AI Software Architecture

## 1. Monorepo Structure

```text
eventflow-ai/
  frontend/
    app/
    components/
    features/
    hooks/
    lib/
    stores/
    styles/
    types/
    public/
  backend/
    app/
      api/
      core/
      db/
      ml/
      orm/
      schemas/
      services/
      utils/
    alembic/
    data/
    models/
    scripts/
    tests/
  docs/
  plan/
  docker-compose.yml
  README.md
  .env.example
```

## 2. Core Backend Modules

| Module | Responsibility |
|---|---|
| data_cleaning_service.py | Load, validate, detect description language, normalize safe text, mask, and persist ASTraM data |
| feature_engineering_service.py | Create time, timestamp-fallback duration, risk, and availability features |
| event_dna_service.py | Generate operational fingerprint from structured fields and safe normalized text |
| hotspot_service.py | Run DBSCAN/geospatial clustering and hotspot scoring |
| similar_event_service.py | Weighted historical event retrieval |
| prediction_service.py | Operational urgency inference and rule/history-primary road-closure likelihood |
| impact_score_service.py | Estimated impact and counterfactual delta |
| manpower_service.py | Risk-aware officer recommendation |
| barricade_service.py | Event/weather-aware checkpoint planning |
| diversion_service.py | Simplified graph-based diversion planning |
| citizen_report_service.py | Report validation, matching, confidence scoring |
| weather_service.py | Manual/Open-Meteo weather modifier |
| multi_event_service.py | Simultaneous event conflict detection |
| emergency_corridor_service.py | Protected emergency access advisory |
| logistics_impact_service.py | Flipkart corridor/delivery risk estimate |
| live_escalation_service.py | Live deviation and adaptive action |
| post_event_report_service.py | After-action learning report |
| auth_service.py | Firebase ID-token verification and AuthContext construction |
| authorization_service.py | Level 1/2/3 access checks and response shaping |
| officer_management_service.py | Officer registration, activation, deactivation, assignment |

## 3. Domain Objects

- Event
- EventFeature
- EventDNA
- Prediction
- Recommendation
- HotspotCluster
- CitizenReport
- LiveEventUpdate
- PostEventReport
- DemoScenario
- ModelRun
- UserAccount
- PoliceOfficerProfile
- OfficerEventAssignment
- SystemAuditLog

## 4. Decision Engine Composition

The "AI" is a hybrid engine:

```text
historical data -> ML predictions -> impact score -> modifiers -> recommendations
```

Components:

- ML classifiers for priority and closure likelihood
- DBSCAN for hotspot clustering
- Weighted similarity for historical memory
- Rule engines for manpower/barricade/diversion
- Weather modifier for rain/waterlogging/fog
- Multi-event conflict scoring
- Report confidence scoring

## 5. Public Interfaces

Frontend communicates only with FastAPI. No direct Supabase client exists in the browser.

```text
frontend/lib/api.ts
  createOfficer()
  loginOfficer()
  getOfficerAssignments()
  getSummary()
  getEvents(filters)
  getEventDetail(id)
  getHotspots(filters)
  simulateEvent(payload)
  generateEventPlan(payload)
  submitCitizenReport(payload)
  submitLiveUpdate(eventId, payload)
  analyzeMultiEvent(payload)
generatePostEventReport(eventId)
```

Role-aware interfaces:

- Level 1 Admin / Control Room can call protected admin endpoints with a Firebase ID token and admin/control-room role.
- Level 2 Registered Police Officer can call officer endpoints with a Firebase ID token and active officer assignment.
- Level 3 Public / Citizen can call public-safe endpoints without login.
- Frontend must send Firebase ID tokens as `Authorization: Bearer <token>` for protected routes.
- Backend must verify Firebase identity and then load EventFlow role/assignment from PostgreSQL.

## 6. Error Handling

API responses use a consistent shape:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid latitude/longitude",
    "details": {}
  }
}
```

Expected error categories:

- VALIDATION_ERROR
- NOT_FOUND
- DATABASE_UNAVAILABLE
- MODEL_UNAVAILABLE
- MAP_PROVIDER_UNAVAILABLE
- WEATHER_PROVIDER_UNAVAILABLE
- RATE_LIMITED
- UNAUTHORIZED
- FORBIDDEN
- MISSING_FIREBASE_TOKEN
- INVALID_FIREBASE_TOKEN
- INACTIVE_ACCOUNT
- FORBIDDEN_ROLE
- OFFICER_ASSIGNMENT_REQUIRED
- INTERNAL_ERROR

## 7. Labels For Data Honesty

Every displayed output must be tagged:

- Dataset-backed
- Predicted
- Estimated
- Recommended
- Simulated
- Future integration
