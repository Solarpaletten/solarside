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

---

## Security hardening (Sprint 4C.9d)

The public URL means anyone with the URL **and** a valid key can spend your
Anthropic credits. 4C.9d adds three layers, all configurable via env (no code
change to tune):

### Rate limiting (on by default)

Per `(api-key + client IP)`, sliding window. Defaults: **30 requests / 60s**.
Over the limit → `429 Too Many Requests` with a `Retry-After` header. Tune in
the Render dashboard:

| Variable                          | Default | Meaning                          |
|-----------------------------------|---------|----------------------------------|
| `SOLAR_RATE_LIMIT_ENABLED`        | true    | master switch                    |
| `SOLAR_RATE_LIMIT_REQUESTS`       | 30      | max requests per window          |
| `SOLAR_RATE_LIMIT_WINDOW_SECONDS` | 60      | window length                    |
| `SOLAR_MAX_TEXT_CHARS`            | 20000   | reject oversize payloads         |

> In-memory limiter — correct for a single Render instance. If you scale to
> multiple instances later, this becomes per-instance; move to a shared store
> (Redis) at that point.

### Payload cap

Both `/v1/process` and `/v1/translate-air` reject text over 20k chars, so an
abusive giant request can't reach a paid provider.

### Origin lock (optional, tighter than CORS)

By default any `chrome-extension://...` origin is accepted (plus localhost).
To lock to **your** published extension only:

1. Find your extension ID at `chrome://extensions` (e.g. `abcd...` 32 chars).
2. In the Render dashboard set:
   `SOLAR_ALLOWED_ORIGINS = chrome-extension://<your-id>,http://localhost:3000`
3. Redeploy. Now only that exact origin passes CORS.

Leave it blank during development; set it before sharing the product widely.

### Key rotation

If a key leaks: edit `SOLAR_API_KEYS` in the dashboard (comma-separated, so you
can run old+new during a transition), redeploy, then update the extension's
API-key field. The compromised `dev-key-1` is never used in production.
