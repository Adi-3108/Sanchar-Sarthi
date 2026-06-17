# PHASE 3 — ASTraM Data Cleaning And Ingestion

## Phase Overview

Load, validate, clean, mask, and persist ASTraM event records.

This phase is part of EventFlow AI, a predictive traffic command twin for Bengaluru event-driven congestion. The project uses ASTraM historical event data, FastAPI, Next.js, Supabase PostgreSQL free tier, explainable AI/rule-based planning, MapmyIndia/Mappls primary integration using available 1000 INR credits, OpenStreetMap fallback, and only free/open-source APIs or services.

---

## Why This Phase Exists

- **Problem being solved:** Load, validate, clean, mask, and persist ASTraM event records.
- **User need addressed:** Traffic operators, planners, field officers, citizens, delivery stakeholders, and judges need a reliable implementation step that advances the Predict -> Plan -> Monitor -> Adapt -> Learn workflow.
- **Business requirement satisfied:** This phase supports a complete Flipkart Gridlock 2.0 prototype that demonstrates feasibility, innovation, scalability, security, user experience, and real-world impact.
- **Why now:** This phase depends on Phase 02 and must exist before Feature engineering and analytics.
- **How it contributes:** It strengthens EventFlow AI as an operational command system rather than a generic dashboard.

---

## Original Intent Preservation

### Original Problem

Bengaluru event-driven congestion needs data-backed planning for impact, manpower, barricading, diversions, live escalation, and post-event learning.

### User Pain Point

Traffic response is often reactive, delayed, and experience-driven. Users need explainable, map-first, action-oriented intelligence.

### Product Goal

Deliver this capability: Load, validate, clean, mask, and persist ASTraM event records.

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

- **New functionality:** Load, validate, clean, mask, and persist ASTraM event records.
- **New APIs:** POST /api/datasets/upload; POST /api/datasets/load-demo
- **New workflows:** The product moves forward in the end-to-end traffic command workflow.
- **New capabilities:** Feature engineering and analytics
- **New infrastructure:** backend/app/services/data_cleaning_service.py; backend/app/services/text_normalization_service.py; backend/app/utils/masking_utils.py; backend/app/api/routes_datasets.py; backend/scripts/load_csv_to_db.py; backend/scripts/seed_demo_data.py
- **New data models:** events

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

- backend/app/services/data_cleaning_service.py
- backend/app/services/text_normalization_service.py
- backend/app/utils/masking_utils.py
- backend/app/api/routes_datasets.py
- backend/scripts/load_csv_to_db.py
- backend/scripts/seed_demo_data.py


## Implementation Code Snippets

### Dataset-Specific Cleaning Rules

The full ASTraM CSV has dataset realities that must be handled explicitly:

- `description` includes Kannada/non-English script in a meaningful number of rows. Do not feed raw description text directly into Event DNA.
- `requires_road_closure` is highly imbalanced. Preserve the raw label exactly and compute closure rates later; do not oversell it as a balanced ML target.
- `end_datetime` is null for most rows. Preserve `closed_datetime` and `resolved_datetime` for Phase 4 duration fallback.

### `backend/app/services/text_normalization_service.py`
```python
from dataclasses import dataclass
from typing import Any

KANNADA_RANGE = ('\u0C80', '\u0CFF')

KANNADA_TRAFFIC_GLOSSARY = {
    '\u0c9c\u0c82\u0c95\u0ccd\u0cb7\u0ca8\u0ccd': 'junction',
    '\u0cb0\u0cb8\u0ccd\u0ca4\u0cc6': 'road',
    '\u0c85\u0caa\u0c98\u0cbe\u0ca4': 'accident',
    '\u0cae\u0cb3\u0cc6': 'rain',
    '\u0ca8\u0cc0\u0cb0\u0cc1': 'water',
    '\u0cb8\u0c82\u0c9a\u0cbe\u0cb0': 'traffic',
    '\u0cb5\u0cbe\u0cb9\u0ca8': 'vehicle',
    '\u0cad\u0cbe\u0cb0\u0cbf': 'heavy',
    '\u0ca8\u0cbf\u0ca7\u0cbe\u0ca8': 'slow',
}

@dataclass(frozen=True)
class NormalizedDescription:
    raw: str | None
    language: str
    text_for_features: str | None
    method: str
    confidence: float

def _empty(value: Any) -> bool:
    return value is None or str(value).strip().upper() in {'', 'NULL', 'NAN'}

def detect_description_language(value: Any) -> str:
    if _empty(value):
        return 'unknown'
    text = str(value)
    kannada_chars = sum(1 for char in text if '\u0C80' <= char <= '\u0CFF')
    ascii_letters = sum(1 for char in text if char.isascii() and char.isalpha())
    if kannada_chars and ascii_letters:
        return 'mixed'
    if kannada_chars:
        return 'kn'
    return 'en'

def normalize_description(value: Any) -> NormalizedDescription:
    if _empty(value):
        return NormalizedDescription(None, 'unknown', None, 'empty', 0.0)

    raw = str(value).strip()
    language = detect_description_language(raw)
    if language == 'en':
        return NormalizedDescription(raw, 'en', raw.lower(), 'raw_ascii', 0.95)

    mapped_terms = [english for kannada, english in KANNADA_TRAFFIC_GLOSSARY.items() if kannada in raw]
    if mapped_terms:
        return NormalizedDescription(
            raw=raw,
            language=language,
            text_for_features=' '.join(sorted(set(mapped_terms))),
            method='static_kannada_glossary',
            confidence=0.55,
        )

    return NormalizedDescription(raw, language, None, 'skipped_low_confidence', 0.0)
```

