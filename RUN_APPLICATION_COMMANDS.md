# Sanchar Sarthi - Complete Run Commands

Use these commands on Windows PowerShell from the project root.

## 1. Go To Project Root

```powershell
cd C:\Users\Hema\Downloads\FLipkart\FlipKart-Gridlock
```

## 2. Create And Activate Python Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 3. Install Backend Dependencies

```powershell
pip install --upgrade pip
pip install -r backend\requirements.txt
```

## 4. Install Frontend Dependencies

```powershell
npm install --prefix frontend
```

## 5. Create Local Environment File

```powershell
Copy-Item .env.example .env
```

## 6. Recommended Local `.env` For MVP

Open `.env` and use this local-friendly configuration.

```env
APP_NAME="Sanchar Sarthi"
APP_ENV=local
FRONTEND_ORIGIN=http://localhost:3000
DATABASE_URL=
RAW_DATA_PATH="Astram event data_anonymized - Astram event data_anonymizedb40ac87 (1).csv"

FIREBASE_PROJECT_ID=
FIREBASE_CLIENT_EMAIL=
FIREBASE_PRIVATE_KEY=

MAP_PROVIDER=mapmyindia
MAP_PRIMARY_PROVIDER=mapmyindia
MAP_FALLBACK_PROVIDER=osm
MAPMYINDIA_API_KEY=
MAPMYINDIA_REST_KEY=
MAPMYINDIA_CREDIT_BUDGET_INR=1000
MAPMYINDIA_DAILY_SOFT_LIMIT_INR=150
MAPMYINDIA_ENABLE_ROUTING=true
MAPMYINDIA_ENABLE_GEOCODING=true
MAPMYINDIA_ENABLE_DISTANCE_MATRIX=false
MAP_FALLBACK_ON_ERROR=true

OPEN_METEO_ENABLED=true

GOOGLE_TRANSLATE_ENABLED=false
GOOGLE_TRANSLATE_PROVIDER=google
GOOGLE_TRANSLATE_TARGET_LANGUAGE=en
GOOGLE_TRANSLATE_DAILY_CHAR_LIMIT=50000
GOOGLE_TRANSLATE_MONTHLY_CHAR_LIMIT=500000
GOOGLE_TRANSLATE_FAIL_OPEN=true
GOOGLE_CLOUD_PROJECT_ID=
GOOGLE_APPLICATION_CREDENTIALS_JSON=

NEXT_PUBLIC_FIREBASE_API_KEY=
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=
NEXT_PUBLIC_FIREBASE_PROJECT_ID=
NEXT_PUBLIC_MAP_PROVIDER=mapmyindia
NEXT_PUBLIC_MAP_FALLBACK_PROVIDER=osm
NEXT_PUBLIC_MAPMYINDIA_MAP_KEY=
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Notes:
- Keep `DATABASE_URL=` blank for easiest local setup. The backend will fall back to local SQLite and create `eventflow_local.db` in the repo root.
- If Firebase keys are blank, public pages still work, but protected admin, control-room, and officer login flows will not work.
- If MapmyIndia keys are blank, the app should fall back to OSM or demo behavior where supported.
- If you want Google Translate later, switch `GOOGLE_TRANSLATE_ENABLED=true` and add real Google Cloud credentials.

## 7. Run Database Migrations

Run this from the repo root:

```powershell
alembic upgrade head
```

## 8. Load The Main ASTraM Dataset

```powershell
python backend\scripts\seed_demo_data.py
```

## 9. Generate Derived Event Features

```powershell
python backend\scripts\create_features.py
```

## 10. Rebuild Hotspots

```powershell
python backend\scripts\rebuild_hotspots.py
```

## 11. Rebuild Event DNA

```powershell
python backend\scripts\rebuild_event_dna.py
```

## 12. Optional Foundation Seed For Phase 1-3 Flows

This is useful for the user, control-room, and admin foundation incident workflow.

```powershell
python backend\scripts\seed_foundation_data.py
```

## 13. Optional Judge Demo Scenario Seed

This prepares deterministic demo data for settings, walkthroughs, reports, post-event learning, and other showcase screens.

```powershell
python backend\scripts\create_demo_scenarios.py
```

## 14. Optional Train ML Artifacts

Run these if you want model artifacts to appear as loaded in health and model-insights.

```powershell
cd backend
python -m app.ml.train_priority_model
python -m app.ml.train_road_closure_model
python -m app.ml.train_resolution_time_model
cd ..
```

Expected artifacts:

```text
backend/artifacts/priority_model.joblib
backend/artifacts/road_closure_model.joblib
backend/artifacts/resolution_time_model.joblib
```

If these artifacts are missing, the app can still run using dataset-backed or rule-based fallback logic.

## 15. Start The Backend

Open terminal 1:

```powershell
cd C:\Users\Hema\Downloads\FLipkart\FlipKart-Gridlock\backend
..\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend URLs:

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/api/health
```

## 16. Start The Frontend

Open terminal 2:

```powershell
cd C:\Users\Hema\Downloads\FLipkart\FlipKart-Gridlock\frontend
npm run dev
```

Frontend URL:

```text
http://localhost:3000
```

## 17. Main Pages To Open

```text
http://localhost:3000/
http://localhost:3000/user
http://localhost:3000/control-room
http://localhost:3000/admin
http://localhost:3000/officer
http://localhost:3000/reports
http://localhost:3000/command-center
http://localhost:3000/explorer
http://localhost:3000/simulation
http://localhost:3000/map-intelligence
http://localhost:3000/model-insights
http://localhost:3000/post-event-learning
http://localhost:3000/settings
```

## 18. Fastest MVP Run Order

If you want the shortest working local flow, run these in order:

```powershell
cd C:\Users\Hema\Downloads\FLipkart\FlipKart-Gridlock
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
npm install --prefix frontend
Copy-Item .env.example .env
alembic upgrade head
python backend\scripts\seed_demo_data.py
python backend\scripts\create_features.py
python backend\scripts\rebuild_hotspots.py
python backend\scripts\rebuild_event_dna.py
python backend\scripts\seed_foundation_data.py
python backend\scripts\create_demo_scenarios.py
```

Then start backend and frontend in two terminals.

## 19. Validation Commands

### Backend syntax check

```powershell
python -m py_compile backend\app\api\routes_foundation.py
```

### Run all backend tests

```powershell
pytest backend\tests
```

### Run focused foundation tests

```powershell
pytest backend\tests\test_foundation_phase1.py backend\tests\test_foundation_phase2.py backend\tests\test_foundation_phase3.py
```

### Run frontend type check

```powershell
cd frontend
npm run test
cd ..
```

### Run frontend production build

```powershell
cd frontend
npm run build
cd ..
```

### Root frontend build shortcut

```powershell
npm run build
```

## 20. Admin / Control Room / Officer Login Notes

- Public pages can be opened without Firebase.
- Protected actions require valid Firebase-backed users.
- For local UI testing without real Firebase credentials, you can still inspect most public pages, health, model, map, simulation, and dataset-driven screens.
- The foundation seed and demo scenario seed scripts prepare data, but they do not automatically create a working real Firebase login account.

## 21. MapmyIndia Notes

- Browser map key goes in `NEXT_PUBLIC_MAPMYINDIA_MAP_KEY`.
- Backend routing and geocode keys go in `MAPMYINDIA_API_KEY` and `MAPMYINDIA_REST_KEY`.
- If not configured, fallback behavior should keep the app usable for local development.
- For localhost testing, use your local frontend URL such as `http://localhost:3000` in the MapmyIndia dashboard if the key requires browser/domain whitelisting.

