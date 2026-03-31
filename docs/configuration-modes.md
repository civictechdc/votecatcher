# Configuration Modes

Votecatcher supports multiple configuration modes for different use cases: production deployment, development, testing, and demos.

## Quick Reference

| Mode | LLM API | Database | Use Case |
|------|---------|----------|----------|
| Production | Real calls | PostgreSQL | Live deployment |
| Development (Real LLM) | Real calls | SQLite/PostgreSQL | Feature development with real OCR |
| Simulation | Mock data | SQLite | Development without API keys |
| Demo | Pre-baked | In-memory | Presentations, stakeholder demos |
| Testing | Mock/Real | SQLite (ephemeral) | Automated test suites |

**Quick PostgreSQL Setup:**
```bash
make dev-postgres  # Starts Postgres container + runs migrations
```

---

## Configuration Variables

### Backend Variables

| Variable | Production | Dev (Real) | Simulation | Demo | Testing |
|----------|------------|------------|------------|------|---------|
| `DATABASE_URL` | PostgreSQL | SQLite | SQLite | SQLite | SQLite |
| `OCR_PROVIDER_NAME` | Required | Required | Optional | Optional | Optional |
| `OCR_PROVIDER_MODEL` | Required | Required | Optional | Optional | Optional |
| `OCR_PROVIDER_API_KEY` | Required | Required | Not used | Not used | Optional |
| `FEATURE_ENABLE_SIMULATION` | `0` | `0` | `1` | `1` | `1` |
| `FEATURE_ENABLE_DEBUG_MODE` | `0` | `1` | `1` | `0` | `0` |
| `FEATURE_DEMO_MODE` | `0` | `0` | `0` | `1` | `0` |
| `FEATURE_DEMO_RESET` | `0` | `0` | `0` | `1` | `0` |
| `FEATURE_ENABLE_BETA_FEATURES` | `0` | `1` | `0` | `0` | `0` |

### Frontend Variables

| Variable | Production | Dev (Real) | Simulation | Demo | Testing |
|----------|------------|------------|------------|------|---------|
| `PUBLIC_API_URL` | Prod URL | `http://localhost:8080` | `http://localhost:8080` | `http://localhost:8080` | Test server |
| `PUBLIC_DEMO_MODE` | `false` | `false` | `false` | `true` | `false` |
| `DEMO_MODE` | `false` | `false` | `false` | `true` | `false` |
| `BETTER_AUTH_SECRET` | Secure secret | Any string | Any string | Any string | Test secret |
| `ORIGIN` | Prod domain | `http://localhost:5173` | `http://localhost:5173` | `http://localhost:5173` | Test URL |

---

## Mode Configurations

### 1. Production Mode

Use for live deployments with real LLM API calls.

**Backend `.env.local`:**
```bash
# Database (PostgreSQL required)
DATABASE_URL=postgresql+psycopg://user:secure_password@host:5432/votecatcher

# OCR Provider (Required - choose one)
OCR_PROVIDER_NAME=open_ai
OCR_PROVIDER_MODEL=gpt-4o
OCR_PROVIDER_API_KEY=sk-your-production-key

# Feature Flags (all disabled)
FEATURE_ENABLE_SIMULATION=0
FEATURE_ENABLE_DEBUG_MODE=0
FEATURE_ENABLE_BETA_FEATURES=0
FEATURE_DEMO_MODE=0
FEATURE_DEMO_RESET=0
```

**Frontend `.env`:**
```bash
PUBLIC_API_URL=https://api.yourdomain.com
PUBLIC_DEMO_MODE=false
DEMO_MODE=false
BETTER_AUTH_SECRET=your-secure-random-secret-min-32-chars
ORIGIN=https://yourdomain.com
```

**Security Checklist:**
- [ ] Strong database password
- [ ] API key stored in secrets manager (not in .env)
- [ ] `BETTER_AUTH_SECRET` is cryptographically random
- [ ] HTTPS enabled
- [ ] All `FEATURE_*` flags set to `0`

---

### 2. Development Mode (Real LLM)

Use for feature development with real OCR processing.

