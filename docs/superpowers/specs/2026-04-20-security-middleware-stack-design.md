# Security Middleware Stack — Behavioral Specification

> **Epic:** Crosslink #16
> **Date:** 2026-04-20
> **Status:** DRAFT

## Overview

Add a security middleware stack to the FastAPI application covering three concerns: HTTP security headers, hardened CORS configuration, and per-endpoint rate limiting. All three are configurable via environment variables and have sensible defaults for local development vs production.

## Current State

- **CORS:** Hardcoded `allow_origins=["http://localhost", "http://localhost:5173"]`, `allow_methods=["*"]`, `allow_headers=["*"]`, `allow_credentials=True` in `app/api.py:47-58`
- **Security headers:** None. No HSTS, X-Content-Type-Options, X-Frame-Options, CSP, or any security header middleware.
- **Rate limiting:** None. All endpoints accept unlimited requests. Existing tests in `tests/security/test_rate_limiting.py` document this gap with `pass` stubs.
- **Auth:** `oauth2_scheme` defined in `dependencies.py:17-19` but unused. No JWT enforcement.
- **API key:** `DATABASE_API_KEY` env var for database endpoints via `verify_database_api_key`. Falls back to open if not set.

## Scope

### In Scope

1. **Security Headers Middleware** — Starlette middleware that injects OWASP-recommended security headers on every response
2. **CORS Hardening** — Environment-aware CORS: strict origins in production, relaxed in development, no wildcard methods
3. **Rate Limiting** — In-memory per-IP rate limiting via slowapi with configurable per-endpoint limits

### Out of Scope

- Authentication/authorization (JWT enforcement, RBAC) — separate epic
- Request body size limits — separate concern
- Error response sanitization (stack trace hiding) — separate concern
- HTTPS/TLS enforcement at application level — handled by deployment proxy
- PII redaction — separate epic

---

## Behavioral Contracts

### Contract 1: Security Headers Middleware

**Name:** `SecurityHeadersMiddleware`

**Preconditions:**
- Application is running (any environment)

**Postconditions:** Every HTTP response includes these headers:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME-type sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limit referrer information leakage |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | Disable unnecessary browser features |
| `X-Request-ID` | UUID4 string | Request correlation (generated if not present) |

**Environment-conditional headers:**

| Header | Production Value | Development Behavior |
|--------|-----------------|---------------------|
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains; preload` | **Not set** (would break localhost) |
| `Content-Security-Policy` | `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'` | `Content-Security-Policy-Report-Only` with same value (report, don't block) |

**Invariants:**
- Headers are set after response processing, never before
- Existing header values are NOT overwritten (allows endpoint-level overrides)
- Middleware is added BEFORE CORS middleware in the stack (Starlette processes middleware in reverse add order — CORS must be added after security headers so it runs first)

**Edge Cases:**
- Preflight `OPTIONS` requests: security headers still attached
- WebSocket upgrades: headers attached (no harm)
- Health check endpoint (`/api/health`): headers attached (no exception)

---

### Contract 2: CORS Hardening

**Name:** Environment-aware CORS configuration

**Preconditions:**
- `ENVIRONMENT` or `NODE_ENV` env var set (defaults to `development`)

**Postconditions:**

**Development mode** (`ENVIRONMENT=development` or unset):
- `allow_origins`: `["http://localhost", "http://localhost:5173"]` (current defaults)
- `allow_methods`: `["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]` (explicit list, no wildcard)
- `allow_headers`: `["*"]` (keep wildcard for dev flexibility)
- `allow_credentials`: `True`

**Production mode** (`ENVIRONMENT=production`):
- `allow_origins`: value of `CORS_ORIGINS` env var (comma-separated, required in production)
- `allow_methods`: `["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]` (explicit list)
- `allow_headers`: `["Authorization", "Content-Type", "X-API-Key"]` (explicit list)
- `allow_credentials`: `True`

**Invariants:**
- If `ENVIRONMENT=production` and `CORS_ORIGINS` is empty/missing → application logs warning, NOT crash
- CORS middleware processes before security headers middleware (correct preflight handling)

**Edge Cases:**
- Empty `CORS_ORIGINS` in production: warning logged, falls back to no allowed origins (locked down)
- Extra whitespace in `CORS_ORIGINS`: trimmed
- Trailing slashes in origins: normalized (stripped)

