# Observability Signal Catalog

> Living reference for all structured log events in VoteCatcher.
> Crosslink #42

## Event Schemas

### `ocr_api_call`

Logged on every OCR API call (success).

| Field | Type | Description |
|-------|------|-------------|
| `event` | `str` | `"ocr_api_call"` |
| `gen_ai_system` | `str` | Provider name (e.g., `"openai"`, `"google"`) |
| `gen_ai_request_model` | `str` | Model identifier (e.g., `"gpt-4o"`) |
| `latency_ms` | `float` | Round-trip latency in milliseconds |
| `gen_ai_usage_input_tokens` | `int \| None` | Input token count (if available) |
| `gen_ai_usage_output_tokens` | `int \| None` | Output token count (if available) |
| `gen_ai_response_finish_reason` | `str \| None` | Finish reason (e.g., `"stop"`) |
| `job_id` | `str` | Job identifier |
| `status_code` | `int \| None` | HTTP status code from provider |
| `retry_attempt` | `int \| None` | Retry attempt number (if retried) |

Source: `app/ocr/ocr_client_factory.py`

### `ocr_api_call_failed`

Logged on OCR API call failure.

| Field | Type | Description |
|-------|------|-------------|
| `event` | `str` | `"ocr_api_call_failed"` |
| `gen_ai_system` | `str` | Provider name |
| `gen_ai_request_model` | `str` | Model identifier |
| `latency_ms` | `float` | Time until failure in milliseconds |
| `error_type` | `str` | Exception class name |
| `job_id` | `str` | Job identifier |
| `status_code` | `int \| None` | HTTP status code (if applicable) |
| `retry_attempt` | `int \| None` | Retry attempt number |

Source: `app/ocr/ocr_client_factory.py`

### `slow_query`

Logged when a SQL query exceeds the configured threshold (default 500ms).

| Field | Type | Description |
|-------|------|-------------|
| `event` | `str` | `"slow_query"` |
| `statement` | `str` | Truncated SQL statement (max 200 chars) |
| `duration_ms` | `float` | Query duration in milliseconds |
| `threshold_ms` | `float` | Configured slow query threshold |

Source: `app/observability/query_logging.py`

### `query`

Logged for every SQL query when `LOG_SQL=true` (default: off).

| Field | Type | Description |
|-------|------|-------------|
| `event` | `str` | `"query"` |
| `statement` | `str` | Truncated SQL statement (max 200 chars) |
| `duration_ms` | `float` | Query duration in milliseconds |

Source: `app/observability/query_logging.py`

## Middleware Signals

### Correlation ID

- **Header:** `X-Correlation-ID`
- **Middleware:** `CorrelationIdMiddleware` (outermost, wraps all others)
- **Behavior:** Generates UUID v4 if not provided; propagates if valid UUID
- **Source:** `app/middleware/correlation.py` (wraps `asgi-correlation-id`)

### Health Check

- **Endpoint:** `GET /api/health`
- **Response shape:**
  ```json
  {
    "status": "ok" | "degraded" | "unhealthy",
    "version": "1.0.0-alpha.5",
    "uptime_seconds": 123.4,
    "checks": {
      "database": {
        "status": "ok",
        "latency_ms": 1.2
      }
    }
  }
  ```
- **Source:** `app/observability/health.py`

### Sentry

- **Init:** Optional, requires `SENTRY_DSN` environment variable
- **PII scrubbing:** Voter fields (`voter_name`, `address`, `email`, `phone`, `date_of_birth`) filtered via `before_send` hook
- **Tracing:** Health endpoint excluded (`traces_sampler` returns 0 for `/health`)
- **Source:** `app/observability/sentry.py`

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `SENTRY_DSN` | `""` | Sentry DSN (empty = disabled) |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.1` | Global trace sampling rate |
| `SLOW_QUERY_THRESHOLD_MS` | `500` | Slow query warning threshold |
| `LOG_SQL` | `false` | Log all SQL queries (debug) |

## Adding New Signals

1. Define the event name and fields in `app/observability/event_validation.py` (`_EVENT_SCHEMAS`)
2. Add the event to this catalog
3. Use `structlog.get_logger(__name__)` for new loggers
4. Follow OTel semantic convention naming where applicable
