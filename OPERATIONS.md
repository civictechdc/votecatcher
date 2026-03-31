# VoteCatcher Operations Guide

This document provides operational guidance for the VoteCatcher project, including current status, development workflows, and CI/CD practices.

## Current Status

**Phase Status:**
- ✅ Phase 1: Stability - Worker tests, metrics API, error handling
- ✅ Phase 2: Polish - Keyboard nav, E2E tests, documentation
- ✅ Phase 3: Page Hierarchy - Route restructure, campaign scoping
- ✅ Phase 4: Stretch - LLM config UI, provider selection on job creation

**MVP Status:** Complete
- Backend API: Fully functional with comprehensive test coverage
- Frontend: SvelteKit application with responsive design
- Database: PostgreSQL/SQLite support with migrations
- OCR Integration: Multi-provider LLM batch processing
- Real-time Updates: SSE-based job status updates
- Security: Row-level security, encrypted API keys, input validation

## Development Environment

### DevContainer Setup

VoteCatcher uses VS Code DevContainers for consistent development environments. The devcontainer includes:

- **Python 3.13**: Backend development with FastAPI and SQLModel
- **Bun**: Fast JavaScript runtime for frontend development
- **Go**: For security tools and utilities (nuclei, etc.)
- **PostgreSQL**: Development database with persistent volumes
- **just**: Task runner for consistent commands across environments
- **Common utilities**: git, curl, jq, and other essential tools

### Quick Start with DevContainer

1. Open the project in VS Code
2. When prompted, reopen in DevContainer
3. Wait for postCreateCommand to complete (installs dependencies via justfile)
4. Start development servers:
   - Backend: `just dev-backend`
   - Frontend: `just dev-frontend`

### Manual Setup

