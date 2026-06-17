# EventFlow AI Backend Architecture

## 1. Technology Stack

| Technology | Purpose | Why Selected | Free/Open Source |
|---|---|---|---|
| FastAPI | REST backend | Fast, typed, OpenAPI support | Yes |
| Python 3.11+ | Backend/ML language | Best fit for data/ML | Yes |
| Pydantic v2 | Request/response validation | Strong schema validation | Yes |
| SQLAlchemy 2.0 | ORM | PostgreSQL support | Yes |
| Alembic | Migrations | Versioned DB schema | Yes |
| pandas/numpy | Data processing | CSV/features | Yes |
| scikit-learn | ML models | Free ML library | Yes |
| NetworkX | Demo routing graph | Open-source graph algorithms | Yes |
| Uvicorn | ASGI server | FastAPI standard | Yes |

## 2. Folder Structure

```text
backend/
  app/
    main.py
    api/
      routes_health.py
      routes_datasets.py
      routes_events.py
      routes_analytics.py
      routes_predictions.py
      routes_recommendations.py
      routes_reports.py
      routes_translation.py
      routes_live_updates.py
      routes_post_event.py
      routes_admin.py
      routes_officers.py
    core/
      config.py
      database.py
      errors.py
      firebase.py
      logging.py
      security.py
      translation_budget.py
      constants.py
    db/
      base.py
      session.py
      init_db.py
    orm/
      event.py
      event_feature.py
      event_dna.py
      prediction.py
      recommendation.py
      hotspot_cluster.py
      citizen_report.py
      live_update.py
      post_event_report.py
      model_run.py
      demo_scenario.py
      user_account.py
      police_officer_profile.py
      officer_event_assignment.py
      system_audit_log.py
    schemas/
      event_schema.py
      analytics_schema.py
      simulation_schema.py
      recommendation_schema.py
      report_schema.py
      post_event_schema.py
      auth_schema.py
      officer_schema.py
      translation_schema.py
    services/
      data_cleaning_service.py
      feature_engineering_service.py
      event_dna_service.py
      hotspot_service.py
      similar_event_service.py
      prediction_service.py
      impact_score_service.py
      manpower_service.py
      barricade_service.py
      diversion_service.py
      citizen_report_service.py
      translation_service.py
      weather_service.py
      multi_event_service.py
      emergency_corridor_service.py
      logistics_impact_service.py
      live_escalation_service.py
      post_event_report_service.py
      auth_service.py
      officer_management_service.py
      authorization_service.py
    ml/
      feature_pipeline.py
      train_priority_model.py
      train_road_closure_model.py
      train_resolution_time_model.py
      inference_priority.py
      inference_road_closure.py
      inference_resolution_time.py
      model_registry.py
    utils/
      datetime_utils.py
      geo_utils.py
      masking_utils.py
      response_utils.py
  alembic/
  scripts/
    load_csv_to_db.py
    seed_demo_data.py
    train_models.py
    create_demo_scenarios.py
  tests/
```

## 3. Controllers

Routes should be thin. They validate inputs, call services, and return schemas.

Example:

```text
routes_events.py -> EventService / SimulationService
routes_reports.py -> CitizenReportService
routes_recommendations.py -> RecommendationOrchestrator
routes_post_event.py -> PostEventReportService
routes_admin.py -> AdminService / OfficerManagementService
routes_officers.py -> OfficerAuthService / OfficerAssignmentService
```

Access boundaries:

- Level 1 Admin / Control Room endpoints require a verified Firebase ID token and an active admin/control-room role in `user_accounts`.
- Level 2 Registered Police Officer endpoints require a verified Firebase ID token, an active officer profile, and assignment checks.
- Level 3 Public / Citizen endpoints allow anonymous access but return only public-safe data.

## 4. Services

Services contain business logic. They must be unit-testable and must not depend on frontend assumptions.

Primary orchestration:

```text
SimulationService
  -> EventDNAService
  -> SimilarEventService
  -> PredictionService
  -> ImpactScoreService
  -> WeatherService
  -> MultiEventService
  -> RecommendationOrchestrator
```

## 5. Repositories

Use repository functions for database operations:

- `EventRepository`
- `FeatureRepository`
- `PredictionRepository`
- `RecommendationRepository`
- `ReportRepository`
- `HotspotRepository`
- `ModelRunRepository`
- `UserAccountRepository`
- `PoliceOfficerRepository`
- `OfficerAssignmentRepository`
- `AuditLogRepository`

## 6. Middleware

MVP middleware:

