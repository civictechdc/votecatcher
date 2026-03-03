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

```env
DATABASE_URL=postgresql://user:password@localhost:5432/votecatcher
VITE_API_URL=http://localhost:8080
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
