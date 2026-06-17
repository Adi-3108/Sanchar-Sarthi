# EventFlow AI MapmyIndia / Mappls Integration Specification

## 1. Decision

MapmyIndia / Mappls is the primary map provider for the MVP because the team has `1000 INR` credits available.

OpenStreetMap + MapLibre remains a safety fallback only for:

- exhausted MapmyIndia credits
- missing/invalid MapmyIndia key
- MapmyIndia SDK/API outage
- local/offline demo fallback

The product must avoid vague conditional wording about MapmyIndia availability. The correct MVP wording is:

```text
Primary: MapmyIndia / Mappls using available 1000 INR credits.
Fallback: OSM + MapLibre safety mode.
```

## 2. MVP MapmyIndia Scope

Use MapmyIndia only for the map capabilities that improve judge-visible traffic operations.

| Capability | MVP Provider | Purpose | Fallback |
|---|---|---|---|
| Base map | Mappls Web/JS SDK | Bengaluru operational map canvas | OSM raster/vector through MapLibre |
| Markers | Frontend overlay layer | events, reports, hotspots, officers, barricades | same frontend overlay on OSM |
| Route display | Mappls routing/polyline if credits allow | diversion and emergency corridor visualization | local NetworkX demo graph polyline |
| Geocoding / reverse geocoding | Optional Mappls REST API | convert typed address to coordinates and label report locations | manual coordinate/address fields |
| Distance / ETA | Optional Mappls distance/routing API | route comparison and logistics risk estimate | haversine + simplified speed assumptions |

Do not depend on paid traffic-speed feeds for MVP. EventFlow AI still labels outputs as estimated/recommended/simulated.

## 3. Provider Adapter Contract

All map logic must go through a provider adapter so the app can switch providers safely.

```ts
export type MapProvider = "mapmyindia" | "osm";

export type MapProviderStatus = {
  activeProvider: MapProvider;
  primaryProvider: "mapmyindia";
  fallbackProvider: "osm";
  creditsBudgetInr: number;
  budgetGuardEnabled: boolean;
  fallbackReason?: "missing_key" | "api_error" | "credit_guard" | "manual_demo";
};

export type RouteRequest = {
  origin: [number, number]; // [lng, lat]
  destination: [number, number];
  waypoints?: Array<[number, number]>;
  mode: "driving";
};

export type RouteResult = {
  provider: MapProvider;
  polyline: Array<[number, number]>;
  distanceMeters?: number;
  durationSeconds?: number;
  confidence: "provider_route" | "local_demo_route";
};
```

## 4. Backend Configuration

Backend environment variables:

```env
MAP_PROVIDER=mapmyindia
MAP_PRIMARY_PROVIDER=mapmyindia
MAP_FALLBACK_PROVIDER=osm
MAPMYINDIA_API_KEY=replace_with_key
MAPMYINDIA_REST_KEY=replace_if_different
MAPMYINDIA_CREDIT_BUDGET_INR=1000
MAPMYINDIA_DAILY_SOFT_LIMIT_INR=150
MAPMYINDIA_ENABLE_ROUTING=true
MAPMYINDIA_ENABLE_GEOCODING=true
MAPMYINDIA_ENABLE_DISTANCE_MATRIX=false
MAP_FALLBACK_ON_ERROR=true
```

Frontend environment variables:

```env
NEXT_PUBLIC_MAP_PROVIDER=mapmyindia
NEXT_PUBLIC_MAP_FALLBACK_PROVIDER=osm
NEXT_PUBLIC_MAPMYINDIA_MAP_KEY=replace_with_browser_allowed_key
```

Security rule:

- Browser-allowed Mappls SDK keys may be exposed only if MapmyIndia allows that key type.
- Server REST keys must stay backend-only.
- Never commit MapmyIndia keys.

## 5. Budget Guardrails

Because credits are limited to `1000 INR`, MapmyIndia usage must be controlled.

Rules:

- Use MapmyIndia base map on the main map screens.
- Cache route/geocode responses in PostgreSQL or in-memory cache during demo.
- Do not call routing APIs repeatedly on every map pan/zoom.
- Call route APIs only when an event plan is generated or the user explicitly requests route refresh.
- Prefer local overlay rendering for hotspots, impact radius, barricades, and reports.
- Disable optional distance matrix unless there is enough credit headroom.
- Show `/settings` provider status: active provider, fallback status, route cache count, and credit-guard mode.

Suggested local tracking table:

```sql
CREATE TABLE IF NOT EXISTS map_api_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider TEXT NOT NULL,
    api_name TEXT NOT NULL,
    cache_hit BOOLEAN NOT NULL DEFAULT FALSE,
    estimated_cost_inr NUMERIC(8,2) NOT NULL DEFAULT 0,
    request_hash TEXT,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_map_api_usage_provider_created
ON map_api_usage_logs(provider, created_at DESC);
```

## 6. API Endpoints

### `GET /api/map/config`

Returns provider configuration safe for frontend.

```json
{
  "activeProvider": "mapmyindia",
  "primaryProvider": "mapmyindia",
  "fallbackProvider": "osm",
  "mapKeyAvailable": true,
  "creditsBudgetInr": 1000,
  "budgetGuardEnabled": true,
  "fallbackReason": null
}
```

### `POST /api/map/route`

Generates a provider route when allowed, otherwise returns local demo route.

```json
{
  "origin": [77.5946, 12.9716],
  "destination": [77.6850, 12.9308],
  "mode": "driving",
  "purpose": "diversion_plan"
}
```

Response:

```json
{
  "provider": "mapmyindia",
  "polyline": [[77.5946, 12.9716], [77.6100, 12.9600], [77.6850, 12.9308]],
  "distanceMeters": 12400,
  "durationSeconds": 2100,
  "confidence": "provider_route",
  "cached": false
}
```

### `POST /api/map/geocode`

Optional. Converts an address/search text into coordinates. If disabled, frontend uses manual coordinate entry.

## 7. Fallback Rules

Fallback is automatic and visible.

| Failure | Behavior |
|---|---|
| Missing key | Use OSM base map and local demo routes |
| API error | Retry once, then use OSM/local route |
| Credit guard hit | Use OSM/local route and show `credit_guard` fallback reason |
| Browser SDK fails | Render non-map panels and retry button |

Fallback must not break core EventFlow AI features. Predictions, recommendations, reports, and post-event learning still work without MapmyIndia.

## 8. Demo Script

Judge-facing line:

```text
EventFlow AI uses MapmyIndia / Mappls as the primary geospatial layer with our available 1000 INR credits. To keep the prototype reliable, all MapmyIndia calls go through a provider adapter with caching, budget guardrails, and an automatic OSM/MapLibre fallback.
```

## 9. Implementation Priority

1. Implement provider adapter and `/api/map/config`.
2. Render MapmyIndia base map in `/map-intelligence`.
3. Render existing event/hotspot/report overlays on MapmyIndia.
4. Add `/api/map/route` with caching and budget logs.
5. Add local NetworkX route fallback.
6. Add settings health panel for provider/fallback status.
