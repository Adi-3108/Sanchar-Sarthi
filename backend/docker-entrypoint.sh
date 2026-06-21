#!/usr/bin/env sh
# docker-entrypoint.sh — runs inside the backend container at startup
# Steps:
#   1. Wait for PostgreSQL to be ready
#   2. Run Alembic migrations (idempotent)
#   3. Seed the database on first run only (detected via empty events table)
#   4. Start the Uvicorn server

set -e

# ── Colours ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { printf "${GREEN}[entrypoint]${NC} %s\n" "$*"; }
warn() { printf "${YELLOW}[entrypoint]${NC} %s\n" "$*"; }
err()  { printf "${RED}[entrypoint]${NC} %s\n" "$*"; }

# ── 1. Wait for PostgreSQL ────────────────────────────────────────────────────
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${POSTGRES_USER:-postgres}"

log "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT} ..."

MAX_RETRIES=30
RETRY_INTERVAL=3
attempt=0

until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -q; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge "$MAX_RETRIES" ]; then
        err "PostgreSQL did not become ready after $((MAX_RETRIES * RETRY_INTERVAL))s. Aborting."
        exit 1
    fi
    warn "  PostgreSQL not ready yet (attempt ${attempt}/${MAX_RETRIES}) — retrying in ${RETRY_INTERVAL}s ..."
    sleep "$RETRY_INTERVAL"
done

log "PostgreSQL is ready."

# ── 2. Run migrations in two passes to handle narrow alembic_version column ───
# The initial schema (0001) creates alembic_version with VARCHAR(32).
# Subsequent migration names are >32 chars, causing StringDataRightTruncation.
# Fix: run 0001 first → widen column → run rest of migrations.

log "Running initial schema migration (0001) ..."
alembic upgrade 0001_initial_schema
log "Initial schema applied."

log "Widening alembic_version.version_num to VARCHAR(64) ..."
python - <<'PYEOF'
import os
try:
    import psycopg
    dsn = os.environ.get("DATABASE_URL", "").replace("postgresql+psycopg://", "postgresql://")
    conn = psycopg.connect(dsn)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(64)")
    print("[entrypoint] alembic_version.version_num widened to VARCHAR(64)")
    conn.close()
except Exception as e:
    print(f"[entrypoint] Column patch warning: {e}")
PYEOF

log "Running remaining migrations to head ..."
alembic upgrade head
log "All migrations complete."


# ── 3. Seed database on first run ─────────────────────────────────────────────
# Detect first run by checking if the events table is empty.
# Uses an inline Python snippet so we don't need a separate psql binary format.
log "Checking if database needs seeding ..."

EVENT_COUNT=$(python - <<'PYEOF'
try:
    from app.core.database import build_engine
    from sqlalchemy import text
    engine = build_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM events"))
        print(result.scalar())
except Exception:
    # Table may not exist yet or DB not reachable — treat as unseeded
    print("0")
PYEOF
)

if [ "$EVENT_COUNT" = "0" ]; then
    log "Empty database detected — running seed scripts (first-run only) ..."

    log "  [1/6] Loading ASTraM event dataset ..."
    python backend/scripts/seed_demo_data.py

    log "  [2/6] Generating event features ..."
    python backend/scripts/create_features.py

    log "  [3/6] Rebuilding hotspot clusters ..."
    python backend/scripts/rebuild_hotspots.py

    log "  [4/6] Rebuilding event DNA ..."
    python backend/scripts/rebuild_event_dna.py

    log "  [5/6] Seeding foundation data (users/officers) ..."
    python backend/scripts/seed_foundation_data.py

    log "  [6/6] Creating demo scenarios ..."
    python backend/scripts/create_demo_scenarios.py

    log "Database seeding complete."
else
    log "Database already seeded (${EVENT_COUNT} events found) — skipping seed step."
fi

# ── 4. Start Uvicorn ──────────────────────────────────────────────────────────
log "Starting Uvicorn on 0.0.0.0:8000 ..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --log-level info
