# Running VoteCatcher Locally

## Prerequisites

- Python 3.13+
- uv package manager
- Node.js 20+
- Bun package manager
- PostgreSQL (optional, for full functionality)

## Backend Setup

### Installation

```bash
cd backend
uv sync --dev
```

### Environment Configuration

Create `.env.local` in the backend directory:

#### Required Variables

```env
# OCR Provider (for petition text extraction)
OCR_PROVIDER_NAME=open_ai
OCR_PROVIDER_MODEL=gpt-4o-mini
OCR_PROVIDER_API_KEY=your-openai-api-key-here
```

#### Local Development Paths

```env
# Runtime directory structure (relative to backend/)
DEV_LOCAL_RUNTIME_DIR=runtime
DEV_LOCAL_RUNTIME_DB_DIR=database
DEV_LOCAL_RUNTIME_DB_FILE=database/local_db.db
DEV_LOCAL_BALLOT_CROP_DIR=crops
DEV_LOCAL_CAMPAIGNS_DIR=campaigns
DEV_LOCAL_PETITION_SCAN_DIR=scans
DEV_LOCAL_VOTER_REGISTRATION_DIR=voters
DEV_LOCAL_OCR_DIR=ocr

# Clear runtime on launch (useful for clean dev starts)
DEV_CLEAR_RUNTIME_ON_LAUNCH=1
```

#### Optional: Supabase (Production)

```env
SUPABASE_PROJECT_URL=your-project-url
SUPABASE_PROJECT_KEY=your-project-key
ENABLE_SUPABASE=0  # Set to 1 for production
```

#### Feature Flags

```env
FEATURE_ENABLE_SIMULATION=0      # Enable OCR simulation mode
FEATURE_ENABLE_BETA_FEATURES=0   # Enable beta features
FEATURE_ENABLE_DEBUG_MODE=0      # Enable debug mode
```

#### Development Settings

```env
DEV_LOGGING_ENABLED=1            # Enable detailed logging
DEV_LOCAL_DB_ENABLE_LOGGING=1    # Enable database query logging
```

### Running

```bash
cd backend

# Local development
uv run main.py --env local

# Debug mode
uv run main.py --env debug

# Development
uv run main.py --env dev

# Production
uv run main.py --env prod
```

The API will be available at http://localhost:8080

API documentation: http://localhost:8080/docs

### Testing

```bash
cd backend

# Run all tests
uv run pytest

# Run with verbose output
uv run pytest tests/ -v

# Run with coverage
uv run pytest --cov=app

# Run specific test module
uv run pytest tests/matching/ -v
```

### Linting & Formatting

```bash
cd backend

# Type check
uv run basedpyright app/

# Lint
uv run ruff check app/

# Format check
uv run ruff format app/ --check

# Auto-fix lint issues
uv run ruff check app/ --fix

# Auto-format
uv run ruff format app/
```

## Frontend Setup

### Installation

```bash
cd frontend-svelt
bun install
```

### Environment Configuration

Create `.env.local` in the frontend directory:

#### Required Variables

```env
# Backend API URL (must include trailing slash)
PUBLIC_API_URL="http://localhost:8080/"

# Demo mode (uses sample data)
DEMO_MODE=1

# Database connection (for server-side queries)
DATABASE_URL="postgres://postgres:postgres@localhost:5432/votecatcher"

# App origin (for CORS and auth)
ORIGIN="http://localhost:5173"

# Better Auth secret (32+ chars for production)
# Generate with: openssl rand -base64 32
BETTER_AUTH_SECRET="dev-secret-key-for-local-development-32ch"
```

#### OCR Configuration (Frontend)

```env
# These mirror backend config for client-side reference
OCR_PROVIDER_NAME="open_ai"
OCR_PROVIDER_MODEL=gpt-4o-mini
OCR_PROVIDER_API_KEY=your-openai-api-key-here
```

### Running

```bash
cd frontend-svelt

# Development server
bun run dev
```

The app will be available at http://localhost:5173

### Testing

```bash
cd frontend-svelt

# Unit tests
bun run test:unit

# Unit tests (watch mode)
bun run test:unit --watch

# E2E tests
bun run test:e2e

# All tests
bun run test
```

