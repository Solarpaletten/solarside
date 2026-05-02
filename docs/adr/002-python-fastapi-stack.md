# ADR-002: Python + FastAPI as Phase 1 stack

**Status:** Accepted
**Date:** 2026-05-02

## Context

Core needs a language + framework. Three candidates:

1. **Pure Python (FastAPI)** — best AI ecosystem, slower at I/O than Node
   but plenty fast for our throughput.
2. **Pure Node.js** — same stack as SOLAR ERP, but anaemic AI tooling
   compared to Python.
3. **Hybrid (Python Core + Node BFF)** — Python for AI heavy lifting,
   thin Node BFF for ERP integration.

## Decision

**Pure Python (FastAPI) for Phase 1.** Hybrid is reserved for Phase 2 if
ERP-side ergonomics demand it.

## Rationale

- The Anthropic SDK, OpenAI SDK, embeddings libraries, vector DBs, and
  prompt-engineering tooling are first-class in Python.
- FastAPI gives us auto-generated OpenAPI docs (`/docs`), Pydantic v2
  validation, async/await, and dependency injection out of the box.
- A BFF can always be added later — a wrong language choice up front is
  expensive, a missing layer is cheap to add.

## Consequences

- Team needs Python competence (acceptable — Claude operates fluently in
  both, Dashka can review).
- ERP integration goes through HTTP — slightly more overhead, but
  consistent with treating ERP as a connector (see ADR-001).

## Revisit when

ERP integration patterns become so frequent that we want them inline,
or when the AI ecosystem in Node achieves parity with Python.
