# Manual Testing Guide

This guide is for manual testing after both backend and frontend environment files are set up.

## 1. Start The App

From repo root, start the backend:

```powershell
python -m uvicorn app.main:app --reload --app-dir backend --port 8000
```

In a second terminal, start the frontend:

```powershell
npm --prefix frontend run dev
```

## 2. First Smoke Checks

Verify these before testing flows:

1. Open `http://localhost:8000/api/health`
2. Open `http://localhost:8000/docs`
3. Open `http://localhost:3000`

Expected:

- `/api/health` returns `status: ok`
- Swagger loads at `/docs`
- Frontend redirects to `/command-center`

## 3. Demo Firebase Accounts

Use these demo users:

- `control.room.demo@eventflow.local` / `DemoPass@123`
- `officer.hsr.demo@eventflow.local` / `DemoPass@123`
- `officer.peenya.demo@eventflow.local` / `DemoPass@123`

## 4. Seeded Demo Event IDs

These are useful for testing:

- `DEMO_EVENT_RALLY_ORR`
- `DEMO_EVENT_CROWD_IBLUR`
- `DEMO_EVENT_WATERLOGGING_HSR`
- `DEMO_EVENT_BREAKDOWN_TUMKUR`
- `DEMO_EVENT_CONSTRUCTION_TUMKUR`
- `DEMO_EVENT_ACCIDENT_PEENYA`

## 5. Expected Seeded State

Current local demo-ready counts:

- `events=8179`
- `event_dna=8179`
- `user_accounts=3`
- `police_officer_profiles=2`
- `event_predictions=6`
- `event_recommendations=6`
- `demo_scenarios=4`

## 6. Recommended Test Order

### 6.1 Command Center

Open `http://localhost:3000/command-center`

Check:

- backend health card loads
- navigation links work
- no blank/error shell state

### 6.2 Demo Readiness

Open `http://localhost:3000/settings`

Sign in as:

- `control.room.demo@eventflow.local`

Check:

- demo readiness loads
- scenario cards are visible
- quick launch links open
- seeded demo counts appear

### 6.3 Admin Portal

Open `http://localhost:3000/admin`

Check:

- backend health info loads
- dataset snapshot loads
- model run block loads
- map provider block loads
- protected actions are enabled after sign-in

Note:

- do not press dataset reload or feature generation buttons unless you intentionally want to rerun them

### 6.4 Explorer

Open `http://localhost:3000/explorer`

Check:

- hotspot list loads after sign-in
- cluster type filters work
- opening a dossier by event ID works

Suggested event:

- `DEMO_EVENT_RALLY_ORR`

### 6.5 Event Dossier

Open:

- `http://localhost:3000/events/DEMO_EVENT_RALLY_ORR`

Check:

- event detail loads
- features load
- Event DNA loads
- prediction loads
- recommendation loads
- similar events load
- map overlays load

### 6.6 Simulation

Open `http://localhost:3000/simulation`

Stay signed in as control-room/admin and run one simulation with default values.

Check:

- predicted priority appears
- impact category appears
- Event DNA card appears
- weather panel appears
- manpower plan appears
- barricade plan appears
- diversion plan appears
- emergency corridor appears
- logistics impact appears

### 6.7 Map Intelligence

Open `http://localhost:3000/map-intelligence`

Check:

- hotspot overlays load
- provider status loads
- `Refresh demo route` works
- geocode search works for `MG Road, Bengaluru`
- multi-event analysis works

Suggested multi-event pair:

- `DEMO_EVENT_BREAKDOWN_TUMKUR, DEMO_EVENT_CONSTRUCTION_TUMKUR`

Expected:

- conflict output appears
- conflict overlays appear

### 6.8 Officer Portal

Open `http://localhost:3000/officer`

Sign in first as:

- `officer.hsr.demo@eventflow.local`

Check:

- assignments load
- assigned event auto-fills
- event detail is visible
- live update submission works

Repeat once with:

- `officer.peenya.demo@eventflow.local`

Goal:

- confirm assignment scoping works for both demo officers

### 6.9 Post-Event Learning

Open `http://localhost:3000/post-event-learning`

Use:

- `DEMO_EVENT_WATERLOGGING_HSR`

Check:

- report generation works
- event summary appears
- lessons learned appear
- future recommendations appear

### 6.10 Public Report Flow

Open `http://localhost:3000/reports`

Test this without login.

Suggested inputs:

- Bengaluru coordinates: `12.9716`, `77.5946`
- report type: `congestion` or `road_blockage`

Check:

- submission succeeds
- confidence appears
- alert level appears
- matched event or not-matched result appears
- recommended action appears

## 7. Useful Walkthrough Anchors

These are the best seeded anchors for end-to-end checks:

- Predict and plan: `DEMO_EVENT_RALLY_ORR`
- Live escalation / learning: `DEMO_EVENT_WATERLOGGING_HSR`
- Multi-event coordination: `DEMO_EVENT_BREAKDOWN_TUMKUR` + `DEMO_EVENT_CONSTRUCTION_TUMKUR`

## 8. Troubleshooting

### 8.1 401 Or 403 Errors

Usually means:

- Firebase login succeeded
- backend role check failed, or
- officer assignment check failed

### 8.2 Frontend Loads But Protected Data Does Not

Check:

- browser console
- backend terminal logs
- Firebase sign-in state

### 8.3 SQLite Database Locked

If backend reports DB locked:

1. close stray `python.exe` processes from Task Manager
2. restart only the backend server

### 8.4 What Not To Rerun During Manual Testing

Avoid rerunning heavy setup unless you intentionally want a refresh:

- `rebuild_event_dna.py`
- dataset reload scripts
- feature rebuild scripts
- demo seeding scripts

## 9. Suggested Minimal End-To-End Pass

If you want the shortest meaningful verification pass, test in this order:

1. `/command-center`
2. `/settings`
3. `/events/DEMO_EVENT_RALLY_ORR`
4. `/simulation`
5. `/map-intelligence`
6. `/officer`
7. `/post-event-learning`
8. `/reports`
