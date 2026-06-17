# EventFlow AI Testing Strategy

## 1. Test Goals

- Validate data cleaning and feature engineering.
- Validate prediction and recommendation logic.
- Ensure map/report/demo flows work.
- Prevent sensitive data exposure.
- Keep judge demo stable.

## 2. Unit Testing

Backend unit tests:

- Firebase ID-token verification
- Firebase-linked role lookup
- inactive Firebase-linked account rejection
- Level 1/2/3 authorization decisions
- officer assignment filtering
- event cause normalization
- Kannada/non-English description detection and safe normalization
- timestamp parsing
- duration fallback source selection: `end_datetime`, `closed_datetime`, `resolved_datetime`, unavailable
- resolution-time label selection: valid `resolved_datetime` under 24h, else valid `closed_datetime` under 24h, else no ML training label
- vehicle impact scoring: unknown/blank vehicle type gives no adjustment; known vehicle types use controlled additive scoring, not raw 2.5x multiplication
- coordinate validation
- sensitive field masking
- Event DNA generation
- impact score boundaries
- road-closure rule/history scorer with sparse TRUE-class dataset
- manpower recommendation rules
- barricade weather adjustment
- diversion graph route selection
- citizen report confidence
- multi-event conflict scoring
- post-event lesson generation

Frontend unit tests:

- risk badge rendering
- form validation
- API error state components
- language labels
- any-language report input state
- recommendation panels

## 3. Integration Testing

- dataset load -> events stored
- events -> features generated
- Kannada/mixed descriptions -> raw text preserved and normalized feature text stored when confidence allows
- mostly-null `end_datetime` rows -> duration source recorded without fake imputation
- simulate event -> predictions + recommendations
- citizen report -> matched event/hotspot
- citizen report -> optional translation -> matched event/hotspot
- live update -> alert level changed
- post-event report -> stored and returned

## 4. API Testing

Use pytest + httpx or FastAPI TestClient.

Required tests:

- GET /api/health
- POST /api/datasets/load-demo
- GET /api/events
- GET /api/events/{id}
- POST /api/events/simulate
- POST /api/reports/congestion
- POST /api/events/{id}/live-update
- POST /api/events/multi-event-analysis
- POST /api/events/{id}/post-event-report
- POST /api/admin/officers
- GET /api/officer/assignments

Optional only if the backend token-exchange endpoint is intentionally implemented:

- POST /api/officer/login

## 5. Contract Testing

Validate that frontend TypeScript types match backend Pydantic response schemas.

## 6. Security Testing

- invalid coordinate rejection
- CSV invalid schema rejection
- oversized description rejection
- Kannada descriptions do not corrupt Event DNA or similar-event scoring
- Google Translate disabled mode still accepts reports
- Google Translate enabled mode stores `translated_description`
- translation budget guard blocks translation without blocking report submission
- road-closure likelihood remains available when the optional closure ML artifact is missing or weak
- no raw `veh_no` exposure
- no Supabase credentials in frontend bundle
- no Firebase Admin SDK service account secrets in frontend bundle or `NEXT_PUBLIC_*`
- protected admin routes reject missing/invalid Firebase ID token
- officer routes reject inactive/unassigned officers
- public routes never expose officer identities, exact manpower internals, or admin-only fields
- report endpoint rate limiting

## 7. Performance Testing

Targets:

- dashboard load under 5 seconds
- simulation API under 3 seconds
- event plan generation under 5 seconds
- map layer toggle under 2 seconds
- CSV cleaning under 30 seconds for 8173 rows

## 8. End-To-End Demo Testing

Demo acceptance flow:

1. Load Command Center.
2. View hotspots.
3. Simulate planned procession.
4. Generate Event DNA and recommendations.
5. Submit citizen reports.
6. Trigger heavy rain adjustment.
7. Run multi-event analysis.
8. Trigger live escalation.
9. Generate post-event playbook.

## 9. Release Gates

Do not submit if:

- demo dataset does not load
- simulation fails
- recommendation panel lacks reasons
- map fails without fallback
- sensitive fields are visible
- post-event report fails
