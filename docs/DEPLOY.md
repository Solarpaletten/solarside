# Solar Core — Production Deploy (Render, Air-first)

Sprint 4C.9a. Deploys the FastAPI Core to Render as an always-on web service,
**without** a database. The Air translate path (the primary UX) and health need
no DB; Summarize/Extract still return their AI result but won't be saved
(`saved: false`) until Postgres lands in 4C.9e.

This is a checklist, not automation — production steps you do once, by hand,
in the Render dashboard. The pipeline only ships the files.

## Before you start

- A Render account (https://render.com), logged in.
- The repo pushed to GitHub with `render.yaml` at its root (the pipeline does this).
- Your Anthropic API key ready to paste (and OpenAI key if you use the fallback).

## Step 1 — Create the Blueprint

1. Render Dashboard → **New** → **Blueprint**.
2. Connect the `Solarpaletten/solarside` repo.
3. Render reads `render.yaml` and shows one service: `solar-core` (Docker, Ohio, starter plan).
4. Click **Apply**.

## Step 2 — Fill the secrets (the `sync: false` ones)

Render will prompt for the values it can't generate:

| Variable             | What to enter                              |
|----------------------|--------------------------------------------|
| `ANTHROPIC_API_KEY`  | your real Anthropic key (paste it)         |
| `OPENAI_API_KEY`     | your OpenAI key (fallback provider)        |

`SOLAR_API_KEYS` and `SOLAR_SECRET_KEY` are **auto-generated** by Render — you
don't type them. After deploy, open the service → **Environment** → copy the
generated `SOLAR_API_KEYS` value. You'll need it for the extension in 4C.9b.

> The old `dev-key-1` is **not** used in production. It's compromised (it lives
> in git history and chat logs). The generated key replaces it. Keep `dev-key-1`
> only for your local Docker.

## Step 3 — First deploy

Render builds the Docker image (`api/Dockerfile`) and starts the service.
Watch the logs for:

```
solar_core_startup ... env=production
solar_core_db_unavailable ...   ← EXPECTED in Air-first (no DB). Not an error.
Uvicorn running on http://0.0.0.0:10000   ← Render's injected $PORT
```

The `db_unavailable` warning is **normal** here — there is no Postgres yet, and
the app is built to boot fine without one.

## Step 4 — Verify it's alive

Your service URL will look like `https://solar-core-XXXX.onrender.com`.

```bash
curl -fsS https://solar-core-XXXX.onrender.com/v1/health
# → {"status":"ok",...}
```

Then a real Air translate (use the generated SOLAR_API_KEYS value):

```bash
curl -X POST https://solar-core-XXXX.onrender.com/v1/translate-air \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <generated-key>" \
  -d '{"text":"Hello world","target_language":"auto"}'
# → a Russian translation
```

If both work, the backend is live. Next sprint (4C.9b) points the extension at
this URL.

## What is intentionally NOT here

- **No Postgres / pgvector.** Deferred to 4C.9e. The `CREATE EXTENSION vector;`
  step and a Postgres service will be added then.
- **No rate-limiting / origin lock.** Deferred to 4C.9d. Until then, anyone with
  the URL **and** the key can spend your Anthropic credits — so do **not** share
  the URL+key widely before 4C.9d. Testing it yourself is fine.
- **No custom domain.** The `onrender.com` URL is enough for testing.

## Rollback

The deploy is just a git push + a Render service. To roll back:
- Code: `node solar-apply.js sprint-4c9a-render-air-first --rollback`, re-push.
- Service: Render dashboard → the service → **Manual Deploy** → pick a previous commit,
  or **Suspend** the service to stop it entirely.
