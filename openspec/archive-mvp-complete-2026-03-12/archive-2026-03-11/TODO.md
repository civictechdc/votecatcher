# Votecatcher Implementation Tasks

**Generated from:** SPEC.md v1.0.0
**Last Updated:** 2026-03-08
**Timeline:** 4-6 weeks

---

## Legend

- `[ ]` Not started
- `[~]` In progress
- `[x]` Complete
- `[!]` Blocked

---

## Phase 0: Setup & Infrastructure (3-4 days)

### Entry Criteria
- [x] Repository cloned and accessible
- [x] Development machine meets prerequisites (Python 3.12+, Node 20+, Docker)
- [x] Access to at least one LLM provider API key

### Tasks

#### Backend Setup
- [x] Initialize FastAPI project structure with feature-based packages
- [x] Configure UV package manager (`pyproject.toml`)
- [x] Setup structlog for structured logging
- [x] Configure pytest + pytest-asyncio + pytest-cov
- [x] Setup Alembic for database migrations
- [x] Create Docker Compose for dev environment
- [x] Create Makefile or scripts for common commands

#### Frontend Setup
- [x] Initialize SvelteKit project with TypeScript
- [x] Configure Bun as package manager
- [x] Setup Tailwind CSS v4
- [x] Configure Vitest for unit tests
- [x] Configure Playwright for E2E tests
- [x] Create base component structure (`ui/`, `layout/`, etc.)

#### API Specification
- [x] Write OpenAPI 3.1 spec for all MVP endpoints
- [x] Validate spec with swagger-cli
- [x] Generate TypeScript client from spec
- [x] Integrate generated client into frontend

#### CI/CD
- [x] Create GitHub Actions workflow for PR checks
- [x] Add lint job (ruff for Python, oxlint for TypeScript)
- [x] Add typecheck job (basedpyright, tsc)
- [x] Add test job (pytest, vitest)
- [x] Configure pre-commit hooks

#### Security Scanning
- [x] Add Bandit to backend dev dependencies (pyproject.toml)
- [x] Add pip-audit to backend dev dependencies
- [x] Create `.github/workflows/security.yml` with security jobs
- [x] Add Gitleaks for secrets scanning
- [x] Configure Trivy for container scanning
- [ ] Enable Dependabot in repository settings (manual: GitHub UI)
- [x] Create `.secrets.baseline` for detect-secrets (if used)

#### Documentation
- [x] Create `docs/` directory structure
- [x] Write C4 Context diagram (`docs/architecture/c4-context.md`)
- [x] Write C4 Containers diagram (`docs/architecture/c4-containers.md`)
- [x] Create ADR template (`docs/architecture/decisions/template.md`)
- [x] Create ADR-0001: Record Architecture Decisions
- [x] Update README.md with documentation links

### Exit Criteria
```bash
# Backend
cd backend && uv run pytest tests/ -v
uv run ruff check .
uv run basedpyright

# Frontend
cd frontend-svelt && bun run test
bun run lint
bun run typecheck

# Security
uv run bandit -r app/
uv run pip-audit
cd frontend-svelt && bun audit

# Integration
docker-compose up -d
curl http://localhost:8000/health
curl http://localhost:5173
docker-compose down
```

### Sign-off
- [x] `docker-compose up` starts full stack without errors
- [x] OpenAPI spec validates
- [x] Generated TypeScript client compiles
- [ ] CI pipeline runs green on empty PR (requires GitHub PR to test)
- [x] Security scanning jobs configured in CI

---

## Phase 1: Data Layer (5-7 days)

### Entry Criteria
- [ ] Phase 0 exit criteria verified and signed off
- [ ] Database server accessible (PostgreSQL or SQLite)

### Tasks

#### Database Schema
- [ ] Create Alembic migration: `campaign`, `region`, `user` tables
- [ ] Create Alembic migration: `petition_scan`, `petition_crop` tables
- [ ] Create Alembic migration: `ocr_job`, `matcher_job` tables
- [ ] Create Alembic migration: `ocr_result`, `match_result` tables
- [ ] Create Alembic migration: `session` table
- [ ] Create Alembic migration: `registered_voters` table
- [ ] Add indexes for performance (see data-model.md)

#### SQLModel Definitions
- [ ] Define `Campaign`, `Region` models with relationships
- [ ] Define `PetitionScan`, `PetitionCrop` models
- [ ] Define `OcrJob`, `MatcherJob` models with status enums
- [ ] Define `OcrResult`, `MatchResult` models
- [ ] Define `Session` model
- [ ] Define `RegisteredVoter` model

