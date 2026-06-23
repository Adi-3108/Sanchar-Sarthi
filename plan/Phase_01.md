# PHASE 1 — Repository Scaffold And Environment

## Phase Overview

Create the monorepo, FastAPI backend, Next.js frontend, base config, and health endpoint.

This phase is part of EventFlow AI, a predictive traffic command twin for Bengaluru event-driven congestion. The project uses ASTraM historical event data, FastAPI, Next.js, Supabase PostgreSQL free tier, explainable AI/rule-based planning, MapmyIndia/Mappls primary integration using available 1000 INR credits, Mappls-only map policy, and only free/open-source APIs or services.

---

## Why This Phase Exists

- **Problem being solved:** Create the monorepo, FastAPI backend, Next.js frontend, base config, and health endpoint.
- **User need addressed:** Traffic operators, planners, field officers, citizens, delivery stakeholders, and judges need a reliable implementation step that advances the Predict -> Plan -> Monitor -> Adapt -> Learn workflow.
- **Business requirement satisfied:** This phase supports a complete Flipkart Gridlock 2.0 prototype that demonstrates feasibility, innovation, scalability, security, user experience, and real-world impact.
- **Why now:** This phase depends on None and must exist before All later phases.
- **How it contributes:** It strengthens EventFlow AI as an operational command system rather than a generic dashboard.

---

## Original Intent Preservation

### Original Problem

Bengaluru event-driven congestion needs data-backed planning for impact, manpower, barricading, diversions, live escalation, and post-event learning.

### User Pain Point

Traffic response is often reactive, delayed, and experience-driven. Users need explainable, map-first, action-oriented intelligence.

### Product Goal

Deliver this capability: Create the monorepo, FastAPI backend, Next.js frontend, base config, and health endpoint.

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

- **New functionality:** Create the monorepo, FastAPI backend, Next.js frontend, base config, and health endpoint.
- **New APIs:** GET /api/health
- **New workflows:** The product moves forward in the end-to-end traffic command workflow.
- **New capabilities:** All later phases
- **New infrastructure:** backend/app/main.py; backend/app/core/config.py; backend/app/api/routes_health.py; frontend/app/page.tsx; frontend/app/command-center/page.tsx; frontend/lib/api.ts; .env.example; README.md
- **New data models:** None

---

## Full Implementation Requirements

Implementation agents must create executable production-ready source files for every path listed in this phase.

Required implementation standards:

- Complete imports, classes, interfaces, functions, DTOs, models, controllers, services, repositories, middleware, tests, and configuration must be written by the implementation agent.
- No paid APIs may be introduced in the base MVP. Optional Phase 19 Google Translate configuration may be present but must remain disabled unless explicitly enabled with backend credentials and budget guardrails.
- No placeholder or TODO code may be committed.
- All code must be directly executable in the repository.
- All outputs must preserve EventFlow AI's dataset-honest wording: Dataset-backed, Predicted, Estimated, Recommended, Simulated, or Future integration.

### Exact Repository Paths For This Phase

- backend/app/main.py
- backend/app/core/config.py
- backend/app/core/firebase.py
- backend/app/core/security.py
- backend/app/api/routes_health.py
- frontend/app/page.tsx
- frontend/app/command-center/page.tsx
- frontend/lib/api.ts
- frontend/lib/firebase.ts
- .env.example
- README.md


## Implementation Code Snippets