- CORS
- request logging
- error handling
- Firebase ID token verification dependency for Level 1 and Level 2 endpoints
- role and officer-assignment dependencies for protected operational endpoints
- simple report rate limiting

Use FastAPI dependencies for route-level authorization instead of a broad global middleware so endpoint permissions remain explicit.

```python
from dataclasses import dataclass
from fastapi import Depends, Header, HTTPException, status
import firebase_admin
from firebase_admin import auth as firebase_auth
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.orm.police_officer_profile import PoliceOfficerProfile
from app.orm.user_account import UserAccount

@dataclass(frozen=True)
class AuthContext:
    firebase_uid: str
    email: str | None
    role: str
    user_account_id: str
    officer_profile_id: str | None = None
    officer_id: str | None = None
    police_station: str | None = None
    assigned_corridors: list[str] | None = None
    assigned_zones: list[str] | None = None

def verify_firebase_token(authorization: str | None = Header(default=None, alias="Authorization")) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "MISSING_FIREBASE_TOKEN"})
    if not firebase_admin._apps:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"code": "FIREBASE_NOT_CONFIGURED"})
    try:
        return firebase_auth.verify_id_token(authorization.removeprefix("Bearer ").strip(), check_revoked=True)
    except firebase_auth.RevokedIdTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "REVOKED_FIREBASE_TOKEN"})
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "INVALID_FIREBASE_TOKEN"})

def get_auth_context(token_payload: dict = Depends(verify_firebase_token), db: Session = Depends(get_db)) -> AuthContext:
    account = (
        db.query(UserAccount)
        .filter(UserAccount.auth_provider == "firebase")
        .filter(UserAccount.auth_provider_uid == token_payload["uid"])
        .first()
    )
    if not account or not account.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "INACTIVE_ACCOUNT"})

    officer_profile = None
    if account.role == "police_officer":
        officer_profile = (
            db.query(PoliceOfficerProfile)
            .filter(PoliceOfficerProfile.user_account_id == account.id)
            .filter(PoliceOfficerProfile.active.is_(True))
            .first()
        )
        if not officer_profile:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "OFFICER_PROFILE_REQUIRED"})

    return AuthContext(
        firebase_uid=token_payload["uid"],
        email=token_payload.get("email"),
        role=account.role,
        user_account_id=str(account.id),
        officer_profile_id=str(officer_profile.id) if officer_profile else None,
        officer_id=officer_profile.officer_id if officer_profile else None,
        police_station=officer_profile.police_station if officer_profile else None,
        assigned_corridors=officer_profile.assigned_corridors_json if officer_profile else None,
        assigned_zones=officer_profile.assigned_zones_json if officer_profile else None,
    )
```

Officer authorization flow:

```text
Firebase token verified -> user_accounts role/is_active check -> active officer profile -> station/corridor/event assignment check -> officer-safe response
```

## 7. Configuration

Environment variables:

```text
APP_ENV
BACKEND_PORT
CORS_ORIGINS
DATABASE_URL
RAW_DATA_PATH
PROCESSED_DATA_PATH
MODEL_DIR
PRIORITY_MODEL_PATH
ROAD_CLOSURE_MODEL_PATH
ENABLE_DEMO_MODE
ENABLE_AUTH
FIREBASE_PROJECT_ID
FIREBASE_CLIENT_EMAIL
FIREBASE_PRIVATE_KEY
NEXT_PUBLIC_FIREBASE_API_KEY
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN
NEXT_PUBLIC_FIREBASE_PROJECT_ID
OPEN_METEO_ENABLED
MAP_PROVIDER
```

Configuration rules:

- Firebase Admin SDK credentials are backend-only and must never appear in `NEXT_PUBLIC_*`.
- Firebase web config values use `NEXT_PUBLIC_FIREBASE_*` and are safe for the browser.
- Backend must reject protected routes if Firebase Admin SDK is not configured.
- EventFlow roles and officer assignments are still read from PostgreSQL, not trusted from client-side state.
- Full Firebase startup, token verification, role lookup, and officer-profile mapping are specified in `docs/Firebase_Auth_Implementation.md`.

## 8. Background Jobs

MVP can run synchronously for demo. Optional background jobs:

- model training
- CSV ingestion
- hotspot recomputation
- post-event report export

Use simple scripts, not paid queues.

## 9. Caching Layer

MVP caching:

- in-memory cache for analytics summary
- query-level caching in frontend
- no Redis required

Production future:

- self-hosted Redis
- precomputed materialized views

## 10. Logging

Use structured JSON logs:

```json
{
  "timestamp": "...",
  "level": "INFO",
  "request_id": "...",
  "event": "simulation_completed",
  "duration_ms": 421
}
```
