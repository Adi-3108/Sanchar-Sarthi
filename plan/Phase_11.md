# PHASE 11 — Citizen And Field Report Verification

## Phase Overview

Allow reports while scoring confidence and preventing blind trust.

This phase is part of EventFlow AI, a predictive traffic command twin for Bengaluru event-driven congestion. The project uses ASTraM historical event data, FastAPI, Next.js, Supabase PostgreSQL free tier, explainable AI/rule-based planning, MapmyIndia/Mappls primary integration using available 1000 INR credits, Mappls-only map policy, and only free/open-source APIs or services.

---

## Why This Phase Exists

- **Problem being solved:** Allow reports while scoring confidence and preventing blind trust.
- **User need addressed:** Traffic operators, planners, field officers, citizens, delivery stakeholders, and judges need a reliable implementation step that advances the Predict -> Plan -> Monitor -> Adapt -> Learn workflow.
- **Business requirement satisfied:** This phase supports a complete Flipkart Gridlock 2.0 prototype that demonstrates feasibility, innovation, scalability, security, user experience, and real-world impact.
- **Why now:** This phase depends on Phase 05, Phase 08, Phase 09 and must exist before Live escalation and report map markers.
- **How it contributes:** It strengthens EventFlow AI as an operational command system rather than a generic dashboard.

---

## Original Intent Preservation

### Original Problem

Bengaluru event-driven congestion needs data-backed planning for impact, manpower, barricading, diversions, live escalation, and post-event learning.

### User Pain Point

Traffic response is often reactive, delayed, and experience-driven. Users need explainable, map-first, action-oriented intelligence.

### Product Goal

Deliver this capability: Allow reports while scoring confidence and preventing blind trust.

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

- **New functionality:** Allow reports while scoring confidence and preventing blind trust.
- **New APIs:** POST /api/reports/congestion
- **New workflows:** The product moves forward in the end-to-end traffic command workflow.
- **New capabilities:** Live escalation and report map markers
- **New infrastructure:** backend/app/services/citizen_report_service.py; backend/app/api/routes_reports.py; frontend/app/reports/page.tsx; frontend/components/reports/ReportForm.tsx; frontend/lib/i18n.ts
- **New data models:** citizen_reports, events, hotspot_clusters

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

- backend/app/services/citizen_report_service.py
- backend/app/api/routes_reports.py
- frontend/app/reports/page.tsx
- frontend/components/reports/ReportForm.tsx
- frontend/lib/i18n.ts


## Implementation Code Snippets

### `backend/app/schemas/reports.py`
```python
from pydantic import BaseModel, Field

class CitizenReportCreate(BaseModel):
    report_source: str = Field(pattern='^(citizen|field_officer|control_room|demo)$')
    report_type: str = Field(min_length=2, max_length=80)
    latitude: float = Field(ge=12.0, le=14.0)
    longitude: float = Field(ge=76.0, le=78.5)
    severity: str | None = Field(default=None, max_length=32)
    description: str = Field(min_length=10, max_length=500)
    language: str = Field(default='auto', min_length=2, max_length=16)
    event_id: str | None = None
```

Language codes:

| Code | Language | MVP usage |
|---|---|---|
| `en` | English | default dashboard and report labels |
| `kn` | Kannada | public/citizen report labels for Bengaluru local accessibility |
| `hi` | Hindi | public/citizen report labels |
| `auto` | Auto detect | Phase 19 Google Translate source detection |
| other BCP-47 code | Any language | accepted as raw text; translated when Phase 19 is enabled |

Base MVP does not need paid translation APIs. Use static dictionaries for labels and store the selected language code with each report. Phase 19 optionally enables Google Translate for semantic normalization of any-language descriptions.