### `backend/app/core/config.py`
```python
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'EventFlow AI'
    environment: str = Field(default='local', pattern='^(local|test|production)$')
    database_url: str = Field(default='postgresql+psycopg://postgres:postgres@localhost:5432/eventflow')
    frontend_origin: str = 'http://localhost:3000'
    map_provider: str = Field(default='mapmyindia', pattern='^mapmyindia$')
    map_primary_provider: str = 'mapmyindia'
    mapmyindia_api_key: str | None = None
    mapmyindia_rest_key: str | None = None
    mapmyindia_credit_budget_inr: int = 1000
    mapmyindia_daily_soft_limit_inr: int = 150
    mapmyindia_enable_routing: bool = True
    mapmyindia_enable_geocoding: bool = True
    mapmyindia_enable_distance_matrix: bool = False
    map_fallback_on_error: bool = True
    open_meteo_enabled: bool = True
    google_translate_enabled: bool = False
    google_translate_provider: str = 'google'
    google_translate_target_language: str = 'en'
    google_translate_daily_char_limit: int = 50000
    google_translate_monthly_char_limit: int = 500000
    google_translate_fail_open: bool = True
    google_cloud_project_id: str | None = None
    google_application_credentials_json: str | None = None
    firebase_project_id: str | None = None
    firebase_client_email: str | None = None
    firebase_private_key: str | None = None

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origin.split(',') if origin.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### `backend/app/main.py` and `backend/app/api/routes_health.py`
```python
# backend/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_health import router as health_router
from app.core.config import get_settings
from app.core.firebase import initialize_firebase

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_firebase(settings)
    yield

app = FastAPI(title=settings.app_name, version='0.1.0', lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE'],
    allow_headers=['*'],
)
app.include_router(health_router)

# backend/app/api/routes_health.py
from datetime import datetime, timezone
from fastapi import APIRouter

router = APIRouter(prefix='/api', tags=['health'])

@router.get('/health')
def health() -> dict[str, str]:
    return {
        'status': 'ok',
        'service': 'eventflow-api',
        'checked_at': datetime.now(timezone.utc).isoformat(),
    }
```

### `backend/app/core/firebase.py`
```python
import firebase_admin
from firebase_admin import credentials
from app.core.config import Settings

def initialize_firebase(settings: Settings) -> firebase_admin.App | None:
    if firebase_admin._apps:
        return firebase_admin.get_app()

    if not settings.firebase_project_id or not settings.firebase_client_email or not settings.firebase_private_key:
        return None

    private_key = settings.firebase_private_key.replace('\\n', '\n')
    cred = credentials.Certificate(
        {
            'type': 'service_account',
            'project_id': settings.firebase_project_id,
            'client_email': settings.firebase_client_email,
            'private_key': private_key,
            'token_uri': 'https://oauth2.googleapis.com/token',
        }
    )
    return firebase_admin.initialize_app(cred)
```

### `backend/app/core/security.py`
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

def verify_firebase_token(authorization: str | None = Header(default=None, alias='Authorization')) -> dict:
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={'code': 'MISSING_FIREBASE_TOKEN'})
    if not firebase_admin._apps:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={'code': 'FIREBASE_NOT_CONFIGURED'})
    try:
        return firebase_auth.verify_id_token(authorization.removeprefix('Bearer ').strip(), check_revoked=True)
    except firebase_auth.RevokedIdTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={'code': 'REVOKED_FIREBASE_TOKEN'})
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={'code': 'INVALID_FIREBASE_TOKEN'})

def get_auth_context(token_payload: dict = Depends(verify_firebase_token), db: Session = Depends(get_db)) -> AuthContext:
    account = (
        db.query(UserAccount)
        .filter(UserAccount.auth_provider == 'firebase')
        .filter(UserAccount.auth_provider_uid == token_payload['uid'])
        .first()
    )
    if not account or not account.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={'code': 'INACTIVE_ACCOUNT'})

    officer_profile = None
    if account.role == 'police_officer':
        officer_profile = (
            db.query(PoliceOfficerProfile)
            .filter(PoliceOfficerProfile.user_account_id == account.id)
            .filter(PoliceOfficerProfile.active.is_(True))
            .first()
        )
        if not officer_profile:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={'code': 'OFFICER_PROFILE_REQUIRED'})

    return AuthContext(
        firebase_uid=token_payload['uid'],
        email=token_payload.get('email'),
        role=account.role,
        user_account_id=str(account.id),
        officer_profile_id=str(officer_profile.id) if officer_profile else None,
        officer_id=officer_profile.officer_id if officer_profile else None,
        police_station=officer_profile.police_station if officer_profile else None,
        assigned_corridors=officer_profile.assigned_corridors_json if officer_profile else None,
        assigned_zones=officer_profile.assigned_zones_json if officer_profile else None,
    )

def require_role(*allowed_roles: str):
    def dependency(auth: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if auth.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={'code': 'FORBIDDEN_ROLE'})
        return auth
    return dependency
```

