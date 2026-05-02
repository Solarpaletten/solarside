# Migration: standalone projects → monorepo (v1)

**Date:** 2026-05-02
**Scope:** Restructure two standalone repos (`solar-core/`, `solar-side/`) into a single monorepo (`solar/`). No code changes; only file relocation and a few path fixes.

## Result

```
solar/
├── api/                ← was solar-core/
├── app/
│   └── solar-side/     ← was solar-side/
├── packages/           ← reserved (placeholder)
├── infra/              ← docker compose + postgres init
├── docs/               ← ADRs + future notes
├── scripts/            ← developer convenience
├── .gitignore
└── README.md
```

## Changes

### Moved

| From                                     | To                                      | Why                                            |
|------------------------------------------|-----------------------------------------|------------------------------------------------|
| `solar-core/solar_core/`                 | `solar/api/solar_core/`                 | Backend Python package                         |
| `solar-core/tests/`                      | `solar/api/tests/`                      | Test suite stays with the package it tests     |
| `solar-core/pyproject.toml`              | `solar/api/pyproject.toml`              | Per-target build config                        |
| `solar-core/Dockerfile`                  | `solar/api/Dockerfile`                  | Per-target container build                     |
| `solar-core/.env.example`                | `solar/api/.env.example`                | Per-target env template                        |
| `solar-core/docs/adr/*`                  | `solar/docs/adr/*`                      | Architecture decisions are project-wide        |
| `solar-core/docs/future/*`               | `solar/docs/future/*`                   | Same                                           |
| `solar-core/docker-compose.yml`          | `solar/infra/docker-compose.yml`        | Infra is project-wide                          |
| `solar-core/scripts/init-pgvector.sql`   | `solar/infra/postgres/init-pgvector.sql`| Lives next to the service it initialises       |
| `solar-core/scripts/demo.sh`             | `solar/scripts/demo.sh`                 | Developer convenience, project-wide            |
| `solar-core/.gitignore`                  | `solar/.gitignore` (extended)           | Single ignore at the monorepo root             |
| `solar-side/`                            | `solar/app/solar-side/`                 | Extension is one of multiple future clients    |

### Created

- `solar/README.md` — top-level overview
- `solar/api/README.md` — short, points back to top-level
- `solar/packages/README.md` — placeholder explanation

### Deleted

- All `__pycache__/`, `*.egg-info/`, `.pytest_cache/`, `*.db` — build/runtime artefacts
- Old standalone roots (`solar-core/`, `solar-side/`) once empty

### Edited (only path fixes — no code changes)

- `solar/infra/docker-compose.yml`
  - `build: .`  →  `build: { context: ../api, dockerfile: Dockerfile }`
  - `./scripts/init-pgvector.sql:...`  →  `./postgres/init-pgvector.sql:...`
  - `./solar_core:/app/solar_core:ro`  →  `../api/solar_core:/app/solar_core:ro`

### NOT changed

- ❌ Python imports (`solar_core.*` paths still work — package name preserved)
- ❌ FastAPI routes (`/v1/health`, `/v1/process`, etc.)
- ❌ Pydantic schemas, business logic, AI orchestrator
- ❌ Extension manifest, content scripts, side panel JS/CSS
- ❌ API contract between extension and Core

## How to reproduce (manual mv/mkdir commands)

If you ever need to redo this from the old layout:

```bash
# Start at the parent dir that holds solar-core/ and solar-side/
mkdir -p solar/api solar/app solar/packages solar/infra/postgres solar/docs solar/scripts

# Backend → api/
mv solar-core/solar_core      solar/api/
mv solar-core/tests           solar/api/
mv solar-core/pyproject.toml  solar/api/
mv solar-core/Dockerfile      solar/api/
mv solar-core/.env.example    solar/api/

# Docs → docs/
mv solar-core/docs/* solar/docs/

# Infra → infra/
mv solar-core/docker-compose.yml         solar/infra/
mv solar-core/scripts/init-pgvector.sql  solar/infra/postgres/

# Scripts → scripts/
mv solar-core/scripts/demo.sh solar/scripts/

# Root config
mv solar-core/.gitignore solar/

# Extension → app/
mv solar-side solar/app/solar-side

# Empties
rmdir solar-core/docs solar-core/scripts solar-core
```

Then patch `solar/infra/docker-compose.yml` build context (see "Edited" above).

## Verification

- ✅ `cd solar/api && pytest` → 12/12 pass
- ✅ `python -c "from solar_core.main import app"` → 11 routes registered
- ✅ `node --check` on every extension JS file → all pass
- ✅ `python -c "import json; json.load(open('solar/app/solar-side/manifest.json'))"` → valid

## Run from the new layout

```bash
# Backend
cd solar/api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn solar_core.main:app --reload --port 8000

# Extension — load unpacked from solar/app/solar-side/

# Docker (Postgres + Core together)
cd solar/infra && docker compose up
```