#### Repository Layer
- [ ] Implement `CampaignRepository` with CRUD
- [ ] Implement `JobRepository` with status updates
- [ ] Implement `FileRepository` for metadata
- [ ] Write unit tests for all repositories (>90% coverage)

#### Documentation
- [ ] Create ERD diagram in Mermaid format (`docs/architecture/erd.md`)
- [ ] Document database schema decisions (if non-obvious) in ADR

### Exit Criteria
```bash
cd backend
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head
uv run pytest tests/unit/models/ -v
uv run pytest tests/unit/repositories/ -v
uv run pytest tests/integration/database/ -v
```

### Sign-off
- [ ] All migrations run forward without errors
- [ ] All migrations rollback cleanly
- [ ] Foreign key constraints enforced
- [ ] Repository tests achieve >90% coverage
- [ ] Can query all tables via repository methods

---

## Phase 2: Core Backend Services (7-10 days)

### Entry Criteria
- [ ] Phase 1 exit criteria verified and signed off
- [ ] At least one LLM provider API key configured

### Tasks

#### File Service
- [ ] Implement `FileService.upload_petition()` with validation
- [ ] Implement PDF cropping with pdf2image + Pillow
- [ ] Implement crop storage with correct naming convention
- [ ] Implement region-level voter list storage
- [ ] Write unit tests for FileService
- [ ] Write integration tests for upload flow

#### OCR Client Abstraction
- [ ] Define `OCRClient` abstract interface
- [ ] Implement `OpenAIClient` with batch API support
- [ ] Implement `GeminiClient` with batch API support
- [ ] Implement `MistralClient` with batch API support
- [ ] Write mock tests for each client
- [ ] Implement client factory pattern

#### OCR Service
- [ ] Implement `OCRService.create_job()`
- [ ] Implement batch submission logic
- [ ] Implement polling with FastAPI BackgroundTasks
- [ ] Implement result parsing and storage
- [ ] Handle partial failures (some crops fail)
- [ ] Write integration tests with mocked providers

#### Job Orchestrator
- [ ] Implement state machine for MatcherJob
- [ ] Implement phase coordination (OCR → Matching)
- [ ] Implement `JobService.start_job()`
- [ ] Implement error handling and retries
- [ ] Support re-running matching without re-running OCR
- [ ] Write unit tests for state transitions

#### Matching Service
- [ ] Implement voter list loading into memory
- [ ] Implement DB pre-filtering (region, zipcode)
- [ ] Implement RapidFuzz fuzzy matching
- [ ] Implement weighted similarity scoring (name 0.6, address 0.4)
- [ ] Implement top-5 ranking
- [ ] Implement confidence level assignment
- [ ] Store match results
- [ ] Write unit tests for matching algorithm

#### Confidence Calibration (Collaborative)
- [ ] Prepare test dataset (20-50 representative crops)
- [ ] Establish ground truth for test dataset
- [ ] Run initial matching with default thresholds
- [ ] **Collaborate with user:** Review results together
- [ ] Analyze false positives and false negatives
- [ ] Iterate on thresholds based on analysis
- [ ] Document final thresholds with rationale
- [ ] Record precision/recall metrics

#### SSE Implementation
- [ ] Implement `/api/jobs/{id}/status` SSE endpoint
- [ ] Implement connection manager
- [ ] Integrate SSE with BackgroundTasks
- [ ] Write SSE integration tests

#### Documentation
- [ ] Write C4 Components diagram for backend (`docs/architecture/c4-components.md`)
- [ ] Create ADR-0002: Use FastAPI BackgroundTasks
- [ ] Create ADR-0003: Use SSE for Real-time Updates
- [ ] Create ADR-0004: Hybrid Matching Strategy
- [ ] Document confidence calibration results
- [ ] Add sequence diagram for job orchestration flow

### Exit Criteria
```bash
uv run pytest tests/unit/services/ -v
uv run pytest tests/unit/ocr/ -v
uv run pytest tests/unit/matching/ -v
uv run pytest tests/integration/ocr/ -v
uv run pytest tests/integration/jobs/ -v
uv run pytest tests/integration/matching/ -v
uv run pytest tests/integration/sse/ -v
python -m app.cli create-test-job
python -m app.cli check-job-status 1
```

### Sign-off
- [ ] File upload creates crops correctly
- [ ] OCR clients return results (with mock or real API)
- [ ] Job orchestrator transitions through all states
- [ ] Matching produces top 5 predictions with scores
- [ ] SSE delivers real-time updates to connected client
- [ ] All service tests achieve >85% coverage
- [ ] **Confidence thresholds calibrated with user**

---

## Phase 3: Frontend Foundation (5-7 days)

### Entry Criteria
- [ ] Phase 2 exit criteria verified and signed off
- [ ] Backend API endpoints functional (can test with curl)