### `frontend/lib/api.ts`
```ts
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`API ${response.status}: ${await response.text()}`);
  }
  return response.json() as Promise<T>;
}
```

### `frontend/lib/firebase.ts`
```ts
import { initializeApp, getApps } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY!,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN!,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID!,
};

const firebaseApp = getApps().length ? getApps()[0] : initializeApp(firebaseConfig);

export const firebaseAuth = getAuth(firebaseApp);
```

### `.env.example`
```env
APP_ENV=local
FRONTEND_ORIGIN=http://localhost:3000
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/eventflow
FIREBASE_PROJECT_ID=eventflow-ai-demo
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@eventflow-ai-demo.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
NEXT_PUBLIC_FIREBASE_API_KEY=public_web_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=eventflow-ai-demo.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=eventflow-ai-demo
MAP_PROVIDER=mapmyindia
MAP_PRIMARY_PROVIDER=mapmyindia
MAPMYINDIA_API_KEY=replace_with_key
MAPMYINDIA_REST_KEY=replace_if_different
MAPMYINDIA_CREDIT_BUDGET_INR=1000
MAPMYINDIA_DAILY_SOFT_LIMIT_INR=150
MAPMYINDIA_ENABLE_ROUTING=true
MAPMYINDIA_ENABLE_GEOCODING=true
MAPMYINDIA_ENABLE_DISTANCE_MATRIX=false
OPEN_METEO_ENABLED=true
GOOGLE_TRANSLATE_ENABLED=false
GOOGLE_TRANSLATE_PROVIDER=google
GOOGLE_TRANSLATE_TARGET_LANGUAGE=en
GOOGLE_TRANSLATE_DAILY_CHAR_LIMIT=50000
GOOGLE_TRANSLATE_MONTHLY_CHAR_LIMIT=500000
GOOGLE_TRANSLATE_FAIL_OPEN=true
GOOGLE_CLOUD_PROJECT_ID=
GOOGLE_APPLICATION_CREDENTIALS_JSON=
NEXT_PUBLIC_MAP_PROVIDER=mapmyindia
NEXT_PUBLIC_MAPMYINDIA_MAP_KEY=replace_with_browser_allowed_key
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Do not expose Firebase Admin SDK service account values in `NEXT_PUBLIC_*`. Firebase web config values are allowed in the frontend.
---

## Database Requirements

- **Database entities affected:** None
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

- **APIs affected:** GET /api/health
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

- **Frontend scope:** /, /command-center placeholder
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

- **Required previous phases:** None
- **Integration method:** This phase reuses previous contracts and creates outputs consumed by All later phases.
- **Compatibility requirements:** Do not break existing API shapes, database schema contracts, environment variables, or frontend route expectations.
- **Required interfaces:** GET /api/health
- **Required contracts:** the database entities and file paths listed in this phase plus the shared schema in docs/Database_Design.md.
- **Validation process:** Run this phase's validation commands plus smoke checks for earlier completed phases.

Every dependency is explicit in this file. No previous chat context is required.

## Deliverables

- backend/app/main.py
- backend/app/core/config.py
- backend/app/core/firebase.py
- backend/app/core/security.py
- backend/app/api/routes_health.py
- frontend/app/page.tsx
- frontend/app/command-center/page.tsx
- frontend/lib/api.ts
- frontend/lib/firebase.ts
- .env.example
- README.md

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
npm run build; pytest; python -m uvicorn app.main:app --reload
```

---

## Completion Criteria

Phase is complete only if:

- Code builds successfully.
- Tests pass.
- Security checks pass.
- Performance checks pass for phase-relevant targets.
- Documentation and environment examples are updated.
- Validation checklist passes.
- No mandatory paid API dependency is introduced. Optional Phase 19 Google Translate remains disabled by default.

---
