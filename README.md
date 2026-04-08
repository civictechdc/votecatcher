# VoteCatcher

**Open Source Campaign Infrastructure**

Automate ballot signature recognition and validation. Put powerful organizing tools in the hands of grassroots campaigns. Democracy should be accessible to everyone.

## Features

- **Signature Validation**: High-accuracy signature triaging using multimodal LLMs integrated with voter files
- **Grassroots Focused**: Built for community organizers and campaigns that need powerful tools without the high costs
- **Open Source**: Transparent, community-driven technology that strengthens democratic participation
- **PDF Processing**: OCR capabilities for processing petition documents with pre-cropping
- **Fuzzy Matching**: Advanced name and address matching with RapidFuzz
- **Real-time Updates**: SSE-powered job status updates
- **Campaign Management**: Multi-campaign support with session persistence

## Quick Start

### Prerequisites

- **Python 3.12+**
- **Node.js 20+** or **Bun**
- **Docker** (optional, for PostgreSQL)
- **PostgreSQL** (optional, SQLite works for development)
- **API key** for at least one LLM provider (optional - use simulation mode without)

### 1. Clone and Setup

```bash
git clone https://github.com/civictechdc/votecatcher
cd votecatcher
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies
uv sync --dev

# Create environment file
cp .env.example .env.local

# For quick start without API keys, enable simulation mode:
# Edit .env.local and set FEATURE_ENABLE_SIMULATION=1
#
# For real OCR, add your API keys:
# OCR_PROVIDER_NAME=open_ai
# OCR_PROVIDER_MODEL=gpt-4o-mini
# OCR_PROVIDER_API_KEY=your-key-here

# Initialize database
uv run alembic upgrade head
```

> **See [Configuration Modes](docs/configuration-modes.md) for all setup options.**

### 3. Frontend Setup

```bash
cd frontend-svelt

# Install dependencies
bun install

# Create environment file
cp .env.example .env.local

# For demo mode, set PUBLIC_DEMO_MODE=true and DEMO_MODE=true
```

> **See [Configuration Modes](docs/configuration-modes.md) for all setup options.**

### 4. Run Development Servers

**Terminal 1 - Backend:**
```bash
cd backend
uv run python main.py --env local
# API runs at http://localhost:8080
# Docs available at http://localhost:8080/docs
```

**Terminal 2 - Frontend:**
```bash
cd frontend-svelt
bun run dev
# Frontend runs at http://localhost:5173
```

### 5. Access the Application

Open http://localhost:5173 to see the landing page, or http://localhost:5173/workspace/campaigns to get started with campaigns.

### Route Structure

```
/                             → Marketing landing page
/workspace                    → Redirects to /workspace/campaigns
/workspace/campaigns          → Campaign list
/workspace/[id]               → Campaign dashboard (metrics, jobs, results)
/workspace/[id]/jobs          → Jobs scoped to campaign
/workspace/[id]/jobs/[job_id] → Job details and status
/workspace/[id]/results       → Match results scoped to campaign
/workspace/[id]/upload        → Upload page (Voter List / Petitions tabs)
/workspace/settings           → Global settings + LLM providers
/workspace/demo               → Demo mode (virtual campaign)
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Backend** | FastAPI + SQLModel | Async API with type-safe ORM |
| **Frontend** | SvelteKit + TypeScript | Fast, compiled UI framework |
| **Database** | PostgreSQL / SQLite | Production / Development |
| **OCR** | LLM Batch APIs (OpenAI, Gemini, Mistral) | Cost-effective async processing |
| **Matching** | RapidFuzz | Fast fuzzy string matching |
| **Real-time** | Server-Sent Events (SSE) | Live job status updates |
| **Styling** | Tailwind CSS v4 | Utility-first CSS |
| **Build** | Vite + Bun | Fast frontend tooling |

## Project Structure

```
votecatcher/
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── api.py           # Application entry point
│   │   ├── routers/         # API route handlers
│   │   ├── services/        # Business logic
│   │   ├── data/            # Database models & migrations
│   │   ├── ocr/             # OCR client implementations
│   │   ├── matching/        # Fuzzy matching engine
│   │   └── jobs/            # Job orchestration
│   ├── tests/               # Test suites
│   └── openapi.yaml         # API specification
│
├── frontend-svelt/          # SvelteKit frontend
│   ├── src/
│   │   ├── routes/          # Page routes
│   │   ├── lib/
│   │   │   ├── components/  # UI components
│   │   │   ├── stores/      # Svelte stores
│   │   │   └── api/         # API client
│   │   └── app.html         # HTML template
│   └── tests/               # Test suites
│
├── app/                     # Root-level API assets
│   └── api/
│       └── voter_spec.json  # Voter data field specification
│
├── scripts/                 # Build and maintenance scripts
│   ├── just-to-make.py      # Generate Makefile from justfile
│   ├── validate-docs.sh     # Documentation accuracy validation
│   └── init-dev-db.sql      # Initialize development database
│
├── supabase/                # Supabase configuration
│   ├── functions/           # Edge Functions (Deno)
│   └── migrations/          # Database migrations
│
├── sqlite/                  # SQLite database files (development)
│
├── docs/                    # Documentation
│   ├── architecture/        # C4 diagrams & ADRs
│   ├── development/         # Dev guides
│   └── running-locally.md   # Detailed setup
```

## Documentation

### For Users

- **[Configuration Modes](docs/configuration-modes.md)** - All configuration options (production, dev, simulation, demo)
- **[Running Locally](docs/running-locally.md)** - Detailed setup and configuration
- **[Demo Walkthrough](docs/demo-walkthrough.md)** - Demo script for presentations
- **[Deployment Guide](docs/deployment/docker-compose-deployment.md)** - Production deployment with Docker Compose

### For Developers

- **[Architecture Overview](docs/architecture/README.md)** - System design
- **[C4 Diagrams](docs/architecture/)** - Context, containers, components
- **[Architecture Decisions](docs/architecture/decisions/)** - ADRs
- **[API Specification](backend/openapi.yaml)** - OpenAPI 3.1 spec

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest --cov=app

# Run specific test category
uv run pytest tests/unit/services/ -v
uv run pytest tests/integration/ -v
```

