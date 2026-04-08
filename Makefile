# DO NOT EDIT - Generated from justfile by scripts/just-to-make.py
# To update: python scripts/just-to-make.py > Makefile

.PHONY: default install dev dev-backend dev-frontend test lint typecheck clean docker-up docker-down dev-postgres dev-postgres-stop dev-postgres-clean docker-logs migrate migrate-down migrate-create db-reset security-scan security-scan-backend security-scan-frontend sast sast-pr sca container-scan docker-lint lint-backend lint-frontend typecheck-backend typecheck-frontend test-backend test-backend-integration security-test dast duplication duplication-frontend duplication-all complexity complexity-check dead-code dead-code-frontend fallow fallow-dead-code fallow-dupes fallow-health fallow-audit test-frontend sbom license-check edge-functions bundle-size benchmark ci-sim install-tools install-hooks validate-docs sync-makefile

default:
	@just --list

install:
	cd backend && uv sync
	cd frontend && bun install

dev:
	docker compose up --build

dev-backend:
	cd backend && uv run python -m app --env local

dev-frontend:
	cd frontend && bun run dev

test:
	cd backend && uv run pytest
	cd frontend && bun run test:unit

lint:
	@echo "=== Linting all modified files ==="
	cd backend && uv run ruff check .
	cd backend && uv run ruff format --check .
	cd frontend && bun run lint
	cd frontend && bun run fmt:check
	@echo "=== Linting complete ==="

typecheck:
	@echo "=== Typechecking all modified files ==="
	cd backend && uv run basedpyright
	cd frontend && bun run check
	@echo "=== Typechecking complete ==="

clean:
	rm -rf backend/.pytest_cache backend/.ruff_cache backend/__pycache__ backend/**/__pycache__
	rm -rf frontend/.svelte-kit frontend/node_modules/.cache

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

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

dev-postgres-stop:
	docker compose stop db
	@echo "PostgreSQL stopped. Data preserved in docker volume."

dev-postgres-clean:
	docker compose down -v
	@echo "PostgreSQL stopped and data volume removed."

docker-logs:
	docker-compose logs -f

migrate:
	cd backend && uv run alembic upgrade head

migrate-down:
	cd backend && uv run alembic downgrade -1

migrate-create: MSG=$(or $MSG,description)
	cd backend && uv run alembic revision --autogenerate -m "$(MSG)"

db-reset:
	cd backend && uv run alembic downgrade base && uv run alembic upgrade head

security-scan:
	just security-scan-backend
	just security-scan-frontend

security-scan-backend:
	cd backend && uv run bandit -r app/
	cd backend && uv audit

security-scan-frontend:
	cd frontend && bun audit --ignore GHSA-4w7w-66w2-5vf9 --ignore GHSA-v2wj-q39q-566r --ignore GHSA-p9ff-h696-f583 --ignore GHSA-chqc-8p9q-pq6q --ignore GHSA-36xv-jgw5-4q75

sast:
	semgrep --config auto --config p/owasp-top-ten --config p/fastapi --config p/jwt --config p/xss --json -o semgrep-results.json backend/ frontend/src/

sast-pr:
	semgrep --config auto --config p/owasp-top-ten --config p/fastapi --config p/jwt --config p/xss --baseline-commit origin/main --json -o semgrep-pr.json backend/ frontend/src/

sca:
	osv-scanner scan --lockfile=backend/uv.lock --lockfile=frontend/bun.lock
	trivy fs --severity CRITICAL,HIGH --scanners vuln,license --format json --output trivy-results.json .

container-scan:
	docker build -t votecatcher-backend ./backend
	docker build -t votecatcher-frontend ./frontend
	trivy image --severity CRITICAL,HIGH votecatcher-backend
	trivy image --severity CRITICAL,HIGH votecatcher-frontend

docker-lint:
	hadolint backend/Dockerfile
	hadolint frontend/Dockerfile

lint-backend:
	cd backend && uv run ruff check .
	cd backend && uv run ruff format --check .

lint-frontend:
	cd frontend && bun run lint
	cd frontend && bun run fmt:check

typecheck-backend:
	bash scripts/check-typecheck-baseline.sh

typecheck-frontend:
	cd frontend && bun run check

test-backend:
	cd backend && uv run pytest tests/unit tests/matching tests/test_config.py --cov=app --cov-report=xml

test-backend-integration:
	cd backend && uv run pytest tests/integration

security-test:
	@echo "=== Running Security Tests ==="
	cd backend && uv run pytest tests/security/ -v --tb=short
	@echo "=== Security Tests Complete ==="

dast:
	nuclei -t .agent-workspace/quality-automation/nuclei-templates/ -u http://localhost:8080 -json -o nuclei-results.json

duplication:
	jscpd backend/app/ --min-lines 5 --min-tokens 50 --threshold 5 --reporters html

duplication-frontend:
	cd frontend && npx fallow dupes

duplication-all:
	just duplication
	just duplication-frontend

complexity:
	cd backend && uv run radon cc app/ -a -nb --total-average
	cd backend && uv run radon mi app/ -s -nc

complexity-check:
	cd backend && uv run radon cc app/ -nc -n B

dead-code:
	cd backend && uv run vulture app/ vulture-whitelist.py --format json > vulture-report.json

dead-code-frontend:
	cd frontend && npx fallow dead-code

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

test-frontend:
	cd frontend && bun run test:unit

sbom:
	syft backend/ -o spdx-json > sbom-backend.spdx.json
	syft frontend/ -o spdx-json > sbom-frontend.spdx.json

license-check:
	@command -v osv-scanner >/dev/null 2>&1 || (echo "ERROR: osv-scanner not installed — run 'just install-tools'" && exit 1)
	@osv-scanner --lockfile=backend/uv.lock --lockfile=frontend/bun.lock --licenses --format json --output /tmp/osv-licenses.json || (echo "ERROR: osv-scanner failed — check lockfiles exist" && exit 1)
	@if [ ! -s /tmp/osv-licenses.json ]; then echo "ERROR: osv-scanner produced no output" && exit 1; fi
	@if grep -q "AGPL\|GPL\|LGPL" /tmp/osv-licenses.json; then echo "ERROR: AGPL/GPL/LGPL licenses detected" && exit 1; fi
	@echo "OK: No copyleft license violations"

edge-functions:
	cd supabase/functions && deno lint
	cd supabase/functions && deno check */index.ts

bundle-size:
	cd frontend && bun run build
	@echo "=== Bundle size ===" && find frontend/.svelte-kit/output/client -name "*.js" -exec du -ch {} + | tail -1

benchmark:
	cd backend && uv run pytest tests/benchmarks/ --benchmark-only --benchmark-json=../benchmark-results.json

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

install-hooks:
	pre-commit install
	pre-commit install --hook-type pre-push

validate-docs:
	@bash scripts/validate-docs.sh

sync-makefile:
	@python scripts/just-to-make.py > Makefile
	@echo "Makefile synced from justfile"
