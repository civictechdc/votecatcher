# Project Structure

Directory layout and module overview for VoteCatcher.

```
votecatcher/
├── backend/                 # FastAPI application
│   ├── app/                # Application source
│   │   ├── api.py          # FastAPI entry point
│   │   ├── routers/        # API route handlers
│   │   ├── services/       # Business logic
│   │   ├── persistence/    # Database engines (SQLite/PostgreSQL/Supabase)
│   │   ├── ocr/            # OCR provider integrations
│   │   ├── matching/       # Fuzzy matching algorithms
│   │   ├── campaign/       # Campaign management
│   │   └── settings/       # Configuration management
│   ├── alembic/            # Database migrations
│   ├── tests/              # Test suite
│   └── pyproject.toml      # Python dependencies
├── frontend/               # SvelteKit application
│   ├── src/
│   │   ├── lib/            # Shared libraries, components, utilities
│   │   ├── routes/         # SvelteKit routes
│   │   └── hooks.server.ts # Server hooks (auth, CORS)
│   ├── e2e/                # Playwright end-to-end tests
│   ├── tests/              # Vitest unit tests
│   └── package.json        # Node dependencies
├── supabase/               # Supabase migrations and edge functions
├── security/               # Security configs (nuclei templates, semgrep rules)
├── docs/                   # Documentation
├── .devcontainer/          # VS Code dev container configuration
├── docker-compose.yml      # Docker Compose for local/production
├── justfile                # Task runner recipes
└── Makefile                # Auto-generated from justfile
```

## Module Overview

### Backend (`backend/`)

The backend is a Python FastAPI application providing REST APIs for signature validation, campaign management, and OCR processing.

| Module | Purpose |
|--------|---------|
| `app/routers/` | API route handlers — request/response contracts |
| `app/services/` | Business logic — signature validation, job orchestration |
| `app/persistence/` | Database abstraction — SQLite, PostgreSQL, Supabase engines |
| `app/ocr/` | OCR provider integrations — OpenAI, Mistral, Gemini |
| `app/matching/` | Fuzzy matching algorithms — name and address matching |
| `app/campaign/` | Campaign CRUD and lifecycle management |
| `app/settings/` | Configuration management and environment handling |
| `alembic/` | Database migration scripts |
| `tests/` | Unit, integration, security, and benchmark tests |

### Frontend (`frontend/`)

A SvelteKit 5 application with server-side rendering, Tailwind CSS v4 styling, and Better Auth integration.

| Module | Purpose |
|--------|---------|
| `src/lib/` | Shared components, utilities, and stores |
| `src/routes/` | SvelteKit file-based routing |
| `src/hooks.server.ts` | Server hooks — auth middleware, CORS |
| `e2e/` | Playwright end-to-end test suite |
| `tests/` | Vitest unit tests |

### Infrastructure

| Directory | Purpose |
|-----------|---------|
| `supabase/` | Supabase migrations and edge functions |
| `security/` | SAST/DAST configs — nuclei templates, semgrep rules |
| `.devcontainer/` | VS Code dev container setup with Docker Compose |
| `docs/` | Project documentation, architecture, and guides |

## Key Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Service orchestration (backend, frontend, PostgreSQL) |
| `justfile` | Task runner recipes — build, test, lint, deploy commands |
| `backend/openapi.yaml` | Generated OpenAPI specification |
| `backend/pyproject.toml` | Python dependencies and tool config |
| `frontend/package.json` | Node dependencies and scripts |
