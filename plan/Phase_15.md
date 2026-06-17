# PHASE 15 — Command Center Explorer Simulation Reports Event Detail Model Insights

## Phase Overview

Build primary web experience and connect all APIs to UI.

This phase is part of EventFlow AI, a predictive traffic command twin for Bengaluru event-driven congestion. The project uses ASTraM historical event data, FastAPI, Next.js, Supabase PostgreSQL free tier, explainable AI/rule-based planning, MapmyIndia/Mappls primary integration using available 1000 INR credits, OpenStreetMap fallback, and only free/open-source APIs or services.

---

## Why This Phase Exists

- **Problem being solved:** Build primary web experience and connect all APIs to UI.
- **User need addressed:** Traffic operators, planners, field officers, citizens, delivery stakeholders, and judges need a reliable implementation step that advances the Predict -> Plan -> Monitor -> Adapt -> Learn workflow.
- **Business requirement satisfied:** This phase supports a complete Flipkart Gridlock 2.0 prototype that demonstrates feasibility, innovation, scalability, security, user experience, and real-world impact.
- **Why now:** This phase depends on Phase 14 and must exist before Post-event dashboard and demo.
- **How it contributes:** It strengthens EventFlow AI as an operational command system rather than a generic dashboard.

---

## Original Intent Preservation

### Original Problem

Bengaluru event-driven congestion needs data-backed planning for impact, manpower, barricading, diversions, live escalation, and post-event learning.

### User Pain Point

Traffic response is often reactive, delayed, and experience-driven. Users need explainable, map-first, action-oriented intelligence.

### Product Goal

Deliver this capability: Build primary web experience and connect all APIs to UI.

### Architecture Goal

Maintain backend-owned business logic, frontend-only rendering/API consumption, database persistence through Supabase PostgreSQL, and map provider independence.

### Security Goal

Protect sensitive ASTraM fields, avoid frontend database credentials, enforce three-level access, validate all inputs, rate-limit risky endpoints, and prevent untrusted reports from becoming official automatically.

### Scalability Goal

Keep this phase modular so future phases and production integrations can extend it without breaking contracts.

### Performance Goal

Support MVP targets: dashboard under 5 seconds, simulation under 3 seconds, event-plan generation under 5 seconds, map layer toggles under 2 seconds, and CSV processing under 30 seconds where applicable.

---

## Expected Outcome

After completion:

- **New functionality:** Build primary web experience and connect all APIs to UI.
- **New APIs:** All MVP APIs
- **New workflows:** The product moves forward in the end-to-end traffic command workflow.
- **New capabilities:** Post-event dashboard and demo
- **New infrastructure:** frontend/app/command-center/page.tsx; frontend/app/admin/page.tsx; frontend/app/officer/page.tsx; frontend/app/explorer/page.tsx; frontend/app/simulation/page.tsx; frontend/app/events/[id]/page.tsx; frontend/app/model-insights/page.tsx; frontend/lib/firebase.ts; frontend/lib/auth.ts; frontend/lib/authHeaders.ts; frontend/lib/i18n.ts
- **New data models:** All core tables

---

## Full Implementation Requirements

Implementation agents must create executable production-ready source files for every path listed in this phase.

Required implementation standards:

- Complete imports, classes, interfaces, functions, DTOs, models, controllers, services, repositories, middleware, tests, and configuration must be written by the implementation agent.
- No paid APIs may be introduced.
- No placeholder or TODO code may be committed.
- All code must be directly executable in the repository.
- All outputs must preserve EventFlow AI's dataset-honest wording: Dataset-backed, Predicted, Estimated, Recommended, Simulated, or Future integration.

### Exact Repository Paths For This Phase

- frontend/app/command-center/page.tsx
- frontend/app/admin/page.tsx
- frontend/app/officer/page.tsx
- frontend/app/explorer/page.tsx
- frontend/app/simulation/page.tsx
- frontend/app/events/[id]/page.tsx
- frontend/app/model-insights/page.tsx
- frontend/lib/firebase.ts
- frontend/lib/auth.ts
- frontend/lib/authHeaders.ts
- frontend/lib/i18n.ts


## Implementation Code Snippets

### `frontend/lib/firebase.ts`
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

