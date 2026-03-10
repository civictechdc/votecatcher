# Phase 0: Setup & Infrastructure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete all Phase 0 setup tasks to establish development environment, CI/CD, security scanning, and documentation foundation.

**Architecture:** FastAPI backend with feature-based packages, SvelteKit frontend with TypeScript, PostgreSQL database, Docker Compose for local development, GitHub Actions for CI/CD.

**Tech Stack:** Python 3.12+, FastAPI, SQLModel, Alembic, pytest | Node 20+, SvelteKit, TypeScript, Bun, Tailwind CSS v4, Vitest, Playwright | Docker, GitHub Actions

---

## Assessment: Already Complete

- ✓ Backend FastAPI project with feature-based packages
- ✓ Backend pyproject.toml with UV package manager
- ✓ Backend structlog configured
- ✓ Backend pytest + pytest-cov configured
- ✓ Frontend SvelteKit initialized with TypeScript
- ✓ Frontend Bun configured
- ✓ Frontend Tailwind CSS v4 configured
- ✓ Frontend Vitest + Playwright configured
- ✓ Docker Compose configured
- ✓ C4 diagrams exist (context, containers, components)
- ✓ Documentation directory structure exists

---

## Tasks

### Task 1: Add pytest-asyncio to Backend

**Files:**
- Modify: `backend/pyproject.toml`

**Step 1: Add pytest-asyncio to dev dependencies**

In `backend/pyproject.toml`, add to `[dependency-groups]` dev list:

```toml
[dependency-groups]
dev = [
    "basedpyright>=1.32.1",
    "devtools>=0.12.2",
    "diagrams>=0.25.1",
    "flake8>=7.2.0",
    "pandas-stubs>=2.3.2.250926",
    "pymupdf-stubs>=1.26.1.post1",
    "pytest>=8.3.5",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.1.1",
    "pytest-watcher>=0.6.3",
    "ruff>=0.11.4",
    "ty>=0.0.5",
]
```

**Step 2: Install dependency**

Run: `cd backend && uv sync`
Expected: Dependencies installed successfully

**Step 3: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock
git commit -m "chore(backend): add pytest-asyncio for async test support"
```

---

### Task 2: Add Alembic to Backend

**Files:**
- Modify: `backend/pyproject.toml`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/.gitkeep`

**Step 1: Add Alembic to dependencies**

In `backend/pyproject.toml`, add to dependencies list (after sqlalchemy):

```toml
    "sqlalchemy>=2.0.44",
    "sqlmodel>=0.0.27",
    "alembic>=1.14.0",
```

**Step 2: Install dependency**

Run: `cd backend && uv sync`
Expected: Alembic installed successfully

**Step 3: Initialize Alembic**

Run: `cd backend && uv run alembic init alembic`
Expected: Creates `alembic/` directory and `alembic.ini` file

**Step 4: Configure alembic.ini**

In `backend/alembic.ini`, update `sqlalchemy.url`:

```ini
# Line 63: Comment out the default URL
# sqlalchemy.url = driver://user:pass@localhost/dbname

# Add this below it:
sqlalchemy.url = postgresql://votecatcher:votecatcher_dev@localhost:5432/votecatcher
```

**Step 5: Configure alembic/env.py**

In `backend/alembic/env.py`, update imports and target_metadata:

```python
# Add imports at top (after existing imports):
from sqlmodel import SQLModel
import sys
from pathlib import Path

# Add path to app module
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all models so Alembic can detect them
from app.data.models import *  # noqa

# Update target_metadata (around line 25):
target_metadata = SQLModel.metadata
```

**Step 6: Verify setup**

Run: `cd backend && uv run alembic current`
Expected: Shows current migration status (will be empty initially)

**Step 7: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock backend/alembic.ini backend/alembic/
git commit -m "chore(backend): setup Alembic for database migrations"
```

---

### Task 3: Create Makefile

**Files:**
- Create: `Makefile`

**Step 1: Create Makefile with common commands**

Create `Makefile` in project root:

```makefile
.PHONY: help install dev test lint typecheck clean docker-up docker-down migrate

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	cd backend && uv sync
	cd frontend-svelt && bun install

