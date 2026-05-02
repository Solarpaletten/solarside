# ADR-003: PostgreSQL + pgvector from day 1

**Status:** Accepted
**Date:** 2026-05-02

## Context

Where do we store documents and embeddings?

1. **Supabase** — managed Postgres + pgvector + auth. Vendor lock-in, $.
2. **Notion-like custom engine** — bespoke storage. Years of work for
   features we get for free elsewhere.
3. **Existing PostgreSQL 16 (`solarerp` DB on Ubuntu, port 5433) +
   pgvector extension.**

## Decision

**Reuse the existing PostgreSQL + add the `pgvector` extension** for
embeddings/semantic search. Use SQLAlchemy as ORM (Alembic for
migrations later). For local development and tests we use SQLite with a
JSON-column fallback for embeddings.

## Rationale

- The Postgres instance is already running, already credentialed, already
  backed up. Avoiding a new piece of infrastructure is the cheapest win
  available.
- pgvector is mature in 2026 and outperforms most boutique vector DBs at
  our scale.
- Same DB as SOLAR ERP means future joins between Core documents and ERP
  entities (invoices, counterparties) are trivial when we want them —
  but only when we want them. The ADR-001 separation still holds because
  Core writes only to its own tables (`solar_documents`, `solar_actions`).
- SQLite-friendly fallback keeps dev loops fast and CI cheap.

## Consequences

- **Pro:** Zero new infrastructure for Phase 1. Embeddings ready when we
  flip the switch.
- **Pro:** One DB to back up.
- **Con:** Schema migrations must be coordinated between Core and ERP
  teams. Mitigated because Core's tables are in their own namespace
  (`solar_*` prefix).

## Revisit when

We outgrow PostgreSQL's vector performance (millions of documents,
sub-100ms latency requirements) — at which point we evaluate Qdrant /
Weaviate.
