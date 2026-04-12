# VoteCatcher

**Open Source Campaign Infrastructure**

Automate ballot signature recognition and validation. Put powerful organizing tools in the hands of grassroots campaigns. Democracy should be accessible to everyone.

## Features

- **Signature Validation**: High-accuracy signature triaging using multimodal LLMs integrated with voter files
- **Grassroots Focused**: Built for community organizers and campaigns that need powerful tools without the high costs
- **Open Source**: Transparent, community-driven technology that strengthens democratic participation
- **PDF Processing**: OCR capabilities for processing petition documents
- **Fuzzy Matching**: Advanced name and address matching algorithms
- **Campaign Management**: Multi-campaign support with user isolation
- **Demo Mode**: Full workspace experience with sample data, no API keys required

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | SvelteKit 5, Svelte 5, TypeScript, Tailwind CSS v4 |
| Backend | FastAPI, Python 3.12+, SQLModel, Alembic |
| Database | PostgreSQL / SQLite / Supabase |
| Auth | Better Auth |
| ORM | Drizzle (frontend), SQLModel (backend) |
| AI/ML | OpenAI, Mistral, Gemini API integration |
| Package Managers | bun (frontend), uv (backend) |
| Task Runner | [just](https://github.com/casey/just) |

## Quick Start

### Prerequisites

- [Python 3.12+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/) package manager
- [Bun](https://bun.sh/) runtime
- [Git](https://git-scm.com/)
- API key for at least one LLM provider (optional — use simulation mode without)
- [just](https://github.com/casey/just) task runner (recommended)

> **No API key?** Run in simulation mode — all features work with mock OCR. See [Configuration Modes](docs/configuration-modes.md).

### 1. Clone and Install

```bash
git clone https://github.com/civictechdc/votecatcher
cd votecatcher
just install
```

Or manually:

```bash
cd backend && uv sync --dev
cd ../frontend && bun install
```

### 2. Configure Environment

```bash
cp backend/.env.example backend/.env.local
cp frontend/.env.example frontend/.env
```

Edit `backend/.env.local` — for simulation mode (no API key needed):

```env
DATABASE_URL=sqlite:///./dev.db
OCR_PROVIDER_NAME=open_ai
OCR_PROVIDER_MODEL=gpt-4o-mini
OCR_PROVIDER_API_KEY=
FEATURE_ENABLE_SIMULATION=1
```

### 3. Run Database Migrations

```bash
just migrate
```

### 4. Start Development Servers

**Terminal 1 — Backend** (`http://localhost:8080`):

```bash
just dev-backend
```

**Terminal 2 — Frontend** (`http://localhost:5173`):

```bash
just dev-frontend
```

**Or use Docker Compose** (starts all services):

```bash
just dev
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | SvelteKit application |
| Backend API | http://localhost:8080 | FastAPI application |
| API Docs | http://localhost:8080/docs | Swagger UI |
| ReDoc | http://localhost:8080/redoc | Alternative API docs |

## Project Structure

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
├── docker-compose.yml      # Docker Compose for local/production
├── justfile                # Task runner recipes
└── Makefile                # Auto-generated from justfile
```

## Configuration

VoteCatcher supports multiple database and OCR configurations. See [Configuration Modes](docs/configuration-modes.md) for the full guide.

### Database Options

| Database | Use Case | Setup |
|----------|----------|-------|
| SQLite | Local development, testing | Zero config (`sqlite:///./dev.db`) |
| PostgreSQL | Production, concurrent users | `just dev-postgres` |
| Supabase | Managed PostgreSQL + Auth + Storage | [Supabase Setup](#supabase-setup) |

### Supabase Setup

VoteCatcher supports Supabase as a fully-managed database backend:

```bash
supabase login
chmod +x setupSupabase.sh
./setupSupabase.sh
```

Then set in `backend/.env.local`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_DB_PASSWORD=your-db-password
```

## Common Commands

All commands use [just](https://github.com/casey/just). Run `just` to see all available recipes.

| Command | Description |
|---------|-------------|
| `just install` | Install all dependencies |
| `just dev-backend` | Start backend dev server |
| `just dev-frontend` | Start frontend dev server |
| `just dev` | Start all services via Docker Compose |
| `just test` | Run all tests (backend + frontend) |
| `just lint` | Run linters (ruff + oxlint) |
| `just typecheck` | Run type checkers (basedpyright + svelte-check) |
| `just migrate` | Run database migrations |
| `just ci-sim` | Simulate full CI pipeline locally |
| `just security-scan` | Run security scans |

## Security

- **Row Level Security**: Data protected by RLS policies (Supabase)
- **Encrypted API Keys**: User API keys encrypted at rest
- **User Isolation**: Campaigns isolated by user ownership
- **SAST/SCA/DAST**: Full security pipeline in CI
- **Secret Scanning**: Gitleaks integration
- **Container Scanning**: Trivy vulnerability scanning
- **Dependency Auditing**: OSV Scanner + pip audit + bun audit

## Documentation

| Document | Description |
|----------|-------------|
| [Running Locally](docs/running-locally.md) | Detailed local development setup |
| [Configuration Modes](docs/configuration-modes.md) | All configuration options |
| [Architecture](docs/architecture/README.md) | C4 model diagrams and ADRs |
| [Docker Deployment](docs/deployment/docker-compose-deployment.md) | Production deployment guide |
| [User Guide](docs/user-guide.md) | Application usage guide |
| [Demo Walkthrough](docs/demo-walkthrough.md) | Demo mode walkthrough |
| [API Spec](backend/openapi.yaml) | OpenAPI specification |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, code standards, and PR process.

## License

This project is open source. See [LICENSE](LICENSE) for details.