dev: ## Start development servers
	docker-compose up -d
	@echo "Backend: http://localhost:8080"
	@echo "Frontend: http://localhost:5173"

test: ## Run all tests
	cd backend && uv run pytest tests/ -v --cov=app --cov-report=term-missing
	cd frontend-svelt && bun run test

lint: ## Run linters
	cd backend && uv run ruff check .
	cd frontend-svelt && bun run lint

typecheck: ## Run type checkers
	cd backend && uv run basedpyright
	cd frontend-svelt && bun run check

clean: ## Clean build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-up: ## Start Docker Compose stack
	docker-compose up -d

docker-down: ## Stop Docker Compose stack
	docker-compose down

docker-logs: ## Show Docker Compose logs
	docker-compose logs -f

migrate: ## Run database migrations
	cd backend && uv run alembic upgrade head

migrate-down: ## Rollback last migration
	cd backend && uv run alembic downgrade -1

migrate-create: ## Create new migration (usage: make migrate-create msg="description")
	cd backend && uv run alembic revision --autogenerate -m "$(msg)"

db-reset: ## Reset database (WARNING: destroys all data)
	cd backend && uv run alembic downgrade base && uv run alembic upgrade head

security-scan: ## Run security scans
	cd backend && uv run bandit -r app/
	cd backend && uv run pip-audit
	cd frontend-svelt && bun audit
```

**Step 2: Verify Makefile**

Run: `make help`
Expected: Shows list of available commands

**Step 3: Commit**

```bash
git add Makefile
git commit -m "chore: add Makefile with common development commands"
```

---

### Task 4: Organize Frontend Component Structure

**Files:**
- Create: `frontend-svelt/src/lib/components/ui/`
- Create: `frontend-svelt/src/lib/components/layout/`
- Move: Existing components to appropriate directories

**Step 1: Create directory structure**

Run:
```bash
cd frontend-svelt
mkdir -p src/lib/components/ui
mkdir -p src/lib/components/layout
```

**Step 2: Move existing components to appropriate locations**

Run:
```bash
cd frontend-svelt/src/lib/components
# Move UI components
mv Button.svelte ui/ 2>/dev/null || true
mv Input.svelte ui/ 2>/dev/null || true
mv Pagination.svelte ui/ 2>/dev/null || true
mv Progress.svelte ui/ 2>/dev/null || true

# Move layout components
mv Navbar.svelte layout/ 2>/dev/null || true

# Keep domain-specific components at current level
# (MatchConfidenceIndicator, PaginatedMatchTable, DevFlags, FeatureFlagsPanel)
```

**Step 3: Create index files for easy imports**

Create `frontend-svelt/src/lib/components/ui/index.ts`:

```typescript
// UI component barrel export
// Add components as they are created
export { default as Pagination } from './Pagination.svelte';
export { default as Progress } from './Progress.svelte';
```

Create `frontend-svelt/src/lib/components/layout/index.ts`:

```typescript
// Layout component barrel export
// Add components as they are created
export { default as Navbar } from './Navbar.svelte';
```

**Step 4: Commit**

```bash
git add frontend-svelt/src/lib/components/
git commit -m "refactor(frontend): organize component structure into ui/ and layout/"
```

---

### Task 5: Create OpenAPI 3.1 Specification

**Files:**
- Create: `backend/openapi.yaml`

**Step 1: Create OpenAPI spec file**

Create `backend/openapi.yaml` with all MVP endpoints based on SPEC.md §5:

```yaml
openapi: 3.1.0
info:
  title: Votecatcher API
  description: Petition signature verification API
  version: 1.0.0
  contact:
    name: Votecatcher Team

servers:
  - url: http://localhost:8080/api
    description: Local development server

tags:
  - name: campaigns
    description: Campaign management
  - name: upload
    description: File upload operations
  - name: jobs
    description: Job orchestration and status
  - name: results
    description: Match results
  - name: sessions
    description: Session management