## 22. Translation Notes

- MVP works without Google Translate.
- With `GOOGLE_TRANSLATE_ENABLED=false`, the app still supports the platform flow and uses fallback behavior where translation is not configured.
- If enabling Google Translate later, update the `.env` with real Google Cloud credentials before running translation-dependent flows.

## 23. Common Problems

### PowerShell blocks virtual environment activation

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### `alembic upgrade head` fails

Make sure:
- you are in the repo root
- `.env` exists
- `DATABASE_URL` is either valid or blank for SQLite fallback

### Frontend cannot talk to backend

Check:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
FRONTEND_ORIGIN=http://localhost:3000
```

### Firebase login does not work

That is expected if Firebase env values are empty or dummy.

### Models show `Artifact not loaded`

Run:

```powershell
cd backend
python -m app.ml.train_priority_model
python -m app.ml.train_road_closure_model
python -m app.ml.train_resolution_time_model
cd ..
```

## 24. Final Recommended Terminal Setup

### Terminal 1 - backend

```powershell
cd C:\Users\Hema\Downloads\FLipkart\FlipKart-Gridlock\backend
..\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Terminal 2 - frontend

```powershell
cd C:\Users\Hema\Downloads\FLipkart\FlipKart-Gridlock\frontend
npm run dev
```

### Terminal 3 - optional validation

```powershell
cd C:\Users\Hema\Downloads\FLipkart\FlipKart-Gridlock
.\.venv\Scripts\Activate.ps1
pytest backend\tests
```
