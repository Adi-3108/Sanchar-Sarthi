# PHASE 22_D - Android Officer Workflow Aligned To Current Assignments, Dossiers, And Live Escalation

## Phase Overview

The current backend already supports the core officer workflow through three real capabilities:

- assignment loading
- event dossier viewing
- live-update submission

This Android phase should be built around those verified capabilities first.

---

## Verified Current Officer Surface

### Real Backend Routes Already Present

- `GET /api/officer/assignments`
- `GET /api/events/{event_id}`
- `POST /api/events/{event_id}/live-update`
- `POST /api/recommendations/event-plan` (optional internal re-plan action)

### Real Officer Access Rules Already Present

- officer login alone is not enough
- backend requires an active `PoliceOfficerProfile`
- officer access is valid only if the user matches:
  - explicit event assignment
  - assigned corridor
  - assigned zone
  - matching police station

### Real Data Already Returned By Assignments API

`GET /api/officer/assignments` currently returns:

- `officer_id`
- `police_station`
- `assigned_events`
- `assigned_corridors`
- `assigned_zones`
- `pending_report_confirmations`
- `map_overlays`

Important clarification:

- `pending_report_confirmations` exists in the response, but the backend does **not** currently expose confirm/deny report endpoints for officer use.
- The Android app should therefore treat pending reports as **read context**, not as an action flow, unless backend routes are added later.

---

## Correct Mobile Officer Scope

### In Scope For This Phase

- Sign in as a registered officer.
- Load officer assignments.
- Open an assigned event dossier.
- Read officer-safe plan context.
- Submit live escalation updates against assigned events.
- Queue live updates offline and retry later.

### Not Yet Supported In Current Backend

- `POST /api/reports/{report_id}/confirm`
- `POST /api/reports/{report_id}/deny`

These should remain future backlog items until real backend endpoints exist.

---

## Event Dossier Expectations

`GET /api/events/{event_id}` already powers the web dossier view and returns a rich operational package:

- event snapshot
- Event DNA
- similar-event memory
- prediction summary
- recommendation summary
- citizen reports
- live updates
- map overlays

Android should reuse that same dossier contract rather than creating a reduced ad hoc endpoint.

---

## Live Update Contract

Mirror the current request shape:

```kotlin
data class LiveUpdateRequest(
    val current_congestion_level: String,
    val field_update: String? = null,
    val road_closure_active: Boolean = false,
    val officer_shortage: Boolean = false,
    val crowd_increase: Boolean = false,
    val rain_waterlogging: Boolean = false,
    val new_nearby_incident: Boolean = false,
)
```

Current allowed congestion levels:

- `Info`
- `Watch`
- `Stable`
- `Warning`
- `Critical`

Current response behavior:

- backend recomputes current impact against expected impact
- backend stores alert level and adaptive action
- update source becomes `field_officer` for officer submissions

---

## Recommended Android Officer Screens

```text
OfficerHomeScreen
  -> AssignmentSummaryCard
  -> AssignedEventList
  -> PendingReportsContextCard

OfficerEventScreen
  -> EventDossierHeader
  -> EventDnaCard
  -> SimilarEventsCard
  -> PredictionCard
  -> RecommendationCards
  -> LiveUpdateBottomSheet
```

Recommended UX decision:

- Keep `Submit live update` as a fixed bottom action or bottom sheet.
- This mirrors the current web officer workflow where live escalation is the most important field action.

---

## Offline Rules

- Save live updates locally before attempting sync.
- Mark locally queued updates as pending until server confirmation.
- Never display queued local state as official command-center state.
- Retry only for assignment-valid events already cached in the officer session.

Recommended local entity:

```kotlin
data class PendingFieldUpdate(
    val localId: String,
    val eventId: String,
    val payloadJson: String,
    val syncStatus: String,
    val retryCount: Int,
    val createdAtMillis: Long,
    val failureReason: String? = null,
)
```

---

## Officer-Safe Data Rules

Android officer mode may show:

- assigned event ids
- corridor and station scope
- recommended action summary
- live escalation timeline
- map overlays relevant to the assignment

Android officer mode must not assume access to:

- unassigned events
- full admin controls
- unrestricted city-wide internal analytics
- hidden backend secrets

---

## Phase 22_D Completion Criteria

- Officer mobile docs now reflect the real backend route surface.
- Assignment loading, dossier viewing, and live updates are documented as the primary field workflow.
- Report confirmation is marked future because confirm/deny routes do not currently exist.
- Officer access rules document active-profile and assignment-scope enforcement accurately.
