# Contributing to VoteCatcher

Thanks for your interest in contributing. This guide covers development setup, code standards, and the PR process.

## Development Setup

### Prerequisites

- [Python 3.12+](https://www.python.org/downloads/) (3.13 recommended)
- [uv](https://docs.astral.sh/uv/) — Python package manager
- [Bun](https://bun.sh/) — JavaScript runtime and package manager
- [Git](https://git-scm.com/)
- [just](https://github.com/casey/just) — Task runner
- Docker (optional, for PostgreSQL and containerized dev)

### Install Everything

```bash
git clone https://github.com/civictechdc/votecatcher
cd votecatcher
just install
```

### Configure Environment

```bash
cp backend/.env.example backend/.env.local
cp frontend/.env.example frontend/.env
```

For simulation mode (no API keys needed), set in `backend/.env.local`:

```env
DATABASE_URL=sqlite:///./dev.db
FEATURE_ENABLE_SIMULATION=1
```

### Start Development

**Two terminals:**

```bash
just dev-backend    # http://localhost:8080
just dev-frontend   # http://localhost:5173
```

**Or Docker Compose:**

```bash
just dev
```

## Code Standards

### Backend (Python)

| Tool | Command | Purpose |
|------|---------|---------|
| Ruff | `just lint-backend` | Linting and formatting |
| basedpyright | `just typecheck-backend` | Type checking |
| pytest | `just test-backend` | Unit tests |

**Standards:**
- Follow [PEP 8](https://peps.python.org/pep-0008/) (enforced by ruff)
- Type hints required on all public functions (enforced by basedpyright)
- Docstrings for public APIs
- Tests for new features and bug fixes

### Frontend (TypeScript/Svelte)

| Tool | Command | Purpose |
|------|---------|---------|
| oxlint | `just lint-frontend` | Linting |
| oxfmt | `just fmt:check` (in frontend/) | Formatting |
| svelte-check | `just typecheck-frontend` | Type checking |
| vitest + playwright | `just test-frontend` | Tests |

**Standards:**
- TypeScript strict mode
- Svelte 5 runes syntax (`$state`, `$derived`, `$effect`)
- Tailwind CSS for styling (no inline styles)
- Component tests for UI components
- E2E tests for critical flows

## Making Changes

### 1. Create a Branch

```bash
git checkout main
git pull origin main
git checkout -b feature/short-description
```

Branch naming:
- `feature/` — new features
- `fix/` — bug fixes
- `refactor/` — code refactoring
- `docs/` — documentation
- `ci/` — CI/CD changes

### 2. Make Changes

Keep changes focused. One logical change per PR.

### 3. Verify Locally

```bash
just lint
just typecheck
just test
```

Or simulate the full CI pipeline:

```bash
just ci-sim
```

### 4. Commit

Write clear, concise commit messages. Explain *why*, not just *what*.

```
fix(backend): handle empty voter file gracefully

Previously, uploading an empty CSV would crash the matching service.
Now returns a validation error to the client.
```

### 5. Push and Create PR

```bash
git push -u origin feature/short-description
```

Open a PR against `main`. Fill in the PR template.

## PR Process

### CI Checks

All PRs must pass these checks:

| Check | What it validates |
|-------|-------------------|
| `prepare` | Lockfile integrity, doc sync |
| `secrets-scan` | No leaked credentials |
| `backend-quality` | Lint, typecheck, tests, bandit, audit |
| `frontend-quality` | Lint, typecheck, tests, audit |
| `frontend-fallow` | Dead code and duplication analysis |
| `sast` | Static application security testing |
| `sca` | Dependency vulnerability scanning |
| `dast-smoke` | Runtime security testing |
| `docker-build` | Container build + Trivy scan |

### Review

- At least one approval required
- All CI checks must pass
- No merge conflicts

### After Merge

- Delete your branch
- Squash merges preferred for clean history

## Testing

### Backend Tests

```bash
just test-backend                  # Unit tests with coverage
just test-backend-integration      # Integration tests (needs PostgreSQL)
just security-test                 # Security-focused tests
```

### Frontend Tests

```bash
just test-frontend                 # Unit tests
cd frontend && bun run test:e2e    # E2E tests (needs running app)
```

### Database Tests

Integration tests require PostgreSQL. Start it with:

```bash
just dev-postgres
```

## Database Migrations

When changing SQLModel schemas:

```bash
just migrate-create msg="Add new table"
just migrate                      # Apply
just migrate-down                 # Rollback
```

## Getting Help

- **Slack:** Join the conversation in [#vote_catcher](https://civictechdc.slack.com/archives/C04U3D9AWER) on the [CivicTech DC Slack](https://www.civictechdc.org/)
- **Issues:** Open a [bug report](https://github.com/civictechdc/votecatcher/issues/new?template=bug_report.yml) or [feature request](https://github.com/civictechdc/votecatcher/issues/new?template=feature_request.yml)
- **Security:** Report vulnerabilities privately via [GitHub Security Advisories](https://github.com/civictechdc/votecatcher/security/advisories/new) — see [SECURITY.md](SECURITY.md)
- **Code of Conduct:** All participants must follow the [Code of Conduct](CODE_OF_CONDUCT.md)
- **Docs:** Check [docs/](docs/) for detailed documentation
- Run `just` to see all available commands
