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

# Run all security scans
security-scan:
    just security-scan-backend
    just security-scan-frontend

# Run backend security scans (bandit, pip-audit)
security-scan-backend:
    cd backend && uv run bandit -r app/
    cd backend && uv run pip-audit

# Run frontend security scan (bun audit)
security-scan-frontend:
    cd frontend-svelt && bun audit

# Run SAST with semgrep (full scan)
sast:
    semgrep --config auto --config p/owasp-top-ten --config p/fastapi --config p/jwt --config p/xss --json -o semgrep-results.json backend/ frontend-svelt/src/

# Run SAST with baseline commit mode (PR diffs only)
sast-pr:
    semgrep --config auto --config p/owasp-top-ten --config p/fastapi --config p/jwt --config p/xss --baseline-commit origin/main --json -o semgrep-pr.json backend/ frontend-svelt/src/

# Run SCA — dependency vulnerability + license scanning
sca:
    osv-scanner --lockfile=backend/uv.lock --lockfile=frontend-svelt/bun.lock --licenses
    trivy fs --severity CRITICAL,HIGH --scanners vuln,license .

# Run container image scanning
container-scan:
    docker build -t votecatcher-backend ./backend
    docker build -t votecatcher-frontend ./frontend-svelt
    trivy image --severity CRITICAL,HIGH votecatcher-backend
    trivy image --severity CRITICAL,HIGH votecatcher-frontend

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
    cd frontend-svelt && bun run lint
    cd frontend-svelt && bun run fmt:check

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

# Run DAST scan with nuclei (requires running backend at localhost:8080)
dast:
    nuclei -t .agent-workspace/quality-automation/nuclei-templates/ -u http://localhost:8080 -json -o nuclei-results.json

# Run code duplication analysis
duplication:
    jscpd backend/app/ frontend-svelt/src/ --min-lines 5 --min-tokens 50 --threshold 5 --reporters html

# Run complexity analysis
complexity:
    cd backend && uv run radon cc app/ -a -nb
    cd backend && uv run radon mi app/ -nb

# Run dead code analysis
dead-code:
    cd backend && uv run vulture app/ --min-confidence 80 --format json > vulture-report.json
    cd frontend-svelt && bunx ts-prune --json > ts-prune-report.json

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
    just security-scan
    @echo "=== Docker Lint ==="
    just docker-lint
    @echo "=== CI Simulation Complete ==="

# Sync Makefile from justfile (for Unix users)
sync-makefile:
    @python scripts/just-to-make.py > Makefile
    @echo "Makefile synced from justfile"
