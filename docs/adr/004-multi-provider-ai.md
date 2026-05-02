# ADR-004: Multi-provider AI with task-based routing

**Status:** Accepted
**Date:** 2026-05-02

## Context

Should Core be locked to a single AI provider (cheapest, simplest), or
support multiple with routing?

## Decision

**Multi-provider with a task-based router**, fronted by a thin
abstraction (`BaseAIProvider`). Default routing:

| Task          | Primary           | Fallback         |
|---------------|-------------------|------------------|
| reasoning     | Claude Sonnet     | GPT-4o           |
| extraction    | Claude Haiku      | DeepSeek → 4o-mini |
| summarization | Claude Haiku      | DeepSeek → 4o-mini |
| translation   | Claude Sonnet     | GPT-4o           |

DeepSeek and OpenAI use the same SDK (OpenAI-compatible API), reducing
implementation cost.

## Rationale

- **Vendor risk.** A single-provider dependency is a single point of
  failure (rate limits, outages, price changes, policy shifts).
- **Cost optimisation.** Cheap models are good enough for high-volume
  extraction; expensive models earn their keep on reasoning.
- **Privacy gradient.** Confidential documents (Melasa, legal materials)
  can be routed to a local Ollama provider when we add it — the abstraction
  is in place from day 1.
- **Quality benchmarking.** We can A/B-test providers per task without
  rewriting actions.

## Consequences

- **Pro:** No lock-in. Each task uses the right tool.
- **Pro:** Adding a new provider (Mistral, local Ollama, Google Gemini)
  is one file in `solar_core/ai/providers/`.
- **Con:** Slightly more complex than a single SDK call. Mitigated by
  the orchestrator hiding all of this from action authors.

## Revisit when

A single provider becomes dominant for our use cases by such a margin
that the abstraction is pure overhead.
