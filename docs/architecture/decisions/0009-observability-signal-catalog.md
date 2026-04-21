# ADR 0009: Observability Signal Catalog

**Status:** Accepted
**Date:** 2026-04-21
**Crosslink:** #42

## Context

The observability foundation (Crosslink #26) introduces structured logging events, correlation IDs, health checks, and Sentry integration. Without a catalog, developers must read source files to discover available signals, and new code may introduce inconsistent field naming or duplicate event types.

## Decision

Establish a signal catalog as a living reference document (`docs/architecture/signal-catalog.md`) covering all structured log events, their fields, naming conventions, and usage guidelines.

### Naming Conventions

| Domain | Prefix | Example |
|--------|--------|---------|
| AI/OCR calls | `gen_ai_*` | `gen_ai_system`, `gen_ai_request_model` |
| Database queries | `db.*` | `slow_query`, `query` |
| HTTP requests | via middleware | `x-correlation-id` header |
| Health | `status` | `ok`, `degraded`, `unhealthy` |

### Event Schemas

Each event is a structlog event name with a defined set of allowed fields. Unknown fields trigger a dev/test warning via the `validate_event_schema` processor.

See `docs/architecture/signal-catalog.md` for the full catalog.

## Consequences

- New observability signals must be added to both the catalog and the event validation schema
- Unknown fields in known events produce warnings in dev/test (never raise in production)
- OTel semantic conventions (`gen_ai.*`, `db.*`) guide naming for future OpenTelemetry migration
