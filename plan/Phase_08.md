# PHASE 8 — Estimated Impact Score And Counterfactual Engine

## Phase Overview

Create estimated impact score, category, radius, and baseline-vs-event delta.

This phase is part of EventFlow AI, a predictive traffic command twin for Bengaluru event-driven congestion. The project uses ASTraM historical event data, FastAPI, Next.js, Supabase PostgreSQL free tier, explainable AI/rule-based planning, MapmyIndia/Mappls primary integration using available 1000 INR credits, OpenStreetMap fallback, and only free/open-source APIs or services.

---

## Why This Phase Exists

- **Problem being solved:** Create estimated impact score, category, radius, and baseline-vs-event delta.
- **User need addressed:** Traffic operators, planners, field officers, citizens, delivery stakeholders, and judges need a reliable implementation step that advances the Predict -> Plan -> Monitor -> Adapt -> Learn workflow.
- **Business requirement satisfied:** This phase supports a complete Flipkart Gridlock 2.0 prototype that demonstrates feasibility, innovation, scalability, security, user experience, and real-world impact.
- **Why now:** This phase depends on Phase 05, Phase 06, Phase 07 and must exist before Recommendation engine.
- **How it contributes:** It strengthens EventFlow AI as an operational command system rather than a generic dashboard.

---

## Original Intent Preservation

### Original Problem

Bengaluru event-driven congestion needs data-backed planning for impact, manpower, barricading, diversions, live escalation, and post-event learning.

### User Pain Point

Traffic response is often reactive, delayed, and experience-driven. Users need explainable, map-first, action-oriented intelligence.

### Product Goal

Deliver this capability: Create estimated impact score, category, radius, and baseline-vs-event delta.

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

- **New functionality:** Create estimated impact score, category, radius, and baseline-vs-event delta.
- **New APIs:** Included in POST /api/events/simulate and GET /api/events/{event_id}
- **New workflows:** The product moves forward in the end-to-end traffic command workflow.
- **New capabilities:** Recommendation engine
- **New infrastructure:** backend/app/services/impact_score_service.py; frontend/components/recommendations/ImpactScorePanel.tsx; frontend/components/recommendations/CounterfactualImpactCard.tsx
- **New data models:** event_predictions

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

- backend/app/services/impact_score_service.py
- frontend/components/recommendations/ImpactScorePanel.tsx
- frontend/components/recommendations/CounterfactualImpactCard.tsx


## Implementation Code Snippets

### Dataset-Specific: Vehicle Type Impact Weighting

The ASTraM dataset has a `veh_type` field populated for all vehicle breakdown events. Different vehicle types cause measurably different congestion duration in the dataset.

Multiplier derivation rule:
- Compute `avg_clearance_minutes` per `veh_type` using valid clearance timestamps: prefer `resolved_datetime` when it is after `start_datetime` and within 24 hours; otherwise use `closed_datetime` with the same filter.
- Normalize against `private_car` baseline (1.0).
- Cap the multiplier at `1.5x` for MVP scoring stability.
- Apply as a controlled additive adjustment after weather and multi-event factors: `adjusted_score = score + ((vehicle_multiplier - 1) * 12)`.
- If `veh_type` is NULL, blank, or unknown, multiplier defaults to 1.0 - no penalty, no benefit. Blank `veh_type` rows are not used for multiplier derivation because they mix non-vehicle and poorly typed incidents.

Known vehicle types in dataset: `lcv`, `heavy_vehicle`, `bmtc_bus`, `ksrtc_bus`, `private_bus`, `private_car`, `auto`, `truck`, `others`.

UI label: "Vehicle Impact Factor" with note: "Derived from ASTraM resolution time averages per vehicle type."

Impact vocabulary contract:

- `impact_category` uses the operational taxonomy `Low`, `Medium`, `High`, `Critical`.
- This is separate from the raw ASTraM `priority` label, which remains a two-level dataset field in the current CSV.