**Backend `.env.local`:**
```bash
# Database (SQLite for simplicity)
DATABASE_URL=sqlite+aiosqlite:///./dev.db

# OCR Provider (Required)
OCR_PROVIDER_NAME=open_ai
OCR_PROVIDER_MODEL=gpt-4o-mini
OCR_PROVIDER_API_KEY=sk-your-dev-key

# Development settings
DEV_LOGGING_ENABLED=1
DEV_LOCAL_DB_ENABLE_LOGGING=1

# Feature Flags
FEATURE_ENABLE_SIMULATION=0
FEATURE_ENABLE_DEBUG_MODE=1
FEATURE_ENABLE_BETA_FEATURES=1
FEATURE_DEMO_MODE=0
FEATURE_DEMO_RESET=0
```

**Frontend `.env.local`:**
```bash
PUBLIC_API_URL=http://localhost:8080
PUBLIC_DEMO_MODE=false
DEMO_MODE=false
BETTER_AUTH_SECRET=dev-secret-not-for-production
ORIGIN=http://localhost:5173
```

**When to use:**
- Testing real OCR integration
- Debugging LLM responses
- Developing new provider support
- Validating matching accuracy with real data

---

### 3. Simulation Mode

Use for development without LLM API keys. OCR returns mock data.

**Backend `.env.local`:**
```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./dev.db

# OCR Provider (Not used in simulation, but must be set)
OCR_PROVIDER_NAME=open_ai
OCR_PROVIDER_MODEL=gpt-4o-mini
OCR_PROVIDER_API_KEY=  # Can be empty

# Feature Flags
FEATURE_ENABLE_SIMULATION=1
FEATURE_ENABLE_DEBUG_MODE=1
FEATURE_ENABLE_BETA_FEATURES=0
FEATURE_DEMO_MODE=0
FEATURE_DEMO_RESET=0
```

**Frontend `.env.local`:**
```bash
PUBLIC_API_URL=http://localhost:8080
PUBLIC_DEMO_MODE=false
DEMO_MODE=false
BETTER_AUTH_SECRET=dev-secret
ORIGIN=http://localhost:5173
```

**Simulation Behavior:**
- Worker returns mock OCR results (see `backend/app/jobs/worker.py`)
- 1-second simulated processing delay
- No API calls to LLM providers
- Useful for testing UI flows and job orchestration

**When to use:**
- Developing without API keys
- Testing job workflows
- CI/CD pipelines
- Offline development

---

### 4. Demo Mode

Use for presentations and stakeholder demos. Uses pre-baked sample data.

**Backend `.env.local`:**
```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./demo.db

# OCR Provider (Demo uses pre-baked data)
OCR_PROVIDER_NAME=open_ai
OCR_PROVIDER_MODEL=gpt-4o-mini
OCR_PROVIDER_API_KEY=  # Not required

# Feature Flags
FEATURE_ENABLE_SIMULATION=1
FEATURE_ENABLE_DEBUG_MODE=0
FEATURE_ENABLE_BETA_FEATURES=0
FEATURE_DEMO_MODE=1
FEATURE_DEMO_RESET=1
```

**Frontend `.env.local`:**
```bash
PUBLIC_API_URL=http://localhost:8080
PUBLIC_DEMO_MODE=true
DEMO_MODE=true
BETTER_AUTH_SECRET=demo-secret
ORIGIN=http://localhost:5173
```

**Demo Behavior:**
- `/workspace/demo` route shows virtual campaign
- Pre-loaded with sample petitions and results
- Reset button clears all demo data
- Data uses `demo-` prefix in database
- Session can load pre-baked demo sessions

**When to use:**
- Stakeholder presentations
- Sales demos
- Onboarding new users
- Testing full workflow end-to-end

**Demo Data Management:**
```bash
# Reset demo from UI
Navigate to /workspace/demo → Click "Reset Demo"

# Load pre-baked session
Navigate to /workspace/demo → Select session → Click "Load"
```

---

### 5. Testing Mode

Use for running automated test suites.

**Backend (pytest fixtures handle this):**
```bash
# Tests use temporary SQLite databases
# Feature flags controlled by test fixtures
# See: backend/tests/test_config.py
```

**Frontend (Vitest/Playwright):**
```bash
# Set in playwright.config.ts or vitest.config.ts
PUBLIC_API_URL=http://localhost:8080
PUBLIC_DEMO_MODE=false
DEMO_MODE=false
```