paths:
  # Campaign Management
  /campaigns:
    get:
      tags: [campaigns]
      summary: List campaigns
      operationId: listCampaigns
      parameters:
        - name: offset
          in: query
          schema:
            type: integer
            default: 0
        - name: limit
          in: query
          schema:
            type: integer
            default: 25
      responses:
        '200':
          description: List of campaigns
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CampaignList'
        '500':
          $ref: '#/components/responses/InternalError'

    post:
      tags: [campaigns]
      summary: Create campaign
      operationId: createCampaign
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateCampaign'
      responses:
        '201':
          description: Campaign created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Campaign'
        '400':
          $ref: '#/components/responses/BadRequest'
        '500':
          $ref: '#/components/responses/InternalError'

  /campaigns/{campaign_id}:
    get:
      tags: [campaigns]
      summary: Get campaign details
      operationId: getCampaign
      parameters:
        - $ref: '#/components/parameters/CampaignId'
      responses:
        '200':
          description: Campaign details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Campaign'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalError'

  # File Upload
  /upload/voter-list:
    post:
      tags: [upload]
      summary: Upload voter list CSV/Excel
      operationId: uploadVoterList
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required:
                - file
                - region_id
              properties:
                file:
                  type: string
                  format: binary
                region_id:
                  type: integer
      responses:
        '201':
          description: Voter list uploaded
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/VoterListUpload'
        '400':
          $ref: '#/components/responses/BadRequest'
        '500':
          $ref: '#/components/responses/InternalError'

  /upload/petition:
    post:
      tags: [upload]
      summary: Upload petition PDF
      operationId: uploadPetition
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required:
                - file
                - campaign_id
              properties:
                file:
                  type: string
                  format: binary
                campaign_id:
                  type: integer
      responses:
        '201':
          description: Petition uploaded
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PetitionUpload'
        '400':
          $ref: '#/components/responses/BadRequest'
        '500':
          $ref: '#/components/responses/InternalError'

  # Job Orchestration
  /jobs:
    post:
      tags: [jobs]
      summary: Create matcher job
      operationId: createJob
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateJob'
      responses:
        '201':
          description: Job created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Job'
        '400':
          $ref: '#/components/responses/BadRequest'
        '500':
          $ref: '#/components/responses/InternalError'

  /jobs/{job_id}:
    get:
      tags: [jobs]
      summary: Get job status
      operationId: getJob
      parameters:
        - $ref: '#/components/parameters/JobId'
      responses:
        '200':
          description: Job details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Job'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalError'

  /jobs/{job_id}/status:
    get:
      tags: [jobs]
      summary: SSE endpoint for job status updates
      operationId: getJobStatusStream
      parameters:
        - $ref: '#/components/parameters/JobId'
      responses:
        '200':
          description: SSE stream
          content:
            text/event-stream:
              schema:
                type: string

  /jobs/{job_id}/cancel:
    post:
      tags: [jobs]
      summary: Cancel job
      operationId: cancelJob
      parameters:
        - $ref: '#/components/parameters/JobId'
      responses:
        '200':
          description: Job cancelled
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Job'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalError'

  # Results
  /jobs/{job_id}/results:
    get:
      tags: [results]
      summary: Get match results
      operationId: getResults
      parameters:
        - $ref: '#/components/parameters/JobId'
        - name: offset
          in: query
          schema:
            type: integer
            default: 0
        - name: limit
          in: query
          schema:
            type: integer
            default: 25
        - name: confidence
          in: query
          description: Filter by confidence level
          schema:
            type: string
            enum: [HIGH, MEDIUM, LOW]
      responses:
        '200':
          description: Match results
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ResultList'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalError'

  /jobs/{job_id}/results/export:
    get:
      tags: [results]
      summary: Export results to CSV
      operationId: exportResults
      parameters:
        - $ref: '#/components/parameters/JobId'
      responses:
        '200':
          description: CSV file
          content:
            text/csv:
              schema:
                type: string
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalError'

  # Session Management
  /sessions:
    post:
      tags: [sessions]
      summary: Save session
      operationId: saveSession
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SaveSession'
      responses:
        '201':
          description: Session saved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Session'
        '400':
          $ref: '#/components/responses/BadRequest'
        '500':
          $ref: '#/components/responses/InternalError'

  /sessions/{session_id}/load:
    post:
      tags: [sessions]
      summary: Load session
      operationId: loadSession
      parameters:
        - $ref: '#/components/parameters/SessionId'
      responses:
        '200':
          description: Session loaded
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Session'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalError'

  /sessions/{session_id}/export:
    get:
      tags: [sessions]
      summary: Export session as ZIP
      operationId: exportSession
      parameters:
        - $ref: '#/components/parameters/SessionId'
      responses:
        '200':
          description: ZIP file
          content:
            application/zip:
              schema:
                type: string
                format: binary
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalError'

