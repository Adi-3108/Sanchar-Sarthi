# PHASE 22_C - Android Citizen Reporting Aligned To The Current Dual Intake System

## Phase Overview

The current codebase now has **two different public-reporting paths**, and the Android app must document them clearly instead of collapsing them into one vague form.

### Reporting Path 1 - Sanchar Sarthi Foundation Incident Intake

Used for broader public incident creation and local traffic police intake.

Route:

- `POST /api/foundation/incidents/report`

### Reporting Path 2 - EventFlow Congestion Intelligence Signal

Used for traffic/congestion reports that should be matched into the EventFlow event intelligence pipeline.

Route:

- `POST /api/reports/congestion`

The Android app can expose both, but it must label them clearly.

---

## Verified Current Web Behavior

- `/reports` now uses `FoundationShell` report mode for public-facing reporting.
- Public users can submit without login.
- The congestion-report flow already returns operational feedback such as:
  - `matched_event_id`
  - `report_confidence`
  - `impact_score_change`
  - `new_alert_level`
  - `recommended_action`
- Backend translation happens server-side through the translation service. The client should send raw description text plus language hint.

---

## Recommended Android Citizen Reporting UX

### Option A - Single Entry With Report Type Switch

One public screen with two tabs:

- `Traffic issue`
- `Public incident`

### Option B - Two Explicit Buttons

- `Report traffic issue`
- `Report civic/road incident`

Either option is fine, but the app must not mix payload contracts silently.

---

## Route Decision Table

| Mobile intent | Backend route | Notes |
|---|---|---|
| Report a general public-facing incident for station workflow | `POST /api/foundation/incidents/report` | primary Sanchar Sarthi intake |
| Report congestion, waterlogging, crowd buildup, spillback, or traffic pressure that should influence an EventFlow event | `POST /api/reports/congestion` | returns immediate intelligence summary |

---

## Current Payload Contracts

### Foundation Incident Create Contract

Mirror the current frontend type:

```kotlin
data class FoundationIncidentCreateRequest(
    val incident_type: String,
    val title: String,
    val description: String,
    val severity: String,
    val location_name: String,
    val latitude: Double,
    val longitude: Double,
    val locality: String? = null,
    val ward: String? = null,
    val language: String = "auto",
)
```

### Congestion Report Contract

Mirror the current backend schema:

```kotlin
data class CitizenReportCreateRequest(
    val report_source: String = "citizen",
    val report_type: String,
    val latitude: Double,
    val longitude: Double,
    val severity: String? = null,
    val description: String,
    val language: String = "auto",
    val event_id: String? = null,
)
```

Important constraints verified in backend:

- `description` is required
- `language` defaults to `auto`
- `report_source = citizen` does not require auth
- public congestion reports are rate-limited

Current public congestion rate limit:

- 10 reports per 60 seconds per client source bucket

---

## Offline Queue Rules

The Android app should still queue public reports locally, but the docs must stay honest:

- The current backend does **not** expose a formal mobile idempotency-key contract.
- Android must deduplicate locally using a `localId`.
- Retries should be bounded and visible to the user.
- Failed validation must stop auto-retry and surface the reason.

Recommended local model:

```kotlin
data class PendingMobileReport(
    val localId: String,
    val reportMode: String, // foundation or congestion
    val payloadJson: String,
    val syncStatus: String, // queued, syncing, submitted, failed
    val retryCount: Int,
    val createdAtMillis: Long,
    val serverReference: String? = null,
    val failureReason: String? = null,
)
```

---

## Multilingual Rules

- UI labels should be native Android strings, not script-injected translation.
- Report text should be sent as raw user input.
- The `language` field should be populated from the report form selection:
  - `auto`
  - `en`
  - `kn`
  - `hi`
  - `other`

Do not require a client-side translation-preview endpoint because the current backend does not expose one as part of this mobile plan.

---

## Android Citizen Reporting Rules

- Guest users can submit public reports.
- Signed-in citizens may reuse the same public flow.
- GPS should be optional.
- Manual coordinates and manual location name should remain available.
- The congestion flow should show the intelligence response back to the user.
- The foundation flow should show accepted incident status back to the user.

---

## Phase 22_C Completion Criteria

- Android docs distinguish foundation intake from congestion intelligence intake.
- Public submission without login remains supported.
- Payload contracts match current backend/frontend types.
- Offline queue guidance does not assume a nonexistent backend idempotency API.
- Language handling stays backend-translatable and client-simple.