**Test Configuration:**
- Ephemeral databases (created per-test)
- Simulation mode enabled by default
- Mock external API calls
- Deterministic test data

---

## Switching Between Modes

### Quick Reference: Environment Files

| Service | File | How to Load | Use Case |
|---------|------|-------------|----------|
| **Backend** | `.env.local` | `--env local` or default | Local development |
| Backend | `.env.dev` | `--env dev` | Development with real LLM |
| Backend | `.env.prod` | `--env prod` | Production deployment |
| Backend | `.env.simulation` | `ENV_FILE=.env.simulation` | No API keys needed |
| **Frontend** | `.env` | Always loaded | Base config |
| Frontend | `.env.local` | Always loaded | Local overrides |
| Frontend | `.env.development` | `bun run dev` | Development mode |
| Frontend | `.env.demo` | `MODE=demo bun run dev` | Demo presentations |
| Frontend | `.env.production` | `bun run build` | Production build |

### Backend: Using `--env` Flag

The backend supports multiple environment files via the `--env` flag:

```bash
cd backend

# Load .env.local (default)
uv run python main.py --env local

# Load .env.dev
uv run python main.py --env dev

# Load .env.prod
uv run python main.py --env prod

# No flag defaults to .env.local
uv run python main.py
```

**Supported values:** `local`, `debug`, `dev`, `prod`

### Backend: Using ENV_FILE (for tests/scripts)

You can also set `ENV_FILE` directly for tests or scripts that don't use `main.py`:

```bash
cd backend

# Load specific env file
ENV_FILE=.env.dev uv run python -c "from app.settings.env_settings import get_settings; print(get_settings().demo_mode)"

# Or in pytest
ENV_FILE=.env.simulation uv run pytest tests/
```

### Frontend: Using MODE Variable

SvelteKit/Vite uses the `MODE` environment variable:

```bash
cd frontend-svelt

# Default (development mode)
bun run dev                    # Loads .env, .env.local, .env.development

# Custom mode
MODE=demo bun run dev          # Loads .env, .env.local, .env.demo
MODE=staging bun run build     # Loads .env, .env.local, .env.staging
```

---

## Environment File Templates

### Suggested Backend Files

| File | Mode | API Key | Purpose |
|------|------|---------|---------|
| `.env.example` | - | No | Template committed to repo |
| `.env.local` | Local | Required | Local development with real LLM |
| `.env.simulation` | Simulation | No | Development without API keys |
| `.env.dev` | Dev | Required | Development with real LLM |
| `.env.demo` | Demo | No | Demo mode with pre-baked data |
| `.env.prod` | Production | Required | Production deployment (git-ignored) |

### Suggested Frontend Files

| File | Mode | Purpose |
|------|------|---------|
| `.env.example` | - | Template committed to repo |
| `.env.local` | Any | Local overrides (git-ignored) |
| `.env.development` | Development | Development settings |
| `.env.demo` | Demo | Demo mode settings |
| `.env.production` | Production | Production settings |

### Directory Structure

```
backend/
├── .env.example          # Template with all options (committed)
├── .env                  # Base config
├── .env.local            # Local development (git-ignored)
├── .env.simulation       # Simulation mode
├── .env.dev              # Development mode
├── .env.demo             # Demo mode
└── .env.prod             # Production mode (git-ignored)

frontend-svelt/
├── .env.example          # Template (committed)
├── .env                  # Base config
├── .env.local            # Local overrides (git-ignored)
├── .env.development      # Development mode
├── .env.demo             # Demo mode
└── .env.production       # Production mode
```

### Template Contents

**Backend `.env.simulation` (no API keys needed):**
```bash
DATABASE_URL=sqlite:///./dev.db
OCR_PROVIDER_NAME=open_ai
OCR_PROVIDER_MODEL=gpt-4o-mini
OCR_PROVIDER_API_KEY=
FEATURE_ENABLE_SIMULATION=1
FEATURE_ENABLE_DEBUG_MODE=1
FEATURE_DEMO_MODE=0
FEATURE_DEMO_RESET=0
```

