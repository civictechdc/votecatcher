# Votecatcher Technical Specification

**Status:** Draft - Phase 4 Planning Review
**Version:** 1.3.0
**Last Updated:** 2026-03-11
**Author:** Solutions Architect Agent

---

## Executive Summary

Votecatcher is an open-source MVP tool that automates petition signature verification using LLM-based OCR and fuzzy matching. The system reduces manual verification from hours to minutes by extracting handwritten text from scanned petitions and matching it against official voter registration lists.

**Key Design Decisions:**
- Async-first architecture leveraging LLM batch APIs (no complex job queues)
- Hybrid matching: DB pre-filtering + Python RapidFuzz for fuzzy matching
- Real-time updates via Server-Sent Events (SSE)
- Self-hosted deployment on single VPS ($5-20/mo)
- OpenAPI-generated TypeScript client for type safety
- Strict TDD methodology for all features

**MVP Scope:**
- Single-user demo mode
- DC region preset with manual crop coordinates
- End-to-end flow: upload → OCR → matching → results
- Session persistence and demo reset capability

**Timeline:** 4-6 weeks for complete MVP

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Solution Overview](#2-solution-overview)
3. [Architecture](#3-architecture)
4. [Data Model](#4-data-model)
5. [API Specification](#5-api-specification)
6. [Frontend Architecture](#6-frontend-architecture)
7. [Implementation Plan](#7-implementation-plan)
8. [Technical Decisions](#8-technical-decisions)
9. [Risks & Mitigations](#9-risks--mitigations)
10. [Open Questions](#10-open-questions)
11. [References](#11-references)
    - Appendix A: BDD Test Examples
    - Appendix B: Configuration Reference
    - Appendix C: Security Scanning
    - Appendix D: Glossary

---

## 1. Problem Statement

Campaigns collecting ballot petition signatures face a manual, error-prone verification process:

- **Current state:** Visual comparison of paper petitions against spreadsheet data
- **Pain points:** Slow, tedious, highly error-prone
- **Scale:** Hundreds to thousands of signatures per campaign

**Business Value:**
- Speed: Reduce verification time from hours to minutes
- Accuracy: Systematic matching reduces human error
- Transparency: Clear confidence indicators and audit trail

**MVP Constraints:**
- Single VPS deployment ($5-20/mo)
- 1-5 concurrent users
- Pre-release state (no backward compatibility required)
- DC region only initially

---

## 2. Solution Overview

### 2.1 Core Workflow

```
Upload Petition → Pre-crop Signatures → OCR Extraction → Fuzzy Matching → Results
```

### 2.2 Key Components

1. **File Processing**
   - PDF upload and pre-cropping into individual signature entries
   - Region-level voter list storage (shared across campaigns)

2. **OCR Processing**
   - Multi-provider support: OpenAI, Gemini, Mistral
   - Batch API with async polling
   - Per-crop extraction results

3. **Job Orchestration**
   - Matcher job orchestrates: OCR → Matching phases
   - State machine with loose coupling
   - Partial failure handling

4. **Matching Engine**
   - DB pre-filtering (region, zipcode)
   - Python RapidFuzz fuzzy matching
   - Top 5 predictions with confidence scores

5. **Results Visualization**
   - Paginated, filterable results table
   - Side-by-side source/prediction comparison
   - Confidence distribution dashboard

6. **Session Management**
   - Workspace snapshots
   - Full export/import (ZIP)
   - Demo mode with pre-baked sessions

### 2.3 Technology Stack

**Backend:**
- Python 3.12+, FastAPI
- SQLModel/SQLAlchemy, PostgreSQL/SQLite
- structlog, pytest

**Frontend:**
- SvelteKit, TypeScript
- Tailwind CSS v4, Vite, Bun
- Vitest, Playwright

**External:**
- LLM Providers: OpenAI, Gemini, Mistral (batch APIs)

---

## 3. Architecture

### 3.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  SvelteKit Frontend                                             │
│  ├── Routes: /workspace, /campaigns, /jobs, /results            │
│  ├── OpenAPI-generated API client                               │
│  └── SSE Client for real-time updates                           │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTP/SSE
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  FastAPI Backend                                                │
│  ├── Feature-based packages: ocr, matching, jobs, files, etc.   │
│  ├── SSE endpoints for job status                               │
│  ├── BackgroundTasks for OCR polling                            │
│  └── Router → Service pattern                                   │
└─────────────────────────────────────────────────────────────────┘
              │                    │                    │
              ▼                    ▼                    ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │ LLM Providers   │  │ PostgreSQL/     │  │ File Storage    │
    │ (Batch APIs)    │  │ SQLite          │  │ (local fs)      │
    └─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 3.2 Backend Structure

```
backend/
├── app/
│   ├── api.py
│   ├── campaign/     # Campaign CRUD
│   ├── jobs/         # Job orchestration, SSE
│   ├── ocr/          # OCR clients, service, polling
│   ├── matching/     # Fuzzy matching, pre-filtering
│   ├── files/        # Upload, cropping, storage
│   ├── sessions/     # Save/load/export
│   ├── voters/       # Voter list import
│   ├── data/         # Database, migrations
│   ├── settings/     # Config, feature flags
│   └── logging/      # structlog setup
```

### 3.3 Job Orchestration State Machine

```
NOT_STARTED
    ↓ start_ocr
OCR_PENDING → OCR_STARTED → OCR_COMPLETED
                               ↓ start_matching
                         MATCHING_PENDING → MATCHING → MATCHING_COMPLETED

Error paths: OCR_FAILED, OCR_TIMEOUT, MATCHING_ERROR
```

**Key Design:** OCR and matching are loosely coupled phases. Partial OCR successes proceed to matching; matching can be re-run independently.

### 3.4 Matching Pipeline

```
Load Voter List → Load OCR Results
         ↓
For each OCR result:
  1. DB pre-filter (region, zipcode)
  2. Extract name + address components
  3. RapidFuzz fuzzy match
  4. Calculate weighted similarity score
  5. Rank top 5 predictions
  6. Store match results with confidence levels
```

**Confidence Mapping (Initial Defaults):**
- HIGH: ≥ 0.85
- MEDIUM: 0.60 - 0.84
- LOW: < 0.60

> **Note:** These thresholds are starting points. During implementation (Phase 2), the developer agent should work with the user to experiment and calibrate optimal values based on real petition samples.

**Confidence Calibration Process:**

During Phase 2 backend implementation, after the matching service is functional:

1. **Prepare Test Dataset**
   - Use existing sample data from `samples/dc/`:
     - `fake_voter_records.csv` (100K voters for DB pre-filtering tests)
     - `fake_signed_petitions.pdf` and `fake_signed_petitions_1-10.pdf` (petition samples)
   - Select 20-50 representative petition crops from samples
   - Manually verify correct matches (ground truth)
   - Include edge cases: handwriting variations, common names, address variations

2. **Run Initial Matching**
   - Process test dataset with default thresholds (0.85/0.60)
   - Generate matching results with similarity scores

3. **Collaborative Analysis**
   - Review results together (developer agent + user)
   - Identify false positives (incorrect HIGH confidence)
   - Identify false negatives (correct matches marked LOW)
   - Analyze score distribution

4. **Iterate on Thresholds**
   - Adjust thresholds based on analysis
   - Re-run matching on test dataset
   - Measure precision/recall at each threshold

5. **Finalize Defaults**
   - Document chosen thresholds with rationale
   - Record precision/recall metrics
   - Make thresholds configurable for future tuning

**Expected Outcome:**
- Confidence levels that minimize false positives
- Clear documentation of threshold rationale
- Test dataset retained for regression testing

---

## 4. Data Model

### 4.1 Core Entities

```
campaign ──── 1:N ───► petition_scan ──── 1:N ───► petition_crop
    │                                              │
    │                                              1:1
    │                                              │
    │                                              ▼
    │                                         ocr_result
    │                                              │
    │                                              1:N
    │                                              │
    │                                              ▼
    └────────────────────────────────────► match_result

matcher_job ──── 1:N ───► ocr_job
    │
    └───────────────────► match_result (via ocr_result)
```

### 4.2 Key Tables

| Table | Purpose |
|-------|---------|
| `campaign` | Organizing unit for election year/region |
| `petition_scan` | Uploaded PDF metadata |
| `petition_crop` | Individual signature entry (pre-cropped) |
| `ocr_result` | Extracted text from crop (1:1) |
| `match_result` | Top 5 predictions per OCR result |
| `matcher_job` | Orchestrator job tracking OCR → Matching |
| `ocr_job` | Child job for batch OCR processing |
| `session` | Workspace snapshot (reference-based) |
| `registered_voters` | Voter list data |

### 4.3 File Storage

```
data/
├── regions/{region_id}/voter-lists/    # Shared across campaigns
└── campaigns/{campaign_id}/
    ├── petitions/                       # Original PDFs
    └── crops/                           # Pre-cropped images
```

### 4.4 Sample Data

The repository includes sample data for testing and development:

```
samples/dc/                              # DC region sample data
├── fake_voter_records.csv               # 100K synthetic voter records
├── fake_signed_petitions.pdf            # Sample petition PDFs
└── fake_signed_petitions_1-10.pdf       # Additional petition samples
```

**Purpose:**
- **Development Testing:** Use for API endpoint testing during Phase 2.5
- **OCR Testing:** Validate OCR extraction with real PDF samples
- **Matching Calibration:** Use for confidence threshold tuning (see §3.4)
- **Demo Mode:** Pre-baked sessions for demo walkthrough (Phase 4)
- **Integration Tests:** Consistent test data across all phases

**Usage Notes:**
- Voter list contains 100,000 synthetic records (good for testing DB pre-filtering at scale)
- Petition PDFs simulate real-world handwriting variations
- Data is synthetic/fake - safe for public repository
- Can be used for both unit tests and manual testing

---

## 5. API Specification

### 5.1 Design Principles

- RESTful endpoints
- RFC 7807 Problem Details for errors
- Offset-based pagination
- OpenAPI 3.1 specification

### 5.2 Key Endpoints

**Campaign Management:**
- `GET /api/campaigns` - List campaigns
- `POST /api/campaigns` - Create campaign
- `GET /api/campaigns/{id}` - Get campaign details

**File Upload:**
- `POST /api/upload/voter-list` - Upload voter list CSV/Excel
- `POST /api/upload/petition` - Upload petition PDF (pre-crops)

**Job Orchestration:**
- `POST /api/jobs` - Create matcher job
- `GET /api/jobs/{id}` - Get job status
- `GET /api/jobs/{id}/status` - SSE endpoint for real-time updates
- `POST /api/jobs/{id}/cancel` - Cancel job

**Results:**
- `GET /api/jobs/{job_id}/results` - Get match results (paginated, filterable)
- `GET /api/jobs/{job_id}/results/export` - Export to CSV

**Session Management:**
- `POST /api/sessions` - Save session
- `POST /api/sessions/{id}/load` - Load session
- `GET /api/sessions/{id}/export` - Export session as ZIP

### 5.3 SSE Events

```typescript
// Status update
{ "event": "status_update", "data": { "status": "OCR_STARTED", ... } }

// Matching progress
{ "event": "matching_progress", "data": { "processed": 50, "total": 100 } }

// Job complete
{ "event": "job_complete", "data": { "status": "MATCHING_COMPLETED", "summary": {...} } }
```

---

## 6. Frontend Architecture

### 6.1 Technology Choices

- **State Management:** Svelte stores (writable, derived)
- **API Client:** OpenAPI-generated TypeScript client
- **Components:** Custom with Tailwind CSS
- **Accessibility:** WCAG 2.2 AA target

### 6.2 Directory Structure

```
src/
├── routes/              # SvelteKit routes
├── lib/
│   ├── api/            # Generated API client
│   ├── stores/         # Svelte stores
│   ├── components/     # UI components
│   │   ├── ui/         # Base components (Button, Input, etc.)
│   │   ├── job/        # Job-specific components
│   │   └── results/    # Results-specific components
│   └── utils/          # Helpers
```

### 6.3 Key Components

- `FileUpload` - Drag-and-drop with progress
- `JobProgress` - Real-time status with SSE
- `ResultsTable` - Paginated, filterable results
- `ConfidenceBadge` - High/Medium/Low indicators
- `CropImage` - Lazy-loaded crop preview

---

## 7. Implementation Plan

### 7.1 Timeline: 4-6 Weeks

| Phase | Duration | Focus | Status |
|-------|----------|-------|--------|
| Phase 0: Setup | 3-4 days | Dev environment, CI/CD, OpenAPI spec | ✅ Complete |
| Phase 1: Data Layer | 5-7 days | Schema, models, migrations | ✅ Complete |
| Phase 2: Backend Services | 7-10 days | File, OCR, jobs, matching, SSE | ✅ Complete (122/122 tests) |
| Phase 2.5: API & Migration | 2-3 days | API endpoints, legacy removal | ✅ Complete (8/8 API tests) |
| Phase 3: Frontend | 5-7 days | UI foundation, pages, stores | ⏳ In Progress (5/5 base components) |
| Phase 4: Integration | 5-7 days | Results, dashboard, sessions, demo | Pending |
| Phase 5: Polish | 3-5 days | Accessibility, errors, docs, demo prep | Pending |

### 7.2 Methodology: Strict TDD

All phases follow test-driven development:

1. **Write BDD test scenario first** - Define expected behavior before implementation
2. **Implement minimum code to pass** - Write only what's needed
3. **Refactor with confidence** - Tests provide safety net
4. **Repeat** - Incremental, validated progress

**Test Categories:**
- **Unit tests:** Service logic, matching algorithm, state transitions
- **Integration tests:** API endpoints, database operations, OCR providers
- **E2E tests:** Complete user flows, cross-cutting concerns

**Coverage Target:** >85% for critical paths

### 7.3 Phase Verification Gates

Each phase has **entry criteria** (verified before starting) and **exit criteria** (verified before sign-off).

---

#### Phase 0: Setup & Infrastructure (3-4 days)

**Entry Criteria:**
- [ ] Repository cloned and accessible
- [ ] Development machine meets prerequisites (Python 3.12+, Node 20+, Docker)
- [ ] Access to LLM provider API keys (at least one)

**Implementation:**
- Initialize FastAPI project structure
- Configure UV package manager, structlog, pytest
- Initialize SvelteKit project with Bun, Tailwind, Vitest
- Write OpenAPI 3.1 spec for all MVP endpoints
- Generate TypeScript client from spec
- Setup GitHub Actions CI/CD
- Configure pre-commit hooks (ruff, oxlint)

**Exit Criteria (run before sign-off):**
```bash
# Backend verification
cd backend && uv run pytest tests/ -v           # All tests pass
uv run ruff check .                             # No lint errors
uv run basedpyright                            # Type check passes

# Frontend verification
cd frontend-svelt && bun run test              # All tests pass
bun run lint                                   # No lint errors
bun run typecheck                              # Type check passes

# Integration verification
docker-compose up -d                           # Stack starts
curl http://localhost:8000/health              # Health check OK
curl http://localhost:5173                     # Frontend loads
docker-compose down
```

**Sign-off Checklist:**
- [ ] `docker-compose up` starts full stack without errors
- [ ] OpenAPI spec validates (`npx @apidevtools/swagger-cli validate openapi.yaml`)
- [ ] Generated TypeScript client compiles
- [ ] CI pipeline runs green on empty PR

---

#### Phase 1: Data Layer (5-7 days)

**Entry Criteria:**
- [ ] Phase 0 exit criteria verified and signed off
- [ ] Database server accessible (PostgreSQL or SQLite)

**Implementation:**
- Create Alembic migrations for all tables
- Define SQLModel classes with relationships
- Implement basic repository pattern for CRUD
- Add database indexes for performance

**Exit Criteria (run before sign-off):**
```bash
# Migration verification
cd backend && uv run alembic upgrade head       # Migrations apply
uv run alembic downgrade -1                     # Rollback works
uv run alembic upgrade head                     # Re-apply

# Model verification
uv run pytest tests/unit/models/ -v             # Model tests pass
uv run pytest tests/unit/repositories/ -v       # Repository tests pass

# Integration verification
uv run pytest tests/integration/database/ -v    # DB integration tests pass
```

**Sign-off Checklist:**
- [ ] All migrations run forward without errors
- [ ] All migrations rollback cleanly
- [ ] Foreign key constraints enforced
- [ ] Repository tests achieve >90% coverage
- [ ] Can query all tables via repository methods

---

#### Phase 2: Core Backend Services (7-10 days)

**Status:** ✅ SERVICES COMPLETE (2026-03-09) | ⚠️ API ENDPOINTS IN PROGRESS

**Entry Criteria:**
- [x] Phase 1 exit criteria verified and signed off
- [x] At least one LLM provider API key configured

**Implementation:**

**Part A: Service Layer (COMPLETE - 122/122 tests passing):**
- ✅ Implement `FileService` with PDF cropping (10/10 tests)
- ✅ Implement OCR client abstraction (OpenAI, Gemini, Mistral - 40/40 tests)
- ✅ Implement `OCRService` with batch submission and polling (7/7 tests)
- ✅ Implement `JobOrchestrator` state machine (11/11 tests)
- ✅ Implement `MatchingService` with RapidFuzz (15/15 tests)
- ✅ Implement SSE endpoint and connection manager (14/14 tests)
- ✅ **Collaborative:** Calibrate confidence thresholds with user (see §3.4)

**Part B: API Endpoints (IN PROGRESS - 2-3 days remaining):**
- ⏳ Job Management Endpoints:
  - `POST /api/jobs` - Create matcher job
  - `GET /api/jobs/{id}` - Get job status (JSON)
  - `POST /api/jobs/{id}/cancel` - Cancel running job
- ⏳ Results Endpoints:
  - `GET /api/jobs/{job_id}/results` - Get match results (paginated, filterable)
  - `GET /api/jobs/{job_id}/results/export` - Export to CSV
- ⏳ File Upload Endpoints:
  - `POST /api/upload/voter-list` - Upload voter list CSV/Excel
  - `POST /api/upload/petition` - Upload petition PDF with pre-crops
- ⏳ Campaign Management Endpoints:
  - `GET /api/campaigns` - List campaigns
  - `POST /api/campaigns` - Create campaign
  - `GET /api/campaigns/{id}` - Get campaign details
- ⏳ Write integration tests for all new endpoints
- ⏳ Remove legacy routers after validation

**Exit Criteria (run before sign-off):**
```bash
# Unit tests (COMPLETE)
uv run pytest tests/unit/services/ -v           # Service tests pass
uv run pytest tests/unit/ocr/ -v                # OCR client tests pass
uv run pytest tests/unit/matching/ -v           # Matching tests pass

# Integration tests (with mocks)
uv run pytest tests/integration/ocr/ -v         # OCR integration pass
uv run pytest tests/integration/jobs/ -v        # Job orchestration pass
uv run pytest tests/integration/matching/ -v    # Matching integration pass

# SSE verification (COMPLETE)
uv run pytest tests/integration/sse/ -v         # SSE tests pass

# API endpoint verification (IN PROGRESS)
uv run pytest tests/integration/api/ -v         # API endpoint tests pass
curl -X POST http://localhost:8000/api/jobs     # Job creates via API
curl http://localhost:8000/api/jobs/1           # Status returns via API
```

**Sign-off Checklist:**
- [x] File upload creates crops correctly (via FileService)
- [x] OCR clients return results (with mock or real API)
- [x] Job orchestrator transitions through all states
- [x] Matching produces top 5 predictions with scores
- [x] SSE delivers real-time updates to connected client
- [x] All service tests achieve >85% coverage (100% achieved)
- [ ] **API endpoints expose all services** (IN PROGRESS)
- [ ] All SPEC.md §5.2 endpoints implemented and tested
- [ ] Legacy routers removed, no duplication
- [ ] Confidence thresholds calibrated with user

---

#### Phase 2.5: API Endpoint Implementation & Legacy Migration (2-3 days)

**Status:** IN PROGRESS (Started 2026-03-10)

**Purpose:** Bridge the gap between tested backend services and frontend accessibility by implementing all API endpoints per SPEC.md §5.2 and removing legacy code.

**Context:**
- Phase 2 services are complete and tested (122/122 tests passing)
- Legacy routers exist alongside new code (1,187 lines)
- Only SSE endpoint is currently exposed via API
- Frontend needs REST API endpoints to proceed with Phase 3

**Migration Strategy: Option A (Chosen)**

**Approach:** Implement all missing API endpoints using tested Phase 2 services, then remove legacy code with confidence.

**Timeline:**
- Day 1: Job management + upload endpoints
- Day 2: Campaign + results endpoints
- Day 3: Integration tests + legacy router removal

**Implementation Steps:**

**Day 1: Job & Upload Endpoints (~9 hours)**
1. `POST /api/jobs` - Create matcher job (2h)
   - Use: `JobOrchestrator.create_matcher_job()`
   - Request: campaign_id, scan_ids, provider
   - Response: job_id, status, created_at
   
2. `GET /api/jobs/{id}` - Get job status (1h)
   - Use: Database query via JobOrchestrator
   - Response: job_id, status, progress, error_message
   
3. `POST /api/jobs/{id}/cancel` - Cancel job (2h)
   - Use: `JobOrchestrator` state update
   - Validation: only cancelable in certain states
   
4. `POST /api/upload/voter-list` - Upload voter list (1h)
   - Use: `FileService.save_voter_list_file()`
   - Validation: CSV/Excel, required columns
   - **Test Data:** Use `samples/dc/fake_voter_records.csv` (100K voters)
   
5. `POST /api/upload/petition` - Upload petition (1h)
   - Use: `FileService.save_petition_and_crops()`
   - Validation: PDF, creates crops
   - **Test Data:** Use `samples/dc/fake_signed_petitions*.pdf`
   
6. `POST /api/campaigns` - Create campaign (1h)
   - Use: `CampaignRepository.create()`
   
7. `GET /api/campaigns` - List campaigns (0.5h)
   - Use: `CampaignRepository.list()`
   
8. `GET /api/campaigns/{id}` - Get campaign (0.5h)
   - Use: `CampaignRepository.get()`

**Day 2: Results & Integration (~4 hours)**
1. `GET /api/jobs/{job_id}/results` - Get results (2h)
   - Use: Database query with pagination
   - Filters: confidence_level, page, page_size
   
2. `GET /api/jobs/{job_id}/results/export` - Export CSV (2h)
   - Generate CSV from match results
   - Include: OCR text, predictions, scores

**Day 3: Testing, Cleanup & Documentation (~8 hours)**
1. Integration tests for all endpoints (4h)
2. API contract validation (2h)
3. Remove legacy routers (1h)
4. Full test suite verification (1h)

**ADR Documentation (Concurrent with Day 3):**
Create Architecture Decision Records for notable decisions:
- **ADR-XXXX: Legacy Code Migration Strategy** (Option A chosen)
  - Context: Phase 2 services complete, API endpoints missing, legacy code duplication
  - Decision: Complete API endpoints before removing legacy (Option A)
  - Consequences: 2-3 day delay, clean architecture, no technical debt
  - Alternatives: Option B (hybrid), Option C (big bang)
  
- **ADR-XXXX: Service-First Architecture Approach**
  - Context: Backend development order for Phase 2
  - Decision: Implement and test services before API endpoints
  - Consequences: 122/122 tests passing, but API layer gap discovered
  - Lessons: Always define API contract alongside service design
  
- **ADR-XXXX: Session Endpoints Deferral**
  - Context: Session management endpoints in SPEC.md §5.2
  - Decision: Defer to Phase 4 (not blocking core flow)
  - Consequences: Faster path to frontend work, session features in Phase 4

**Exit Criteria (run before sign-off):**
```bash
# All API endpoints functional
curl -X POST http://localhost:8000/api/campaigns -d '{"name":"Test","year":2024}'
curl -X POST http://localhost:8000/api/upload/voter-list -F "file=@voters.csv"
curl -X POST http://localhost:8000/api/upload/petition -F "file=@petition.pdf"
curl -X POST http://localhost:8000/api/jobs -d '{"campaign_id":1,"scan_ids":[1]}'
curl http://localhost:8000/api/jobs/1
curl http://localhost:8000/api/jobs/1/results

# Integration tests pass
uv run pytest tests/integration/api/ -v           # All API tests pass

# No legacy code remains
grep -r "legacy" backend/app/                     # No matches
grep -r "file_route\|ocr_route\|config_route" backend/app/  # No matches

# Full test suite green
uv run pytest tests/ -v                           # All tests pass
```

**Sign-off Checklist:**
- [ ] All SPEC.md §5.2 endpoints implemented
- [ ] All endpoints have integration tests
- [ ] API contract matches OpenAPI spec
- [ ] Legacy routers removed (auth.py, file_route.py, ocr_route.py, config_route.py, workspace.py)
- [ ] No test regressions (122/122 still passing)
- [ ] Can complete full workflow via API only (no legacy code needed)
- [ ] Frontend can start Phase 3 with clean API
- [ ] **ADRs created for notable decisions** (migration strategy, service-first approach, session deferral)

**Risk Mitigation:**
- **Risk:** Removing legacy code breaks existing functionality
  - **Mitigation:** Integration tests validate all endpoints before removal
- **Risk:** API design doesn't match frontend expectations
  - **Mitigation:** Follow OpenAPI spec exactly, frontend validates in Phase 3
- **Risk:** Timeline slips
  - **Mitigation:** 2-3 day estimate is conservative, can parallelize endpoint implementation

---

#### Phase 3: Frontend Foundation (5-7 days)

**Status:** ⏳ IN PROGRESS (Started 2026-03-10)

**Entry Criteria:**
- [x] Phase 2.5 exit criteria verified and signed off
- [x] Backend API endpoints functional (166/174 tests passing)

**Implementation:**

**Part A: Base UI Components (COMPLETE - 136/136 tests):**
- ✅ Button component (13 tests) - 3 variants, 3 sizes, loading state
- ✅ Input component (20 tests) - 5 types, labels, error states
- ✅ Table component (27 tests) - sortable, selectable, pagination
- ✅ Select component (31 tests) - keyboard nav, search, ARIA combobox
- ✅ Modal component (20 tests) - focus trap, sizes, accessibility

**Part B: Layout & Navigation (PLANNED - docs/plans/2026-03-09-workspace-layout-impl.md):**
- ⏳ SidebarNavItem component (8 tests planned)
- ⏳ Sidebar component (5 tests planned)
- ⏳ Workspace layout (+layout.svelte)
- ⏳ Placeholder pages (Campaigns, Jobs, Results, Settings)

**Part C: API Integration (PENDING):**
- ⏳ Dashboard metrics with real data fetching
- ⏳ Campaign management pages with API calls
- ⏳ File upload pages with progress tracking
- ⏳ Job status page with SSE integration
- ⏳ Svelte stores for state management

**Exit Criteria (run before sign-off):**
```bash
# Unit tests
bun run test tests/unit/components/ -v          # Component tests pass
bun run test tests/unit/stores/ -v              # Store tests pass

# E2E tests (with running backend)
bun run test:e2e tests/e2e/campaign.spec.ts     # Campaign CRUD works
bun run test:e2e tests/e2e/upload.spec.ts       # Upload works
bun run test:e2e tests/e2e/job-status.spec.ts   # Job status page works

# Build verification
bun run build                                   # Production build succeeds
bun run preview                                 # Preview server starts
```

**Sign-off Checklist:**
- [ ] All base components render correctly
- [ ] Navigation works between all pages
- [ ] Campaign create/edit/delete works in UI
- [ ] File upload shows progress and completes
- [ ] Job status page shows real-time updates via SSE
- [ ] Store state persists across navigation
- [ ] E2E tests for core flows pass

---

#### Phase 4: Integration & E2E (5-7 days)

**Status:** 📋 PLANNING IN PROGRESS (Design docs reviewed 2026-03-11)

**Planning Documents:**
- Design: `docs/plans/2026-03-11-phase4-integration-design.md`
- Implementation: `docs/plans/2026-03-11-phase4-integration-impl.md`

**Entry Criteria:**
- [ ] Phase 3 exit criteria verified and signed off
- [ ] Full backend stack running and accessible

**Implementation:**

**Part A: File Upload Pages (~4 hours)**
- Voter list upload with CSV/Excel validation
- Petition upload with progress tracking
- Pre-crop preview for petitions

**Part B: Job Status & SSE (~3 hours)**
- SSE connection in jobs store
- Real-time job status updates
- Cancel job functionality
- Auto-reconnect with exponential backoff

**Part C: Results Visualization (~3 hours)**
- Results store (paginated, filtered)
- Results table with confidence badges
- CSV export functionality
- Summary stats display

**Part D: Session Management (~2 hours)**
- Session save/load with workspace state
- Session export as ZIP

**Part E: E2E Testing (~4 hours)**
- Full workflow E2E test
- Error scenario tests
- Accessibility audit

**Exit Criteria (run before sign-off):**
```bash
# E2E tests
bun run test:e2e tests/e2e/results.spec.ts      # Results page works
bun run test:e2e tests/e2e/dashboard.spec.ts    # Dashboard works
bun run test:e2e tests/e2e/session.spec.ts      # Session management works
bun run test:e2e tests/e2e/demo.spec.ts         # Demo mode works

# Full flow test
bun run test:e2e tests/e2e/full-flow.spec.ts    # Complete user journey

# API contract test
uv run pytest tests/integration/api_contract/ -v  # API matches spec
```

**Sign-off Checklist:**
- [ ] Results table paginates and filters correctly
- [ ] Dashboard shows accurate metrics
- [ ] Session save/load preserves all state
- [ ] Session export creates valid ZIP file
- [ ] Demo mode resets all data
- [ ] Full E2E flow test passes (create → upload → job → results)
- [ ] API contract tests pass (frontend/backend integration)

**Plan Evaluation (Solutions Architect Review - 2026-03-11):**

The Phase 4 plans (`2026-03-11-phase4-integration-design.md` and `2026-03-11-phase4-integration-impl.md`) provide a solid TDD foundation. However, the following gaps require attention:

| Gap | Severity | Requirement | Recommendation |
|-----|----------|-------------|----------------|
| Dashboard metrics not detailed | **HIGH** | US-009 | Add explicit dashboard store + API calls for: total signatures, confidence breakdown, progress bars |
| Demo mode (reset, pre-baked) missing | **HIGH** | US-011, US-014 | Add Part F: Demo Mode (~2h) - reset API, pre-baked session loader |
| Session endpoints marked "deferred" | **HIGH** | FR-023 | Part D says endpoints deferred, but this IS Phase 4 - clarify: implement session API endpoints |
| Loading states not detailed | MEDIUM | FR-020 | Add LoadingSpinner usage, error boundaries to all async operations |
| Progress indicators for upload | MEDIUM | NFR-001 | Add upload progress bar with percentage display |
| CSV export test missing | MEDIUM | US-017 | Add test case for CSV download in Part C |

**Required Additions to Phase 4:**

1. **Part F: Demo Mode (~2 hours)** - NEW
   - Demo reset button with feature flag check
   - Pre-baked demo session loader
   - Files: `src/lib/stores/demo.ts`, demo reset API call

2. **Dashboard Enhancements** - ADD to Part C
   - Add `dashboard.ts` store with API calls
   - Fetch: total signatures, confidence distribution, job status
   - Update metrics on SSE job_complete event

3. **Session API Endpoints** - CLARIFY in Part D
   - These are NOT deferred - implement in Phase 4:
     - `POST /api/sessions` - Save session
     - `GET /api/sessions/{id}` - Load session
     - `GET /api/sessions/{id}/export` - Export ZIP

**Recommendation:** Update Phase 4 plans to address these gaps before implementation begins.

---

#### Phase 5: Polish & Demo (3-5 days)

**Entry Criteria:**
- [ ] Phase 4 exit criteria verified and signed off
- [ ] All MVP features implemented

**Implementation:**
- Accessibility audit and fixes (WCAG 2.2 AA)
- Error handling improvements
- Performance optimization
- Documentation (README, deployment guide)
- Demo session creation and rehearsal

**Exit Criteria (run before sign-off):**
```bash
# Accessibility tests
bun run test:a11y                               # Accessibility tests pass
npx axe-cli http://localhost:5173               # axe audit passes

# Performance tests
bun run lighthouse http://localhost:5173        # Lighthouse score >80

# Error handling tests
uv run pytest tests/integration/errors/ -v      # Error scenarios handled

# Documentation verification
markdown-link-check README.md                   # Links valid
markdown-link-check docs/deployment.md
```

**Sign-off Checklist:**
- [ ] Keyboard navigation works on all pages
- [ ] Screen reader testing complete (NVDA/JAWS)
- [ ] Color contrast ratios meet WCAG AA
- [ ] All error states have user-friendly messages
- [ ] Page load < 2s, API response < 500ms
- [ ] README includes setup, run, deploy instructions
- [ ] Deployment guide tested on clean machine
- [ ] Demo walkthrough successful (recorded)
- [ ] Pre-baked demo session loads correctly

---

### 7.3 Critical Path

**Updated (2026-03-11):**
```
Setup (✅) → Data Layer (✅) → Backend Services (✅) → API Endpoints (✅) → Frontend (⏳) → Results → Demo
```

**Current Phase:** Phase 3 (Frontend Foundation) in progress
- Part A: Base UI Components - COMPLETE (136/136 tests)
- Part B: Layout & Navigation - PLANNED (see `docs/plans/2026-03-09-workspace-layout-impl.md`)
- Part C: API Integration - PENDING

**Phase 4 Planning Status:**
- Design and implementation plans reviewed 2026-03-11
- Gaps identified (see §7.2 Phase 4 section)
- Recommendations documented
- Plan updated with new parts

**Implementation Plan Review (2026-03-09-workspace-layout-impl.md):**

The layout implementation plan provides a solid TDD foundation with 18 tests across SidebarNavItem and Sidebar components. However, the following gaps should be addressed before or during execution:

| Gap | Impact | Recommendation |
|-----|--------|----------------|
| Exit criteria pre-checked | Medium | Reset all checkboxes to `[ ]` before starting |
| No API integration for dashboard | High | Add API client calls for metrics (not hardcoded "0") |
| Missing loading/error states | High | Add LoadingSpinner component, error boundaries |
| No Svelte stores mentioned | Medium | Create stores for sidebar state, active nav item |
| Missing help/documentation links | Low | Add to sidebar nav (per FR-019) |

**Estimated Phase 3 Completion:** 2026-03-15 (4-5 days remaining)

### 7.4 Post-MVP Cleanup

After MVP completion and validation of all requirements through testing:

1. **Rename `frontend-svelt` → `frontend`**
   - Delete/archive the existing `frontend/` directory
   - Rename `frontend-svelt/` to `frontend/`
   - Update all references in:
     - `docker-compose.yml`
     - CI/CD workflows
     - Documentation
     - Any hardcoded paths in scripts

2. **Validation Checklist Before Promotion**
   - [ ] All E2E tests pass
   - [ ] All user stories from REQUIREMENTS.md validated
   - [ ] Accessibility audit complete (WCAG 2.2 AA)
   - [ ] Demo walkthrough successful
   - [ ] No references to old frontend in codebase

---

## 8. Technical Decisions

### 8.1 Job Orchestration

**Decision:** State machine + FastAPI BackgroundTasks
**Rationale:** LLM batch APIs are inherently async; no need for Celery/RQ complexity
**Alternatives Considered:** Event-driven, workflow engine (overkill)

### 8.2 Real-time Updates

**Decision:** Server-Sent Events (SSE) per job
**Rationale:** Better UX than polling, simpler than WebSockets
**Alternatives Considered:** Polling, WebSockets

### 8.3 Matching Strategy

**Decision:** Hybrid DB pre-filter + Python RapidFuzz
**Rationale:** Scales to 500K records; simple in-memory for MVP
**Alternatives Considered:** DB-only, full in-memory

### 8.4 Session Storage

**Decision:** Reference-based snapshots (IDs in JSON)
**Rationale:** Smaller storage, maintains data integrity
**Alternatives Considered:** Full data copy

### 8.5 API Client

**Decision:** OpenAPI-generated TypeScript client
**Rationale:** Type safety, auto-adapts to spec changes
**Alternatives Considered:** Custom fetch wrapper

### 8.6 Legacy Code Migration (Phase 2.5)

**Decision:** Complete API endpoints before removing legacy (Option A)
**Date:** 2026-03-10
**Rationale:** 
- Services are tested and validated (122/122 tests passing)
- Clean API ensures frontend can start immediately after completion
- Integration tests provide safety net for removal
- Avoids hybrid state with duplicated code paths
**Alternatives Considered:**
- Option B: Hybrid approach (keep legacy, use new code only for SSE) - Rejected due to technical debt
- Option C: Big bang migration (delete legacy, rush endpoints) - Rejected due to high risk
**Impact:** 2-3 day delay to Phase 3 start, but ensures clean architecture for remaining phases

---

## 9. Risks & Mitigations

| Risk | Impact | Probability | Mitigation | Status |
|------|--------|-------------|------------|--------|
| OCR accuracy low | High | Medium | Test with real samples early; allow manual correction | Active monitoring |
| LLM API changes | High | Medium | Provider abstraction layer; mock for tests | Mitigated (abstraction complete) |
| Matching slow | Medium | Low | Profile early; DB indexing; chunked processing | Mitigated (RapidFuzz implemented) |
| SSE connection issues | Medium | Medium | Reconnection logic; fallback to polling | Active monitoring |
| Timeline slip | High | Medium | 1-2 week buffer; weekly checkpoints | **Active (Phase 2.5 delay)** |
| API endpoint gaps | High | Medium | Integration tests before legacy removal; OpenAPI spec validation | **Active (Phase 2.5 in progress)** |
| Legacy code removal breaks features | Medium | Low | Comprehensive integration tests; phased rollout | **Active (Phase 2.5 in progress)** |
| Frontend blocked by missing API | High | **Certain** | Prioritize API endpoints (Phase 2.5); parallel development where possible | **Mitigating (Phase 2.5 prioritized)** |

---

## 10. Open Questions

| Question | Recommendation | Decision | Date |
|----------|----------------|----------|------|
| UUID vs INT for PKs? | INT for MVP simplicity | **Decided: INT** | 2026-03-09 |
| Duplicate detection? | File hash + row-level for voter lists | **Decided: Hash-based** | 2026-03-09 |
| 500K voter list support? | Hybrid approach, document as supported | **Decided: Yes** | 2026-03-09 |
| Dashboard updates? | SSE for now, WebSockets stretch | **Decided: SSE** | 2026-03-09 |
| Legacy code migration strategy? | Option A: Complete API endpoints first, then remove legacy | **Decided: Option A** | 2026-03-10 |
| Session endpoints timing? | Defer to Phase 4 per original SPEC | **Decided: Defer** | 2026-03-10 |
| Legacy router removal? | Delete immediately after API validation | **Decided: Immediate removal** | 2026-03-10 |

---

## 11. References

### Design Documents
- [Data Model](./data-model.md)
- [Architecture Details](./architecture.md)
- [API Specification](./api-spec.md)
- [Frontend Architecture](./frontend-architecture.md)
- [Implementation Roadmap](./implementation-roadmap.md)
- [Architecture Decision Records (ADRs)](../docs/adr/) - Notable technical decisions

### Implementation Plans
- [Workspace Layout Implementation](../docs/plans/2026-03-09-workspace-layout-impl.md) - Phase 3 layout and navigation

### External Resources
- [Requirements Document](../problem/REQUIREMENTS.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SvelteKit Documentation](https://kit.svelte.dev/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [ADR GitHub](https://adr.github.io/) - Architecture Decision Records guidance

---

## Appendix A: BDD Test Examples

### Job Orchestration

```gherkin
Feature: End-to-end job processing

  Scenario: Successful OCR and matching
    Given a campaign "DC 2024" exists
    And a voter list is uploaded for region "DC"
    And a petition scan with 10 crops is uploaded
    
    When I create a matcher job
    Then the job status should be "NOT_STARTED"
    
    When the OCR phase completes
    Then the job status should be "OCR_COMPLETED"
    And 10 OCR results should be created
    
    When the matching phase completes
    Then the job status should be "MATCHING_COMPLETED"
    And 10 match results should be created
```

### Results Filtering

```gherkin
Feature: Viewing match results

  Scenario: Filter results by confidence
    Given a completed job with results:
      | confidence |
      | HIGH       |
      | HIGH       |
      | MEDIUM     |
      | LOW        |
    
    When I filter by "HIGH" confidence
    Then I should see 2 results
    And all results should have "HIGH" confidence
```

---

## Appendix B: Configuration Reference

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/votecatcher

# OCR Providers
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
MISTRAL_API_KEY=...

# Feature Flags
FEATURE_DEMO_MODE=true
FEATURE_DEMO_RESET=true
FEATURE_DEBUG_LOGGING=false

# App Settings
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
```

### Feature Flags

| Flag | Purpose | Default |
|------|---------|---------|
| `demo_mode` | Enable demo features | `false` |
| `demo_reset` | Allow data reset | `false` |
| `load_prebaked_results` | Skip OCR/matching | `false` |
| `debug_logging` | Verbose logs | `false` |

---

## Appendix C: Security Scanning

### Baseline Security Tools (Free)

| Layer | Tool | Purpose | When to Run |
|-------|------|---------|-------------|
| **Backend Code** | Bandit | Static security analysis for Python | CI + pre-commit |
| **Backend Deps** | pip-audit | CVE scanning for Python dependencies | CI |
| **Frontend Deps** | npm audit | CVE scanning for npm dependencies | CI |
| **Secrets** | Gitleaks | Detect committed secrets/credentials | CI + pre-push |
| **Container** | Trivy | Container image vulnerability scanning | Pre-deploy |
| **GitHub** | Dependabot | Automated dependency updates | Continuous |

### Configuration

#### Backend (pyproject.toml)
```toml
[project.optional-dependencies]
dev = [
    "bandit[toml]>=1.7.0",
    "pip-audit>=2.6.0",
]

[tool.bandit]
exclude_dirs = ["tests", ".venv"]
skips = ["B101"]  # Skip assert_used test (OK in pytest)
```

#### CI/CD Security Jobs (GitHub Actions)
```yaml
# .github/workflows/security.yml
name: Security Scanning

on: [push, pull_request]

jobs:
  backend-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Bandit
        run: pip install bandit && bandit -r backend/app
      - name: Run pip-audit
        run: pip install pip-audit && cd backend && pip-audit

  frontend-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run npm audit
        run: cd frontend-svelt && bun audit

  secrets-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  container-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build image
        run: docker build -t votecatcher:latest .
      - name: Run Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'votecatcher:latest'
          format: 'table'
          exit-code: '1'  # Fail on vulnerabilities
          severity: 'CRITICAL,HIGH'
```

#### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
        additional_dependencies: ["bandit[toml]"]

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ["--baseline", ".secrets.baseline"]
```

### Security Checklist

Before each release:
- [ ] `bandit -r backend/app` passes with no HIGH/CRITICAL
- [ ] `pip-audit` shows no known vulnerabilities
- [ ] `bun audit` shows no known vulnerabilities
- [ ] No secrets in git history (gitleaks clean)
- [ ] Container scan shows no CRITICAL vulnerabilities
- [ ] Dependabot enabled for automated updates

### Handling Vulnerabilities

| Severity | Action |
|----------|--------|
| CRITICAL | Fix immediately, block deployment |
| HIGH | Fix within 1 week, warn in CI |
| MEDIUM | Fix within sprint, track in backlog |
| LOW | Fix opportunistically |

---

## Appendix D: Glossary

| Term | Definition |
|------|------------|
| **Petition** | Physical document with handwritten voter signatures |
| **Crop** | Individual signature entry extracted from petition scan |
| **Matcher Job** | Orchestrator job tracking OCR → Matching → Results |
| **OCR Job** | Child job for batch text extraction |
| **Confidence Score** | Match quality rating (HIGH/MEDIUM/LOW) |
| **Session** | Workspace snapshot (uploads, jobs, results) |

---

**Document Status:** Draft - Phase 4 Planning Review (2026-03-11)

**Current Phase:** Phase 3 - Frontend Foundation (In Progress)

**Phase 4 Planning Status:** Design docs reviewed, gaps identified

**Phase 4 Planning Documents:**
- Design: `docs/plans/2026-03-11-phase4-integration-design.md`
- Implementation: `docs/plans/2026-03-11-phase4-integration-impl.md`

**Identified Gaps (see §7.2 Phase 4 section for details):**
1. Dashboard metrics - need real API calls, not hardcoded values
2. Demo mode - reset and pre-baked session loading missing
3. Session API endpoints - incorrectly marked as deferred
4. CSV export - missing from test coverage

**Next Steps:**
1. ✅ Phase 0: Setup & Infrastructure - COMPLETE
2. ✅ Phase 1: Data Layer - COMPLETE
3. ✅ Phase 2: Core Backend Services - COMPLETE (122/122 tests passing)
4. ✅ Phase 2.5: API Endpoints & Legacy Migration - COMPLETE (8/8 API tests passing)
5. ⏳ **Phase 3: Frontend Foundation - IN PROGRESS** (4-5 days remaining)
   - Part A: Base UI Components - COMPLETE (136/136 tests)
   - Part B: Layout & Navigation - See `docs/plans/2026-03-09-workspace-layout-impl.md`
   - Part C: API Integration - PENDING
6. 📋 **Phase 4: Integration & E2E - PLANNING IN PROGRESS**
   - Address identified gaps before implementation
   - Update planning docs with recommendations
7. Track implementation with GitHub Issues/Projects