### `backend/app/services/impact_score_service.py`
```python
from dataclasses import dataclass

# Vehicle impact multipliers derived from ASTraM avg clearance times per veh_type.
# Uses valid clearance timestamps (resolved or closed within 24h of start_datetime).
# Normalized against private_car as 1.0 baseline.
# If veh_type is NULL (non-vehicle events), multiplier = 1.0.
# This table must be reused by the Phase 07 clearance estimator as well; do not maintain a second conflicting vehicle map.
VEHICLE_IMPACT_MULTIPLIER: dict[str, float] = {
    # Approximate ASTraM clearance-time ratios normalized to private_car.
    # Final implementation should regenerate these values from the loaded dataset
    # and store the derivation output in model_runs.
    'bmtc_bus': 1.42,
    'truck': 1.42,
    'heavy_vehicle': 1.37,
    'private_bus': 1.36,
    'taxi': 1.34,
    'others': 1.22,
    'lcv': 1.20,
    'ksrtc_bus': 1.13,
    'private_car': 1.0,
    'auto': 0.93,
}

# NOTE TO IMPLEMENTATION AGENT:
# Before hardcoding these values, run the following query on the loaded dataset
# to derive dataset-backed multipliers:
#
# WITH clearance_rows AS (
#   SELECT
#     id,
#     veh_type,
#     start_datetime,
#     CASE
#       WHEN resolved_datetime IS NOT NULL
#        AND resolved_datetime - start_datetime < INTERVAL '24 hours'
#        AND resolved_datetime - start_datetime > INTERVAL '0 minutes'
#       THEN resolved_datetime
#       WHEN closed_datetime IS NOT NULL
#        AND closed_datetime - start_datetime < INTERVAL '24 hours'
#        AND closed_datetime - start_datetime > INTERVAL '0 minutes'
#       THEN closed_datetime
#       ELSE NULL
#     END AS valid_end
#   FROM events
# )
# SELECT veh_type,
#        COUNT(*) as sample_count,
#        AVG(EXTRACT(EPOCH FROM (valid_end - start_datetime)) / 60) as avg_clearance_min
# FROM clearance_rows
# WHERE valid_end IS NOT NULL
#   AND veh_type IS NOT NULL
#   AND TRIM(veh_type) <> ''
# GROUP BY veh_type
# ORDER BY avg_clearance_min DESC;
#
# Normalize each avg_clearance_min against private_car's avg_clearance_min,
# then cap each multiplier to 1.5 for MVP score stability.
# Replace the values above with the computed results if the dataset changes.
# Store the derivation query and output in model_runs for audit/explainability.


@dataclass(frozen=True)
class ImpactInput:
    urgency_score: float
    road_closure_likelihood: float
    hotspot_risk_score: float
    similar_event_risk: float
    veh_type: str | None = None
    weather_factor: float = 1.0
    multi_event_factor: float = 1.0


def get_vehicle_multiplier(veh_type: str | None) -> tuple[float, str]:
    """Returns (multiplier, reason_label) for a given vehicle type."""
    if not veh_type or not veh_type.strip():
        return 1.0, 'veh_type:unknown_no_adjustment'
    multiplier = min(VEHICLE_IMPACT_MULTIPLIER.get(veh_type.lower(), 1.0), 1.5)
    return multiplier, f'veh_type:{veh_type}:multiplier:{multiplier}'


def impact_category(score: float) -> str:
    if score >= 75:
        return 'Critical'
    if score >= 50:
        return 'High'
    if score >= 30:
        return 'Medium'
    return 'Low'


def estimate_impact(input_data: ImpactInput) -> dict[str, float | str | list]:
    raw = (
        input_data.urgency_score * 35
        + input_data.road_closure_likelihood * 25
        + input_data.hotspot_risk_score * 20
        + input_data.similar_event_risk * 20
    )
    weather_adjusted = min(raw * input_data.weather_factor * input_data.multi_event_factor, 100)

    vehicle_multiplier, vehicle_reason = get_vehicle_multiplier(input_data.veh_type)
    adjusted = min(weather_adjusted + ((vehicle_multiplier - 1.0) * 12.0), 100.0)

    radius_km = round(0.5 + (adjusted / 100) * 3.5, 2)
    return {
        'estimated_impact_score': round(adjusted, 2),
        'impact_category': impact_category(adjusted),
        'impact_radius_km': radius_km,
        'vehicle_impact_factor': vehicle_multiplier,
        'vehicle_impact_note': 'Derived from ASTraM resolution time averages per vehicle type.',
        'score_reason_codes': [vehicle_reason],
    }
```

### Counterfactual Baseline Calculation
```python
def counterfactual_delta(current: ImpactInput) -> dict[str, float | str]:
    baseline = ImpactInput(
        urgency_score=max(current.urgency_score - 0.2, 0),
        road_closure_likelihood=max(current.road_closure_likelihood - 0.2, 0),
        hotspot_risk_score=current.hotspot_risk_score,
        similar_event_risk=current.similar_event_risk,
    )
    with_event = estimate_impact(current)
    without_event = estimate_impact(baseline)
    return {
        'baseline_score': without_event['estimated_impact_score'],
        'event_adjusted_score': with_event['estimated_impact_score'],
        'estimated_delta': round(float(with_event['estimated_impact_score']) - float(without_event['estimated_impact_score']), 2),
        'honesty_note': 'Delta is a relative operational estimate, not measured vehicle delay.',
    }
```
---

## Database Requirements

- **Database entities affected:** event_predictions
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

- **APIs affected:** Included in POST /api/events/simulate and GET /api/events/{event_id}
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

- **Frontend scope:** ImpactScorePanel, CounterfactualImpactCard
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

- **Required previous phases:** Phase 05, Phase 06, Phase 07
- **Integration method:** This phase reuses previous contracts and creates outputs consumed by Recommendation engine.
- **Compatibility requirements:** Do not break existing API shapes, database schema contracts, environment variables, or frontend route expectations.
- **Required interfaces:** Included in POST /api/events/simulate and GET /api/events/{event_id}
- **Required contracts:** the database entities and file paths listed in this phase plus the shared schema in docs/Database_Design.md.
- **Validation process:** Run this phase's validation commands plus smoke checks for earlier completed phases.

Every dependency is explicit in this file. No previous chat context is required.

## Deliverables

- backend/app/services/impact_score_service.py
- frontend/components/recommendations/ImpactScorePanel.tsx
- frontend/components/recommendations/CounterfactualImpactCard.tsx

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
pytest backend/tests/test_impact_score.py
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








