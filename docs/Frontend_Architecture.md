# EventFlow AI Frontend Architecture

## 1. Technology Stack

| Technology | Purpose | Why Selected | Free/Open Source |
|---|---|---|---|
| Next.js 14+ | Web app framework | Routing, SSR option, Vercel deploy | Yes |
| TypeScript | Type safety | Safer implementation handoff | Yes |
| Tailwind CSS | Styling | Fast, consistent dashboard UI | Yes |
| MapmyIndia/Mappls SDK | Primary map provider | Uses available 1000 INR credits for Bengaluru map, routing, and corridor visualization | Paid credits available |
| ECharts/Recharts | Charts | Operational dashboards | Yes |
| Zustand | Client state | Simple map/filter/simulation state | Yes |
| TanStack Query | Server state | API caching/retry/loading states | Yes |
| Firebase Auth client SDK | Admin/officer login | Free email/password auth for MVP | Free tier |

## 2. Folder Structure

```text
frontend/
  app/
    page.tsx
    command-center/page.tsx
    admin/page.tsx
    officer/page.tsx
    explorer/page.tsx
    simulation/page.tsx
    map-intelligence/page.tsx
    reports/page.tsx
    events/[id]/page.tsx
    post-event-learning/page.tsx
    model-insights/page.tsx
    settings/page.tsx
  components/
    layout/
    map/
    charts/
    command/
    reports/
    recommendations/
    ui/
  features/
    analytics/
    citizen-reports/
    events/
    map-layers/
    model-insights/
    recommendations/
    simulation/
  hooks/
    use-events.ts
    use-simulation.ts
    use-hotspots.ts
    use-citizen-reports.ts
    use-session.ts
    use-officer-assignments.ts
  lib/
    api.ts
    auth.ts
    authHeaders.ts
    firebase.ts
    constants.ts
    formatters.ts
    map-provider.ts
    map-utils.ts
    risk-utils.ts
    role-utils.ts
  stores/
    use-event-store.ts
    use-map-layer-store.ts
    use-simulation-store.ts
    use-session-store.ts
  styles/
    globals.css
  types/
    analytics.ts
    event.ts
    map.ts
    recommendation.ts
    report.ts
```

## 3. Routing Architecture

| Route | Purpose |
|---|---|
| `/` | Redirect to `/command-center` |
| `/command-center` | Admin/control-room operational dashboard |
| `/admin` | Level 1 admin portal for officer management, dataset/demo actions, and system controls |
| `/officer` | Level 2 registered police officer portal for assigned events, routes, field updates, and report confirmation |
| `/explorer` | Historical ASTraM analytics |
| `/simulation` | New event planning lab |
| `/map-intelligence` | Full map overlays |
| `/reports` | Level 3 public/citizen report intake |
| `/events/[id]` | Event intelligence dossier |
| `/post-event-learning` | After-action reports |
| `/model-insights` | AI metrics and limitations |
| `/settings` | Demo assumptions and health |

## 4. Component Architecture

Signature components:

- `EventDNACard`
- `SimilarEventMemoryPanel`
- `ImpactScorePanel`
- `CounterfactualImpactCard`
- `ActionConfidenceLedger`
- `ManpowerPlanPanel`
- `BarricadePlanPanel`
- `DiversionPlanPanel`
- `WeatherRiskPanel`
- `MultiEventConflictPanel`
- `EmergencyCorridorPanel`
- `FlipkartLogisticsImpactPanel`
- `PostEventPlaybookPanel`

Map components:

- `MapCanvas`
- `MapProviderAdapter`
- `MapmyIndiaProvider`
- `OsmFallbackProvider`
- `EventMarkerLayer`
- `HotspotLayer`
- `ImpactRadiusLayer`
- `CitizenReportLayer`
- `DeploymentLayer`
- `BarricadeLayer`
- `DiversionRouteLayer`
- `EmergencyCorridorLayer`
- `MultiEventConflictLayer`

## 5. State Management

Zustand stores:

- current access level: admin, control_room, police_officer, public/citizen
- Firebase user session, ID token, role, and officer assignment context
- selected event
- selected hotspot
- active map layers
- simulation form draft
- current alert state
- selected language for citizen report page