---

### Contract 3: Rate Limiting

**Name:** In-memory per-IP rate limiting

**Preconditions:**
- `slowapi` installed and `Limiter` initialized

**Postconditions:**

**Default limits:**
| Endpoint Category | Limit | Window |
|-------------------|-------|--------|
| General API (all routes) | 60 requests | per minute |
| Upload endpoints (`/api/upload/*`) | 10 requests | per minute |
| Job creation (`POST /api/jobs`) | 10 requests | per minute |

**On rate limit exceeded:**
- HTTP 429 Too Many Requests
- Response body: `{"detail": "Rate limit exceeded"}`
- Response headers: `Retry-After` with seconds until limit resets

**On successful request:**
- Response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

**Configuration via env vars:**

| Env Var | Default | Description |
|---------|---------|-------------|
| `RATE_LIMIT_ENABLED` | `true` | Enable/disable rate limiting |
| `RATE_LIMIT_DEFAULT` | `60/minute` | Default limit |
| `RATE_LIMIT_UPLOAD` | `10/minute` | Upload endpoint limit |
| `RATE_LIMIT_JOB_CREATE` | `10/minute` | Job creation limit |

**Invariants:**
- Rate limiting is per client IP (via `request.client.host`)
- Behind reverse proxy: uses `X-Forwarded-For` header if present (first IP)
- In-memory storage — limits reset on application restart
- Rate limiting disabled in test environment (configurable)

**Edge Cases:**
- IP is `None` (e.g., Unix socket): falls back to `127.0.0.1`
- Health check endpoint (`/api/health`): exempt from rate limiting
- `RATE_LIMIT_ENABLED=false`: middleware is not added (no overhead)

---

## Architecture

### Module Structure

```
app/middleware/
├── __init__.py
├── security_headers.py    # SecurityHeadersMiddleware
├── cors.py                # build_cors_config() → CORS middleware args
└── rate_limit.py          # rate limiter setup + dependency
```

### Settings Changes

Add to `Settings` in `app/settings/settings.py`:

```python
environment: str = Field(default="development", alias="ENVIRONMENT")
cors_origins: str = Field(default="", alias="CORS_ORIGINS")
rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
rate_limit_default: str = Field(default="60/minute", alias="RATE_LIMIT_DEFAULT")
rate_limit_upload: str = Field(default="10/minute", alias="RATE_LIMIT_UPLOAD")
rate_limit_job_create: str = Field(default="10/minute", alias="RATE_LIMIT_JOB_CREATE")
```

### Integration Point

`app/api.py` — middleware registration order (added in this order, Starlette processes reverse):

```python
app.add_middleware(SecurityHeadersMiddleware)        # runs 3rd (innermost)
# CORSMiddleware added via build_cors_config()        # runs 2nd
# Rate limiting via slowapi extension (outermost)     # runs 1st (rate limit before anything)
```

### Dependencies

New dependency: `slowapi` (adds `limits` transitive dep)

---

## Non-Functional Requirements

1. **Zero overhead when disabled:** `RATE_LIMIT_ENABLED=false` means no slowapi initialization, no per-request overhead
2. **No performance regression:** Security header injection adds <1ms per request (simple dict assignment)
3. **Test environment:** Rate limiting disabled by default in test config
4. **No production crash on misconfiguration:** Missing env vars produce warnings, not exceptions

## Test Strategy

### Unit Tests
- `tests/unit/middleware/test_security_headers.py` — per-header assertion
- `tests/unit/middleware/test_cors_config.py` — environment-specific CORS config
- `tests/unit/middleware/test_rate_limit_config.py` — limiter setup from settings

### Security Tests (update existing)
- `tests/security/test_rate_limiting.py` — replace `pass` stubs with real assertions

### Integration Tests
- `tests/integration/api/test_middleware.py` — full middleware stack via TestClient
- Verify header presence, CORS preflight, rate limit 429 response

## Acceptance Criteria

- [ ] Every response includes all security headers per Contract 1
- [ ] HSTS only present in production mode
- [ ] CSP in report-only mode during development
- [ ] CORS rejects non-allowed origins in production
- [ ] Rate limiting returns 429 with proper headers when exceeded
- [ ] Rate limiting exempt on health check
- [ ] All 1161+ existing tests continue to pass
- [ ] No new dependencies beyond `slowapi`
