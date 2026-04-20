# Observability Foundation — Behavioral Specification

> **Status:** Approved
> **Date:** 2026-04-20
> **GH Issues:** #72 (Sentry), #73 (Correlation ID), #74 (Health Check), #75 (Query Logging), #76 (OCR Logging)
> **Depends on:** asgi-correlation-id (installed), structlog (installed)
> **Deferred:** #122 (stdlib logger migration)

## Behavioral Contracts

### Contract 1: Correlation ID Middleware

**Preconditions:**
- `asgi-correlation-id` dependency is installed
- `CorrelationIdMiddleware` is added to FastAPI middleware stack

**Postconditions:**
- Every HTTP response includes `X-Correlation-ID` header
- Every structlog entry within a request includes `request_id` field
- Incoming `X-Correlation-ID` headers are accepted and propagated
- Middleware is outermost in stack (added last, runs first)

**Invariants:**
- Correlation ID is a UUID4 string
- Correlation ID processor `add_correlation` already exists in `app_logger.py` — no duplication

**Edge cases:**
- Request with no `X-Correlation-ID` header → new UUID4 generated
- Request with existing `X-Correlation-ID` → accepted and propagated
- Background tasks (asyncio) → correlation ID may not propagate (acceptable for v1)

### Contract 2: Enhanced Health Check

**Preconditions:**
- FastAPI app is running with database and storage configured

**Postconditions:**
- `GET /health` returns JSON with `status`, `version`, `checks`, `uptime_seconds`
- `status` is one of: `"ok"`, `"degraded"`, `"unhealthy"`
- Response includes `Cache-Control: no-cache` header

**Status determination:**
- `ok` — all checks pass
- `degraded` — non-critical checks fail (storage path missing, OCR API key not configured)
- `unhealthy` — database unreachable

**Checks:**
| Check | Critical | What it tests |
|-------|----------|---------------|
| `database` | Yes | `SELECT 1` via SQLAlchemy session, report latency_ms |
| `storage` | No | Upload directory exists and is writable |

**Invariants:**
- Health check never throws 500 — always returns JSON even when unhealthy
- Response time < 100ms (no external API calls in health check)
- Version read from `app.settings.settings.version` or package metadata

**Edge cases:**
- Database connection fails → `status: "unhealthy"`, HTTP 503
- Storage path missing → `status: "degraded"`, HTTP 200
- All checks pass → `status: "ok"`, HTTP 200

### Contract 3: Sentry Integration

**Preconditions:**
- `sentry-sdk[fastapi]` is installed as dependency
- `SENTRY_DSN` is configured in settings (optional)

**Postconditions:**
- When `SENTRY_DSN` is set: Sentry initializes with FastAPI integration
- When `SENTRY_DSN` is empty/absent: no initialization, no warnings, no errors
- Sentry captures unhandled exceptions and sends to configured project
- Sentry traces sample rate configurable via `SENTRY_TRACES_SAMPLE_RATE`

**PII scrubbing:**
- Before sending, scrub fields matching: `voter_name`, `address`, `email`, `phone`, `date_of_birth`
- Use `before_send` callback to strip these from event contexts

**Invariants:**
- Sentry never causes application crash — init wrapped in try/except
- Health check endpoint excluded from Sentry tracing (`traces_sampler` returns 0 for `/health`)
- `environment` tag set from `settings.environment`

**Edge cases:**
- Invalid DSN → Sentry SDK handles gracefully (no crash)
- Sentry server unreachable → events queued, no blocking
- `sentry_sdk` import fails → logged as warning, app continues

### Contract 4: Database Query Logging

**Preconditions:**
- SQLAlchemy engine is created and events can be attached
- Structlog is configured with correlation ID processor

**Postconditions:**
- Queries exceeding `SLOW_QUERY_THRESHOLD_MS` (default: 500ms) are logged at WARNING level
- Log event includes: `event="slow_query"`, `db_duration_ms`, `db_statement` (truncated to 200 chars), `request_id` (when available)
- When `LOG_SQL=true`: all queries logged at DEBUG level with full statement and duration
- Query timing uses SQLAlchemy `before_cursor_execute` / `after_cursor_execute` events

**Invariants:**
- Query logging never raises exceptions (event handlers wrapped in try/except)
- Statement text is sanitized — no parameter values logged (only bind parameter names)
- Query logging has zero overhead when `LOG_SQL=false` and query is under threshold (timing still occurs but no log emit)

**Edge cases:**
- Query with no connection → timing skipped
- Very long query → statement truncated to 200 chars
- Multiple engines (SQLite + Supabase) → events attached to whichever engine is active

### Contract 5: OCR API Call Logging

**Preconditions:**
- OCR client factory dispatches to provider (OpenAI, Gemini, Mistral)
- Structlog is configured

