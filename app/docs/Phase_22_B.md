# PHASE 22_B - Android Authentication, Session, And Role Boundary Aligned To The Current Codebase

## Phase Overview

This phase defines Android authentication and session behavior against the current implementation.

The web platform already proves a few important things:

- Firebase client auth is working.
- Sign-in, sign-up, email verification, and resend-verification flows exist in the shared auth UI.
- The frontend stores a role-aware session locally.
- Backend role checks are stricter than UI role selection.

The Android app must copy that model exactly.

---

## Verified Current Auth Model

### Web Behavior Already Present

- `AuthPanel` supports:
  - sign in
  - sign up
  - email verification
  - resend verification
- `/login` exists and redirects signed-in users toward the main user shell.
- The web session store uses role-aware local state rather than trusting Firebase alone.
- The sidebar can expose many portals, but protected actions are still rejected by backend when the role is wrong.

### Backend Behavior Already Present

- New valid Firebase users can be auto-created as `citizen`.
- `police_officer` access requires an active `PoliceOfficerProfile`.
- Officer event access can come from:
  - explicit event assignment
  - assigned corridor
  - assigned zone
  - matching police station
- Role aliases are normalized by backend helpers, so Android must not hardcode role assumptions independently.

---

## Current Role Model

### Frontend Access Levels In Use

The current frontend session store uses:

- `admin`
- `control_room`
- `police_officer`
- `citizen`
- `public_citizen`

### Backend Authority Model

Backend authorization still decides what each signed-in user can access.

| Mobile session meaning | Current backend expectation | Notes |
|---|---|---|
| `public_citizen` | no token required | guest-only public experience |
| `citizen` | Firebase user, backend may auto-provision account | can use citizen-authenticated flows later |
| `control_room` | internal control-room access | backend alias handling applies |
| `police_officer` | active officer profile required | assignment scope matters |
| `admin` | full internal access | admin APIs remain restricted |

Important rule:

- The UI role picker is a hint for UX.
- The backend role and profile state are the only trusted source.

---

## Current Route Bootstrap Strategy

There is **no** dedicated `/api/officer/login` backend endpoint in the current codebase.

Android login bootstrap must work like this:

1. Firebase sign-in on device.
2. Fetch protected backend route(s) using the Firebase ID token.
3. Build app session from backend-verified data.

### Verified Protected Bootstrap Routes

| Audience | Recommended bootstrap route | Why |
|---|---|---|
| Officer | `GET /api/officer/assignments` | returns officer id, station, assigned events, corridors, zones, pending reports, overlays |
| Control room | `GET /api/foundation/control-room` | returns incident/station/hotspot state |
| Admin | `GET /api/foundation/admin/overview` and `GET /api/health` | returns internal overview and system state |
| Guest citizen | none required | public flow should remain usable without login |

---

## Android Session Model

Recommended session model:

```kotlin
data class AppSession(
    val firebaseUid: String? = null,
    val email: String? = null,
    val accessLevel: AccessLevel = AccessLevel.PublicCitizen,
    val backendRole: String? = null,
    val officerId: String? = null,
    val policeStation: String? = null,
    val assignedCorridors: List<String> = emptyList(),
    val assignedZones: List<String> = emptyList(),
    val assignedEventIds: List<String> = emptyList(),
)

enum class AccessLevel {
    Admin,
    ControlRoom,
    PoliceOfficer,
    Citizen,
    PublicCitizen,
}
```

Do not store backend secrets or privileged claims that were never returned by the server.

---

## Android Auth Rules

- Protected requests must attach the Firebase ID token as `Authorization: Bearer <token>`.
- Public report submission must remain available without a token.
- Missing officer profile must produce a clear, user-facing error.
- Signed-in citizen users must not automatically see officer or admin UI.
- Android landing behavior should be role-aware, not hardcoded to one page.

Suggested landing behavior:

- guest -> citizen report shell
- citizen -> citizen shell
- police officer -> officer assignments
- control room -> control-room shell
- admin -> admin summary shell

---

## Error States Android Must Handle

- Firebase sign-in failed
- email not verified
- Firebase token expired
- backend user auto-created as citizen
- officer profile missing
- officer assignment access denied
- admin/control-room role missing
- backend unavailable

The Android app should display backend errors honestly instead of masking them as generic login failures.

---

## Phase 22_B Completion Criteria

- Android auth design no longer references a nonexistent `/api/officer/login`.
- Session design matches the current frontend role model.
- Backend remains the final authority for role and scope.
- Officer access rules document active profile plus assignment checks.
- Guest and citizen flows remain separated from internal planning flows.
