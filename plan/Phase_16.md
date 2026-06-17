# PHASE 16 — Post Event Learning Dashboard

## Phase Overview

Generate after-action learning reports and future playbooks.

This phase is part of EventFlow AI, a predictive traffic command twin for Bengaluru event-driven congestion. The project uses ASTraM historical event data, FastAPI, Next.js, Supabase PostgreSQL free tier, explainable AI/rule-based planning, MapmyIndia/Mappls primary integration using available 1000 INR credits, OpenStreetMap fallback, and only free/open-source APIs or services.

---

## Why This Phase Exists

- **Problem being solved:** Generate after-action learning reports and future playbooks.
- **User need addressed:** Traffic operators, planners, field officers, citizens, delivery stakeholders, and judges need a reliable implementation step that advances the Predict -> Plan -> Monitor -> Adapt -> Learn workflow.
- **Business requirement satisfied:** This phase supports a complete Flipkart Gridlock 2.0 prototype that demonstrates feasibility, innovation, scalability, security, user experience, and real-world impact.
- **Why now:** This phase depends on Phase 12, Phase 15 and must exist before Demo closing and learning loop.
- **How it contributes:** It strengthens EventFlow AI as an operational command system rather than a generic dashboard.

---

## Original Intent Preservation

### Original Problem

Bengaluru event-driven congestion needs data-backed planning for impact, manpower, barricading, diversions, live escalation, and post-event learning.

### User Pain Point

Traffic response is often reactive, delayed, and experience-driven. Users need explainable, map-first, action-oriented intelligence.

### Product Goal

Deliver this capability: Generate after-action learning reports and future playbooks.

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

- **New functionality:** Generate after-action learning reports and future playbooks.
- **New APIs:** POST /api/events/{event_id}/post-event-report
- **New workflows:** The product moves forward in the end-to-end traffic command workflow.
- **New capabilities:** Demo closing and learning loop
- **New infrastructure:** backend/app/services/post_event_report_service.py; backend/app/api/routes_post_event.py; frontend/app/post-event-learning/page.tsx; frontend/components/reports/PostEventReportView.tsx
- **New data models:** post_event_reports, predictions, recommendations, reports, updates

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

- backend/app/services/post_event_report_service.py
- backend/app/api/routes_post_event.py
- frontend/app/post-event-learning/page.tsx
- frontend/components/reports/PostEventReportView.tsx


## Implementation Code Snippets

### `backend/app/services/post_event_learning_service.py`
```python
from sqlalchemy.orm import Session
from app.orm.citizen_report import CitizenReport
from app.orm.event import Event
from app.orm.event_recommendation import EventRecommendation
from app.orm.post_event_report import PostEventReport


def generate_lessons(event: Event, report_count: int, recommendation: EventRecommendation | None) -> list[str]:
    lessons: list[str] = []
    if report_count >= 3:
        lessons.append('Multiple reports indicated live crowd/traffic pressure; increase report monitoring for similar events.')
    if recommendation and recommendation.barricade_plan.get('barricade_level') == 'controlled_entry_exit_points':
        lessons.append('Controlled entry/exit planning should be prepared earlier for high-impact corridor events.')
    if event.requires_road_closure:
        lessons.append('Road-closure likelihood was present in historical data; pre-position manpower near junction approaches.')
    return lessons or ['No strong post-event learning signal; retain baseline playbook and collect richer outcomes next time.']


def build_post_event_report(db: Session, event_id: str) -> PostEventReport:
    event = db.get(Event, event_id)
    if event is None:
        raise ValueError('Event not found')
    reports = db.query(CitizenReport).filter(CitizenReport.event_id == event_id).all()
    recommendation = db.query(EventRecommendation).filter(EventRecommendation.event_id == event_id).order_by(EventRecommendation.created_at.desc()).first()
    lessons = generate_lessons(event, len(reports), recommendation)
    record = PostEventReport(
        event_id=event_id,
        recommendation_summary=str(recommendation.confidence_ledger if recommendation else []),
        citizen_report_summary=f'{len(reports)} citizen/field reports considered',
        lessons_learned='\n'.join(lessons),
        future_recommendations='Use this Event DNA profile for similar corridor/time-window events.',
    )
    db.add(record)
    db.commit()
    return record
```

### `frontend/app/post-event-learning/page.tsx`
```tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api';

export default function PostEventLearningPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['post-event-reports'],
    queryFn: () => apiGet<Array<{ eventId: string; lessonsLearned: string }>>('/api/post-event-reports'),
  });
  if (isLoading) return <main className="p-6">Loading learning reports...</main>;
  return <main className="space-y-3 p-6">{data?.map((report) => <article key={report.eventId} className="rounded border p-4">{report.lessonsLearned}</article>)}</main>;
}
```
---

## Database Requirements

- **Database entities affected:** post_event_reports, predictions, recommendations, reports, updates
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

- **APIs affected:** POST /api/events/{event_id}/post-event-report
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

- **Frontend scope:** /post-event-learning, PostEventReportView
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

- **Required previous phases:** Phase 12, Phase 15
- **Integration method:** This phase reuses previous contracts and creates outputs consumed by Demo closing and learning loop.
- **Compatibility requirements:** Do not break existing API shapes, database schema contracts, environment variables, or frontend route expectations.
- **Required interfaces:** POST /api/events/{event_id}/post-event-report
- **Required contracts:** the database entities and file paths listed in this phase plus the shared schema in docs/Database_Design.md.
- **Validation process:** Run this phase's validation commands plus smoke checks for earlier completed phases.

Every dependency is explicit in this file. No previous chat context is required.

## Deliverables

- backend/app/services/post_event_report_service.py
- backend/app/api/routes_post_event.py
- frontend/app/post-event-learning/page.tsx
- frontend/components/reports/PostEventReportView.tsx

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
pytest backend/tests/test_post_event_report.py; npm run build
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