components:
  parameters:
    CampaignId:
      name: campaign_id
      in: path
      required: true
      schema:
        type: integer

    JobId:
      name: job_id
      in: path
      required: true
      schema:
        type: integer

    SessionId:
      name: session_id
      in: path
      required: true
      schema:
        type: integer

  schemas:
    Campaign:
      type: object
      required:
        - id
        - name
        - year
        - region_id
        - created_at
      properties:
        id:
          type: integer
        name:
          type: string
        year:
          type: integer
        region_id:
          type: integer
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    CreateCampaign:
      type: object
      required:
        - name
        - year
        - region_id
      properties:
        name:
          type: string
          minLength: 1
        year:
          type: integer
          minimum: 2020
        region_id:
          type: integer

    CampaignList:
      type: object
      required:
        - items
        - total
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Campaign'
        total:
          type: integer

    Job:
      type: object
      required:
        - id
        - campaign_id
        - status
        - created_at
      properties:
        id:
          type: integer
        campaign_id:
          type: integer
        status:
          type: string
          enum:
            - NOT_STARTED
            - OCR_PENDING
            - OCR_STARTED
            - OCR_COMPLETED
            - OCR_FAILED
            - OCR_TIMEOUT
            - MATCHING_PENDING
            - MATCHING
            - MATCHING_COMPLETED
            - MATCHING_ERROR
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time
        error_message:
          type: string

    CreateJob:
      type: object
      required:
        - campaign_id
        - petition_scan_ids
      properties:
        campaign_id:
          type: integer
        petition_scan_ids:
          type: array
          items:
            type: integer

    VoterListUpload:
      type: object
      required:
        - id
        - filename
        - region_id
        - row_count
      properties:
        id:
          type: integer
        filename:
          type: string
        region_id:
          type: integer
        row_count:
          type: integer

    PetitionUpload:
      type: object
      required:
        - id
        - filename
        - campaign_id
        - crop_count
      properties:
        id:
          type: integer
        filename:
          type: string
        campaign_id:
          type: integer
        crop_count:
          type: integer

    ResultList:
      type: object
      required:
        - items
        - total
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/MatchResult'
        total:
          type: integer

    MatchResult:
      type: object
      required:
        - id
        - ocr_result_id
        - confidence
        - predictions
      properties:
        id:
          type: integer
        ocr_result_id:
          type: integer
        confidence:
          type: string
          enum: [HIGH, MEDIUM, LOW]
        predictions:
          type: array
          maxItems: 5
          items:
            $ref: '#/components/schemas/Prediction'

    Prediction:
      type: object
      required:
        - voter_id
        - name_similarity
        - address_similarity
        - overall_score
      properties:
        voter_id:
          type: integer
        name_similarity:
          type: number
          format: float
          minimum: 0
          maximum: 1
        address_similarity:
          type: number
          format: float
          minimum: 0
          maximum: 1
        overall_score:
          type: number
          format: float
          minimum: 0
          maximum: 1

    Session:
      type: object
      required:
        - id
        - name
        - created_at
      properties:
        id:
          type: integer
        name:
          type: string
        created_at:
          type: string
          format: date-time
        data:
          type: object
          description: Reference-based snapshot data

    SaveSession:
      type: object
      required:
        - name
      properties:
        name:
          type: string
          minLength: 1

    Error:
      type: object
      required:
        - type
        - title
        - status
        - detail
      properties:
        type:
          type: string
          format: uri
        title:
          type: string
        status:
          type: integer
        detail:
          type: string
        instance:
          type: string

  responses:
    BadRequest:
      description: Bad request
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/Error'

    NotFound:
      description: Resource not found
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/Error'

    InternalError:
      description: Internal server error
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/Error'
```

**Step 2: Validate OpenAPI spec**

Run: `npx @apidevtools/swagger-cli validate backend/openapi.yaml`
Expected: Document is valid

**Step 3: Commit**

```bash
git add backend/openapi.yaml
git commit -m "feat(api): add OpenAPI 3.1 specification for MVP endpoints"
```

---

### Task 6: Generate TypeScript Client from OpenAPI Spec

**Files:**
- Create: `frontend-svelt/src/lib/api/generated/`

**Step 1: Install OpenAPI generator**

Run: `cd frontend-svelt && bun add -D @openapitools/openapi-generator-cli`

**Step 2: Generate TypeScript client**

Run:
```bash
cd frontend-svelt
bunx openapi-generator-cli generate \
  -i ../backend/openapi.yaml \
  -g typescript-fetch \
  -o src/lib/api/generated \
  --additional-properties=typescriptThreePlus=true
