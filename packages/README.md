# packages/ — Shared libraries (reserved)

Reserved for shared code consumed by both `api/` and `app/` (and future
clients):

- `solar-sdk-js/` — TypeScript SDK to talk to Solar Core (Phase 2)
- `solar-prompts/` — versioned prompt library
- `solar-types/` — shared schemas (OpenAPI-generated)

Empty in v0.1.0 — extension and Core duplicate the API contract by hand.
This is acceptable for two consumers; will be promoted to a real package
when a third client appears (desktop / mobile / Chromium shell).
