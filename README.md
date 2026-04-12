<div align="center">

# VoteCatcher ✓

**Open Source Campaign Infrastructure**

Automate ballot signature recognition and validation. Put powerful organizing tools in the hands of grassroots campaigns.

[![CI](https://github.com/civictechdc/votecatcher/actions/workflows/ci.yml/badge.svg)](https://github.com/civictechdc/votecatcher/actions/workflows/ci.yml)
[![Code Quality](https://github.com/civictechdc/votecatcher/actions/workflows/code-quality.yml/badge.svg)](https://github.com/civictechdc/votecatcher/actions/workflows/code-quality.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![SvelteKit](https://img.shields.io/badge/SvelteKit-5-FF3E00.svg?logo=svelte&logoColor=white)](https://kit.svelte.dev)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)

</div>

---

## Quick Start

### Prerequisites

- [Python 3.12+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/) package manager
- [Bun](https://bun.sh/) runtime
- [Docker](https://www.docker.com/) (for containerized setup)
- [just](https://github.com/casey/just) task runner (recommended)
- API key for an LLM provider (optional — simulation mode works without one)

> **No API key?** Run in simulation mode — all features work with mock OCR. See [Configuration Modes](docs/configuration-modes.md).

### Option 1: Local Development

```bash
git clone https://github.com/civictechdc/votecatcher
cd votecatcher

# Install dependencies
just install

# Configure environment
cp backend/.env.example backend/.env.local
cp frontend/.env.example frontend/.env

# Run migrations
just migrate

# Start backend (http://localhost:8080)
just dev-backend

# Start frontend in another terminal (http://localhost:5173)
just dev-frontend
```

### Option 2: Docker Compose

Starts backend, frontend, and PostgreSQL together:

```bash
git clone https://github.com/civictechdc/votecatcher
cd votecatcher

cp backend/.env.example backend/.env.local
cp frontend/.env.example frontend/.env

just dev
```

### Option 3: Dev Container (VS Code)

1. Open the repo in [VS Code](https://code.visualstudio.com/)
2. When prompted, click **Reopen in Container**
3. Wait for the container to build (~5 min first time)
4. Run the setup:

```bash
.devcontainer/setup.sh
```

5. Start services in separate terminals:

```bash
# Terminal 1 — Backend
cd backend && uv run python -m app --env local

# Terminal 2 — Frontend
cd frontend && bun run dev
```

See [.devcontainer/README.md](.devcontainer/README.md) for troubleshooting.

### Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8080 |
| Swagger UI | http://localhost:8080/docs |
| ReDoc | http://localhost:8080/redoc |

## Common Commands

All commands use [just](https://github.com/casey/just). Run `just` to see all recipes.

| Command | Description |
|---------|-------------|
| `just install` | Install all dependencies |
| `just dev-backend` | Start backend dev server |
| `just dev-frontend` | Start frontend dev server |
| `just dev` | Start all services via Docker Compose |
| `just test` | Run all tests |
| `just lint` | Run linters |
| `just typecheck` | Run type checkers |
| `just migrate` | Run database migrations |
| `just security-scan` | Run security scans |
| `just ci-sim` | Simulate full CI pipeline locally |

## Configuration

VoteCatcher supports multiple database and OCR configurations:

| Database | Use Case | Setup |
|----------|----------|-------|
| SQLite | Local development, testing | Zero config (`sqlite:///./dev.db`) |
| PostgreSQL | Production, concurrent users | `just dev-postgres` |
| Supabase | Managed PostgreSQL + Auth + Storage | [Supabase Setup](docs/configuration-modes.md) |

For full configuration details, see [Configuration Modes](docs/configuration-modes.md).

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | SvelteKit 5, Svelte 5, TypeScript, Tailwind CSS v4 |
| Backend | FastAPI, Python 3.12+, SQLModel, Alembic |
| Database | PostgreSQL / SQLite / Supabase |
| Auth | Better Auth |
| AI/ML | OpenAI, Mistral, Gemini API integration |
| Package Managers | bun (frontend), uv (backend) |

## Documentation

| Document | Description |
|----------|-------------|
| [Running Locally](docs/running-locally.md) | Detailed local development setup |
| [Configuration Modes](docs/configuration-modes.md) | All configuration options |
| [Architecture](docs/architecture/README.md) | C4 model diagrams and ADRs |
| [Project Structure](docs/architecture/project-structure.md) | Directory layout and module overview |
| [Docker Deployment](docs/deployment/docker-compose-deployment.md) | Production deployment guide |
| [User Guide](docs/user-guide.md) | Application usage guide |
| [Demo Walkthrough](docs/demo-walkthrough.md) | Demo mode walkthrough |
| [API Spec](backend/openapi.yaml) | OpenAPI specification |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, code standards, and PR process.

## License

This project is open source under the [MIT License](LICENSE).