### `frontend/lib/i18n.ts`
```ts
export type AppLanguage = 'en' | 'kn' | 'hi';

export const reportLabels: Record<AppLanguage, Record<string, string>> = {
  en: {
    reportIssue: 'Report traffic issue',
    issueType: 'Issue type',
    description: 'Description',
    useLocation: 'Use my location',
    submit: 'Submit report',
    accepted: 'Report accepted',
  },
  kn: {
    reportIssue: 'ಸಂಚಾರ ಸಮಸ್ಯೆಯನ್ನು ವರದಿ ಮಾಡಿ',
    issueType: 'ಸಮಸ್ಯೆಯ ಪ್ರಕಾರ',
    description: 'ವಿವರಣೆ',
    useLocation: 'ನನ್ನ ಸ್ಥಳ ಬಳಸಿ',
    submit: 'ವರದಿ ಸಲ್ಲಿಸಿ',
    accepted: 'ವರದಿ ಸ್ವೀಕರಿಸಲಾಗಿದೆ',
  },
  hi: {
    reportIssue: 'ट्रैफिक समस्या रिपोर्ट करें',
    issueType: 'समस्या का प्रकार',
    description: 'विवरण',
    useLocation: 'मेरी लोकेशन इस्तेमाल करें',
    submit: 'रिपोर्ट सबमिट करें',
    accepted: 'रिपोर्ट स्वीकार की गई',
  },
};

export function t(language: AppLanguage, key: string): string {
  return reportLabels[language]?.[key] ?? reportLabels.en[key] ?? key;
}
```

### Canonical Report-Service Contract

Use `backend/app/services/citizen_report_service.py` as the source of truth for:

- `haversine_km(...)`
- nearest-event matching
- duplicate-area counting
- source-weight scoring
- language/source-language bookkeeping
- translation handoff when optional Phase 19 is enabled

Persistence must target the richer `citizen_reports` schema from `docs/Database_Design.md`, including:

- `report_source`
- `severity`
- `language`
- `source_language`
- `translated_description`
- `translation_provider`
- `translation_status`
- `translation_character_count`
- `matched_event_id`
- `location_match_confidence`
- `report_confidence`
- `impact_score_change`
- `new_alert_level`
- `recommended_action`
- `status`

### Canonical Report Endpoint Contract

The route path must be `POST /api/reports/congestion`.

Authentication/authorization rules:

- `report_source=citizen`: public allowed, rate-limited.
- `report_source=field_officer`: verified Firebase Level 2 officer required; do not trust a free-form `officer_id` string from the request body.
- `report_source=control_room`: verified Firebase Level 1 admin/control-room role required.

Implementation rules:

- Route handlers should depend on the shared auth context helpers already used elsewhere in the backend.
- The endpoint must create `CitizenReport` rows using the canonical DB column names, especially `report_source` and `report_confidence`.
- Match nearby events and compute `location_match_confidence` before persisting.
- Response payloads must match `docs/API_Specification.md` Section 11.
---

## Database Requirements

- **Database entities affected:** citizen_reports, events, hotspot_clusters
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

- **APIs affected:** POST /api/reports/congestion
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

- **Frontend scope:** /reports, ReportForm, ReportResultPanel
- **Pages/components:** Create exact pages/components listed in repository paths.
- **Hooks:** Use typed API hooks with TanStack Query where remote data is fetched.
- **State management:** Use Zustand for selected event, active map layers, simulation state, filter state, and language where needed.
- **Language support:** Public/citizen report UI must support static English (`en`), Kannada (`kn`), and Hindi (`hi`) labels. Descriptions in any language are accepted as raw text. Phase 19 optionally translates descriptions to English using Google Translate.
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

- **Required previous phases:** Phase 05, Phase 08, Phase 09
- **Integration method:** This phase reuses previous contracts and creates outputs consumed by Live escalation and report map markers.
- **Compatibility requirements:** Do not break existing API shapes, database schema contracts, environment variables, or frontend route expectations.
- **Required interfaces:** POST /api/reports/congestion
- **Required contracts:** the database entities and file paths listed in this phase plus the shared schema in docs/Database_Design.md.
- **Validation process:** Run this phase's validation commands plus smoke checks for earlier completed phases.

Every dependency is explicit in this file. No previous chat context is required.

## Deliverables

- backend/app/services/citizen_report_service.py
- backend/app/api/routes_reports.py
- frontend/app/reports/page.tsx
- frontend/components/reports/ReportForm.tsx
- frontend/lib/i18n.ts

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
pytest backend/tests/test_citizen_reports.py
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