### Tasks

#### Base UI Components
- [ ] Build `Button.svelte` (variants, sizes, loading state)
- [ ] Build `Input.svelte` (validation, error states)
- [ ] Build `Select.svelte` (options, placeholder)
- [ ] Build `Table.svelte` (columns, sorting, pagination)
- [ ] Build `Card.svelte` (header, content, footer)
- [ ] Build `Modal.svelte` (open, close, confirm)
- [ ] Build `Toast.svelte` (success, error, warning)
- [ ] Build `Spinner.svelte` (sizes)
- [ ] Build `Badge.svelte` (variants for confidence levels)
- [ ] Build `Progress.svelte` (determinate, indeterminate)
- [ ] Build `EmptyState.svelte` (icon, message, action)
- [ ] Write unit tests for all components

#### Layout & Navigation
- [ ] Implement `Header.svelte` (logo, nav, user menu)
- [ ] Implement `Sidebar.svelte` (campaign selector, nav items)
- [ ] Implement `PageHeader.svelte` (title, breadcrumbs, actions)
- [ ] Setup route structure (workspace, campaigns, jobs, settings)
- [ ] Implement campaign selector dropdown
- [ ] Write E2E tests for navigation

#### Campaign Pages
- [ ] Campaign list page with pagination
- [ ] Campaign create form
- [ ] Campaign edit form
- [ ] Campaign detail page with stats
- [ ] Write E2E tests for campaign CRUD

#### Upload Pages
- [ ] File upload component with drag-and-drop
- [ ] Upload progress indicator
- [ ] Voter list upload page
- [ ] Petition upload page
- [ ] File list display
- [ ] Write E2E tests for upload

#### Job Status Page
- [ ] Job list page with filters
- [ ] Job status page layout
- [ ] SSE connection setup with EventSource
- [ ] Job progress visualization
- [ ] Job timeline component
- [ ] Reconnection logic for SSE
- [ ] Write E2E tests for job status

#### Svelte Stores
- [ ] Implement `campaignStore`
- [ ] Implement `jobStore` with SSE integration
- [ ] Implement `resultsStore`
- [ ] Implement `sessionStore`
- [ ] Implement `uiStore` (toasts, modals)
- [ ] Write unit tests for stores

#### Documentation
- [ ] Document frontend architecture decisions (if non-obvious) in ADR
- [ ] Update C4 diagrams if component structure changed

### Exit Criteria
```bash
bun run test tests/unit/components/ -v
bun run test tests/unit/stores/ -v
bun run test:e2e tests/e2e/campaign.spec.ts
bun run test:e2e tests/e2e/upload.spec.ts
bun run test:e2e tests/e2e/job-status.spec.ts
bun run build
bun run preview
```

### Sign-off
- [ ] All base components render correctly
- [ ] Navigation works between all pages
- [ ] Campaign create/edit/delete works in UI
- [ ] File upload shows progress and completes
- [ ] Job status page shows real-time updates via SSE
- [ ] Store state persists across navigation
- [ ] E2E tests for core flows pass

---

## Phase 4: Integration & E2E (5-7 days)

### Entry Criteria
- [ ] Phase 3 exit criteria verified and signed off
- [ ] Full backend stack running and accessible

### Tasks

#### Results Visualization
- [ ] Results table with pagination (25, 50, 100 per page)
- [ ] Confidence filter buttons (All, High, Medium, Low)
- [ ] Sortable columns (confidence, date)
- [ ] Crop image display with lazy loading
- [ ] Match detail expansion (top 5 alternatives)
- [ ] Side-by-side source/prediction comparison
- [ ] Write E2E tests for results table

#### Dashboard
- [ ] Confidence distribution chart (pie or bar)
- [ ] Progress bar toward goal
- [ ] Stats cards (total, high/medium/low)
- [ ] Recent jobs list
- [ ] Write E2E tests for dashboard

#### Session Management
- [ ] Session list page
- [ ] Save session functionality
- [ ] Load session (restore state)
- [ ] Session export as ZIP
- [ ] Session import from ZIP
- [ ] Write E2E tests for sessions

#### Demo Mode
- [ ] Feature flag system implementation
- [ ] Demo reset endpoint
- [ ] Demo reset UI button (behind feature flag)
- [ ] Pre-baked demo session in database
- [ ] Load pre-baked demo session
- [ ] Write E2E tests for demo mode

#### Full E2E Suite
- [ ] Test: Create campaign → Upload → Job → Results
- [ ] Test: Session save → load → verify
- [ ] Test: Demo reset → verify clean state
- [ ] API contract tests (frontend/backend integration)

