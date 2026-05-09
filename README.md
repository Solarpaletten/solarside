# Solar

> **AI operational layer for the Solar ecosystem** — Melasa Rail (LT), Vagonupaletas (LV), SOLARPALETTEN (DE), YPL Group (US).
>
> Highlight text on any web page → Solar AI processes it → action lands in Solar ERP.

## Monorepo layout

```
solar/
├── api/             ← FastAPI backend (Python). Package: solar_core
├── app/             ← User-facing clients
│   └── solar-side/  ← Chrome extension (Manifest V3, side panel)
├── packages/        ← Shared libraries (future: SDK, types, prompts)
├── infra/           ← Docker, compose, init scripts
├── docs/            ← Architecture decisions and design notes
├── scripts/         ← Developer convenience scripts
└── README.md
```

| Module           | Status     | What it is                                                       |
|------------------|------------|------------------------------------------------------------------|
| `api/`           | ✅ v0.1.0  | FastAPI backend with AI orchestrator, actions, connectors        |
| `app/solar-side/`| ✅ v0.1.0  | Chrome extension — floating button + side panel + context menu   |
| `packages/`      | 🟡 reserved | Shared SDK / types / prompts. Empty in v0.1.0                    |
| `infra/`         | ✅         | docker-compose with PostgreSQL + pgvector                        |
| `docs/`          | ✅         | ADRs, architecture, future-work notes                            |

## Quick start (90 seconds)

### 1. Run the backend

```bash
cd api
python3 -m venv venv 
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env             # add ANTHROPIC_API_KEY=sk-ant-...
uvicorn solar_core.main:app --reload --port 8000
```

Verify: <http://localhost:8000/v1/health>

### 2. Install the Chrome extension

1. Open `chrome://extensions/`
2. Enable **Developer mode**
3. Click **Load unpacked** → pick `app/solar-side/`
4. Pin the Solar icon to the toolbar

### 3. Try it

1. Highlight any text on a web page
2. Click the orange **Solar** button (or right-click → Solar → Summarize)
3. Side panel opens with the AI result
4. Click **→ Save as Solar Note** to send it to the Solar ERP connector

### Optional: Postgres + pgvector via Docker

```bash
cd infra
docker compose up -d postgres
# then point api/.env at it:
#   SOLAR_DATABASE_URL=postgresql+asyncpg://solar_user:solar_dev_password@localhost:5433/solarerp
```

## Architecture decisions

All major decisions are recorded in [`docs/adr/`](docs/adr/):

- **ADR-001** — Core as a separate service (not embedded in SOLAR ERP)
- **ADR-002** — Python + FastAPI for Phase 1
- **ADR-003** — PostgreSQL + pgvector from day 1
- **ADR-004** — Multi-provider AI with task-based routing

## Status & roadmap

**Phase 1**

- ✅ Step 1 — Core v0.1.0 (`api/`)
- ✅ Step 2 — Extension v0.1.0 (`app/solar-side/`)
- ⏭️ Step 3 — Real Solar ERP connector (replace mock in `solar_core/connectors/solar_erp.py`)

**Phase 2** (deferred)

- Voice pipeline (Whisper / Deepgram)
- Desktop app (Tauri shell over Solar Core)
- AI Dev System / Context Layer (see `docs/future/ai-dev-system-architecture.md`)

## License

Proprietary — Solar Team / Leanid Kanoplich.
