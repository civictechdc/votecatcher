.PHONY: help install dev test lint typecheck clean docker-up docker-down docker-logs migrate migrate-down migrate-create db-reset security-scan

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies (backend + frontend)
	cd backend && uv sync
	cd frontend-svelt && bun install

dev: ## Start development servers via docker-compose
	docker-compose up --build

test: ## Run all tests (backend pytest, frontend vitest)
	cd backend && uv run pytest
	cd frontend-svelt && bun run test:unit

lint: ## Run linters (ruff, oxlint)
	cd backend && uv run ruff check .
	cd frontend-svelt && bun run lint

typecheck: ## Run type checkers (basedpyright, svelte-check)
	cd backend && uv run basedpyright
	cd frontend-svelt && bun run check

clean: ## Clean build artifacts
	rm -rf backend/.pytest_cache backend/.ruff_cache backend/__pycache__ backend/**/__pycache__
	rm -rf frontend-svelt/.svelte-kit frontend-svelt/node_modules/.cache

docker-up: ## Start docker containers
	docker-compose up -d

docker-down: ## Stop docker containers
	docker-compose down

docker-logs: ## Show docker logs
	docker-compose logs -f

migrate: ## Run database migrations
	cd backend && uv run alembic upgrade head

migrate-down: ## Rollback last migration
	cd backend && uv run alembic downgrade -1

migrate-create: ## Create new migration (usage: make migrate-create MSG="description")
	cd backend && uv run alembic revision --autogenerate -m "$(MSG)"

db-reset: ## Reset database (drop all tables and re-run migrations)
	cd backend && uv run alembic downgrade base && uv run alembic upgrade head

security-scan: ## Run security scans (bandit, pip-audit, bun audit)
	cd backend && uv run bandit -r app/ || true
	cd backend && uv run pip-audit || true
	cd frontend-svelt && bun audit || true
