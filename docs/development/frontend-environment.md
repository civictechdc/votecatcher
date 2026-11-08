# Frontend Environment Variables

The SvelteKit frontend reads every deployment-varying value from runtime environment variables — one set of build artifacts serves every environment. Variables are declared and validated in `frontend/src/env.ts` (Kit 3 `defineEnvVars` contract): invalid or missing required values fail app startup with an actionable error naming the variable, instead of surfacing as broken requests later.

## Variable Matrix

| Variable | Scope | Required | Description |
| -------- | ----- | -------- | ----------- |
| `PUBLIC_API_URL` | public | yes | Backend API base URL, without the `/api` suffix (e.g. `http://localhost:8080`). Must be http(s). |
| `PUBLIC_DEMO_MODE` | public | no | Set to `true` to enable the demo workspace route with sample data. |
| `PUBLIC_FEATURES` | public | no | Comma-separated feature flags seeded at startup (e.g. `mockApi,2fa`), merged with the developer panel's `vc:flags` localStorage set. |
| `DATABASE_URL` | private | yes | PostgreSQL connection string used by the SvelteKit server (Better Auth sessions and demo data). |
| `BETTER_AUTH_SECRET` | private | yes | Secret used to sign Better Auth session tokens. |
| `ORIGIN` | private | recommended | The deployment's canonical origin (no trailing slash). Consumed by Better Auth (`baseURL`) and the trusted-origin helper. **Not consumed by SvelteKit itself** — see [Origin Derivation](#origin-derivation) below. |
| `TRUSTED_ORIGINS` | private | prod: yes / dev: optional | Comma-separated allowlist of origins the server may fetch (e.g. `https://app.example.com,https://staging.example.com`). Wildcards (`*`) are rejected. When unset in development, defaults to `http://localhost,http://localhost:5173`. Missing/empty in production fails startup. |
| `OCR_PROVIDER_NAME` | private | yes\* | OCR provider for signature verification (e.g. `openai`). |
| `OCR_PROVIDER_MODEL` | private | yes\* | OCR model identifier (e.g. `gpt-4o-mini`). |
| `OCR_PROVIDER_API_KEY` | private | yes\* | API key for the configured provider. |
| `DEMO_MODE` | private | no | Set to `true` to serve canned demo data from the frontend server routes. |

\* Required unless the deployment uses simulation/demo data only.

Public variables (`PUBLIC_*` prefix) are safe to read in browser code; private variables are server-only.

## Origin Derivation

Since the SvelteKit 3 upgrade (`@sveltejs/adapter-node` 6), SvelteKit no longer consumes an `ORIGIN` environment variable. Instead it derives each request's origin from request headers:

- `PROTOCOL_HEADER` — name of the header carrying the request protocol (set by your reverse proxy, e.g. `x-forwarded-proto`)
- `HOST_HEADER` — name of the header carrying the original host (e.g. `x-forwarded-host`)

Deployments behind a reverse proxy must set both, and the proxy must send those headers, or form submissions will fail CSRF checks (the browser origin and the derived origin won't match):

```env
PROTOCOL_HEADER=x-forwarded-proto
HOST_HEADER=x-forwarded-host
TRUSTED_ORIGINS=https://app.example.com
ORIGIN=https://app.example.com
```

`TRUSTED_ORIGINS` must include the deployment's public origin; multi-origin deployments (staging + production + previews from the same build) list all of them. `ORIGIN` is still read directly by Better Auth and by the app's trusted-origin validation — keep it set to the canonical public origin.

CSRF protection is always on in Kit 3 and derives its self-origin per request; trusted-origin configuration never widens CSRF.

## Running the Production Build

adapter-node does **not** auto-load `.env` in production. Pass variables through the process environment, or load a file explicitly with `node --env-file`:

```bash
cd frontend
ADAPTER=node bun run build
TRUSTED_ORIGINS=http://localhost:5173 PORT=5173 node --env-file=.env build
```

The build itself needs no runtime secrets (validation is relaxed while building); runtime variables are required when the server starts.

## Production Smoke Tests

Two Playwright suites exercise the adapter-node build (PostgreSQL must already be up):

```bash
cd frontend
bun run test:e2e:prod        # direct: node build on :5173, Host-derived origin
bun run test:e2e:prod:proxy  # behind scripts/reverse-proxy.mjs on :5173 ->
                             # app on :5174 with PROTOCOL_HEADER/HOST_HEADER set
```

The proxy variant simulates a reverse proxy (rewrites `Host`, injects `x-forwarded-proto`/`x-forwarded-host`) and verifies auth flows, form submissions (CSRF via the derived origin), and that cross-site POSTs stay rejected.

## Development Behavior

- `bun run dev` loads `frontend/.env` automatically; `TRUSTED_ORIGINS` may stay unset (localhost defaults apply).
- The developer flag panel lists flags from `PUBLIC_FEATURES` plus anything toggled into `vc:flags` localStorage.

See [Configuration Modes](../configuration-modes.md) for backend-side options.
