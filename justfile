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
    cd frontend && bun install

# Start development servers via docker-compose
dev:
    docker compose up --build

# Start backend development server
dev-backend:
    cd backend && uv run python -m app --env local

# Start frontend development server
dev-frontend:
    cd frontend && bun run dev

# Run all tests (backend pytest, frontend vitest)
test:
    cd backend && uv run pytest
    cd frontend && bun run test:unit

# Run linters (ruff, oxlint) - validates all modified files
lint:
    @echo "=== Linting all modified files ==="
    cd backend && uv run ruff check .
    cd backend && uv run ruff format --check .
    cd frontend && bun run lint
    cd frontend && bun run fmt:check
    @echo "=== Linting complete ==="

# Run type checkers (basedpyright, svelte-check) - validates all modified files
typecheck:
    @echo "=== Typechecking all modified files ==="
    cd backend && uv run basedpyright
    cd frontend && bun run check
    @echo "=== Typechecking complete ==="

# Clean build artifacts
clean:
    rm -rf backend/.pytest_cache backend/.ruff_cache backend/__pycache__ backend/**/__pycache__
    rm -rf frontend/.svelte-kit frontend/node_modules/.cache

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

# Run backend security scans (bandit, uv audit)
security-scan-backend:
    cd backend && uv run bandit -r app/
    cd backend && uv audit

# Run frontend security scan (bun audit)
security-scan-frontend:
    cd frontend && bun audit

# Run SAST with semgrep (full scan)
sast:
    semgrep --config auto --config p/owasp-top-ten --config p/fastapi --config p/jwt --config p/xss --json -o semgrep-results.json backend/ frontend/src/

# Run SAST with baseline commit mode (PR diffs only)
sast-pr:
    semgrep --config auto --config p/owasp-top-ten --config p/fastapi --config p/jwt --config p/xss --baseline-commit origin/main --json -o semgrep-pr.json backend/ frontend/src/

# Run SCA — dependency vulnerability + license scanning
sca:
    osv-scanner scan --lockfile=backend/uv.lock --lockfile=frontend/bun.lock
    trivy fs --severity CRITICAL,HIGH --scanners vuln,license --format json --output trivy-results.json .

# Run container image scanning
container-scan:
    docker build -t votecatcher-backend ./backend
    docker build -t votecatcher-frontend ./frontend
    trivy image --severity CRITICAL,HIGH votecatcher-backend
    trivy image --severity CRITICAL,HIGH votecatcher-frontend

# Run Dockerfile linting with hadolint
docker-lint:
    hadolint backend/Dockerfile
    hadolint frontend/Dockerfile

# Lint backend only (ruff check + format check)
lint-backend:
    cd backend && uv run ruff check .
    cd backend && uv run ruff format --check .

# Lint frontend only (oxlint + format check)
lint-frontend:
    cd frontend && bun run lint
    cd frontend && bun run fmt:check

# Typecheck backend only (baseline-aware)
typecheck-backend:
    bash scripts/check-typecheck-baseline.sh

# Typecheck frontend only
typecheck-frontend:
    cd frontend && bun run check

# Run backend tests with coverage (unit only — integration needs running DB)
test-backend:
    cd backend && uv run pytest tests/unit tests/matching tests/test_config.py --cov=app --cov-report=xml

# Run backend integration tests (requires PostgreSQL)
test-backend-integration:
    cd backend && uv run pytest tests/integration

# Run security tests (matches CI security-test-backend job)
security-test:
    @echo "=== Running Security Tests ==="
    cd backend && uv run pytest tests/security/ -v --tb=short
    @echo "=== Security Tests Complete ==="

# Run DAST scan with nuclei (requires running backend at localhost:8080)
dast:
    nuclei -t .agent-workspace/quality-automation/nuclei-templates/ -u http://localhost:8080 -json -o nuclei-results.json

# Run code duplication analysis
duplication:
    jscpd backend/app/ --min-lines 5 --min-tokens 50 --threshold 5 --reporters html

duplication-frontend:
    cd frontend && npx fallow dupes

duplication-all:
    just duplication
    just duplication-frontend

# Run complexity analysis
complexity:
    cd backend && uv run radon cc app/ -a -nb --total-average
    cd backend && uv run radon mi app/ -s -nc

complexity-check:
    cd backend && uv run radon cc app/ -nc -n B

# Run dead code analysis
dead-code:
    cd backend && uv run vulture app/ vulture-whitelist.py --format json > vulture-report.json

dead-code-frontend:
    cd frontend && npx fallow dead-code

