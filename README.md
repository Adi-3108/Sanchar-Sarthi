# EventFlow AI

EventFlow AI is a predictive traffic command twin for Bengaluru event-driven congestion. This repository is organized as a monorepo with a FastAPI backend and a Next.js frontend, following the phased build plan in [plan/README.md](/C:/Users/uadit/Desktop/FLipkart/plan/README.md).

## Phase 1 Status

Phase 1 establishes:

- a FastAPI application shell with a typed `GET /api/health` endpoint
- Firebase bootstrap and authorization primitives for later protected routes
- a Next.js App Router frontend with a command-center landing experience
- environment documentation for backend, Firebase, and map providers
- baseline backend tests for config, health, Firebase bootstrap, and auth guards

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

2. Install frontend dependencies:

   ```bash
   npm install --prefix frontend
   ```

3. Copy `.env.example` to `.env` and provide real credentials only where needed.

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

The base MVP remains free-tier and dataset-honest. Optional Google Translate support stays disabled by default.