```

Expected: TypeScript client generated in `src/lib/api/generated/`

**Step 3: Create API client wrapper**

Create `frontend-svelt/src/lib/api/client.ts`:

```typescript
import { Configuration, CampaignsApi, UploadApi, JobsApi, ResultsApi, SessionsApi } from './generated';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api';

const config = new Configuration({
  basePath: API_BASE_URL,
});

export const campaignsApi = new CampaignsApi(config);
export const uploadApi = new UploadApi(config);
export const jobsApi = new JobsApi(config);
export const resultsApi = new ResultsApi(config);
export const sessionsApi = new SessionsApi(config);

export * from './generated';
```

**Step 4: Add environment variable**

Add to `frontend-svelt/.env.example`:

```bash
VITE_API_BASE_URL=http://localhost:8080/api
```

**Step 5: Update .gitignore**

Add to `frontend-svelt/.gitignore`:

```
# Generated API client
src/lib/api/generated/
```

**Step 6: Commit**

```bash
git add frontend-svelt/src/lib/api/ frontend-svelt/.env.example frontend-svelt/.gitignore frontend-svelt/package.json
git commit -m "feat(frontend): generate TypeScript client from OpenAPI spec"
```

---

### Task 7: Create GitHub Actions CI Workflow

**Files:**
- Create: `.github/workflows/ci.yml`

**Step 1: Create CI workflow file**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend-lint:
    name: Backend Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install UV
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        working-directory: backend
        run: uv sync

      - name: Run Ruff linter
        working-directory: backend
        run: uv run ruff check .

      - name: Run Ruff formatter check
        working-directory: backend
        run: uv run ruff format --check .

  backend-typecheck:
    name: Backend Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install UV
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        working-directory: backend
        run: uv sync

      - name: Run basedpyright
        working-directory: backend
        run: uv run basedpyright

  backend-test:
    name: Backend Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install UV
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        working-directory: backend
        run: uv sync

      - name: Run tests
        working-directory: backend
        run: uv run pytest tests/ -v --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: backend/coverage.xml
          fail_ci_if_error: false

  frontend-lint:
    name: Frontend Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Bun
        uses: oven-sh/setup-bun@v1

      - name: Install dependencies
        working-directory: frontend-svelt
        run: bun install

      - name: Run oxlint
        working-directory: frontend-svelt
        run: bun run lint

      - name: Run formatter check
        working-directory: frontend-svelt
        run: bun run fmt:check

  frontend-typecheck:
    name: Frontend Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Bun
        uses: oven-sh/setup-bun@v1

      - name: Install dependencies
        working-directory: frontend-svelt
        run: bun install

      - name: Run type check
        working-directory: frontend-svelt
        run: bun run check

  frontend-test:
    name: Frontend Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Bun
        uses: oven-sh/setup-bun@v1

      - name: Install dependencies
        working-directory: frontend-svelt
        run: bun install

      - name: Run unit tests
        working-directory: frontend-svelt
        run: bun run test:unit

  docker-build:
    name: Docker Build Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build backend image
        run: docker build -t votecatcher-backend:latest backend/

      - name: Build frontend image
        run: docker build -t votecatcher-frontend:latest frontend-svelt/
```

**Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions workflow for PR checks"
```

---

### Task 8: Create GitHub Actions Security Workflow

**Files:**
- Create: `.github/workflows/security.yml`

**Step 1: Create security workflow file**

Create `.github/workflows/security.yml`:

```yaml
name: Security Scanning

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend-security:
    name: Backend Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install UV
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        working-directory: backend
        run: uv sync

      - name: Run Bandit
        working-directory: backend
        run: uv run bandit -r app/ -c pyproject.toml

      - name: Run pip-audit
        working-directory: backend
        run: uv run pip-audit

  frontend-security:
    name: Frontend Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Bun
        uses: oven-sh/setup-bun@v1

      - name: Install dependencies
        working-directory: frontend-svelt
        run: bun install

      - name: Run bun audit
        working-directory: frontend-svelt
        run: bun audit

  secrets-scan:
    name: Secrets Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  container-scan:
    name: Container Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build backend image
        run: docker build -t votecatcher-backend:latest backend/

      - name: Run Trivy on backend
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'votecatcher-backend:latest'
          format: 'table'
          exit-code: '1'
          severity: 'CRITICAL,HIGH'

      - name: Build frontend image
        run: docker build -t votecatcher-frontend:latest frontend-svelt/

      - name: Run Trivy on frontend
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'votecatcher-frontend:latest'
          format: 'table'
          exit-code: '1'
          severity: 'CRITICAL,HIGH'
```

**Step 2: Add Bandit configuration to backend**

In `backend/pyproject.toml`, add:

```toml
[tool.bandit]
exclude_dirs = ["tests", ".venv", "node_modules"]
skips = ["B101"]  # Skip assert_used test (OK in pytest)
```

**Step 3: Commit**

```bash
git add .github/workflows/security.yml backend/pyproject.toml
git commit -m "ci: add security scanning workflow (Bandit, pip-audit, Gitleaks, Trivy)"
```

---

### Task 9: Configure Pre-commit Hooks

**Files:**
- Create: `.pre-commit-config.yaml`

**Step 1: Install pre-commit**

Run: `pip install pre-commit`

**Step 2: Create pre-commit configuration**

Create `.pre-commit-config.yaml`:

```yaml
repos:
  # Python
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ["-c", "backend/pyproject.toml"]
        additional_dependencies: ["bandit[toml]"]
        files: ^backend/

  # TypeScript/JavaScript
  - repo: https://github.com/oxc-project/mirrors-oxlint
    rev: v1.48.0
    hooks:
      - id: oxlint
        files: ^frontend-svelt/

  # Secrets
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ["--baseline", ".secrets.baseline"]
        exclude: package.lock.json

  # General
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-yaml
      - id: check-json
      - id: check-merge-conflict
      - id: check-case-conflict
      - id: end-of-file-fixer
      - id: trailing-whitespace
```

**Step 3: Create secrets baseline**

Run: `detect-secrets scan > .secrets.baseline`

**Step 4: Install hooks**

Run: `pre-commit install`

**Step 5: Commit**

```bash
git add .pre-commit-config.yaml .secrets.baseline
git commit -m "chore: configure pre-commit hooks for linting and security"
```

---

### Task 10: Create ADR Template

**Files:**
- Create: `docs/architecture/decisions/template.md`

**Step 1: Create ADR template**

Create `docs/architecture/decisions/template.md`:

```markdown
# ADR-NNNN: [Title]

## Status

[Proposed | Accepted | Deprecated | Superseded]

## Context