# Run fallow analysis on frontend (SvelteKit)
fallow:
    cd frontend && npx fallow

fallow-dead-code:
    cd frontend && npx fallow dead-code

fallow-dupes:
    cd frontend && npx fallow dupes

fallow-health:
    cd frontend && npx fallow health

fallow-audit:
    cd frontend && npx fallow audit --base main

# Run frontend tests
test-frontend:
    cd frontend && bun run test:unit

# Generate SBOM (Software Bill of Materials) for backend and frontend
sbom:
    syft backend/ -o spdx-json > sbom-backend.spdx.json
    syft frontend/ -o spdx-json > sbom-frontend.spdx.json

# Check for AGPL/GPL/LGPL license violations
license-check:
    @command -v osv-scanner >/dev/null 2>&1 || (echo "ERROR: osv-scanner not installed — run 'just install-tools'" && exit 1)
    @osv-scanner --lockfile=backend/uv.lock --lockfile=frontend/bun.lock --licenses --format json --output /tmp/osv-licenses.json || (echo "ERROR: osv-scanner failed — check lockfiles exist" && exit 1)
    @if [ ! -s /tmp/osv-licenses.json ]; then echo "ERROR: osv-scanner produced no output" && exit 1; fi
    @if grep -q "AGPL\|GPL\|LGPL" /tmp/osv-licenses.json; then echo "ERROR: AGPL/GPL/LGPL licenses detected" && exit 1; fi
    @echo "OK: No copyleft license violations"

# Lint and type-check Supabase Edge Functions
edge-functions:
    cd supabase/functions && deno lint
    cd supabase/functions && deno check */index.ts

# Build frontend and check bundle size
bundle-size:
    cd frontend && bun run build
    @echo "=== Bundle size ===" && find frontend/.svelte-kit/output/client -name "*.js" -exec du -ch {} + | tail -1

# Run backend performance benchmarks
benchmark:
    cd backend && uv run pytest tests/benchmarks/ --benchmark-only --benchmark-json=../benchmark-results.json

# Simulate full CI pipeline locally
ci-sim:
    @echo "=== Lockfile Integrity ==="
    cd backend && uv lock --check
    cd frontend && bun install --frozen-lockfile
    @echo "=== Backend Lint ==="
    just lint-backend
    @echo "=== Backend Typecheck ==="
    just typecheck-backend
    @echo "=== Backend Tests ==="
    just test-backend
    @echo "=== Security Tests ==="
    just security-test
    @echo "=== Frontend Lint ==="
    just lint-frontend
    @echo "=== Frontend Typecheck ==="
    just typecheck-frontend
    @echo "=== Frontend Tests ==="
    just test-frontend
    @echo "=== Security Scan ==="
    just security-scan
    @echo "=== Docker Lint ==="
    just docker-lint
    @echo "=== Docs Validation ==="
    just validate-docs
    @echo "=== CI Simulation Complete ==="

# Install CI/security tools (idempotent — skips if already installed)
install-tools:
    @echo "=== Installing CI/Security Tools ==="
    @command -v semgrep >/dev/null 2>&1 || pip install semgrep
    @command -v osv-scanner >/dev/null 2>&1 || (command -v go >/dev/null 2>&1 && go install github.com/google/osv-scanner/cmd/osv-scanner@latest || echo "SKIP: osv-scanner (go not available)")
    @command -v trivy >/dev/null 2>&1 || brew install trivy 2>/dev/null || echo "SKIP: trivy (brew not available)"
    @command -v syft >/dev/null 2>&1 || brew install syft 2>/dev/null || echo "SKIP: syft (brew not available)"
    @command -v hadolint >/dev/null 2>&1 || brew install hadolint 2>/dev/null || echo "SKIP: hadolint (brew not available)"
    @command -v actionlint >/dev/null 2>&1 || brew install actionlint 2>/dev/null || echo "SKIP: actionlint (brew not available)"
    @command -v jscpd >/dev/null 2>&1 || npm install -g jscpd 2>/dev/null || echo "SKIP: jscpd (npm not available)"
    @command -v deno >/dev/null 2>&1 || echo "SKIP: deno (install from https://deno.land)"
    @echo "=== Tool installation complete ==="

# Install pre-commit hooks
install-hooks:
    pre-commit install
    pre-commit install --hook-type pre-push

# Validate documentation accuracy
validate-docs:
    @bash scripts/validate-docs.sh

# Sync Makefile from justfile (for Unix users)
sync-makefile:
    @python scripts/just-to-make.py > Makefile
    @echo "Makefile synced from justfile"