### `backend/app/services/data_cleaning_service.py`
```python
import hashlib
import math
from datetime import datetime
from typing import Any
from app.services.text_normalization_service import normalize_description

SENSITIVE_COLUMNS = {'veh_no', 'kgid', 'created_by_id', 'last_modified_by_id', 'assigned_to_police_id'}

def _empty(value: Any) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value)) or str(value).strip().upper() in {'', 'NULL', 'NAN'}

def mask_vehicle_number(value: Any, salt: str = 'eventflow-demo') -> str | None:
    if _empty(value):
        return None
    digest = hashlib.sha256(f'{salt}:{str(value).strip()}'.encode('utf-8')).hexdigest()
    return digest[:16]

def clean_event_cause(value: Any) -> str:
    if _empty(value):
        return 'unknown'
    return str(value).strip().lower().replace(' ', '_').replace('-', '_')

def parse_datetime(value: Any) -> datetime | None:
    if _empty(value):
        return None
    return datetime.fromisoformat(str(value).replace('Z', '+00:00'))

def parse_optional_coordinate(value: Any) -> float | None:
    if _empty(value):
        return None
    number = float(value)
    return None if number == 0 else number

def clean_astram_row(row: dict[str, Any]) -> dict[str, Any]:
    payload = {k: v for k, v in row.items() if k not in SENSITIVE_COLUMNS}
    description = normalize_description(row.get('description'))
    return {
        'id': str(row['id']).strip(),
        'event_type': str(row.get('event_type') or 'unplanned').strip().lower(),
        'latitude': float(row['latitude']),
        'longitude': float(row['longitude']),
        'endlatitude': parse_optional_coordinate(row.get('endlatitude')),
        'endlongitude': parse_optional_coordinate(row.get('endlongitude')),
        'address': None if _empty(row.get('address')) else str(row.get('address')),
        'event_cause': None if _empty(row.get('event_cause')) else str(row.get('event_cause')),
        'event_cause_clean': clean_event_cause(row.get('event_cause')),
        'requires_road_closure': str(row.get('requires_road_closure')).upper() == 'TRUE',
        'start_datetime': parse_datetime(row.get('start_datetime')),
        'end_datetime': parse_datetime(row.get('end_datetime')),
        'closed_datetime': parse_datetime(row.get('closed_datetime')),
        'resolved_datetime': parse_datetime(row.get('resolved_datetime')),
        'status': None if _empty(row.get('status')) else str(row.get('status')).lower(),
        'description': description.raw,
        'description_language': description.language,
        'description_for_features': description.text_for_features,
        'description_normalization_method': description.method,
        'corridor': None if _empty(row.get('corridor')) else str(row.get('corridor')),
        'priority': None if _empty(row.get('priority')) else str(row.get('priority')),
        'police_station': None if _empty(row.get('police_station')) else str(row.get('police_station')),
        'zone': None if _empty(row.get('zone')) else str(row.get('zone')),
        'junction': None if _empty(row.get('junction')) else str(row.get('junction')),
        'veh_type': None if _empty(row.get('veh_type')) else str(row.get('veh_type')),
        'veh_no_hash': mask_vehicle_number(row.get('veh_no')),
        'raw_payload': payload,
    }
```

### `backend/app/services/ingestion_service.py`
```python
import pandas as pd
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from app.orm.event import Event
from app.services.data_cleaning_service import clean_astram_row

REQUIRED_COLUMNS = {'id', 'event_type', 'latitude', 'longitude', 'event_cause', 'start_datetime'}

def ingest_astram_csv(db: Session, csv_path: str) -> dict[str, int]:
    frame = pd.read_csv(csv_path)
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f'Missing ASTraM columns: {sorted(missing)}')

    inserted = 0
    for row in frame.to_dict(orient='records'):
        cleaned = clean_astram_row(row)
        stmt = insert(Event).values(**cleaned)
        stmt = stmt.on_conflict_do_update(index_elements=['id'], set_=cleaned)
        db.execute(stmt)
        inserted += 1
    db.commit()
    return {'rows_processed': len(frame), 'rows_upserted': inserted}
```
---

## Database Requirements

- **Database entities affected:** events
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

- **APIs affected:** POST /api/datasets/upload; POST /api/datasets/load-demo
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

- **Frontend scope:** /settings dataset loader
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

- **Required previous phases:** Phase 02
- **Integration method:** This phase reuses previous contracts and creates outputs consumed by Feature engineering and analytics.
- **Compatibility requirements:** Do not break existing API shapes, database schema contracts, environment variables, or frontend route expectations.
- **Required interfaces:** POST /api/datasets/upload; POST /api/datasets/load-demo
- **Required contracts:** the database entities and file paths listed in this phase plus the shared schema in docs/Database_Design.md.
- **Validation process:** Run this phase's validation commands plus smoke checks for earlier completed phases.

Every dependency is explicit in this file. No previous chat context is required.

## Deliverables

- backend/app/services/data_cleaning_service.py
- backend/app/services/text_normalization_service.py
- backend/app/utils/masking_utils.py
- backend/app/api/routes_datasets.py
- backend/scripts/load_csv_to_db.py
- backend/scripts/seed_demo_data.py

---

## Technical Design Summary

Build this phase as a modular, testable slice of EventFlow AI. Backend code owns data validation, persistence, AI/rule logic, and sensitive handling. Frontend code owns rendering, interaction, and API consumption. Database access is backend-only. MapmyIndia/Mappls is the primary MVP map provider using available 1000 INR credits; OSM/MapLibre fallback must remain functional through the provider adapter.

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
pytest backend/tests/test_data_cleaning.py; python backend/scripts/seed_demo_data.py
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
- No paid API dependency is introduced.

---








