# Development Documentation

Guides for local development and contribution.

## Contents

| Document | Description |
|----------|-------------|
| [Running Locally](../running-locally.md) | Complete local development setup |
| [Versioning](./versioning.md) | Release and version management |
| [Architecture](../architecture/README.md) | System design and ADRs |
| [API Spec](../../backend/openapi.yaml) | OpenAPI 3.1 specification |
| [Field Spec Schema](./field-spec-schema.md) | JSON5 regional spec file format reference |
| [Adding a Region](./adding-a-region.md) | Tutorial: add a new voter region |
| [Testing Guide](./testing.md) | Testing patterns including approval tests |
| [Results Performance](./results-performance.md) | Query pagination, crop serving, and scaling at 10k+ results |

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
cd ../frontend
bun install
cp .env.example .env.local

# 4. Run development servers
# Terminal 1: cd backend && uv run python main.py --env local
# Terminal 2: cd frontend && bun run dev

# 5. Access
# Frontend: http://localhost:5173
# Backend API: http://localhost:8080/docs
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

**Frontend (SvelteKit — `frontend/`):**
```bash
cd frontend
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
│   │   ├── domain/       # Domain value objects and pure functions (field_spec.py)
│   │   ├── regions/      # JSON5 regional spec source files (dc.json5, demo.json5)
│   │   ├── routers/      # API endpoints
│   │   ├── services/     # Business logic (field_spec_service.py, voter_list_service.py)
│   │   ├── matching/     # Fuzzy matching (matching_service.py, voter_data_adapter.py)
│   │   ├── repositories/ # Persistence implementations (field_spec_repo.py)
│   │   ├── data/         # Database layer
│   │   └── ...
│   └── tests/           # Test suites
│
├── frontend/       # SvelteKit frontend
│   ├── src/
│   │   ├── routes/      # Pages
│   │   ├── lib/         # Shared code
│   │   └── ...
│   └── tests/           # Test suites
│
├── app/                  # Root-level API assets
│   └── api/
│       └── voter_spec.json  # Voter data field specification
│
├── scripts/              # Build and maintenance scripts
│   ├── just-to-make.py      # Generate Makefile from justfile
│   ├── validate-docs.sh     # Documentation accuracy validation
│   ├── verify-fix-results.sh # Verify match result fixes
│   └── init-dev-db.sql      # Initialize development database
│
├── supabase/             # Supabase configuration
│   ├── functions/        # Edge Functions (Deno)
│   └── migrations/       # Database migrations
│
├── sqlite/               # SQLite database files (development)
│
└── docs/                 # Documentation
```

## Getting Help

- Review [Architecture](../architecture/README.md) for system design
- Check existing tests for patterns
- Open an issue for bugs or questions

## Related Documentation

- [Running Locally](../running-locally.md) - Detailed setup
- [Architecture](../architecture/README.md) - System design
- [API Specification](../../backend/openapi.yaml) - OpenAPI spec
- [Field Spec Schema](./field-spec-schema.md) - JSON5 regional spec format
- [Adding a Region](./adding-a-region.md) - Tutorial: add a new voter region
- [Matching Process](../architecture/matching-process.md) - Spec-driven matching pipeline
- [Testing Guide](./testing.md) - Approval tests and testing patterns

## Code Quality Tools

### Frontend Static Analysis (fallow)

[Fallow](https://github.com/fallow-rs/fallow) is a Rust-based static analyzer for TypeScript/JavaScript that finds unused code, duplication, and complexity hotspots. It runs in the `frontend/` directory.

```bash
cd frontend
npx fallow                  # Full analysis (dead code + dupes + complexity)
npx fallow dead-code        # Unused files, exports, dependencies
npx fallow dupes            # Code duplication detection
npx fallow health --score   # Complexity analysis with project health score
npx fallow audit --base main  # PR quality gate (pass/warn/fail)
```

Configuration: `frontend/.fallowrc.json` (see [fallow config docs](https://docs.fallow.tools/configuration/overview))

### Backend Quality (Python)

```bash
cd backend
uv run ruff check app/      # Lint
uv run ruff format app/     # Format
uv run basedpyright app/    # Type check
uv run vulture app/         # Dead code detection
```
