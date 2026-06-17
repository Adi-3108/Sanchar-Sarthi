# EventFlow AI

EventFlow AI is a predictive traffic command twin for Bengaluru event-driven congestion. This repository is organized as a monorepo with a FastAPI backend and a Next.js frontend, following the phased build plan in [plan/README.md](/C:/Users/uadit/Desktop/FLipkart/plan/README.md).

## Phase 1 Status

Phase 1 establishes:

- a FastAPI application shell with a typed `GET /api/health` endpoint
- Firebase bootstrap and authorization primitives for later protected routes
- a Next.js App Router frontend with a command-center landing experience
- environment documentation for backend, Firebase, and map providers
- baseline backend tests for config, health, Firebase bootstrap, and auth guards

Phase 2 adds:

- SQLAlchemy models for the core EventFlow schema
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

The base MVP remains free-tier and dataset-honest. Optional Google Translate support stays disabled by default.
