<div align="center">

# VoteCatcher ✓

**Open Source Campaign Infrastructure**

Automate ballot signature recognition and validation. Put powerful organizing tools in the hands of grassroots campaigns.

[![CI](https://github.com/civictechdc/votecatcher/actions/workflows/ci.yml/badge.svg)](https://github.com/civictechdc/votecatcher/actions/workflows/ci.yml)
[![Security](https://github.com/civictechdc/votecatcher/actions/workflows/security.yml/badge.svg)](https://github.com/civictechdc/votecatcher/actions/workflows/security.yml)
[![Version](https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fraw.githubusercontent.com%2Fcivictechdc%2Fvotecatcher%2Fmain%2Fbackend%2Fpyproject.toml&query=%24.project.version&label=version&color=green)](https://github.com/civictechdc/votecatcher/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![SvelteKit](https://img.shields.io/badge/SvelteKit-5-FF3E00.svg?logo=svelte&logoColor=white)](https://kit.svelte.dev)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)

</div>

---

## Deploy to the Cloud

Click a button to deploy VoteCatcher with a managed database. You'll need an OCR provider API key (e.g., OpenAI).

<table border="0">
  <tr>
    <td>
      <a href="https://cloud.digitalocean.com/apps/new?repo=https://github.com/civictechdc/votecatcher/tree/main">
        <img src="https://www.deploytodo.com/do-btn-blue.svg" alt="Deploy to DigitalOcean" height="40">
      </a>
    </td>
    <td>
      <sub>Ephemeral dev DB — <a href="docs/deployment/docker-compose-deployment.md">upgrade to managed Postgres</a> for production</sub>
    </td>
  </tr>
  <tr>
    <td>
      <a href="https://render.com/deploy?repo=https://github.com/civictechdc/votecatcher">
        <img src="https://render.com/images/deploy-to-render-button.svg" alt="Deploy to Render" height="40">
      </a>
    </td>
    <td></td>
  </tr>
  <tr>
    <td>
      <a href="https://railway.com/new">
        <img src="https://railway.com/button.svg" alt="Deploy to Railway" height="40">
      </a>
    </td>
    <td></td>
  </tr>
  <tr>
    <td>
      <a href="https://coolify.io">
        <img src="https://github.com/kbkgk1/deploy-buttons/raw/refs/heads/main/svgs/deploy-coolify.svg" alt="Deploy to Coolify" height="40">
      </a>
    </td>
    <td>
      <sub>Self-hosted — point at this repo's <code>docker-compose.yml</code></sub>
    </td>
  </tr>
</table>

---

## Getting Started

The fastest way to run VoteCatcher is with **Docker** — no Python, Node, or build tools needed. All you need is [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

1. **Download VoteCatcher** — clone with git or download the ZIP from the green "Code" button on GitHub, then open a terminal in the folder

2. **Run the setup script:**

```bash
# macOS / Linux
./start.sh

# Windows Command Prompt
start.bat

# Windows PowerShell
.\start.ps1
```

That's it. The script checks Docker, creates config files, and starts the app. Once ready, open:

| What | URL |
|------|-----|
| **VoteCatcher app** | http://localhost:5173 |
| API docs | http://localhost:8080/docs |

To stop: press `Ctrl+C`, or run `docker compose down`

> **Need to configure OCR providers or database?** See [Configuration Modes](docs/configuration-modes.md).

---

## Quick Start (Developers)

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
| [Versioning](docs/development/versioning.md) | Release and version management |
| [Docker Deployment](docs/deployment/docker-compose-deployment.md) | Production deployment guide |
| [User Guide](docs/user-guide.md) | Application usage guide |
| [Demo Walkthrough](docs/demo-walkthrough.md) | Demo mode walkthrough |
| [API Spec](backend/openapi.yaml) | OpenAPI specification |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, code standards, and PR process.

## License

This project is open source under the [MIT License](LICENSE).
