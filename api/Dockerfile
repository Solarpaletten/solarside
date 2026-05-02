# --------------------------------------------------------------------
# Solar Core — production Dockerfile
# --------------------------------------------------------------------
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Build deps for asyncpg, pgvector, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better layer caching)
COPY pyproject.toml README.md ./
COPY solar_core ./solar_core

RUN pip install --upgrade pip \
    && pip install -e .

# Drop build deps to slim the image
RUN apt-get purge -y --auto-remove build-essential

EXPOSE 8000

# Default command — override in compose for development
CMD ["uvicorn", "solar_core.main:app", "--host", "0.0.0.0", "--port", "8000"]
