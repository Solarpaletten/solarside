# AI Dev System / Context Layer Architecture

**Status:** Deferred (post-ERP-cycle backlog)
**Origin:** GitLab-based AI agent sync pattern (colleague's idea, approved by Dashka)

## Why this exists

This document is a placeholder so the architectural idea isn't lost. The
"AI Dev System" is a Context Layer that lets multiple AI agents
(Claude, Cursor, internal tools) share durable project context — what
the project does, conventions, recent decisions, current sprint state —
through a Git-versioned set of files instead of relying on each agent's
ephemeral memory.

## Sketch

- A `.solar-context/` directory in each repo containing:
  - `CHARTER.md` — project goal and scope
  - `ARCHITECTURE.md` — current architectural decisions (an index of ADRs)
  - `CONVENTIONS.md` — code style, naming, commit format
  - `DECISIONS/` — append-only log of decisions
  - `STATE.json` — machine-readable current sprint, blockers, owners
- An ingestion endpoint in Solar Core (`/v1/context/ingest`) that any
  agent can call to read this directory and inject it into the AI
  Orchestrator's system prompt.

## Why deferred

We finish the ERP integration cycle first (Solar Core → real Solar ERP
connector → first 5–10 users). Without users we have no signal on
whether durable context is actually the bottleneck.

## Revisit when

We have ≥3 AI agents touching the same repos and we observe drift
between their context (Claude says X, Cursor implements Y, Solar Mile
Messenger thinks Z).