[What is the issue that we're seeing that is motivating this decision or change?]

## Decision

[What is the change that we're proposing and/or doing?]

## Consequences

### Positive

- [What positive impact does this have?]

### Negative

- [What negative impact does this have?]

### Neutral

- [What trade-offs are we making?]

## Alternatives Considered

1. **[Alternative 1]**
   - Pros:
   - Cons:
   - Why not chosen:

2. **[Alternative 2]**
   - Pros:
   - Cons:
   - Why not chosen:

## References

- [Link to relevant documentation, discussions, or resources]

---

**Date:** YYYY-MM-DD
**Decision Makers:** [Who was involved in this decision]
```

**Step 2: Commit**

```bash
git add docs/architecture/decisions/template.md
git commit -m "docs: add ADR template for architecture decisions"
```

---

### Task 11: Create ADR-0001

**Files:**
- Create: `docs/architecture/decisions/0001-record-architecture-decisions.md`

**Step 1: Create ADR-0001**

Create `docs/architecture/decisions/0001-record-architecture-decisions.md`:

```markdown
# ADR-0001: Record Architecture Decisions

## Status

Accepted

## Context

We need to record architectural decisions made in this project to:

- Preserve the context and reasoning behind decisions
- Help future contributors understand why the system is built this way
- Avoid re-litigating past decisions
- Provide a clear audit trail of changes

## Decision

We will use Architecture Decision Records (ADRs) to document significant architectural decisions.

ADR Format:
- Title and number (NNNN)
- Status (Proposed, Accepted, Deprecated, Superseded)
- Context (what is the problem)
- Decision (what are we doing)
- Consequences (positive, negative, neutral)
- Alternatives Considered (what else we looked at)
- References (links to relevant info)

Location: `docs/architecture/decisions/`

Numbering:
- Start at 0001
- Increment sequentially
- Keep numbers unique (don't reuse)

## Consequences

### Positive

- Clear documentation of why decisions were made
- Easier onboarding for new contributors
- Reduces "why did we do this?" questions
- Creates institutional knowledge

### Negative

- Requires discipline to write ADRs
- Takes time to document properly

### Neutral

- ADRs should be concise (1-2 pages)
- Not every decision needs an ADR (only significant ones)

## Alternatives Considered

1. **No formal documentation**
   - Pros: No overhead
   - Cons: Knowledge lost over time, repeated discussions
   - Why not chosen: Project is complex enough to need documentation

2. **Wiki-based documentation**
   - Pros: Easy to edit
   - Cons: Hard to version control, can become stale
   - Why not chosen: ADRs in git provide better audit trail

3. **Code comments only**
   - Pros: Close to the code
   - Cons: Doesn't capture high-level decisions
   - Why not chosen: Not sufficient for architectural decisions

## References

- [Documenting Architecture Decisions - Michael Nygard](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [ADR GitHub Organization](https://adr.github.io/)

---

**Date:** 2026-03-09
**Decision Makers:** Votecatcher Team
```

**Step 2: Commit**

```bash
git add docs/architecture/decisions/0001-record-architecture-decisions.md
git commit -m "docs: add ADR-0001 for recording architecture decisions"
```

---

### Task 12: Update README with Documentation Links

**Files:**
- Modify: `README.md`

**Step 1: Add documentation section to README**

In `README.md`, add after the introduction:

```markdown
## Documentation

### Architecture
- [C4 Context Diagram](docs/architecture/c4-context.md) - System context
- [C4 Containers Diagram](docs/architecture/c4-containers.md) - Container architecture
- [C4 Components Diagram](docs/architecture/c4-components.md) - Component structure
- [Architecture Decisions](docs/architecture/decisions/) - ADRs

### Development
- [Running Locally](docs/running-locally.md) - Local development setup
- [Simulation Testing](docs/simulation-testing.md) - Testing strategies
- [API Specification](backend/openapi.yaml) - OpenAPI 3.1 spec

### Deployment
- [Deployment Guide](docs/deployment/) - Production deployment
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add documentation links to README"
```

---

### Task 13: Run Exit Criteria Verification

**Step 1: Run backend verification**

Run:
```bash
cd backend
uv run pytest tests/ -v
uv run ruff check .
uv run basedpyright
```

Expected: All pass

**Step 2: Run frontend verification**

Run:
```bash
cd frontend-svelt
bun run test
bun run lint
bun run check
```

Expected: All pass

**Step 3: Run security scans**

Run:
```bash
cd backend
uv run bandit -r app/
uv run pip-audit
cd ../frontend-svelt
bun audit
```

Expected: No high/critical vulnerabilities

**Step 4: Run integration verification**

Run:
```bash
docker-compose up -d
sleep 10
curl http://localhost:8080/health
curl http://localhost:5173
docker-compose down
```

Expected: All services start and respond

---

### Task 14: Update TODO.md and PROGRESS.md

**Files:**
- Modify: `openspec/TODO.md`
- Modify: `openspec/PROGRESS.md`

**Step 1: Update TODO.md**

Mark Phase 0 entry criteria and tasks as complete:

```markdown
### Entry Criteria
- [x] Repository cloned and accessible
- [x] Development machine meets prerequisites (Python 3.12+, Node 20+, Docker)
- [x] Access to at least one LLM provider API key

### Tasks

#### Backend Setup
- [x] Initialize FastAPI project structure with feature-based packages
- [x] Configure UV package manager (`pyproject.toml`)
- [x] Setup structlog for structured logging
- [x] Configure pytest + pytest-asyncio + pytest-cov
- [x] Setup Alembic for database migrations
- [x] Create Docker Compose for dev environment
- [x] Create Makefile or scripts for common commands

#### Frontend Setup
- [x] Initialize SvelteKit project with TypeScript
- [x] Configure Bun as package manager
- [x] Setup Tailwind CSS v4
- [x] Configure Vitest for unit tests
- [x] Configure Playwright for E2E tests
- [x] Create base component structure (`ui/`, `layout/`, etc.)

#### API Specification
- [x] Write OpenAPI 3.1 spec for all MVP endpoints
- [x] Validate spec with swagger-cli
- [x] Generate TypeScript client from spec
- [x] Integrate generated client into frontend

#### CI/CD
- [x] Create GitHub Actions workflow for PR checks
- [x] Add lint job (ruff for Python, oxlint for TypeScript)
- [x] Add typecheck job (basedpyright, tsc)
- [x] Add test job (pytest, vitest)
- [x] Configure pre-commit hooks

#### Security Scanning
- [x] Add Bandit to backend dev dependencies (pyproject.toml)
- [x] Add pip-audit to backend dev dependencies
- [x] Create `.github/workflows/security.yml` with security jobs
- [x] Add Gitleaks for secrets scanning
- [x] Configure Trivy for container scanning
- [x] Enable Dependabot in repository settings
- [x] Create `.secrets.baseline` for detect-secrets (if used)

#### Documentation
- [x] Create `docs/` directory structure
- [x] Write C4 Context diagram (`docs/architecture/c4-context.md`)
- [x] Write C4 Containers diagram (`docs/architecture/c4-containers.md`)
- [x] Create ADR template (`docs/architecture/decisions/template.md`)
- [x] Create ADR-0001: Record Architecture Decisions
- [x] Update README.md with documentation links
```

**Step 2: Update PROGRESS.md**

```markdown
# Implementation Progress

**Project:** Votecatcher MVP
**Started:** 2026-03-09
**Target Completion:** 4-6 weeks

---

## Current Status

**Phase:** Phase 0 Complete
**Last Updated:** 2026-03-09

---

## Completed Phases

### Phase 0: Setup & Infrastructure
- **Completed:** 2026-03-09
- **Key Achievements:**
  - Added pytest-asyncio for async test support
  - Setup Alembic for database migrations
  - Created Makefile with common development commands
  - Organized frontend component structure (ui/, layout/)
  - Created OpenAPI 3.1 specification for all MVP endpoints
  - Generated TypeScript client from spec
  - Setup GitHub Actions CI/CD workflows
  - Configured security scanning (Bandit, pip-audit, Gitleaks, Trivy)
  - Configured pre-commit hooks
  - Created ADR template and ADR-0001
  - Updated README with documentation links
- **Issues Encountered:**
  - None

---

## Decisions Made During Implementation

| Date | Decision | Rationale | Impact |
|------|----------|-----------|--------|
| 2026-03-09 | Use Alembic for migrations | Industry standard, works well with SQLModel | Enables database schema version control |
| 2026-03-09 | Use OpenAPI 3.1 + generated client | Type safety, auto-adapts to spec changes | Reduces frontend-backend integration issues |
| 2026-03-09 | Use GitHub Actions for CI/CD | Integrated with GitHub, good free tier | Automated quality checks on every PR |

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Tasks | 67 |
| Completed | 14 (Phase 0) |
| In Progress | 0 |
| Blocked | 0 |
| Test Coverage (Backend) | TBD |
| Test Coverage (Frontend) | TBD |
```

**Step 3: Commit**

```bash
git add openspec/TODO.md openspec/PROGRESS.md
git commit -m "docs: mark Phase 0 complete in TODO and PROGRESS"
```

---

## Completion

After all tasks complete, verify:

1. All Phase 0 tasks in TODO.md are checked
2. All exit criteria commands pass
3. CI workflows run green on test PR
4. Documentation is complete and linked

Phase 0 is now complete. Ready to proceed to Phase 1: Data Layer.
