# Running VoteCatcher Locally

This guide covers local development setup. For a quick start, see the main [README.md](../README.md).

## Prerequisites

- **Python 3.12+** (3.13 recommended)
- **uv package manager** - [Install](https://docs.astral.sh/uv/)
- **Node.js 20+** or **Bun** - [Bun Install](https://bun.sh/)
- **PostgreSQL** (optional, SQLite works for development)
- **Git**
- **API key** for at least one LLM provider (optional - use simulation mode without)

> **Note:** See [Configuration Modes](configuration-modes.md) for running without API keys using simulation mode.

## Backend Setup

### Installation

```bash
cd backend
uv sync --dev
```

### Environment Configuration

Create `.env.local` in the backend directory. See [Configuration Modes](configuration-modes.md) for all supported modes.

**Quick Start (Simulation Mode - no API key required):**

```env
# Database (use sqlite:// not sqlite+aiosqlite://)
DATABASE_URL=sqlite:///./dev.db

# OCR Provider (not used in simulation)
OCR_PROVIDER_NAME=open_ai
OCR_PROVIDER_MODEL=gpt-4o-mini
OCR_PROVIDER_API_KEY=

# Feature Flags
FEATURE_ENABLE_SIMULATION=1
FEATURE_ENABLE_DEBUG_MODE=1
```

**Development Mode (with real LLM):**

```env
# Database (use sqlite:// not sqlite+aiosqlite://)
DATABASE_URL=sqlite:///./dev.db

# OCR Provider (required)
OCR_PROVIDER_NAME=open_ai
OCR_PROVIDER_MODEL=gpt-4o-mini
OCR_PROVIDER_API_KEY=your-openai-api-key-here

# Feature Flags
FEATURE_ENABLE_SIMULATION=0
FEATURE_ENABLE_DEBUG_MODE=1
```

### Database Setup

```bash
cd backend

# Run migrations
uv run alembic upgrade head

# Verify tables created
uv run python -c "from app.data.database.session import engine; print(engine.table_names())"
```

### Running the Backend

```bash
cd backend

# Development server with auto-reload (uses .env.local)
uv run python main.py --env local

# Use a different environment file
uv run python main.py --env dev      # Loads .env.dev
uv run python main.py --env prod     # Loads .env.prod

# Server starts at http://localhost:8080
# API documentation at http://localhost:8080/docs
# ReDoc at http://localhost:8080/redoc
```

> **Note:** The `--env` flag loads different `.env` files. See [Configuration Modes](configuration-modes.md#switching-between-modes) for all options.

### Testing

```bash
cd backend

# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test categories
uv run pytest tests/unit/services/ -v        # Unit tests
uv run pytest tests/integration/ -v          # Integration tests
uv run pytest tests/integration/api/ -v      # API tests

# Run specific test file
uv run pytest tests/unit/services/test_file_service.py -v
```

### Code Quality

```bash
cd backend

# Type check
uv run basedpyright app/

# Lint
uv run ruff check app/

# Auto-fix lint issues
uv run ruff check app/ --fix

# Format check
uv run ruff format app/ --check

# Auto-format
uv run ruff format app/
```

## Frontend Setup

### Installation

```bash
cd frontend
bun install
```

### Environment Configuration

Create `.env.local` in the frontend directory. See [Configuration Modes](configuration-modes.md) for all supported modes.

**Quick Start:**

```env
# Backend API URL
PUBLIC_API_URL=http://localhost:8080

# Demo mode (set to true for presentations)
PUBLIC_DEMO_MODE=false
DEMO_MODE=false

# App origin for CORS
ORIGIN=http://localhost:5173

# Auth secret for sessions
BETTER_AUTH_SECRET=your-secret-here
```

**Demo Mode:**

```env
PUBLIC_API_URL=http://localhost:8080
PUBLIC_DEMO_MODE=true
DEMO_MODE=true
ORIGIN=http://localhost:5173
BETTER_AUTH_SECRET=demo-secret
```

### Running the Frontend

```bash
cd frontend

# Development server (loads .env, .env.local, .env.development)
bun run dev

# Run with demo mode (loads .env, .env.local, .env.demo)
MODE=demo bun run dev

# Production build (loads .env, .env.local, .env.production)
bun run build

# Server starts at http://localhost:5173
```

> **Note:** Use `MODE=<name>` to load `.env.<name>` files. See [Configuration Modes](configuration-modes.md#switching-between-modes) for details.

### Testing

```bash
cd frontend

# Run all tests
bun run test

# Run in watch mode
bun run test --watch

# Run with coverage
bun run test --coverage

# Run specific test file
bun run test src/lib/components/ui/Button.test.ts
```

### Code Quality

```bash
cd frontend

# Type check
bun run typecheck
# or
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
cd frontend

# Production build
bun run build

# Preview production build
bun run preview

# Build runs at http://localhost:4173
```

## Full Development Workflow

### Terminal 1 - Backend

```bash
cd backend
uv run python main.py --env local
# http://localhost:8080
```

### Terminal 2 - Frontend

```bash
cd frontend
bun run dev
# http://localhost:5173
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | SvelteKit application |
| Backend API | http://localhost:8080 | FastAPI application |
| API Docs | http://localhost:8080/docs | Swagger UI |
| ReDoc | http://localhost:8080/redoc | Alternative API docs |
| Workspace | http://localhost:5173/workspace | Main application |

## Sample Data

The repository includes sample data for testing:

```
samples/dc/
├── fake_voter_records.csv        # 100K synthetic voter records
├── fake_signed_petitions.pdf      # Sample petition PDFs
└── fake_signed_petitions_1-10.pdf # Additional samples
```

These are used for:
- API endpoint testing
- OCR validation
- Matching algorithm calibration
- Demo sessions

## Database Management

### SQLite vs PostgreSQL

| Aspect | SQLite | PostgreSQL |
|--------|--------|------------|
| **Setup** | Zero config (file-based) | Requires server (Docker or native) |
| **Use case** | Development, local testing | Production, large datasets, concurrent users |
| **Concurrency** | Single writer | Multiple concurrent writers |
| **Data persistence** | `./dev.db` file | Docker volume or external server |
| **Performance** | Fine for <10K records | Better for large voter files |

**Recommendation**: Start with SQLite for quick local development. Switch to PostgreSQL when:
- Testing production-like scenarios
- Working with large voter files (>10K records)
- Multiple developers need shared database
- Testing concurrent write scenarios

### Quick Commands

```bash
# Start PostgreSQL for local dev (Docker required)
just dev-postgres

# Stop PostgreSQL (data preserved)
just dev-postgres-stop

# Reset everything
just dev-postgres-clean
```

> **Note:** This project uses `just` as the primary task runner (works on macOS, Linux, Windows).
> Install with: `brew install just` (macOS) or `winget install just` (Windows).
> See `just --list` for all available commands. A generated `Makefile` is also available for Unix users who prefer `make`.

### SQLite (Development)

```bash
# Location: backend/dev.db
# Auto-created on first run

# Reset database
rm backend/dev.db
cd backend && uv run alembic upgrade head
```

### PostgreSQL (Production-like)

**Option 1: Using Makefile (Recommended)**

```bash
# Start PostgreSQL, wait for ready, run migrations
make dev-postgres

# Stop PostgreSQL (data preserved)
make dev-postgres-stop

# Stop and remove all data
make dev-postgres-clean
```

Then update `backend/.env.local`:
```env
DATABASE_URL=postgresql+psycopg://votecatcher:votecatcher_dev@localhost:5432/votecatcher
```

**Option 2: Manual Docker**

```bash
# Start PostgreSQL with Docker
docker run -d \
  --name votecatcher-db \
  -e POSTGRES_DB=votecatcher \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:16-alpine

# Update .env.local
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/votecatcher

# Run migrations
cd backend && uv run alembic upgrade head
```

### Migrations

```bash
cd backend

# Create new migration
uv run alembic revision --autogenerate -m "Add new table"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# View migration history
uv run alembic history
```

## Troubleshooting

### Backend won't start

1. **Check Python version**: `python --version` (needs 3.12+)
2. **Check uv installed**: `uv --version`
3. **Verify .env.local exists** with required variables
4. **Try fresh install**:
   ```bash
   cd backend
   rm -rf .venv
   uv sync --dev
   ```

### Frontend won't start

1. **Check Node/Bun version**: `node --version` or `bun --version`
2. **Try fresh install**:
   ```bash
   cd frontend
   rm -rf node_modules bun.lockb
   bun install
   ```

### Database errors

1. **Check migrations applied**: `uv run alembic current`
2. **Reset and reapply**:
   ```bash
   rm dev.db
   uv run alembic upgrade head
   ```

### Test failures

1. **Ensure all dependencies**: `uv sync --dev` (backend) / `bun install` (frontend)
2. **Check environment variables**: `.env.local` present
3. **Run with verbose output**: `uv run pytest -v` / `bun run test --reporter=verbose`

### Type errors

1. **Backend**: `uv run basedpyright app/`
2. **Frontend**: `bun run typecheck`
3. **Check for missing type stubs**: `uv add --dev types-<package>`

### Port conflicts

```bash
# Backend (8080)
lsof -ti:8080 | xargs kill -9

# Frontend (5173)
lsof -ti:5173 | xargs kill -9

# Preview (4173)
lsof -ti:4173 | xargs kill -9
```

## Environment Variables Reference

### Backend

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `OCR_PROVIDER_NAME` | Yes* | OCR service provider (`open_ai`, `gemini_ai`, `mistral_ai`) | `open_ai` |
| `OCR_PROVIDER_MODEL` | Yes* | Model to use | `gpt-4o-mini` |
| `OCR_PROVIDER_API_KEY` | Yes* | API key for provider | - |
| `DATABASE_URL` | No | Database connection string | `sqlite+aiosqlite:///./dev.db` |
| `DEV_LOGGING_ENABLED` | No | Enable dev logging | `1` |
| `DEV_LOCAL_DB_ENABLE_LOGGING` | No | Enable DB query logging | `0` |
| `FEATURE_ENABLE_SIMULATION` | No | Enable simulation mode (mock OCR) | `0` |
| `FEATURE_ENABLE_DEBUG_MODE` | No | Enable debug mode | `0` |
| `FEATURE_ENABLE_BETA_FEATURES` | No | Enable beta features | `0` |
| `FEATURE_DEMO_MODE` | No | Enable demo mode | `0` |
| `FEATURE_DEMO_RESET` | No | Enable demo data reset | `0` |

> **Note:** `*` Not required when `FEATURE_ENABLE_SIMULATION=1`. See [Configuration Modes](configuration-modes.md) for details.

### Frontend

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `PUBLIC_API_URL` | Yes | Backend API URL (no /api suffix) | `http://localhost:8080` |
| `PUBLIC_DEMO_MODE` | No | Client-side demo mode flag | `false` |
| `DEMO_MODE` | No | Server-side demo mode flag | `false` |
| `ORIGIN` | No | App origin for CORS | `http://localhost:5173` |
| `BETTER_AUTH_SECRET` | No | Auth secret for sessions | (auto-generated) |

## Production Checklist

Before deploying to production:

- [ ] Strong database password in `DATABASE_URL`
- [ ] Secure `OCR_PROVIDER_API_KEY` (use secrets manager)
- [ ] `DEBUG_MODE=0` and `FEATURE_ENABLE_DEBUG_MODE=0`
- [ ] `PUBLIC_API_URL` points to production backend
- [ ] `ORIGIN` matches production domain
- [ ] HTTPS enabled
- [ ] Database backups configured
- [ ] Rate limiting configured

## Switching Environment Files

### Backend

Use the `--env` flag to load different `.env` files:

| Command | Loads | Use Case |
|---------|-------|----------|
| `uv run python main.py` | `.env.local` | Default local dev |
| `uv run python main.py --env local` | `.env.local` | Local development |
| `uv run python main.py --env dev` | `.env.dev` | Development mode |
| `uv run python main.py --env prod` | `.env.prod` | Production mode |

For scripts/tests, set `ENV_FILE`:
```bash
ENV_FILE=.env.simulation uv run pytest tests/
```

### Frontend

Use `MODE` to load different `.env` files:

| Command | Loads | Use Case |
|---------|-------|----------|
| `bun run dev` | `.env.development` | Development |
| `MODE=demo bun run dev` | `.env.demo` | Demo mode |
| `bun run build` | `.env.production` | Production build |

> **See [Configuration Modes](configuration-modes.md) for complete configuration guide.**

## Related Documentation

- [Configuration Modes](configuration-modes.md) - All configuration modes explained
- [Architecture Overview](architecture/README.md)
- [API Specification](../backend/openapi.yaml)
- [Development Guide](development/README.md)
- [Deployment Guide](deployment/) - Coming soon
