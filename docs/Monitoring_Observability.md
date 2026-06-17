# EventFlow AI Monitoring And Observability Strategy

## 1. Goals

- Know whether demo services are alive.
- Track API latency and failures.
- Track model output availability.
- Track dataset load status.
- Track user-facing errors during demo.

## 2. Health Checks

Endpoint:

```http
GET /api/health
```

Checks:

- backend status
- database connection
- model artifacts loaded
- demo dataset available

## 3. Logging

Use structured JSON logs with:

- timestamp
- level
- request_id
- route
- duration_ms
- user/demo role if available
- error_code

Important events:

- dataset_loaded
- simulation_completed
- recommendation_generated
- citizen_report_received
- officer_login_attempt
- officer_assignment_changed
- officer_field_update_confirmed
- admin_action_attempt
- firebase_token_verification_failed
- live_escalation_triggered
- post_event_report_generated
- model_fallback_used

## 4. Metrics

MVP metrics:

- API latency
- API error rate
- simulation count
- report submission count
- officer login success/failure count
- protected admin action count
- model fallback count
- post-event report count
- map layer load failures

## 5. Alerting

Free approach:

- UptimeRobot monitors `/api/health`
- Platform deployment alerts
- Browser console checks during demo rehearsal

## 6. Model Observability

Store in `model_runs`:

- metrics
- version
- feature list
- training rows
- test rows

Store prediction explanations in `event_predictions.prediction_explanation_json`.

## 7. Frontend Observability

Track manually or through free tools:

- page load time
- API failures
- map provider failures
- form validation errors
- demo flow completion

## 8. Dashboard For Demo Readiness

Settings page should show:

- backend connected
- database connected
- demo data loaded
- priority model loaded
- road closure model loaded
- map provider active
- weather mode active