#### Documentation
- [ ] Document session management approach in ADR
- [ ] Update diagrams if architecture changed
- [ ] Write API usage examples

### Exit Criteria
```bash
bun run test:e2e tests/e2e/results.spec.ts
bun run test:e2e tests/e2e/dashboard.spec.ts
bun run test:e2e tests/e2e/session.spec.ts
bun run test:e2e tests/e2e/demo.spec.ts
bun run test:e2e tests/e2e/full-flow.spec.ts
uv run pytest tests/integration/api_contract/ -v
```

### Sign-off
- [ ] Results table paginates and filters correctly
- [ ] Dashboard shows accurate metrics
- [ ] Session save/load preserves all state
- [ ] Session export creates valid ZIP file
- [ ] Demo mode resets all data
- [ ] Full E2E flow test passes
- [ ] API contract tests pass

---

## Phase 5: Polish & Demo (3-5 days)

### Entry Criteria
- [ ] Phase 4 exit criteria verified and signed off
- [ ] All MVP features implemented

### Tasks

#### Accessibility (WCAG 2.2 AA)
- [ ] Keyboard navigation audit and fixes
- [ ] Focus indicator styling
- [ ] ARIA labels on interactive elements
- [ ] Screen reader testing (NVDA or JAWS)
- [ ] Color contrast verification (4.5:1 for text)
- [ ] Skip links implementation
- [ ] Write accessibility E2E tests

#### Error Handling
- [ ] Implement RFC 7807 error responses in API
- [ ] Frontend error boundary components
- [ ] User-friendly error messages
- [ ] Retry mechanisms for failed operations
- [ ] Write error scenario tests

#### Performance
- [ ] Profile page load times
- [ ] Optimize bundle size (tree shaking)
- [ ] Image lazy loading verification
- [ ] API response time optimization if needed
- [ ] Run Lighthouse audit (target >80)

#### Documentation
- [ ] Write comprehensive README.md (setup, run, test)
- [ ] Write `docs/development/setup.md` (local development)
- [ ] Write `docs/development/testing.md` (testing strategy)
- [ ] Write `docs/deployment/vps-deployment.md` (deployment guide)
- [ ] Verify all documentation links work (markdown-link-check)
- [ ] Ensure all diagrams are current
- [ ] Update ADR index with all decisions

#### Demo Preparation
- [ ] Create pre-baked demo session with sample data
- [ ] Test demo flow end-to-end
- [ ] Prepare demo script/outline
- [ ] Record demo walkthrough video

### Exit Criteria
```bash
bun run test:a11y
npx axe-cli http://localhost:5173
bun run lighthouse http://localhost:5173
uv run pytest tests/integration/errors/ -v
markdown-link-check README.md
markdown-link-check docs/
```

### Sign-off
- [ ] Keyboard navigation works on all pages
- [ ] Screen reader testing complete
- [ ] Color contrast ratios meet WCAG AA
- [ ] All error states have user-friendly messages
- [ ] Page load < 2s, API response < 500ms
- [ ] README includes setup, run, deploy instructions
- [ ] Deployment guide tested on clean machine
- [ ] Demo walkthrough successful (recorded)
- [ ] Pre-baked demo session loads correctly

---

## Post-MVP: Frontend Promotion

### Validation Before Promotion
- [ ] All E2E tests pass
- [ ] All user stories from REQUIREMENTS.md validated
- [ ] Accessibility audit complete (WCAG 2.2 AA)
- [ ] Demo walkthrough successful
- [ ] No references to old frontend in codebase

### Tasks
- [ ] Archive/delete existing `frontend/` directory
- [ ] Rename `frontend-svelt/` to `frontend/`
- [ ] Update `docker-compose.yml` references
- [ ] Update CI/CD workflow references
- [ ] Update documentation references
- [ ] Update any hardcoded paths in scripts
- [ ] Verify all tests still pass after rename

---

## Progress Summary

| Phase | Status | Started | Completed | Notes |
|-------|--------|---------|-----------|-------|
| Phase 0 | Not Started | - | - | |
| Phase 1 | Not Started | - | - | |
| Phase 2 | Not Started | - | - | |
| Phase 3 | Not Started | - | - | |
| Phase 4 | Not Started | - | - | |
| Phase 5 | Not Started | - | - | |

---

## Blockers Log

| Date | Phase | Task | Blocker | Resolution |
|------|-------|------|---------|------------|
| | | | | |

---

## Notes

- Mark tasks `[~]` when starting, `[x]` when complete
- Update Progress Summary when changing phases
- Log blockers immediately with date and details
- Run exit criteria commands before marking phase complete
- Get user sign-off on confidence calibration (Phase 2)
- Update documentation alongside implementation (not at the end)
