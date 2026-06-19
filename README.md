# Sanchar Sarthi

Sanchar Sarthi is a predictive traffic incident and response platform for Bengaluru. This repository is organized as a monorepo with a FastAPI backend and a Next.js frontend.

## Phase 1 Status

Phase 1 establishes:

- a FastAPI application shell with a typed `GET /api/health` endpoint
- Firebase bootstrap and authorization primitives for later protected routes
- a Next.js App Router frontend with a command-center landing experience
- environment documentation for backend, Firebase, and map providers
- baseline backend tests for config, health, Firebase bootstrap, and auth guards

Phase 2 adds:

- SQLAlchemy models for the core Sanchar Sarthi schema
- Alembic migration support for the initial database
- backend database sessions and health-aware connectivity checks

Phase 3 adds:

- ASTraM CSV cleaning, masking, and ingestion services
- protected dataset upload and bundled demo-load endpoints
- backend scripts for loading the bundled Bengaluru event dataset

Phase 4 adds:

- derived event feature generation with duration fallback and historical risk rates
- a protected feature rebuild endpoint for admin/control-room operators
- backend scripts and tests for rebuilding `event_features`

Phase 5 adds:

- dataset-backed hotspot clustering and persisted hotspot profiles
- analytics APIs for hotspot overlays and operational summary metrics
- a reusable frontend `HotspotLayer` component contract for map overlays

Phase 6 adds:

- Event DNA persistence built from structured fields plus safe normalized text
- similar-event memory scoring and internal event dossier retrieval
- frontend recommendation components for Event DNA and historical memory panels

Phase 7 adds:

- prediction diagnostics, artifact metadata, and protected model-run visibility
- dataset-backed road-closure likelihood and resolution-time estimation
- event simulation support for internal operational testing

Phase 8 adds:

- impact scoring, counterfactual deltas, and impact-category classification
- vehicle-sensitive impact adjustment and simulation-ready impact summaries
- richer prediction contracts for event detail and simulation workflows

Phase 9 adds:

- recommendation planning for manpower, barricades, diversions, emergency corridors, and Flipkart logistics impact
- a protected `POST /api/recommendations/event-plan` endpoint with officer-assignment enforcement
- typed recommendation payloads reused by event detail and simulation responses

Phase 10 adds:

- weather-aware impact adjustment for simulation and event-plan workflows
- optional Open-Meteo-backed weather resolution with safe neutral fallback behavior
- rain, waterlogging, and low-visibility modifiers for barricade and diversion recommendations

Phase 11 adds:

- citizen, field-officer, and control-room report intake with confidence scoring
- multilingual public report UI with static English, Kannada, and Hindi labels
- persisted report matching, audit logging, and public rate limiting

Phase 12 adds:

- protected live escalation updates for assigned officers and control-room operators
- adaptive alert-level guidance that compares expected and current impact
- persisted live update timelines reused by event dossiers

Phase 13 adds:

- multi-event conflict analysis across time overlap, impact radius, diversion conflict, and manpower gap
- protected `POST /api/events/multi-event-analysis` coordination workflow
- conflict overlays and structured coordination summaries

Phase 14 adds:

- MapmyIndia / Mappls provider adapter with OSM fallback and budget guardrails
- protected route and geocode APIs plus map usage logging
- operational map layers for events, hotspots, reports, routes, and conflicts

Phase 15 adds:

- role-aware admin, officer, explorer, simulation, map, report, and event-dossier pages
- Firebase-backed frontend auth helpers and shared API contracts
- mounted recommendation, Event DNA, weather, escalation, and conflict UI panels

Phase 16 adds:

- persisted post-event learning reports and after-action summaries
- protected `POST /api/events/{event_id}/post-event-report` generation workflow
- a `/post-event-learning` screen for generating future-playbook reviews

## Repository Layout

```text
backend/
  app/
  tests/
  requirements.txt
frontend/
  app/
  components/
  lib/
docs/
plan/
future/
```

## Local Development

1. Create a virtual environment and install backend dependencies:

   ```bash
   pip install -r backend/requirements.txt
   ```

   Use Python 3.11 or newer for the backend and ML scripts.

2. Install frontend dependencies:

   ```bash
   npm install --prefix frontend
   ```

3. Copy `.env.example` to `.env` and provide real credentials only where needed.
   If `DATABASE_URL` is omitted, the backend falls back to a local SQLite database for local development and scripts.

4. Run the backend from the `backend` directory:

   ```bash
   python -m uvicorn app.main:app --reload
   ```

5. Run the frontend from the `frontend` directory:

   ```bash
   npm run dev
   ```

## Validation

- Root frontend build:

  ```bash
  npm run build
  ```

- Backend tests:

  ```bash
  pytest backend/tests
  ```

- Database migration smoke check:
  This uses the SQLite fallback in `alembic.ini` unless `DATABASE_URL` is set in your shell or `.env`.

  ```bash
  alembic upgrade head
  ```

- Dataset load smoke check:

  ```bash
  python backend/scripts/seed_demo_data.py
  ```

- Feature generation smoke check:

  ```bash
  python backend/scripts/create_features.py
  ```

- Hotspot rebuild smoke check:

  ```bash
  python backend/scripts/rebuild_hotspots.py
  ```

- Event DNA rebuild smoke check:

  ```bash
  python backend/scripts/rebuild_event_dna.py
  ```

- Recommendation workflow smoke check:

  ```bash
  pytest backend/tests/test_recommendations.py
  ```

- Weather workflow smoke check:

  ```bash
  pytest backend/tests/test_weather_service.py
  ```

- Reports, escalation, coordination, and map workflow smoke checks:

  ```bash
  pytest backend/tests/test_citizen_reports.py backend/tests/test_live_escalation.py backend/tests/test_multi_event_service.py backend/tests/test_map_routes.py
  ```

- Post-event learning smoke check:

  ```bash
  pytest backend/tests/test_post_event_report.py
  ```

The base MVP remains free-tier and dataset-honest. Optional Google Translate support stays disabled by default.
