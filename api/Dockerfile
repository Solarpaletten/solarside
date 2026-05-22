# --------------------------------------------------------------------
# Solar Core — production Dockerfile
# --------------------------------------------------------------------
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Build deps for asyncpg, pgvector, etc. curl is kept for container healthcheck.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better layer caching)
COPY pyproject.toml README.md ./
COPY solar_core ./solar_core

RUN pip install --upgrade pip \
    && pip install -e .

# Drop build deps to slim the image (curl stays for healthcheck)
RUN apt-get purge -y --auto-remove build-essential

EXPOSE 8000

# Healthcheck hits the real /v1/health route on whatever port we bind.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT:-8000}/v1/health" || exit 1

# Render injects $PORT — bind to it (fallback 8000 for local/compose).
# Shell form so ${PORT} expands. No --reload in production.
CMD uvicorn solar_core.main:app --host 0.0.0.0 --port ${PORT:-8000}