**Postconditions:**
- Each OCR API call logs a structured event with OTel `gen_ai.*` naming:
  - `gen_ai.system` — provider name (`"openai"`, `"gemini"`, `"mistral"`)
  - `gen_ai.request.model` — model identifier
  - `gen_ai.response.finish_reason` — completion reason
  - `gen_ai.usage.input_tokens` — prompt tokens (when available)
  - `gen_ai.usage.output_tokens` — completion tokens (when available)
  - `latency_ms` — wall-clock time for the API call
  - `request_id` — correlation ID (when available)
  - `job_id` — job identifier (when available)
- Failed API calls log at ERROR level with `error_type`, `status_code`, `retry_attempt`
- Successful calls log at INFO level

**Invariants:**
- OCR logging never raises exceptions (wrapped in try/finally)
- API keys never logged (existing `redact_api_keys` processor handles this)
- Latency is wall-clock, not CPU time

**Edge cases:**
- Provider returns no token counts → `gen_ai.usage.*` fields omitted
- Provider raises timeout → logged as ERROR with `error_type="timeout"`
- Batch operations → one log entry per API call, not per batch

## TypedDict Event Schemas

Each log event type has a corresponding TypedDict for compile-time validation:

```python
class SlowQueryEvent(TypedDict):
    event: str  # Literal["slow_query"]
    db_duration_ms: float
    db_statement: str
    db_operation: str  # SELECT, INSERT, UPDATE, DELETE

class OcrApiCallEvent(TypedDict):
    event: str  # Literal["ocr_api_call"]
    gen_ai_system: str
    gen_ai_request_model: str
    latency_ms: float
    job_id: NotRequired[str]
    gen_ai_usage_input_tokens: NotRequired[int]
    gen_ai_usage_output_tokens: NotRequired[int]
    gen_ai_response_finish_reason: NotRequired[str]

class HealthCheckEvent(TypedDict):
    event: str  # Literal["health_check"]
    status: str  # ok | degraded | unhealthy
    database_latency_ms: NotRequired[float]
    storage_path: NotRequired[str]
```

## Structlog Schema Validation Processor

Optional processor for dev/test that validates log events against known TypedDict schemas:

```python
def validate_event_schema(logger, method_name, event_dict):
    """Warn if known event type is missing required fields. Dev/test only."""
    ...
```

- Runs only when `ENVIRONMENT != "production"`
- Warns via `warnings.warn()`, does not raise
- Checks against a registry of known event names → required fields

## Signal Catalog Documentation

Located at `docs/observability/reference.md`:
- Event registry table: event name, required fields, optional fields, when emitted
- Naming convention reference (OTel semantic conventions used)
- Per-event TypedDict reference

## ADR

ADR documenting: structlog-first logging, OTel naming conventions, why no full OTel SDK, TypedDicts for schema enforcement.

## File Impact

| Area | File | Action |
|------|------|--------|
| Middleware | `app/api.py` | Add `CorrelationIdMiddleware` to stack |
| Health | `app/api.py` | Replace `/health` handler |
| Health module | `app/observability/__init__.py` | New module |
| Health module | `app/observability/health.py` | New: health check logic |
| Sentry | `app/observability/sentry.py` | New: optional Sentry init |
| Query logging | `app/observability/query_logging.py` | New: SQLAlchemy event listeners |
| OCR logging | `app/ocr/ocr_client_factory.py` | Add structured logging to provider calls |
| Event schemas | `app/observability/events.py` | New: TypedDicts + schema validation processor |
| Settings | `app/settings/settings.py` | Add `sentry_dsn`, `sentry_traces_sample_rate`, `slow_query_threshold_ms`, `log_sql` |
| Config | `backend/.env.example` | Add new env vars |
| Deps | `backend/pyproject.toml` | Add `sentry-sdk[fastapi]` |
| Docs | `docs/observability/reference.md` | New: signal catalog |
| Docs | `docs/superpowers/specs/YYYY-MM-DD-observability-adr.md` | New: ADR |
| Tests | `tests/unit/observability/` | New: all test files |

## Boy Scout Refactoring

During implementation, while touching files for observability wiring:
- Flatten nested conditionals to guards/early returns in touched functions
- Remove dead imports in touched files
- Extract repeated patterns into shared helpers
- Full test suite (`uv run pytest`) + type check (`uv run basedpyright`) + lint (`uv run ruff check`) after each slice
- Never refactor untouched files

## Out of Scope

- Full OTel SDK integration (traces, metrics exporters)
- `logging.getLogger()` migration (#122)
- Metrics collection (Prometheus, etc.)
- Rate limit decorators on routes (known gap from previous epic)
- Correlation ID propagation to background tasks
