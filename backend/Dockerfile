# ── Stage 1: Builder ──────────────────────────────────────────────────────────
# Install all Python deps into a venv. Build tools stay in this stage only.
FROM python:3.12-slim AS builder

WORKDIR /build

# Build-time system deps (gcc + libpq headers for psycopg binary wheel)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create isolated venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt


# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
# Lean final image — no build tools, just the venv and app source.
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime-only system deps:
#   libpq5       → psycopg binary runtime
#   postgresql-client → pg_isready used in entrypoint
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built venv from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# ── Application source ────────────────────────────────────────────────────────
# alembic.ini must be at PROJECT_ROOT (/app) — matches config.py parents[3]
COPY alembic.ini ./

# Full backend package (source, alembic migrations, pre-trained ML artifacts,
# model pkl files, and seed/utility scripts)
COPY backend/ ./backend/

# CSV training/seed dataset (needed by seed_demo_data.py and ML scripts)
COPY ["Astram event data_anonymized - Astram event data_anonymizedb40ac87 (1).csv", "./"]

# ── Python path ───────────────────────────────────────────────────────────────
# 'from app.xxx import ...' resolves against /app/backend
ENV PYTHONPATH=/app/backend

# ── Security: non-root user ───────────────────────────────────────────────────
RUN useradd -m -u 1001 appuser \
 && chown -R appuser:appuser /app

# Entrypoint must be executable before switching user
RUN chmod +x /app/backend/docker-entrypoint.sh

USER appuser

# ── Runtime config ────────────────────────────────────────────────────────────
EXPOSE 8000

ENTRYPOINT ["/app/backend/docker-entrypoint.sh"]