### Linting & Formatting

```bash
cd frontend-svelt

# Type check
bun run check

# Lint
bun run lint

# Auto-fix lint issues
bun run lint:fix

# Format check
bun run fmt:check

# Auto-format
bun run fmt
```

### Building

```bash
cd frontend-svelt

# Production build
bun run build

# Preview production build
bun run preview
```

## Feature Flags

The application supports feature flags for development and testing:

### Available Flags

- `SIMULATE_OCR_RESULTS`: When enabled, returns simulated OCR results instead of calling real OCR service

### Usage

```typescript
import { featureFlags } from '$lib/stores/featureFlags';

// Check if simulation is enabled
if (featureFlags.isFeatureEnabled('SIMULATE_OCR_RESULTS')) {
  // Use simulated results
}

// Toggle feature
featureFlags.toggleFeature('SIMULATE_OCR_RESULTS', true);
```

### Storage

Feature flags are persisted in localStorage under the key `votecatcher_feature_overrides`.

## Full Development Workflow

### Terminal 1 - Backend

```bash
cd backend
uv run main.py --env local
```

### Terminal 2 - Frontend

```bash
cd frontend-svelt
bun run dev
```

### Access

- Frontend: http://localhost:5173
- Backend API: http://localhost:8080
- API Docs: http://localhost:8080/docs

## Docker Setup (Coming Soon)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Troubleshooting

### Backend won't start

1. Check Python version: `python --version` (should be 3.13+)
2. Check uv is installed: `uv --version`
3. Check .env.local exists and has correct values
4. Try fresh install: `rm -rf .venv && uv sync --dev`

### Frontend won't start

1. Check Node version: `node --version` (should be 20+)
2. Check Bun is installed: `bun --version`
3. Try fresh install: `rm -rf node_modules && bun install`

### Tests failing

1. Ensure all dependencies are installed
2. Check environment variables are set
3. Run with verbose output for details

### Type errors

1. Run `bun run check` in frontend
2. Run `uv run basedpyright app/` in backend
3. Check for missing type stubs

## Known Issues

### Pre-existing Frontend Errors

The frontend currently has pre-existing type and lint errors in legacy code:

- **Type errors**: ~89 errors in various files
- **Lint errors**: ~28 errors

These errors existed before the recent refactoring work and do not affect the new features:

- Pagination component
- Feature flag system
- Simulate OCR endpoint
- Results table fixes

A separate task will address these legacy errors.

## Environment Variables Quick Reference

### Backend (`.env.local`)

| Variable | Purpose | Example |
|----------|---------|---------|
| `OCR_PROVIDER_NAME` | OCR service provider | `open_ai` |
| `OCR_PROVIDER_MODEL` | OCR model to use | `gpt-4o-mini` |
| `OCR_PROVIDER_API_KEY` | API key for OCR provider | `sk-proj-...` |
| `DEV_LOCAL_RUNTIME_DIR` | Base runtime directory | `runtime` |
| `DEV_LOGGING_ENABLED` | Enable dev logging | `1` |
| `FEATURE_ENABLE_SIMULATION` | Enable simulation mode | `0` |

### Frontend (`.env.local`)

| Variable | Purpose | Example |
|----------|---------|---------|
| `PUBLIC_API_URL` | Backend API URL (trailing slash!) | `http://localhost:8080/` |
| `DEMO_MODE` | Use sample data | `1` |
| `DATABASE_URL` | PostgreSQL connection string | `postgres://...` |
| `ORIGIN` | App origin for CORS/auth | `http://localhost:5173` |
| `BETTER_AUTH_SECRET` | Auth encryption key (32+ chars) | `dev-secret-...` |

### Production Checklist

- [ ] Set `ENABLE_SUPABASE=1` (if using Supabase)
- [ ] Generate strong `BETTER_AUTH_SECRET` (32+ random chars)
- [ ] Update `PUBLIC_API_URL` to production URL
- [ ] Update `ORIGIN` to production domain
- [ ] Secure `OCR_PROVIDER_API_KEY`
- [ ] Set production `DATABASE_URL`
