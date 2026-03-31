# Phase 5: Docker & CI/CD

> **Prerequisite:** Phase 4 complete (all API endpoints work)

**Goal:** Create Docker configurations for Supabase, add gitleaks for secret scanning, and set up schema documentation.

**Duration Estimate:** 3-4 hours

---

## Phase Status

| Task Group | Status | Exit Gate |
|------------|--------|-----------|
| 5A: Docker Compose | Not Started | Containers start |
| 5B: Secret Scanning | Not Started | Gitleaks runs |
| 5C: Schema Documentation | Not Started | Docs generate |
| 5D: CI/CD Workflows | Not Started | CI passes |

---

## Developer Notes

| Date | Status | Notes/Blockers/Concerns |
|------|--------|-------------------------|
| | Not Started | |

---

## Entrance Gate

Verify Phase 4 is complete:

```bash
cd backend && uv run pytest tests/integration/api/test_database.py -v
cd backend && python -m app.scripts.supabase --help
```

**Expected:** Tests pass, CLI works

---

## Task Group 5A: Docker Compose Configurations

**Files:**
- Modify: `docker-compose.yml` (ensure local dev works)
- Create: `docker-compose.supabase.yml`
- Modify: `backend/Dockerfile` (if needed)

### Step 1: Create Supabase Docker Compose

```yaml
# docker-compose.supabase.yml
# For deployments using Supabase as the backend database

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    env_file:
      - ./backend/.env.local
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      # Mount for local development hot reload
      - ./backend/app:/app/app:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend-svelt
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8080
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped
```

### Step 2: Update main docker-compose.yml

```yaml
# docker-compose.yml
# Local development with PostgreSQL container

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/votecatcher  # pragma: allowlist secret
      - PYTHONUNBUFFERED=1
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend-svelt
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8080
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: votecatcher
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
    ports:
      - "5432:5432"
    restart: unless-stopped

volumes:
  postgres_data:
```

### Step 3: Test Docker configurations

```bash
# Test local development
docker compose up --build

# Test Supabase mode (requires .env.local with Supabase credentials)
docker compose -f docker-compose.supabase.yml up --build
```

### Step 4: Commit

```bash
git add docker-compose.yml docker-compose.supabase.yml
git commit -m "feat(docker): add Supabase docker-compose configuration"
```

---

## Task Group 5B: Secret Scanning

**Files:**
- Modify: `.pre-commit-config.yaml`
- Create: `.gitleaks.toml`
- Modify: `.gitignore`

### Step 1: Add gitleaks to pre-commit

```yaml
# .pre-commit-config.yaml (additions)

repos:
  # ... existing repos ...

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.4
    hooks:
      - id: gitleaks
```

### Step 2: Create gitleaks configuration

```toml
# .gitleaks.toml
title = "Votecatcher Secret Detection"

[extend]
useDefault = true

[[rules]]
id = "supabase-service-key"
description = "Supabase Service Role Key"
regex = '''sb_secret_[a-zA-Z0-9]{32,}'''
tags = ["supabase", "secret", "key"]

[[rules]]
id = "supabase-anon-key"
description = "Supabase Anonymous Key"
regex = '''eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*'''
tags = ["supabase", "key"]
[[rules.allowlists]]
regexes = ['''your.*key.*here''']

[[rules]]
id = "database-password"
description = "Database password in connection string"
regex = '''postgresql://[^:]+:([^@]+)@'''
tags = ["database", "password"]
[[rules.allowlists]]
regexes = ['''postgres''']  # Allow default dev password

[allowlist]
description = "Global allowlist"
paths = [
  '''.env.example''',
  '''tests/''',
  '''.*\.md$''',
]
```

### Step 3: Update .gitignore

```gitignore
# .gitignore (additions)

# Environment files with secrets
.env
.env.local
.env.*.local
.env.development
.env.production

# Supabase credentials (never commit)
*.supabase.env
```

### Step 4: Install and test gitleaks

```bash
# Install gitleaks (macOS)
brew install gitleaks

# Install pre-commit hooks
pre-commit install

# Run secret scan
gitleaks detect --source . --config .gitleaks.toml
```

### Step 5: Commit

```bash
git add .pre-commit-config.yaml .gitleaks.toml .gitignore
git commit -m "feat(security): add gitleaks secret scanning"
```

