# PHASE 22_A - Android Foundation Aligned To The Current Sanchar Sarthi And EventFlow Platform

## Phase Overview

This phase defines the future Android app against the codebase that exists today.

The current product is no longer a single dashboard. It is a hybrid platform with:

- **Sanchar Sarthi foundation flows** for public incident intake, station mapping, control-room triage, and admin governance.
- **EventFlow AI intelligence flows** for simulation, Event DNA, recommendations, live escalation, multi-event analysis, map intelligence, and post-event learning.

The Android app must extend this exact platform shape instead of reintroducing older assumptions.

---

## Verified Current Codebase Baseline

### Frontend Routes Already Live

The web app currently exposes the following route surface:

- `/`
- `/user`
- `/control-room`
- `/command-center`
- `/officer`
- `/admin`
- `/map-intelligence`
- `/explorer`
- `/reports`
- `/model-insights`
- `/simulation`
- `/post-event-learning`
- `/settings`
- `/login`
- `/events/[id]`

Important implementation detail:

- `/`, `/user`, `/control-room`, and `/reports` are now backed by the shared `FoundationShell`.
- The global sidebar is intentionally broad, but backend authorization still decides what the user can actually do.

### Backend API Families Already Live

The FastAPI backend already exposes the following route families:

- `/api/foundation/*`
- `/api/reports/*`
- `/api/events/*`
- `/api/officer/*`
- `/api/recommendations/*`
- `/api/map/*`
- `/api/analytics/*`
- `/api/command-center/*`
- `/api/demo/*`
- `/api/admin/*`
- `/api/health`

### Current Platform Rules The App Must Respect

- Firebase Auth proves identity, but FastAPI is the final authorization authority.
- New Firebase users can be auto-provisioned as `citizen` on backend bootstrap.
- Officer access depends on an active `PoliceOfficerProfile` plus event or corridor or zone or station access.
- The map strategy is **MapmyIndia primary with OSM/local-overlay fallback**, not MapmyIndia-only.
- User-facing branding is mixed on purpose right now:
  - **Sanchar Sarthi** is the public/operations shell.
  - **EventFlow AI** is the predictive intelligence layer.

The Android app should preserve that same split instead of inventing a different brand hierarchy.

---

## Why This Phase Exists

- Citizens will report from phones faster than from desktop.
- Officers need assignment-aware field tools.
- Control-room staff may need lightweight mobile visibility when they are not on the main console.
- The app should feel like an extension of the current platform, not a separate rebuild.

This remains future scope and must not break the web-first working system.

---

## Mobile Scope Decision

### In Scope

- Android-only native app.
- Kotlin + Jetpack Compose.
- Firebase client authentication.
- FastAPI-only backend access.
- Public reporting without mandatory login.
- Officer assignment and live-update workflow.
- Read-only or lightweight internal visibility for control-room/admin users.
- Map view that supports provider fallback.
- Offline queue for citizen reports and officer field updates.

### Out Of Scope

- Direct database access from Android.
- Supabase access from Android.
- Firebase Admin SDK on device.
- Exact real-world navigation guarantees.
- Exact traffic speed ground truth.
- Full web-admin parity on mobile.
- iOS build.

---

## Product Model For Android

The app should mirror the current web product structure:

| Mobile area | Current platform source of truth | Audience |
|---|---|---|
| Public issue reporting | `foundation` and `reports` APIs | Citizen |
| Incident browsing and local advisories | `foundation` APIs | Citizen / control-room |
| Officer assignment and escalation | `officer`, `events`, `recommendations` APIs | Police officer |
| Event simulation and planning | `events/simulate` and `recommendations/event-plan` | Internal only |
| Map intelligence | `map`, `analytics`, `foundation` overlays | Internal first |
| Learning and after-action review | `events/{id}` and `post-event-report` | Internal only |

---

## Recommended Android Architecture

```text
android/
  app/
    src/main/java/com/sancharsarthi/eventflow/
      core/
        auth/
        network/
        session/
        location/
        sync/
        datastore/
      data/
        remote/
        local/
        repository/
      domain/
        model/
        usecase/
      feature/
        splash/
        auth/
        citizen/
        officer/
        foundation/
        simulation/
        map/
        learning/
        settings/
      navigation/
      design/
```

Recommended namespace: `com.namangulati.sancharsarthi`

Reason:

- It reflects the current public + intelligence split.
- It avoids locking the app to only the older `EventFlowAI` naming.

---

## Integration Contract

Android must communicate only through FastAPI:

```text
Android app -> FastAPI backend -> database / ML / route provider / analytics
```

Forbidden:

```text
Android app -> PostgreSQL directly
Android app -> Supabase directly
Android app -> Firebase Admin SDK
Android app -> private MapmyIndia REST credentials
Android app -> hidden backend-only admin operations without token validation
```

---

## Cross-Cutting Implementation Rules

- Match existing backend route names. Do not invent mobile-only route aliases unless versioned deliberately.
- Keep citizen flows separate from internal planning flows.
- Treat route visibility as UX only. Backend enforcement remains mandatory.
- Preserve dataset-honest copy:
  - estimated
  - recommended
  - simulated
  - advisory
  - fallback
- Preserve current map honesty:
  - primary provider
  - fallback reason
  - local overlay mode when provider is unavailable

---

## Phase 22_A Completion Criteria

- Android foundation plan reflects the current hybrid platform, not the older web MVP shape.
- Route naming is aligned to the real backend.
- Branding notes acknowledge Sanchar Sarthi plus EventFlow AI coexistence.
- Map architecture explicitly preserves MapmyIndia primary plus OSM fallback.
- Android design assumes backend-only authority for roles and access.
