# Development Documentation

Guides for local development and contribution.

## Contents

| Document | Description |
|----------|-------------|
| [Running Locally](../running-locally.md) | Complete local development setup |
| [Architecture](../architecture/README.md) | System design and ADRs |
| [API Spec](../../backend/openapi.yaml) | OpenAPI 3.1 specification |

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/civictechdc/votecatcher
cd votecatcher

# 2. Backend setup
cd backend
uv sync --dev
cp .env.example .env.local
# Edit .env.local with your API keys

# 3. Frontend setup
cd ../frontend-svelt
bun install
cp .env.example .env.local

# 4. Run development servers
# Terminal 1: cd backend && uv run fastapi dev app/api.py
# Terminal 2: cd frontend-svelt && bun run dev

# 5. Access
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000/docs
```

## Prerequisites

- **Python 3.12+** (3.13 recommended)
- **Node.js 20+** or **Bun**
- **PostgreSQL** (optional, SQLite works for development)
- **Git**
- **LLM Provider API key** (OpenAI, Gemini, or Mistral)

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes with Tests

- Follow TDD: write tests first
- Backend: `pytest tests/`
- Frontend: `bun run test`

### 3. Run Quality Checks

**Backend:**
```bash
cd backend
uv run basedpyright app/    # Type check
uv run ruff check app/      # Lint
uv run ruff format app/     # Format
uv run pytest tests/ -v     # Tests
```

**Frontend:**
```bash
cd frontend-svelt
bun run typecheck           # Type check
bun run lint               # Lint
bun run lint:fix           # Format
bun run test               # Tests
```

### 4. Commit and Push

```bash
git add .
git commit -m "feat: your feature description"
git push origin feature/your-feature-name
```

### 5. Open Pull Request

- All checks must pass
- Include tests for new functionality
- Update documentation if needed

## Code Style

### Backend (Python)

- **Type hints:** Required for all functions
- **Docstrings:** Public APIs only
- **Comments:** Sparingly, explain "why" not "what"
- **Formatting:** Ruff (auto-format)
- **Line length:** 88 characters

### Frontend (TypeScript/Svelte)

- **Type annotations:** Required
- **Comments:** Sparingly, explain "why" not "what"
- **Formatting:** ESLint + Prettier
- **Components:** Svelte 5 runes ($props, $state, $derived)

## Project Structure

```
votecatcher/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── routers/     # API endpoints
│   │   ├── services/    # Business logic
│   │   ├── data/        # Database layer
│   │   └── ...
│   └── tests/           # Test suites
│
├── frontend-svelt/       # SvelteKit frontend
│   ├── src/
│   │   ├── routes/      # Pages
│   │   ├── lib/         # Shared code
│   │   └── ...
│   └── tests/           # Test suites
│
└── docs/                # Documentation
```

## Getting Help

- Check [PROGRESS.md](../../openspec/PROGRESS.md) for current status
- Review [SPEC.md](../../openspec/SPEC.md) for architecture details
- Check existing tests for patterns
- Open an issue for bugs or questions

## Related Documentation

- [Running Locally](../running-locally.md) - Detailed setup
- [Architecture](../architecture/README.md) - System design
- [API Specification](../../backend/openapi.yaml) - OpenAPI spec