If not using DevContainer, follow the [Quick Start](README.md#quick-start) guide.

## Task Runner (just)

This project uses `just` as the primary task runner. All commands are defined in the `justfile`.

### Common Commands

```bash
# Install all dependencies
just install

# Run all tests
just test

# Run linters
just lint

# Run type checkers
just typecheck

# Start development database
just dev-postgres

# Simulate full CI pipeline locally
just ci-sim
```

### Security Commands

```bash
# Run all security scans
just security-scan

# Backend security (bandit, pip-audit)
just security-scan-backend

# Frontend security (bun audit)
just security-scan-frontend

# Run security tests
just security-test
```

### Database Commands

```bash
# Run migrations
just migrate

# Create new migration
just migrate-create msg="description"

# Reset database
just db-reset
```

## CI/CD Pipeline

### GitHub Actions

The project uses GitHub Actions for continuous integration and deployment:

#### Main Workflows

1. **CI** (`.github/workflows/ci.yml`)
   - Runs on every push and pull request to main
   - Lockfile integrity checks
   - Backend lint, typecheck, and tests
   - Frontend lint, typecheck, and tests
   - Security scans and tests
   - Docker builds

2. **Security** (`.github/workflows/security.yml`)
   - Runs on push, PR, and daily schedule
   - Backend and frontend security scans
   - Secrets scanning (gitleaks)
   - SAST (semgrep)
   - SCA (osv-scanner, trivy)
   - Container scanning (trivy)
   - DAST (nuclei) - daily schedule only

3. **Code Quality** (`.github/workflows/code-quality.yml`)
   - Code duplication analysis
   - Complexity analysis
   - Dead code detection

### CI Simulation

To simulate the full CI pipeline locally:

```bash
just ci-sim
```

This runs:
1. Lockfile integrity checks
2. Backend lint, typecheck, and tests
3. Frontend lint, typecheck, and tests
4. Security scans
5. Docker lint

## Testing Strategy

### Backend Tests

- **Unit Tests**: Fast, isolated tests for business logic
- **Integration Tests**: Tests requiring database connections
- **Security Tests**: Tests for security vulnerabilities
- **Benchmark Tests**: Performance benchmarks

Run with:
```bash
just test-backend
just test-backend-integration
just security-test
just benchmark
```

### Frontend Tests

- **Unit Tests**: Component tests with vitest
- **E2E Tests**: End-to-end tests with Playwright

Run with:
```bash
just test-frontend
bun run test:e2e
```

### Test Coverage

Backend test coverage is automatically reported to Codecov. Aim for >80% coverage on critical paths.

## Security Practices

### Automated Security Scanning

1. **SAST**: Static Application Security Testing (semgrep)
   - Runs on every PR
   - OWASP Top 10, FastAPI, JWT, XSS patterns

2. **SCA**: Software Composition Analysis
   - Dependency vulnerability scanning (osv-scanner, trivy)
   - License compliance checks

3. **DAST**: Dynamic Application Security Testing (nuclei)
   - Runs daily on schedule
   - Scans production endpoints

4. **Container Scanning**: (trivy)
   - Scans Docker images for vulnerabilities
   - Fails on CRITICAL/HIGH severity

### Security Tests

Security tests verify:
- JWT token validation and expiration
- Authentication and authorization
- Input validation and sanitization
- SQL injection prevention
- XSS prevention
- CORS configuration

### Manual Security Review

Before merging features:
1. Review security test results
2. Check for sensitive data in logs
3. Verify API key encryption
4. Test with security tools (just security-scan)

## Deployment

### Production Deployment

See [Deployment Guide](docs/deployment/) for production deployment instructions.

### Database Migrations

Always test migrations locally before running in production:

```bash
# Create migration
just migrate-create msg="description"

# Test locally
just db-reset

# Run in production
just migrate
```

## Troubleshooting

### Common Issues

#### DevContainer won't start

1. Check Docker is running: `docker ps`
2. Rebuild the container: `F5` in VS Code → "Rebuild Container"
3. Check logs: `docker-compose logs`

#### Tests fail locally but pass in CI

1. Check Python version (must be 3.13)
2. Ensure all dependencies installed: `just install`
3. Check environment variables in `.env.local`
4. Clear caches: `just clean`

#### PostgreSQL connection issues

1. Check container is running: `docker ps`
2. Check logs: `docker logs votecatcher_db_1`
3. Reset database: `just db-reset`

#### Lockfile integrity fails

1. Backend: `cd backend && uv lock --check`
2. Frontend: `cd frontend-svelt && bun install --frozen-lockfile`
3. If mismatched, regenerate:
   - Backend: `cd backend && uv lock`
   - Frontend: `cd frontend-svelt && bun install && bun install --frozen-lockfile`

## Project Structure

```
votecatcher/
├── backend/                    # FastAPI backend
│   ├── app/                    # Application code
│   ├── tests/                  # Test suites
│   ├── alembic/                # Database migrations
│   ├── Dockerfile              # Backend Docker image
│   └── uv.lock                 # Python lockfile
│
├── frontend-svelt/             # SvelteKit frontend
│   ├── src/                    # Source code
│   ├── tests/                  # Test suites
│   ├── Dockerfile              # Frontend Docker image
│   └── bun.lock                # JavaScript lockfile
│
├── .devcontainer/              # DevContainer configuration
│   ├── devcontainer.json       # VS Code DevContainer spec
│   └── setup.sh                # Setup script
│
├── .github/workflows/          # CI/CD workflows
│   ├── ci.yml                 # Main CI pipeline
│   ├── security.yml           # Security scanning
│   └── code-quality.yml       # Code quality checks
│
├── docs/                       # Documentation
│   ├── architecture/           # Architecture diagrams
│   ├── deployment/            # Deployment guides
│   └── running-locally.md      # Local development guide
│
├── justfile                   # Task runner recipes
├── docker-compose.yml         # Development services
└── README.md                  # Project README
```

## Contributing

1. Fork and create a feature branch
2. Make changes with tests
3. Run `just ci-sim` to verify all checks pass
4. Submit a pull request

All contributions must pass:
- Lint checks
- Type checks
- Tests
- Security scans
- Docker builds

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/civictechdc/votecatcher/issues)
- **Discussions**: [GitHub Discussions](https://github.com/civictechdc/votecatcher/discussions)

## License

This project is open source. See [LICENSE](LICENSE) for details.