---

## Task Group 5C: Schema Documentation

**Files:**
- Create: `backend/scripts/generate_schema_docs.py`
- Create: `docs/database/README.md`
- Add to: `pyproject.toml` (eralchemy2 dependency)

### Step 1: Add dependency

```toml
# backend/pyproject.toml (addition to dependencies)

dependencies = [
  # ... existing dependencies ...
  "eralchemy2>=1.3.0",
]
```

### Step 2: Install dependency

```bash
cd backend && uv sync
```

### Step 3: Create schema generation script

```python
#!/usr/bin/env python
# backend/scripts/generate_schema_docs.py
"""Auto-generate database schema documentation."""

import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import SQLModel


def import_all_models() -> None:
    """Import all models to register with SQLModel metadata."""
    from app.data.database.model.jobs import MatcherJob, OcrJob, OcrModel, OcrProvider  # noqa: F401
    from app.data.database.model.llm_provider_config import LlmProviderConfig  # noqa: F401
    from app.data.database.model.match_result import MatchResult  # noqa: F401
    from app.data.database.model.ocr_result import OcrResult  # noqa: F401
    from app.data.database.model.petition_crop import PetitionCrop  # noqa: F401
    from app.data.database.model.petition_scan import PetitionScan  # noqa: F401
    from app.data.database.model.registered_voter import RegisteredVoter  # noqa: F401
    from app.data.database.model.schema import Campaign, Region  # noqa: F401
    from app.data.database.model.session import Session as SessionModel  # noqa: F401
    from app.data.database.model.user import User  # noqa: F401
    from app.data.database.model.voter_list_upload import VoterListUpload  # noqa: F401
    from app.data.database.model.ocr_model import OcrModelConfig  # noqa: F401


def generate_schema_docs(output_dir: Path | None = None) -> None:
    """Generate schema documentation from SQLModel metadata."""
    if output_dir is None:
        output_dir = Path(__file__).parent.parent.parent / "docs" / "database"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Import models
    import_all_models()

    try:
        from eralchemy2 import render_er

        # Generate Mermaid ERD (renders in GitHub)
        mermaid_path = output_dir / "schema.md"
        render_er(
            SQLModel.metadata,
            str(mermaid_path),
            mode="mermaid_er",
        )
        print(f"Generated: {mermaid_path}")

        # Generate SVG for high-quality docs
        svg_path = output_dir / "schema.svg"
        render_er(
            SQLModel.metadata,
            str(svg_path),
        )
        print(f"Generated: {svg_path}")

    except ImportError:
        print("eralchemy2 not installed. Install with: uv add eralchemy2")
        sys.exit(1)

    # Update README with timestamp
    readme_path = output_dir / "README.md"
    update_readme(readme_path)
    print(f"Updated: {readme_path}")


def update_readme(readme_path: Path) -> None:
    """Update README with current timestamp."""
    content = f"""# Database Schema

Auto-generated from SQLModel definitions.

**Last updated:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}

## Diagrams

- [Mermaid ERD](./schema.md) - Renders in GitHub
- [SVG Diagram](./schema.svg) - High-quality vector

## Tables

| Table | Purpose |
|-------|---------|
| `campaign` | Election campaigns |
| `petition_scan` | Uploaded petition PDFs |
| `petition_crop` | Extracted signature images |
| `registered_voter` | Voter registration data |
| `match_result` | Signature match results |
| `ocr_result` | OCR processing results |
| `user` | User accounts |
| `session` | User sessions |
| `llm_provider_config` | LLM provider configurations |
| `ocr_job` | OCR job queue |
| `matcher_job` | Matching job queue |

## Regeneration

Run to regenerate after model changes:

```bash
cd backend && python scripts/generate_schema_docs.py
```
"""
    readme_path.write_text(content)


if __name__ == "__main__":
    generate_schema_docs()
```

### Step 4: Create docs directory

```bash
mkdir -p docs/database
cd backend && python scripts/generate_schema_docs.py
```

### Step 5: Commit

```bash
git add backend/scripts/generate_schema_docs.py backend/pyproject.toml docs/database/
git commit -m "feat(docs): add schema documentation generation"
```

---