### `frontend/lib/auth.ts`
```ts
import {
  browserLocalPersistence,
  onAuthStateChanged,
  setPersistence,
  signInWithEmailAndPassword,
  signOut,
  type User,
} from 'firebase/auth';
import { firebaseAuth } from './firebase';

export type FirebaseSession = {
  uid: string;
  email: string | null;
  idToken: string;
};

export async function loginWithFirebase(email: string, password: string): Promise<FirebaseSession> {
  await setPersistence(firebaseAuth, browserLocalPersistence);
  const credential = await signInWithEmailAndPassword(firebaseAuth, email, password);
  return {
    uid: credential.user.uid,
    email: credential.user.email,
    idToken: await credential.user.getIdToken(),
  };
}

export async function getCurrentFirebaseToken(forceRefresh = false): Promise<string | undefined> {
  const user = firebaseAuth.currentUser;
  if (!user) return undefined;
  return user.getIdToken(forceRefresh);
}

export function listenToFirebaseUser(callback: (user: User | null) => void): () => void {
  return onAuthStateChanged(firebaseAuth, callback);
}

export async function logoutFirebase(): Promise<void> {
  await signOut(firebaseAuth);
}
```

### `frontend/lib/stores/useCommandStore.ts`
```ts
import { create } from 'zustand';

type CommandState = {
  selectedEventId?: string;
  activeLayers: string[];
  language: 'en' | 'kn' | 'hi';
  setSelectedEventId: (eventId?: string) => void;
  toggleLayer: (layer: string) => void;
};

export const useCommandStore = create<CommandState>((set) => ({
  selectedEventId: undefined,
  activeLayers: ['events', 'hotspots', 'recommendations'],
  language: 'en',
  setSelectedEventId: (eventId) => set({ selectedEventId: eventId }),
  toggleLayer: (layer) => set((state) => ({
    activeLayers: state.activeLayers.includes(layer)
      ? state.activeLayers.filter((item) => item !== layer)
      : [...state.activeLayers, layer],
  })),
}));
```

### `frontend/lib/stores/useSessionStore.ts`
```ts
import { create } from 'zustand';

type AccessLevel = 'admin' | 'control_room' | 'police_officer' | 'public_citizen';

type SessionState = {
  accessLevel: AccessLevel;
  firebaseIdToken?: string;
  firebaseUid?: string;
  officerId?: string;
  policeStation?: string;
  assignedCorridors?: string[];
  assignedZones?: string[];
  setFirebaseSession: (input: {
    accessLevel: AccessLevel;
    firebaseIdToken: string;
    firebaseUid: string;
    officerId?: string;
    policeStation?: string;
    assignedCorridors?: string[];
    assignedZones?: string[];
  }) => void;
  clearSession: () => void;
};

export const useSessionStore = create<SessionState>((set) => ({
  accessLevel: 'public_citizen',
  setFirebaseSession: (input) => set(input),
  clearSession: () => set({
    accessLevel: 'public_citizen',
    firebaseIdToken: undefined,
    firebaseUid: undefined,
    officerId: undefined,
    policeStation: undefined,
    assignedCorridors: undefined,
    assignedZones: undefined,
  }),
}));
```

### `frontend/lib/authHeaders.ts`
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

### `frontend/lib/i18n.ts`
```ts
export type AppLanguage = 'en' | 'kn' | 'hi';

export const labels: Record<AppLanguage, Record<string, string>> = {
  en: {
    commandCenter: 'Command Center',
    reportIssue: 'Report traffic issue',
    submitReport: 'Submit report',
    accepted: 'Report accepted',
  },
  kn: {
    commandCenter: 'ಕಮಾಂಡ್ ಸೆಂಟರ್',
    reportIssue: 'ಸಂಚಾರ ಸಮಸ್ಯೆಯನ್ನು ವರದಿ ಮಾಡಿ',
    submitReport: 'ವರದಿ ಸಲ್ಲಿಸಿ',
    accepted: 'ವರದಿ ಸ್ವೀಕರಿಸಲಾಗಿದೆ',
  },
  hi: {
    commandCenter: 'कमांड सेंटर',
    reportIssue: 'ट्रैफिक समस्या रिपोर्ट करें',
    submitReport: 'रिपोर्ट सबमिट करें',
    accepted: 'रिपोर्ट स्वीकार की गई',
  },
};

export function t(language: AppLanguage, key: string): string {
  return labels[language]?.[key] ?? labels.en[key] ?? key;
}
```