TanStack Query manages:

- event list
- dashboard summary
- hotspots
- event detail
- simulation responses
- report submissions
- post-event report generation

## 6. API Layer

`frontend/lib/api.ts` exposes typed functions:

```ts
getHealth()
loadDemoDataset()
createOfficer()
loginWithFirebase()
logout()
getOfficerAssignments()
getSummary()
getEvents(filters)
getEventDetail(eventId)
getHotspots(filters)
simulateEvent(payload)
generateEventPlan(payload)
submitCitizenReport(payload)
submitLiveUpdate(eventId, payload)
analyzeMultiEvent(payload)
generatePostEventReport(eventId)
```

Access rules in frontend:

- Level 1 admin/control-room users sign in with Firebase Auth email/password.
- Level 2 officer users sign in with Firebase Auth email/password.
- Level 3 public screens require no login and must hide internal data.
- Frontend sends Firebase ID token to FastAPI as `Authorization: Bearer <token>`.
- Officer portal must call `GET /api/officer/assignments` after login and store `officer_id`, `police_station`, `assigned_corridors`, and `assigned_zones` in session state.
- Officer screens may hide unassigned routes/events for UX, but the backend remains the final authority for assignment checks.
- Frontend must never store Firebase Admin SDK service account secrets.
- UI gating is only for experience; backend authorization remains mandatory.

Suggested Firebase-aware API helper:

```ts
import { getCurrentFirebaseToken } from './auth';

export async function authHeaders(): Promise<HeadersInit> {
  const token = await getCurrentFirebaseToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}
```

Suggested Firebase client setup:

```ts
import { initializeApp, getApps } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY!,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN!,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID!,
};

const firebaseApp = getApps().length ? getApps()[0] : initializeApp(firebaseConfig);

export const firebaseAuth = getAuth(firebaseApp);
```

Suggested Firebase login helper:

```ts
import { signInWithEmailAndPassword, signOut } from 'firebase/auth';
import { firebaseAuth } from './firebase';

export async function loginWithFirebase(email: string, password: string) {
  const credential = await signInWithEmailAndPassword(firebaseAuth, email, password);
  const idToken = await credential.user.getIdToken();
  return {
    uid: credential.user.uid,
    email: credential.user.email,
    idToken,
  };
}

export async function getCurrentFirebaseToken(forceRefresh = false): Promise<string | undefined> {
  const user = firebaseAuth.currentUser;
  if (!user) return undefined;
  return user.getIdToken(forceRefresh);
}

export async function logoutFirebase(): Promise<void> {
  await signOut(firebaseAuth);
}
```

Full Firebase login/session implementation is specified in `docs/Firebase_Auth_Implementation.md`.

## 7. Design System

Visual direction: dark civic command center, not generic SaaS.

Colors:

```text
App Background #0B0F14
Panel Background #101820
Elevated Panel #151F2A
Border #233142
Primary Text #E6EDF3
Secondary Text #9FB0C3
Low #2FBF71
Medium #F2C94C
High #F2994A
Critical #EB5757
Road Closure #9B51E0
Citizen Report #56CCF2
Field Report #2F80ED
```

All colors must have operational meaning.

## 8. Accessibility

- Risk labels use color + text + shape/icon.
- All forms are keyboard-accessible.
- Map layers have text alternatives in side drawers.
- Citizen report screen supports English/Kannada/Hindi labels in base MVP.
- Citizen report description input accepts any language; optional Phase 19 translates descriptions server-side through Google Translate.
- Minimum text size 13px.

## 9. Performance Optimizations

- Paginate event tables.
- Use map clustering for large marker sets.
- Memoize map layer data.
- Cache MapmyIndia route/geocode responses and avoid API calls on pan/zoom.
- Use MapmyIndia route APIs only on explicit plan generation or route refresh.
- Show a clear Mappls unavailable state if MapmyIndia fails or the credit guard is hit.
- Cache analytics API results through TanStack Query.
- Lazy-load heavy map and chart components.
- Keep dashboard initial load under 5 seconds.
