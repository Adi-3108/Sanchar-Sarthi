# PHASE 22_E - Android Maps, Geocode, Overlay Behavior, And Future Push Design

## Phase Overview

The older Android docs assumed a Mappls-only future. That is no longer accurate.

The current platform already implements a more honest map strategy:

- **MapmyIndia / Mappls primary**
- **OSM fallback**
- **local demo overlay mode** when the provider or SDK is unavailable

Android must preserve that exact behavior.

---

## Verified Current Map Backend

### Real Routes Already Present

- `GET /api/map/config`
- `POST /api/map/route`
- `POST /api/map/geocode`
- `GET /api/map/active-routes`
- `GET /api/analytics/hotspots`

### Current Authorization Boundary

- `GET /api/map/config` is safe for app bootstrap.
- `POST /api/map/route` requires internal auth.
- `POST /api/map/geocode` requires internal auth.
- `GET /api/map/active-routes` can return active cached overlays.

### Real Provider States Already Supported

The backend currently reports:

- `activeProvider`: `mapmyindia` or `osm`
- `primaryProvider`: `mapmyindia`
- `fallbackProvider`: `osm`
- `fallbackReason`:
  - `missing_key`
  - `api_error`
  - `credit_guard`
  - `manual_demo`

That means the Android app must never assume a single-provider happy path.

---

## Mobile Map Strategy

| Capability | Current source of truth | Android expectation |
|---|---|---|
| Base config | `GET /api/map/config` | decide provider and fallback messaging |
| Protected route overlay | `POST /api/map/route` | officer/control-room only |
| Address lookup | `POST /api/map/geocode` | internal role only |
| Active cached overlays | `GET /api/map/active-routes` | optional shared visual layer |
| Hotspots | `GET /api/analytics/hotspots` | internal and analysis-focused |

---

## What "Search Markers" Mean In This Platform

When a user searches for an address, the backend geocode route can return one or more candidate coordinates.

Those temporary candidate points are the app's **search markers**.

They are not:

- confirmed incidents
- officer assignments
- hotspot clusters
- live traffic sensors

They are simply geocode result candidates to help the user choose a map point.

Android should therefore draw them differently from:

- incident markers
- hotspot markers
- route polyline overlays

---

## Android Map Rules

- Public reporting must not depend on protected geocode.
- Manual coordinate entry should always remain available.
- If MapmyIndia SDK fails to initialize, the app should still render a fallback shell with local overlays or a noninteractive backup state.
- Route-generation UI should be shown only to internal roles.
- Search should explain when geocoding failed and manual entry is required.

This matches the current web behavior where map intelligence can still remain operational even when the primary SDK is unavailable.

---

## Push Notification Status

Push is still future scope.

Important current-state note:

- The backend does **not** currently expose device registration routes for FCM token management.

Therefore Android push should be documented as:

- future-ready design only
- not a currently available backend integration

Do not document nonexistent endpoints such as:

- `/api/device/register`
- `/api/device/unregister`

unless those are actually implemented later.

---

## Recommended Android Map Modules

```text
feature/map/
  MapHomeScreen.kt
  MapIntelligenceScreen.kt
  GeocodeSearchSheet.kt
  RouteOverlayPanel.kt

data/remote/
  MapApi.kt
  MapDtos.kt

domain/model/
  MapProviderState.kt
  SearchMarker.kt
  IncidentMarker.kt
  HotspotMarker.kt
  RouteOverlay.kt
```

---

## Honest UX Copy To Preserve

The map layer must keep the same honest language used in the web app:

- primary provider
- fallback provider
- fallback reason
- local overlay mode
- advisory route

Do not claim:

- exact live navigation
- guaranteed street-level rerouting
- provider-backed traffic speed truth

unless those capabilities are added for real.

---

## Phase 22_E Completion Criteria

- Android map docs now reflect MapmyIndia primary plus OSM fallback.
- Geocode and route endpoints are documented with their real authorization boundaries.
- Search markers are explained as temporary geocode candidates.
- Push remains marked future because backend device-token routes do not yet exist.