### `frontend/app/command-center/page.tsx`
```tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api';
import { useCommandStore } from '@/lib/stores/useCommandStore';

type CommandSummary = {
  activeEvents: number;
  criticalEvents: number;
  hotspotCount: number;
  latestRecommendationCount: number;
};

export default function CommandCenterPage() {
  const { activeLayers, toggleLayer } = useCommandStore();
  const { data, isLoading, error } = useQuery({
    queryKey: ['command-summary'],
    queryFn: () => apiGet<CommandSummary>('/api/command-center/summary'),
  });

  if (isLoading) return <main className="p-6">Loading command view...</main>;
  if (error) return <main className="p-6">Backend unavailable. Check /api/health.</main>;

  return (
    <main className="grid gap-4 p-6 lg:grid-cols-[320px_1fr]">
      <section className="rounded border p-4">
        <h1 className="text-xl font-semibold">EventFlow AI</h1>
        <p className="text-sm text-slate-600">Predict -> Plan -> Monitor -> Adapt -> Learn</p>
        <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
          <div>Active events: {data?.activeEvents}</div>
          <div>Critical: {data?.criticalEvents}</div>
          <div>Hotspots: {data?.hotspotCount}</div>
          <div>Plans: {data?.latestRecommendationCount}</div>
        </div>
        {['events', 'hotspots', 'recommendations', 'conflicts'].map((layer) => (
          <button key={layer} onClick={() => toggleLayer(layer)} className="mt-3 block rounded border px-3 py-2 text-sm">
            {activeLayers.includes(layer) ? 'Hide' : 'Show'} {layer}
          </button>
        ))}
      </section>
      <section className="min-h-[620px] rounded border p-4">Map intelligence panel mounts here.</section>
    </main>
  );
}
```
---

## Database Requirements

- **Database entities affected:** All core tables
- **Migration requirements:** Create or reuse Alembic migrations when schema changes are required. If this phase only reads existing tables, no new migration is required.
- **SQL statements:** Use SQLAlchemy ORM and parameterized queries. Raw SQL is allowed only for safe analytics/materialized-view style operations.
- **Indexes:** Ensure referenced filters and joins are backed by indexes defined in docs/Database_Design.md.
- **Constraints and foreign keys:** Preserve relationships to events where relevant.
- **Composite indexes:** Add only for high-use filters such as event type + datetime, corridor + priority, report type + created_at.
- **RLS policies:** Not required in MVP because frontend never accesses Supabase directly.
- **Triggers/stored procedures/functions:** Not required in MVP unless explicitly introduced in implementation.
- **Materialized views:** Optional future optimization only.
- **Rollback migrations:** Any schema migration must include a downgrade path or explicit rollback notes.
- **Seed data:** Demo seed data belongs in Phase 17 unless this phase explicitly requires test fixtures.

---

## API Requirements

- **APIs affected:** All MVP APIs
- **Route definitions:** Register under FastAPI /api routers.
- **Request schemas:** Define Pydantic v2 schemas for every body/query payload.
- **Response schemas:** Define typed response objects matching frontend needs.
- **Validation logic:** Validate coordinates, enums, dates, IDs, filters, pagination, text lengths, and file schemas where applicable.
- **Error handling:** Return structured errors with code, message, and details.
- **Authentication:** Enforce the three-level access model: Level 1 Admin / Control Room and Level 2 Registered Police Officer use Firebase Auth email/password with backend role and assignment checks; Level 3 Public / Citizen uses open rate-limited access.
- **Authorization:** Shape responses by access level: admin full internal view, assigned officer operational view, public-safe advisory/report view. Firebase identity must be verified on protected routes, while EventFlow roles and officer assignments remain enforced by FastAPI/PostgreSQL.
- **Rate limiting:** Apply to upload/report/simulation endpoints where relevant.
- **Audit logging:** Log dataset loads, admin actions, officer management, officer field confirmations, report submissions, simulations, live updates, post-event report generation, and model fallbacks without logging secret values.
- **OpenAPI:** FastAPI must expose OpenAPI definitions automatically from schemas.

---

## Frontend Requirements

- **Frontend scope:** /command-center, /admin, /officer, /explorer, /simulation, /reports, /events/[id], /model-insights
- **Pages/components:** Create exact pages/components listed in repository paths.
- **Hooks:** Use typed API hooks with TanStack Query where remote data is fetched.
- **State management:** Use Zustand for selected event, active map layers, simulation state, filter state, and selected UI/report language.
- **Language support:** Use static labels for English (`en`), Kannada (`kn`), and Hindi (`hi`) in public/citizen report surfaces. Do not use paid translation APIs in MVP.
- **Forms:** Validate required fields before API calls.
- **API integrations:** Use frontend/lib/api.ts; never call Supabase directly.
- **Error states:** Backend unavailable, empty dataset, invalid input, provider failure.
- **Loading states:** Skeletons or progress states for every async panel.
- **Empty states:** No data, no recommendations, no reports, no map layers.
- **Permission handling:** Implement three UI access levels: admin/control-room portal, registered officer portal, and public/citizen portal. Frontend gating is UX only; backend authorization remains mandatory.
- **Routing:** Use Next.js App Router.

---

## Infrastructure Requirements