> **Note:** Use `sqlite:///` (sync driver) not `sqlite+aiosqlite:///` (async). The `init_db()` function uses synchronous SQLAlchemy calls.

**Backend `.env.demo` (for presentations):**
```bash
DATABASE_URL=sqlite:///./demo.db
OCR_PROVIDER_NAME=open_ai
OCR_PROVIDER_MODEL=gpt-4o-mini
OCR_PROVIDER_API_KEY=
FEATURE_ENABLE_SIMULATION=1
FEATURE_ENABLE_DEBUG_MODE=0
FEATURE_DEMO_MODE=1
FEATURE_DEMO_RESET=1
```

**Backend `.env.prod` (production):**
```bash
DATABASE_URL=postgresql+psycopg://user:password@host:5432/votecatcher
OCR_PROVIDER_NAME=open_ai
OCR_PROVIDER_MODEL=gpt-4o
OCR_PROVIDER_API_KEY=sk-your-production-key
FEATURE_ENABLE_SIMULATION=0
FEATURE_ENABLE_DEBUG_MODE=0
FEATURE_DEMO_MODE=0
FEATURE_DEMO_RESET=0
```

**Frontend `.env.demo`:**
```bash
PUBLIC_API_URL=http://localhost:8080
PUBLIC_DEMO_MODE=true
DEMO_MODE=true
BETTER_AUTH_SECRET=demo-secret
ORIGIN=http://localhost:5173
```

**Frontend `.env.production`:**
```bash
PUBLIC_API_URL=https://api.yourdomain.com
PUBLIC_DEMO_MODE=false
DEMO_MODE=false
BETTER_AUTH_SECRET=your-secure-random-secret-min-32-chars
ORIGIN=https://yourdomain.com
```

---

## Feature Flag Details

### `FEATURE_ENABLE_SIMULATION`

When enabled:
- Worker returns mock OCR data instead of calling LLM APIs
- No API key required
- 1-second processing delay simulated
- Useful for CI/CD and offline development

### `FEATURE_ENABLE_DEBUG_MODE`

When enabled:
- Verbose logging to console
- SQL query logging
- Stack traces on errors
- Additional debug endpoints

### `FEATURE_DEMO_MODE`

When enabled:
- `/workspace/demo` route accessible
- Pre-baked demo sessions available
- Demo data uses `demo-` prefix
- In-memory campaign support

### `FEATURE_DEMO_RESET`

When enabled:
- "Reset Demo" button visible
- Clears all demo-prefixed data
- Required for demo presentations

### `FEATURE_ENABLE_BETA_FEATURES`

When enabled:
- Unreleased features visible
- Experimental UI components
- For internal testing only

---

## How Feature Flags Propagate

Frontend fetches feature flags from backend at runtime:

```
Frontend                    Backend
   │                           │
   │  GET /api/config/settings │
   │──────────────────────────>│
   │                           │
   │  {                        │
   │    features: {            │
   │      simulationMode,      │
   │      demoMode,            │
   │      ...                  │
   │    }                      │
   │  }                        │
   │<──────────────────────────│
```

The frontend `settings` store (`src/lib/stores/settings.ts`) caches these flags for UI conditional rendering.

---

## Troubleshooting

### "OCR_PROVIDER_API_KEY is not configured"

**Cause:** Running in non-simulation mode without API key.

**Fix:**
```bash
# Option 1: Add API key
OCR_PROVIDER_API_KEY=sk-your-key

# Option 2: Enable simulation
FEATURE_ENABLE_SIMULATION=1
```

### Demo mode not working

**Cause:** Frontend env vars not set correctly.

**Fix:**
```bash
# Both must be set to "true" (string)
PUBLIC_DEMO_MODE=true
DEMO_MODE=true
```

### Feature flags not updating

**Cause:** Frontend caches settings.

**Fix:** Refresh browser or clear settings store:
```javascript
// In browser console
localStorage.clear();
location.reload();
```

---

## Related Documentation

- [Running Locally](running-locally.md) - Detailed setup guide
- [Demo Walkthrough](demo-walkthrough.md) - Demo script and checklist
- [SPEC.md](../openspec/SPEC.md#appendix-b-configuration) - Technical specification

---

**Document Version:** 1.0
**Last Updated:** 2026-03-12
