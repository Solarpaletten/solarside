# Solar Core (api/)

Python + FastAPI backend for the Solar monorepo.

For project-wide context see [`../README.md`](../README.md).

## Run locally

```bash
cd api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # add ANTHROPIC_API_KEY
uvicorn solar_core.main:app --reload --port 8000
```

Health check: <http://localhost:8000/v1/health>
OpenAPI docs: <http://localhost:8000/docs>

## Tests

```bash
cd api
python -m pytest -v
```

## Package layout

```
api/
├── solar_core/          ← Python package (import as `solar_core.*`)
│   ├── main.py          ← FastAPI entrypoint
│   ├── api/             ← Routes & schemas
│   ├── ai/              ← Orchestrator, providers, prompts
│   ├── actions/         ← Built-in actions
│   ├── connectors/      ← Solar ERP, Gmail, ...
│   ├── documents/       ← Documents service
│   ├── db/              ← SQLAlchemy models & session
│   └── core/            ← Auth, logging, exceptions
├── tests/
├── pyproject.toml
├── Dockerfile
└── .env.example
```

## Architecture decisions

See [`../docs/adr/`](../docs/adr/).
