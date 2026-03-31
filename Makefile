# DO NOT EDIT - Generated from justfile by scripts/just-to-make.py
# To update: python scripts/just-to-make.py > Makefile

.PHONY: default install dev test lint typecheck clean docker-up docker-down dev-postgres dev-postgres-stop dev-postgres-clean docker-logs migrate migrate-down migrate-create db-reset security-scan security-scan-backend security-scan-frontend sast sast-pr sca container-scan docker-lint lint-backend lint-frontend typecheck-backend typecheck-frontend test-backend test-backend-integration dast duplication complexity dead-code test-frontend ci-sim sync-makefile

default:
	@just --list

install:
	cd backend && uv sync
	cd frontend-svelt && bun install

dev:
	docker-compose up --build

test:
	cd backend && uv run pytest
	cd frontend-svelt && bun run test:unit

lint:
	cd backend && uv run ruff check .
	cd frontend-svelt && bun run lint

typecheck:
	cd backend && uv run basedpyright
	cd frontend-svelt && bun run check

clean:
	rm -rf backend/.pytest_cache backend/.ruff_cache backend/__pycache__ backend/**/__pycache__
	rm -rf frontend-svelt/.svelte-kit frontend-svelt/node_modules/.cache

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
	cd backend && uv run pip-audit

security-scan-frontend:
	cd frontend-svelt && bun audit

sast:
	semgrep --config auto --config p/owasp-top-ten --config p/fastapi --config p/jwt --config p/xss --json -o semgrep-results.json backend/ frontend-svelt/src/

sast-pr:
	semgrep --config auto --config p/owasp-top-ten --config p/fastapi --config p/jwt --config p/xss --baseline-commit origin/main --json -o semgrep-pr.json backend/ frontend-svelt/src/

sca:
	osv-scanner --lockfile=backend/uv.lock --lockfile=frontend-svelt/bun.lock --licenses
	trivy fs --severity CRITICAL,HIGH --scanners vuln,license .

container-scan:
	docker build -t votecatcher-backend ./backend
	docker build -t votecatcher-frontend ./frontend-svelt
	trivy image --severity CRITICAL,HIGH votecatcher-backend
	trivy image --severity CRITICAL,HIGH votecatcher-frontend

docker-lint:
	hadolint backend/Dockerfile
	hadolint frontend-svelt/Dockerfile

lint-backend:
	cd backend && uv run ruff check .
	cd backend && uv run ruff format --check .

lint-frontend:
	cd frontend-svelt && bun run lint
	cd frontend-svelt && bun run fmt:check

typecheck-backend:
	cd backend && uv run basedpyright

typecheck-frontend:
	cd frontend-svelt && bun run check

test-backend:
	cd backend && uv run pytest tests/unit tests/matching tests/test_config.py --cov=app --cov-report=xml

test-backend-integration:
	cd backend && uv run pytest tests/integration

dast:
	nuclei -t .agent-workspace/quality-automation/nuclei-templates/ -u http://localhost:8080 -json -o nuclei-results.json

duplication:
	jscpd backend/app/ frontend-svelt/src/ --min-lines 5 --min-tokens 50 --threshold 5 --reporters html

complexity:
	cd backend && uv run radon cc app/ -a -nb
	cd backend && uv run radon mi app/ -nb

dead-code:
	cd backend && uv run vulture app/ --min-confidence 80 --format json > vulture-report.json
	cd frontend-svelt && bunx ts-prune --json > ts-prune-report.json

test-frontend:
	cd frontend-svelt && bun run test:unit

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

sync-makefile:
	@python scripts/just-to-make.py > Makefile
	@echo "Makefile synced from justfile"