### Frontend Tests

```bash
cd frontend-svelt

# Unit tests
bun run test

# E2E tests
bun run test:e2e
```

## Development Commands

### Task Runner

This project uses [just](https://github.com/casey/just) as the primary task runner. It works on macOS, Linux, and Windows.

```bash
# Install just
brew install just      # macOS
apt install just       # Linux
winget install just    # Windows

# List available commands
just --list

# Common commands
just install           # Install all dependencies
just dev-postgres      # Start PostgreSQL for local dev
just test              # Run all tests
just lint              # Run linters
just typecheck         # Run type checkers
```

A generated `Makefile` is also available for Unix users who prefer `make`. The Makefile is auto-generated from the justfile - run `just sync-makefile` to update it.

### Backend

```bash
cd backend

# Type check
uv run basedpyright app/

# Lint
uv run ruff check app/

# Format
uv run ruff format app/

# Database migrations
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"
```

### Frontend

```bash
cd frontend-svelt

# Type check
bun run typecheck

# Lint
bun run lint

# Format
bun run lint:fix

# Build
bun run build
```

## Security

- **Row Level Security**: Data isolated by campaign
- **Encrypted API Keys**: User credentials encrypted at rest
- **SSE Authentication**: Job updates require valid session
- **CORS Protection**: Configured for production origins
- **Input Validation**: All inputs validated via Pydantic

## Roadmap

- [x] Phase 1: Stability - Worker tests, metrics API, error handling
- [x] Phase 2: Polish - Keyboard nav, E2E tests, documentation
- [x] Phase 3: Page Hierarchy - Route restructure, campaign scoping
- [x] Phase 4: Stretch - LLM config UI, provider selection on job creation

### Current Status: MVP Complete ✅

The core MVP is feature-complete with:
- Full backend API with comprehensive test coverage
- Responsive SvelteKit frontend
- PostgreSQL/SQLite database support
- Multi-provider OCR integration
- Real-time job updates via SSE
- Complete security scanning and testing pipeline
- Enhanced DevContainer with justfile-first architecture

**Recent Enhancements:**
- Enhanced DevContainer with Bun and Go support
- Docker Compose override with development database
- Security test recipe in justfile
- Documentation accuracy validation with pre-commit hooks

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes (with tests!)
4. Run the test suite
5. Commit your changes
6. Push to the branch
7. Open a Pull Request

**Note:** All contributions must pass lint, typecheck, and tests.

## License

This project is open source. See [LICENSE](LICENSE) for details.

## Acknowledgments

Built by [Civic Tech DC](https://github.com/civictechdc) to strengthen democratic participation.
