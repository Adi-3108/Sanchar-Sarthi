# PHASE 22_F - Android QA, Security, Role-Boundary Testing, And Release Readiness

## Phase Overview

This phase updates Android QA and hardening guidance so it matches the current web and backend behavior that has already been manually tested.

The goal is not only "does the app compile?" but also:

- does the role boundary remain correct?
- do citizen and officer flows stay separated?
- does the app remain honest when models, map providers, or protected routes are unavailable?

---

## Verified Current Platform Behaviors To Preserve

The current system already demonstrates these role-boundary rules:

- citizen/public reporting can work without login
- simulation is protected and requires internal login
- officer workflow requires officer auth plus backend assignment/profile checks
- event dossier access is protected
- admin actions remain protected
- map intelligence can fall back when the primary provider is unavailable

Android QA must preserve the same boundaries.

---

## Required Manual Regression Matrix

### Public / Citizen

- open the app without login
- submit a public incident report
- submit a congestion report
- verify no officer/admin-only data appears

### Signed-In Citizen

- sign in as a normal citizen account
- verify citizen reporting still works
- verify officer-only and admin-only actions remain blocked

### Police Officer

- sign in as a registered officer with an active officer profile
- load assignments
- open an assigned event dossier
- submit a live update
- verify access fails for unassigned events

### Control Room / Admin

- sign in as internal user
- open protected planning surfaces
- run simulation
- inspect foundation control/admin data
- verify internal-only actions are available

---

## Model Availability Rules

The current admin and health surfaces expose model availability for:

- priority model
- road closure model
- resolution time model

Android must handle both states honestly:

- `loaded`
- `not_loaded`

If a model artifact is missing:

- show the unavailable state clearly
- do not fake ML-backed output
- allow fallback heuristic behavior only when the backend does so explicitly

This is especially important for future internal Android screens that reuse simulation or planning endpoints.

---

## Localization Guidance

The web app currently uses an internal language provider and also includes a Google Translate widget in the global shell.

Android must **not** copy the web's script-injected translation approach.

Android localization should use:

- `strings.xml`
- locale-specific resource folders
- persisted in-app language preference

Report payloads should still send user-language hints to backend for text processing, but UI translation must remain native on device.

---

## Security Checklist

- no Firebase Admin credentials on device
- no private map API keys on device
- no direct database access
- no Supabase direct access
- protected routes always send Firebase ID token
- public routes remain accessible without token where backend already allows it
- officer session does not bypass backend assignment checks
- local storage does not keep sensitive tokens in logs or debug text

---

## Offline And Failure-State Checklist

- queued citizen reports survive app restart
- queued officer updates survive app restart
- failed validation stops infinite retry
- backend 401 and 403 responses are shown clearly
- backend 503 states show retry or pending-sync messaging
- map provider fallback state is visible
- geocode failure falls back to manual entry

---

## Performance And UX Checklist

- app launches into a usable public shell quickly
- report entry does not require opening the map
- officer assignment screen loads with cached state when possible
- protected route failures do not crash the shell
- layout remains readable on narrow devices
- no text clipping for English, Kannada, or Hindi labels

---

## Suggested Android Test Coverage

### Unit Tests

- auth token attachment
- role-to-session mapping
- officer-profile-required handling
- public report queue state transitions
- officer live-update queue state transitions
- model-availability display mapping
- map fallback display mapping

### Integration Tests

- Firebase auth to protected bootstrap flow
- citizen report submission to foundation endpoint
- citizen report submission to congestion endpoint
- officer assignments fetch
- officer live update submit
- protected geocode failure handling

### UI Tests

- guest reporting screen
- citizen reporting success state
- officer assignment empty/error state
- officer dossier protected state
- simulation protected sign-in state
- map fallback banner/state

---

## Release Readiness Guidance

Before a future demo APK is considered ready:

- role-boundary regression passes
- public and officer queues are stable
- protected routes fail safely
- model availability is surfaced honestly
- map fallback behavior is visible and understandable
- no docs still claim nonexistent mobile-only backend endpoints

---

## Phase 22_F Completion Criteria

- QA guidance matches the current platform's real role-boundary behavior.
- Model availability is treated as a visible runtime state, not an assumption.
- Android localization guidance is native and not script-based.
- Security and offline rules reflect the current backend and frontend implementation accurately.
