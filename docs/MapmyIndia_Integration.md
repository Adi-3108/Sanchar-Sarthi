# EventFlow AI MapmyIndia / Mappls Integration Specification

## 1. Decision

MapmyIndia / Mappls is the only map provider for submission. The project uses the available `1000 INR` credits through backend-mediated calls and does not configure a secondary map provider.

When Mappls access is missing, disabled, credit-guarded, or unavailable, the app must show a clear provider-unavailable state instead of switching providers.

Correct MVP wording:

```text
Provider: MapmyIndia / Mappls using available 1000 INR credits.
Unavailable state: show missing key, API error, or credit guard reason.
```

## 2. MVP MapmyIndia Scope

| Capability | MVP Provider | Purpose | Unavailable Behavior |
|---|---|---|---|
| Base map | Mappls Web/JS SDK | Bengaluru operational map canvas | Show Mappls unavailable canvas/state |
| Markers | Frontend overlay layer on Mappls canvas | events, reports, hotspots, officers, barricades | Keep non-map panels usable |
| Route display | Mappls routing/polyline when credits allow | diversion and emergency corridor visualization | Return provider-unavailable error |
| Geocoding / reverse geocoding | Optional Mappls REST API | convert typed address to coordinates and label report locations | Return provider-unavailable error |
| Distance / ETA | Optional Mappls routing/distance API | route comparison and logistics risk estimate | Use only non-provider estimates where explicitly labeled |

Do not depend on paid traffic-speed feeds for MVP. EventFlow AI still labels outputs as estimated/recommended/simulated.

## 3. Provider Adapter Contract

All map logic goes through the Mappls provider adapter.

```ts
export type MapProvider = "mapmyindia";

export type MapProviderStatus = {
  activeProvider: MapProvider;
  primaryProvider: "mapmyindia";
  mapKeyAvailable: boolean;
  creditsBudgetInr: number;
  budgetGuardEnabled: boolean;
  providerNote: string;
};

export type RouteRequest = {
  origin: [number, number];
  destination: [number, number];
  waypoints?: Array<[number, number]>;
  mode: "driving";
};

export type RouteResult = {
  provider: MapProvider;
  polyline: Array<[number, number]>;
  distanceMeters?: number;
  durationSeconds?: number;
  confidence: "provider_route";
};
```

## 4. Backend Configuration

Backend environment variables:

```env
MAP_PROVIDER=mapmyindia
MAP_PRIMARY_PROVIDER=mapmyindia
MAPMYINDIA_API_KEY=replace_with_key
MAPMYINDIA_REST_KEY=replace_if_different
MAPMYINDIA_CREDIT_BUDGET_INR=1000
MAPMYINDIA_DAILY_SOFT_LIMIT_INR=150
MAPMYINDIA_ENABLE_ROUTING=true
MAPMYINDIA_ENABLE_GEOCODING=true
MAPMYINDIA_ENABLE_DISTANCE_MATRIX=false
```

Frontend environment variables:

```env
NEXT_PUBLIC_MAP_PROVIDER=mapmyindia
NEXT_PUBLIC_MAPMYINDIA_MAP_KEY=replace_with_browser_allowed_key
```

Security rules:

- Browser-allowed Mappls SDK keys may be exposed only if Mappls allows that key type.
- Server REST keys must stay backend-only.
- Never commit Mappls keys.

## 5. Budget Guardrails

Because credits are limited to `1000 INR`, Mappls usage must be controlled.

- Use Mappls base map on the main map screens.
- Cache route/geocode responses during demo where applicable.
- Do not call routing APIs repeatedly on every map pan/zoom.
- Call route APIs only when an event plan is generated or the user explicitly requests route refresh.
- Render hotspots, impact radius, barricades, and reports as frontend overlays.
- Disable optional distance matrix unless there is enough credit headroom.
- Show provider status in settings: active provider, key availability, budget guard, and provider note.

## 6. API Endpoints

### `GET /api/map/config`

```json
{
  "activeProvider": "mapmyindia",
  "primaryProvider": "mapmyindia",
  "mapKeyAvailable": true,
  "creditsBudgetInr": 1000,
  "budgetGuardEnabled": true,
  "defaultCenter": [77.5946, 12.9716],
  "defaultZoom": 11,
  "providerNote": "MapmyIndia / Mappls is the only configured map provider."
}
```

### `POST /api/map/route`

Generates a Mappls route when provider access and budget allow.

Success responses use `provider: "mapmyindia"` and `confidence: "provider_route"`. Missing keys, API errors, or credit guards return `MAPMYINDIA_UNAVAILABLE` with a reason.

### `POST /api/map/geocode`

Geocoding follows the same Mappls-only policy and returns `MAPMYINDIA_UNAVAILABLE` when provider access is missing or guarded.
