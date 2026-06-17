# EventFlow AI Infrastructure And Deployment Architecture

## 1. Environments

| Environment | Purpose |
|---|---|
| Development | Local coding and testing |
| Staging | Optional free deployment for demo rehearsal |
| Production/Demo | Hackathon judge-facing deployment |

## 2. Free-Tier Deployment

| Component | Preferred | Alternative |
|---|---|---|
| Frontend | Vercel free tier | Netlify free tier |
| Backend | Render/Railway free tier | Fly.io free allowance if available |
| Database | Supabase PostgreSQL free tier | Neon free tier |
| Maps | MapmyIndia/Mappls using available 1000 INR credits | OSM + MapLibre fallback |
| Weather | Open-Meteo | Manual selector |
| Monitoring | UptimeRobot free | GitHub Actions cron |

## 3. Build Process

Frontend:

```text
npm install
npm run lint
npm run build
```

Backend:

```text
pip install -r requirements.txt
pytest
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## 3.1 Environment Variables

Backend-only variables:

```env
DATABASE_URL=postgresql+psycopg://...
ENABLE_DEMO_MODE=true
FIREBASE_PROJECT_ID=eventflow-ai-demo
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@eventflow-ai-demo.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
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
OPEN_METEO_ENABLED=true
GOOGLE_TRANSLATE_ENABLED=false
GOOGLE_TRANSLATE_PROVIDER=google
GOOGLE_TRANSLATE_TARGET_LANGUAGE=en
GOOGLE_TRANSLATE_DAILY_CHAR_LIMIT=50000
GOOGLE_TRANSLATE_MONTHLY_CHAR_LIMIT=500000
GOOGLE_TRANSLATE_FAIL_OPEN=true
GOOGLE_CLOUD_PROJECT_ID=eventflow-ai-demo
GOOGLE_APPLICATION_CREDENTIALS_JSON=
```

Frontend public variables:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_MAP_PROVIDER=mapmyindia
NEXT_PUBLIC_MAP_FALLBACK_PROVIDER=osm
NEXT_PUBLIC_MAPMYINDIA_MAP_KEY=replace_with_browser_allowed_key
NEXT_PUBLIC_FIREBASE_API_KEY=public_web_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=eventflow-ai-demo.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=eventflow-ai-demo
```

Rules:

- Firebase Admin SDK credentials must be configured only in backend deployment secrets.
- Firebase private key/client email must never be placed in `NEXT_PUBLIC_*`.
- Firebase web config values are allowed in frontend public variables.
- MVP uses Firebase Auth email/password for Level 1 Admin / Control Room and Level 2 Registered Police Officer login.
- If Firebase Admin SDK is missing, protected Level 1 and Level 2 routes must return a clear auth configuration error.
- MapmyIndia/Mappls is the primary MVP map provider because 1000 INR credits are available.
- MapmyIndia server REST keys must stay backend-only unless MapmyIndia explicitly provides a browser-safe map SDK key.
- Route/geocode calls must be cached and budget-guarded.
- If MapmyIndia fails or credit guard is hit, app must automatically switch to OSM/MapLibre and local demo route overlays.
- Google Translate is optional Phase 19. Credentials must stay backend-only, translation must be disabled by default, and budget limits must be configured before enabling it.

## 4. Deployment Flow

```mermaid
flowchart TD
    A["Merge to main"] --> B["GitHub Actions"]
    B --> C["Run frontend checks"]
    B --> D["Run backend tests"]
    C --> E["Deploy Next.js to Vercel"]
    D --> F["Deploy FastAPI to Render/Railway"]
    F --> G["Run Alembic migrations"]
    G --> H["Seed Firebase-linked demo users/officers and load demo dataset if needed"]
    H --> I["Health check"]
```

## 5. Rollback Strategy

- Frontend: Vercel previous deployment rollback.
- Backend: redeploy previous Git commit.
- Database: Alembic downgrade only for safe reversible migrations.
- Demo fallback: local run with preloaded demo data.

## 6. Backup Strategy

MVP:

- Keep source CSV in repo or secure local data folder if allowed.
- Export Supabase SQL dump before final demo.

Production:

- Scheduled database backups.
- Archived event/report exports.

## 7. Disaster Recovery

If hosted backend fails:

- Run locally and expose via local demo.
- Use static demo JSON fallback for frontend.

If map provider fails:

- Switch to OSM fallback.

If weather API fails:

- Manual weather selector.

## 8. Free Dependency Comparison

| Dependency | Purpose | Free Limits | Advantages | Disadvantages |
|---|---|---|---|---|
| Supabase | PostgreSQL | Free project limits | easy hosted DB | sleep/limits possible |
| Neon | PostgreSQL alternative | Free compute/storage limits | serverless Postgres | cold starts |
| Vercel | frontend | free hobby limits | Next.js native | serverless constraints |
| Render | backend | free sleep possible | simple FastAPI deploy | cold starts |
| MapmyIndia/Mappls | primary maps/routes | 1000 INR credits available | India-local map/routing partner fit | credits must be guarded |
| MapLibre + OSM | fallback maps | free/open | no paid key | limited routing/geocoding |
| Open-Meteo | weather | free no key | reliable free weather | may lack hyperlocal nuance |