## Task Group 5D: CI/CD Workflows

**Files:**
- Create: `.github/workflows/schema-docs.yml`
- Create: `.github/workflows/deploy-supabase.yml`

### Step 1: Create schema docs workflow

```yaml
# .github/workflows/schema-docs.yml
name: Generate Schema Docs

on:
  push:
    branches: [main]
    paths:
      - 'backend/app/data/database/model/**'
      - 'backend/alembic/versions/**'

jobs:
  generate:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: |
          cd backend
          uv sync

      - name: Generate schema docs
        run: |
          cd backend
          uv run python scripts/generate_schema_docs.py

      - name: Commit changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add docs/database/
          git diff --quiet && git diff --staged --quiet || git commit -m "docs: update schema diagrams [skip ci]"
          git push
```

### Step 2: Create deployment workflow

```yaml
# .github/workflows/deploy-supabase.yml
name: Deploy to Supabase

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment }}

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: |
          cd backend
          uv sync

      - name: Run migrations
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
          SUPABASE_DB_PASSWORD: ${{ secrets.SUPABASE_DB_PASSWORD }}
        run: |
          cd backend
          uv run python -m app.scripts.supabase provision

      - name: Health check
        run: |
          curl -f ${{ secrets.API_URL }}/health || exit 1
```

### Step 3: Add secret scanning to CI

Add to existing CI workflow or create new:

```yaml
# .github/workflows/security.yml
name: Security

on:
  push:
    branches: [main]
  pull_request:

jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Step 4: Commit

```bash
git add .github/workflows/
git commit -m "feat(ci): add schema docs and Supabase deployment workflows"
```

---

## Phase 5 Exit Gate

**Run all validation:**

```bash
# Docker builds
docker compose config
docker compose -f docker-compose.supabase.yml config

# Secret scanning
gitleaks detect --source . --config .gitleaks.toml --no-git

# Schema docs generation
cd backend && uv run python scripts/generate_schema_docs.py

# Full test suite
cd backend && uv run pytest tests/ -v

# Type checking
cd backend && uv run basedpyright app/

# Linting
cd backend && uv run ruff check app/
```

**Expected Results:**
- [ ] Docker configs valid
- [ ] No secrets detected
- [ ] Schema docs generated
- [ ] All tests pass
- [ ] No type errors
- [ ] No lint errors

---

## Reviewer Section

**Reviewer:** ___________________

**Date:** ___________________

**Status:** [ ] Approved [ ] Needs Changes

**Feedback:**

| Task Group | Issues | Resolution |
|------------|--------|------------|
| 5A | | |
| 5B | | |
| 5C | | |
| 5D | | |

**Blocking issues:**

-

**Suggestions for improvement:**

-

---

## Final Checklist

After all phases complete:

- [ ] Phase 1: Configuration Architecture ✓
- [ ] Phase 2: Persistence Layer ✓
- [ ] Phase 3: Frontend Onboarding ✓
- [ ] Phase 4: Backend API & CLI ✓
- [ ] Phase 5: Docker & CI/CD ✓

**Global Exit Gate:**

```bash
# Backend
cd backend && uv run pytest tests/ -v
cd backend && uv run basedpyright app/
cd backend && uv run ruff check app/

# Frontend
cd frontend-svelt && npm run check
cd frontend-svelt && npm run lint
cd frontend-svelt && npm run build

# Security
gitleaks detect --source . --config .gitleaks.toml

# Docker
docker compose up --build -d
curl http://localhost:8080/health
docker compose down
```

**Documentation Updated:**
- [ ] README.md updated with Supabase setup instructions
- [ ] docs/database/README.md generated
- [ ] .env.example updated with all new variables

---

## Implementation Complete!

All phases have been implemented. The system now supports:

1. **Unified Configuration** - Type-safe settings with provider pattern
2. **Database Abstraction** - Engine pattern for SQLite/Postgres/Supabase
3. **Onboarding Wizard** - Svelte UI for first-time setup
4. **REST API** - Database status and provisioning endpoints
5. **CLI Tools** - Command-line management for CI/CD
6. **Docker Support** - Compose files for local and Supabase deployment
7. **Security** - Secret scanning with gitleaks
8. **Documentation** - Auto-generated schema diagrams
