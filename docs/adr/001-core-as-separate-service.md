# ADR-001: Core as a Separate Service (not a SOLAR ERP module)

**Status:** Accepted
**Date:** 2026-05-02
**Decision-makers:** Leanid (architect), Dashka (coordinator), Claude (engineer)

## Context

Solar Core needs a deployment shape. Two options were on the table:

1. **Embedded module** — Core lives inside the existing SOLAR ERP backend
   (Node.js + Prisma). Same process, same database, single deploy.
2. **Separate service** — Core is its own Python/FastAPI process,
   communicating with SOLAR ERP through a connector.

## Decision

**Core is a separate service.**

## Rationale

- **Multi-client future.** Core is meant to be consumed by an extension,
  desktop app, mobile app, and (eventually) a Chromium shell. A service
  that is fused into one specific backend cannot serve all of those.
- **Independent scaling.** AI workloads have different scaling
  characteristics from ERP CRUD. Background jobs, retries, and provider
  fallbacks deserve their own process boundary.
- **Independent release cadence.** Core will iterate faster than the ERP
  in the early phases. Coupling them means every Core change risks the ERP.
- **Stack fit.** The AI ecosystem (LiteLLM-style routing, streaming, tool
  calling, embeddings) is mature in Python and immature in Node. Forcing
  Core into the ERP's Node runtime would cost us months in compatibility
  work for no benefit.
- **Lesson from Arc.** The Browser Company tried to build everything as
  one tightly coupled monolith. When they wanted to pivot to Dia, they
  could not — the ADK was too entangled. We avoid that pattern from day 1.

## Consequences

- **Pro:** Core can be deployed anywhere — same machine as ERP, separate
  VM, Kubernetes pod, Fly.io, etc. We can rewrite the extension without
  touching ERP, and vice versa.
- **Pro:** SOLAR ERP becomes "just one of the connectors" — the same
  abstraction we use for Gmail, Google Docs, etc. This is exactly the
  architecture we want long-term.
- **Con:** Two processes to operate. We mitigate with a single
  `docker-compose.yml`.
- **Con:** Inter-service auth required. Phase 1 uses static API keys;
  Phase 2 introduces JWT/OAuth.

## Revisit when

We have >3 clients (extension + desktop + ERP-internal) and the operational
overhead of a separate service starts to hurt — at which point we evaluate
collapsing only if Core remains stable in scope.
