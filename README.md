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
- **PostgreSQL** (optional, SQLite works for development)
- **API key** for at least one LLM provider (OpenAI, Gemini, or Mistral)

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

# Edit .env.local and add your API keys:
# OCR_PROVIDER_NAME=open_ai
# OCR_PROVIDER_MODEL=gpt-4o-mini
# OCR_PROVIDER_API_KEY=your-key-here

# Initialize database
uv run alembic upgrade head
```

### 3. Frontend Setup

```bash
cd frontend-svelt

# Install dependencies
bun install

# Create environment file
cp .env.example .env.local
```

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

Open http://localhost:5173/workspace to get started.

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
├── docs/                    # Documentation
│   ├── architecture/        # C4 diagrams & ADRs
│   ├── development/         # Dev guides
│   └── running-locally.md   # Detailed setup
│
└── openspec/               # Technical specification
    ├── SPEC.md             # Implementation blueprint
    └── PROGRESS.md         # Implementation progress
```

## Documentation

### For Users

- **[Running Locally](docs/running-locally.md)** - Detailed setup and configuration
- **[Deployment Guide](docs/deployment/)** - Production deployment (coming soon)

### For Developers

- **[Architecture Overview](docs/architecture/README.md)** - System design
- **[C4 Diagrams](docs/architecture/)** - Context, containers, components
- **[Architecture Decisions](docs/architecture/decisions/)** - ADRs
- **[API Specification](backend/openapi.yaml)** - OpenAPI 3.1 spec

### Technical Specification

- **[SPEC.md](openspec/SPEC.md)** - Complete technical specification
- **[PROGRESS.md](openspec/PROGRESS.md)** - Implementation status

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

See [Security Scanning](openspec/SPEC.md#appendix-c-security-scanning) for details on automated security checks.

## Roadmap

- [x] Phase 0: Setup & Infrastructure
- [x] Phase 1: Data Layer
- [x] Phase 2: Core Backend Services
- [x] Phase 2.5: API Endpoints
- [x] Phase 3: Frontend Foundation
- [x] Phase 4: Integration & E2E Tests
- [ ] Phase 5: Polish & Demo

See [PROGRESS.md](openspec/PROGRESS.md) for detailed status.

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
