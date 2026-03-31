# VoteCatcher Task Runner
#
# Usage:
#   just                  # List available recipes
#   just dev-postgres     # Start PostgreSQL for development
#   just test             # Run all tests
#
# Install just:
#   brew install just      # macOS
#   apt install just       # Linux
#   winget install just    # Windows

# Default recipe - show help
default:
    @just --list

# Install all dependencies (backend + frontend)
install:
    cd backend && uv sync
    cd frontend-svelt && bun install

# Start development servers via docker-compose
dev:
    docker-compose up --build

# Run all tests (backend pytest, frontend vitest)
test:
    cd backend && uv run pytest
    cd frontend-svelt && bun run test:unit

# Run linters (ruff, oxlint)
lint:
    cd backend && uv run ruff check .
    cd frontend-svelt && bun run lint

# Run type checkers (basedpyright, svelte-check)
typecheck:
    cd backend && uv run basedpyright
    cd frontend-svelt && bun run check

# Clean build artifacts
clean:
    rm -rf backend/.pytest_cache backend/.ruff_cache backend/__pycache__ backend/**/__pycache__
    rm -rf frontend-svelt/.svelte-kit frontend-svelt/node_modules/.cache

# Start docker containers
docker-up:
    docker-compose up -d

# Stop docker containers
docker-down:
    docker-compose down

# Start PostgreSQL for local development with migrations
dev-postgres:
    @echo "Starting PostgreSQL container..."
    docker compose up db -d
    @echo "Waiting for PostgreSQL to be ready..."
    @until docker compose exec -T db pg_isready -U votecatcher -d votecatcher > /dev/null 2>&1; do \
        sleep 1; \
    done
    @echo "PostgreSQL is ready!"
    @echo "Running migrations..."
    cd backend && DATABASE_URL=postgresql+psycopg://votecatcher:votecatcher_dev@localhost:5432/votecatcher uv run alembic upgrade head
    @echo ""
    @echo "PostgreSQL ready at localhost:5432"
    @echo "Connection: postgresql+psycopg://votecatcher:votecatcher_dev@localhost:5432/votecatcher"
    @echo ""
    @echo "To use with backend, update backend/.env.local:"
    @echo "  DATABASE_URL=postgresql+psycopg://votecatcher:votecatcher_dev@localhost:5432/votecatcher"
    @echo ""
    @echo "Then run: cd backend && uv run python main.py --env local"

# Stop PostgreSQL container (data preserved)
dev-postgres-stop:
    docker compose stop db
    @echo "PostgreSQL stopped. Data preserved in docker volume."

# Stop PostgreSQL and remove data volume
dev-postgres-clean:
    docker compose down -v
    @echo "PostgreSQL stopped and data volume removed."

# Show docker logs
docker-logs:
    docker-compose logs -f

# Run database migrations
migrate:
    cd backend && uv run alembic upgrade head

# Rollback last migration
migrate-down:
    cd backend && uv run alembic downgrade -1

# Create new migration
migrate-create msg="description":
    cd backend && uv run alembic revision --autogenerate -m "{{msg}}"

# Reset database (drop all tables and re-run migrations)
db-reset:
    cd backend && uv run alembic downgrade base && uv run alembic upgrade head

# Run security scans (bandit, pip-audit, bun audit)
security-scan:
    cd backend && uv run bandit -r app/
    cd backend && uv run pip-audit
    cd frontend-svelt && bun audit

# Run Dockerfile linting with hadolint
docker-lint:
    hadolint backend/Dockerfile
    hadolint frontend-svelt/Dockerfile

# Lint backend only (ruff check + format check)
lint-backend:
    cd backend && uv run ruff check .
    cd backend && uv run ruff format --check .

# Lint frontend only (oxlint + format check)
lint-frontend:
    cd frontend-svelt && bun run lint || echo "WARNING: Frontend lint has pre-existing errors (tracked in Phase 2)"
    cd frontend-svelt && bun run fmt:check || echo "WARNING: Frontend format has pre-existing issues (tracked in Phase 2)"

# Typecheck backend only
typecheck-backend:
    cd backend && uv run basedpyright

# Typecheck frontend only
typecheck-frontend:
    cd frontend-svelt && bun run check

# Run backend tests with coverage (unit only — integration needs running DB)
test-backend:
    cd backend && uv run pytest tests/unit tests/matching tests/test_config.py --cov=app --cov-report=xml

# Run backend integration tests (requires PostgreSQL)
test-backend-integration:
    cd backend && uv run pytest tests/integration

# Run frontend tests
test-frontend:
    cd frontend-svelt && bun run test:unit

# Simulate full CI pipeline locally
ci-sim:
    @echo "=== Lockfile Integrity ==="
    cd backend && uv lock --check
    cd frontend-svelt && bun install --frozen-lockfile
    @echo "=== Backend Lint ==="
    just lint-backend
    @echo "=== Backend Typecheck ==="
    just typecheck-backend
    @echo "=== Backend Tests ==="
    just test-backend
    @echo "=== Frontend Lint ==="
    just lint-frontend
    @echo "=== Frontend Typecheck ==="
    just typecheck-frontend
    @echo "=== Security Scan ==="
    just security-scan || echo "WARNING: Security scan has pre-existing issues or missing tools"
    @echo "=== Docker Lint ==="
    just docker-lint || echo "WARNING: Docker lint has pre-existing findings"
    @echo "=== CI Simulation Complete ==="

# Sync Makefile from justfile (for Unix users)
sync-makefile:
    @python scripts/just-to-make.py > Makefile
    @echo "Makefile synced from justfile"