- **Dockerfiles:** Add or update only when the phase needs runtime packaging.
- **docker-compose:** Use for local development services if needed.
- **Kubernetes/Terraform:** Not required for MVP; document as future production option only.
- **CI/CD:** Add tests/build checks when implementation reaches deployable surfaces.
- **Environment configuration:** Add new environment variables to .env.example immediately.
- **Secrets configuration:** Store secrets only in backend or deployment provider secret stores.
- **Monitoring configuration:** Update health/status checks if this phase adds a critical dependency.
- **Logging configuration:** Structured logs for new backend operations.
- **Alerting configuration:** Free monitoring only, primarily /api/health.

---

## Security Requirements

- **Authentication model:** MVP uses Firebase Auth email/password for Level 1 admin/control-room and Level 2 registered officer login, with public rate-limited access for Level 3 citizens.
- **Authorization model:** Backend route-level guards verify Firebase ID tokens, then enforce Level 1 roles, Level 2 assignment-based access, and Level 3 public-safe responses.
- **Threat model:** Protect against invalid input, report spam, Firebase token misuse, Firebase Admin SDK secret exposure, unauthorized officer access, sensitive-field leakage, and map/API provider failure.
- **Secrets management:** No .env commits; no frontend database secrets.
- **Audit requirements:** Log dataset loads, admin actions, officer management, officer field confirmations, simulations, report submissions, and post-event report generation without logging secret values.
- **Encryption requirements:** HTTPS in deployed environments, SSL database connection.
- **Compliance requirements:** No personal citizen identity collection in MVP; mask ASTraM sensitive fields.
- **Security controls:** Pydantic validation, SQLAlchemy parameterization, rate limits, CORS restrictions, structured error handling.

---

## Testing Requirements

### Unit Tests

Create unit tests for every service/function introduced in this phase.

### Integration Tests

Verify API + database + service integration where this phase touches backend persistence.

### E2E Tests

For frontend phases, verify the user workflow through the relevant page.

### Security Tests

Validate sensitive-field masking, invalid payload rejection, rate limits, and no direct Supabase access.

### Performance Tests

Verify the relevant phase target: simulation under 3 seconds, plan generation under 5 seconds, map toggle under 2 seconds, dashboard under 5 seconds, or ingestion under 30 seconds.

### Load Tests

Use lightweight local load tests only for report/simulation endpoints where relevant.

### Contract Tests

Ensure frontend TypeScript types match backend Pydantic response schemas.

---

## Cross-Phase References & Dependency Tracking

- **Required previous phases:** Phase 14
- **Integration method:** This phase reuses previous contracts and creates outputs consumed by Post-event dashboard and demo.
- **Compatibility requirements:** Do not break existing API shapes, database schema contracts, environment variables, or frontend route expectations.
- **Required interfaces:** All MVP APIs
- **Required contracts:** the database entities and file paths listed in this phase plus the shared schema in docs/Database_Design.md.
- **Validation process:** Run this phase's validation commands plus smoke checks for earlier completed phases.

Every dependency is explicit in this file. No previous chat context is required.

## Deliverables

- frontend/app/command-center/page.tsx
- frontend/app/admin/page.tsx
- frontend/app/officer/page.tsx
- frontend/app/explorer/page.tsx
- frontend/app/simulation/page.tsx
- frontend/app/events/[id]/page.tsx
- frontend/app/model-insights/page.tsx
- frontend/lib/firebase.ts
- frontend/lib/auth.ts
- frontend/lib/authHeaders.ts
- frontend/lib/i18n.ts

---

## Technical Design Summary

Build this phase as a modular, testable slice of EventFlow AI. Backend code owns data validation, persistence, AI/rule logic, and sensitive handling. Frontend code owns rendering, interaction, and API consumption. Database access is backend-only. MapmyIndia/Mappls is the primary MVP map provider using available 1000 INR credits; OSM/MapLibre fallback must remain functional through the provider adapter.

---

## Validation Checklist

### Automated Verification

Run the commands listed below and all relevant unit/integration tests.

### Manual Verification

Exercise the user workflow affected by this phase in the browser or API client.

### Integration Verification

Confirm previous phase contracts still work and the new outputs feed future phases.

### Security Verification

Check no sensitive fields or secrets are exposed.

### Performance Verification

Measure the relevant endpoint/page timing against MVP targets.

---

## Validation Commands

```bash
npm run test; npm run build
```

---

## Completion Criteria

Phase is complete only if:

- Code builds successfully.
- Tests pass.
- Security checks pass.
- Performance checks pass for phase-relevant targets.
- Documentation and environment examples are updated.
- Validation checklist passes.
- No paid API dependency is introduced.

---








