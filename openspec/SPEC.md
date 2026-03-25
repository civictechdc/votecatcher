# Votecatcher Technical Specification

**Status:** Phase 13 - Voter List Tracking + Dashboard Progress
**Version:** 1.7
**Last Updated:** 2026-03-18
**Author:** Solutions Architect Agent

---

## Executive Summary

**MVP is complete as of 2026-03-12.** Post-MVP Phases 7-12 complete as of 2026-03-18.

**MVP Phases (1-6):** ✅ Complete — Stability, Page Hierarchy, Provider Config, OCR Cache Tracking
**Post-MVP Phases (7-12):** ✅ Complete — Job Creation Flow, Upload Enhancements, Critical Fixes
**Phase 13:** ✅ Complete — Voter List Tracking + Dashboard Progress

**Post-MVP Scope:**
- Phase 7: ✅ Quick Fixes & Cleanup (logo, landing, sidebar, stale docs)
- Phase 8: ✅ Campaign List & Dashboard (sorting, search, empty states)
- Phase 9: ✅ Job Creation Flow (new /jobs/new route with inline upload)
- Phase 10: ✅ Jobs List Enhancements (SSE updates, status filter)
- Phase 11: ✅ Upload Enhancements (show uploads, duplicate handling, queue)
- Phase 12: ✅ Critical Fixes + Polish (orphaned jobs, OCR duplicates, metrics dedup, timestamps)
- Phase 13: ✅ Voter List Tracking + Dashboard Progress (upload history, merge logic, progress stepper)

**Key Architectural Decisions for Post-MVP:**
| Decision | Choice |
|----------|--------|
| Job creation UX | Modal + /jobs/new coexist |
| Job status sync | SSE (real-time) |
| Status filter | Frontend-only |
| NOT_STARTED expiration | None |
| Upload list | Shared component |
| Duplicate uploads | Override with confirmation |

---

## 1. Problem Statement

Votecatcher needs to reach MVP readiness with:
1. Stable background job processing with test coverage
2. Campaign-scoped navigation replacing flat route structure
3. Dashboard with real metrics and confidence visualization
4. LLM provider configuration UI (no external config files)
5. Baseline accessibility and error handling

---

## 2. Solution Overview

### Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| URL format | Numeric ID (`/workspace/123`) | Simpler, no slug management |
| Provider storage | Snapshot only (no FK) | Survives provider deletion, simpler queries |
| Campaign status | On-demand compute | No cache invalidation, always fresh |
| Dashboard updates | Polling (10s) | Simpler than SSE for aggregate metrics |
| Demo data | In-memory only | Resets on reload, no persistence complexity |
| Route migration | Not needed | App not in production |

### Target Route Structure

```
/                             → Marketing landing (mode-aware CTA)
/workspace                    → Redirect to /workspace/campaigns
/workspace/campaigns          → Campaign list (sortable, searchable)
/workspace/[id]               → Campaign dashboard
/workspace/[id]/upload        → Upload page (show uploads, inline upload)
/workspace/[id]/jobs          → Jobs scoped to campaign (SSE updates, status filter)
/workspace/[id]/jobs/new      → Job creation page (full flow) ← NEW
/workspace/[id]/jobs/[job_id] → Job details (duration, timestamps)
/workspace/[id]/results       → Results scoped to campaign
/workspace/settings           → Global settings + LLM providers + feature flags
/workspace/demo               → Demo mode (virtual campaign)
```

---

## 3. Architecture

### 3.1 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (SvelteKit)                    │
├──────────────┬──────────────┬──────────────┬────────────────┤
│   Campaign   │   Dashboard  │    Jobs      │    Settings    │
│    List      │   + Metrics  │   + Results  │   + Providers  │
└──────┬───────┴──────┬───────┴──────┬───────┴───────┬────────┘
       │              │              │               │
       ▼              ▼              ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
├──────────────┬──────────────┬──────────────┬────────────────┤
│  Campaigns   │   Metrics    │    Jobs      │   Providers    │
│    API       │    API       │   + Worker   │     API        │
└──────┬───────┴──────────────┴──────┬───────┴────────────────┘
       │                             │
       ▼                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   SQLite (SQLModel/Drizzle)                  │
├─────────────────────────────────────────────────────────────┤
│ campaigns │ matcher_job │ match_result │ llm_provider_config │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Component Design

#### Frontend Components

| Component | Location | Purpose | Status |
|-----------|----------|---------|--------|
| `CampaignDashboard` | `/workspace/[id]` | Metrics cards, donut chart, recent jobs | ✅ Complete |
| `CampaignSidebar` | Layout | Campaign-scoped nav + switcher | ✅ Complete |
| `UploadTabs` | `/workspace/[id]/upload` | Tabbed voter/petition upload | ✅ Complete |
| `ProviderSettings` | `/workspace/settings` | LLM provider configuration | ✅ Complete |
| `ConfidenceDonut` | Dashboard | High/Medium/Low distribution | ✅ Complete |
| `StatusBadge` | Shared | Campaign/job status indicators | ✅ Complete |
| `CampaignList` | `/workspace/campaigns` | Sortable, searchable campaign table | 🔄 Phase 8 |
| `JobCreationPage` | `/workspace/[id]/jobs/new` | Full job creation with file selection | 🔄 Phase 9 |
| `UploadList` | Shared | List of uploads with actions | 🔄 Phase 11 |
| `FileUploader` | Shared | Inline upload with duplicate handling | 🔄 Phase 11 |
| `JobStatusFilter` | Jobs list | Frontend-only status filtering | 🔄 Phase 10 |

#### Settings Scope

| Route | Scope | Contents | MVP Status |
|-------|-------|----------|------------|
| `/workspace/settings` | Global | LLM providers, app preferences | **Required** |
| `/workspace/[id]/settings` | Per-campaign | Name, region, year, target | **Deferred** |

**Campaign settings for MVP:** Edit via modal from campaign list or dashboard (not separate page).

#### Backend Services

| Service | File | Purpose |
|---------|------|---------|
| `WorkerService` | `backend/app/jobs/worker.py` | Background job processing |
| `MetricsService` | `backend/app/services/metrics.py` | Campaign metric aggregation |
| `ProviderService` | `backend/app/services/providers.py` | LLM provider CRUD + validation |
| `StatusService` | `backend/app/services/status.py` | Campaign status computation |

### 3.3 Data Flow

#### Job Processing Flow

```
Upload PDF → Create Crops → Create Job (status: NOT_STARTED)
                                    │
                                    ▼
                    Worker polls for NOT_STARTED jobs
                                    │
                                    ▼
                    OCR processing (status: OCR_STARTED)
                                    │
                                    ▼
                    OCR complete (status: OCR_COMPLETED)
                                    │
                                    ▼
                    Matching (status: MATCHING)
                                    │
                                    ▼
                    Results created (status: MATCHING_COMPLETED)
                                    │
                                    ▼
                    SSE events emitted throughout
```

#### Dashboard Polling Flow

```
Page mount → GET /api/campaigns/{id}/metrics
                    │
                    ▼
            Set 10s interval
                    │
                    ▼
            Re-fetch metrics on interval
                    │
                    ▼
            Update UI reactively
                    │
                    ▼
            Cleanup interval on unmount
```

---

## 4. Data Model

### 4.1 Schema Changes

#### New Table: `llm_provider_config`

```sql
CREATE TABLE llm_provider_config (
  id INTEGER PRIMARY KEY,
  provider TEXT NOT NULL UNIQUE,    -- 'openai', 'gemini', 'mistral'
  api_key TEXT,                     -- Plaintext (MVP), encrypt post-MVP
  model TEXT NOT NULL,
  is_configured BOOLEAN DEFAULT FALSE,
  last_validated DATETIME,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME
);
```

#### UUID Storage Format

**Requirement:** All UUID fields must be stored as 32-character strings without dashes.

| Table | Field | Format |
|-------|-------|--------|
| `campaigns` | `id` | `25ea5e1c2fd849e88062c15e8b04492c` (32 chars) |
| `matcher_jobs` | `campaign_id` | Same format as campaigns.id |
| `petition_scans` | `campaign_id` | Same format as campaigns.id |

**Validation:** Job creation must validate `campaign_id` format matches expected pattern.

**Defensive Query Pattern:** Worker queries should normalize UUIDs using `REPLACE(campaign_id, '-', '')` to handle legacy data.

#### Modified Table: `matcher_job`

```sql
ALTER TABLE matcher_job ADD COLUMN provider_name TEXT;    -- Snapshot: 'openai'
ALTER TABLE matcher_job ADD COLUMN provider_model TEXT;   -- Snapshot: 'gpt-4o'
ALTER TABLE matcher_job ADD COLUMN parent_job_id INTEGER REFERENCES matcher_job(id);
ALTER TABLE matcher_job ADD COLUMN force_reprocess BOOLEAN DEFAULT FALSE;  -- Re-process all crops
ALTER TABLE matcher_job ADD COLUMN cached_ocr_count INTEGER DEFAULT 0;     -- Cached results count
ALTER TABLE matcher_job ADD COLUMN new_ocr_count INTEGER DEFAULT 0;        -- New results count
```

**Note:** No FK to `llm_provider_config` - jobs store snapshot only.

### 4.2 Status Computation (On-Demand)

Campaign status computed via priority cascade:

```python
def compute_campaign_status(campaign_id: int) -> str:
    """
    Priority: ERROR > IN_PROGRESS > COMPLETED > NOT_STARTED
    """
    jobs = get_jobs_for_campaign(campaign_id)
    uploads = get_uploads_for_campaign(campaign_id)
    results = get_results_for_campaign(campaign_id)

    # Check for error (only if NO usable results)
    if jobs and jobs[-1].status == JobStatus.FAILED:
        if not results or len(results) == 0:
            return "ERROR"

    # Check for in progress
    if uploads or any(j.status in [JobStatus.RUNNING, JobStatus.OCR_STARTED] for j in jobs):
        return "IN_PROGRESS"
    if results and len(get_processed_results(campaign_id)) < len(get_all_signatures(campaign_id)):
        return "IN_PROGRESS"

    # Check for completed
    if results and len(get_processed_results(campaign_id)) == len(get_all_signatures(campaign_id)):
        return "COMPLETED"

    return "NOT_STARTED"
```

### 4.3 Indexes

```sql
-- Campaign metrics queries
CREATE INDEX idx_match_result_campaign ON match_result(campaign_id);
CREATE INDEX idx_match_result_confidence ON match_result(campaign_id, confidence_tier);

-- Job queries
CREATE INDEX idx_matcher_job_campaign ON matcher_job(campaign_id);
CREATE INDEX idx_matcher_job_status ON matcher_job(status);
```

---

## 5. API Specification

### 5.1 New Endpoints

#### Campaign Metrics

```
GET /api/campaigns/{id}/metrics

Response:
{
  "total_signatures": 850,
  "processed": 847,
  "high_confidence": 723,
  "medium_confidence": 98,
  "low_confidence": 26,
  "progress_percentage": 99.6,
  "last_job": {
    "id": 42,
    "status": "MATCHING_COMPLETED",
    "completed_at": "2026-03-11T10:30:00Z"
  }
}
```

#### Provider Configuration

```
GET /api/settings/providers
Response: [{ "provider": "openai", "model": "gpt-4o", "is_configured": true, ... }]

POST /api/settings/providers/{provider}
Body: { "api_key": "sk-...", "model": "gpt-4o" }
Response: { "success": true, "last_validated": "..." }

POST /api/settings/providers/{provider}/test
Response: { "valid": true, "models": ["gpt-4o", "gpt-4o-mini"] }

DELETE /api/settings/providers/{provider}
Response: { "success": true }
```

### 5.2 Modified Endpoints

#### Job Creation (with provider selection)

```
POST /api/jobs
Body: {
  "campaign_id": 123,
  "petition_id": 456,
  "provider_name": "openai",    // NEW
  "provider_model": "gpt-4o"    // NEW
}
```

### 5.3 Error Handling

All errors include CORS headers and user-friendly messages.

#### Error Response Categories

| Error Type | HTTP Code | User Message | Action |
|------------|-----------|--------------|--------|
| Network unreachable | N/A (client-side) | "Unable to connect. Please check your connection." | "Try Again" button |
| API 500 error | 500 | "Something went wrong. Please try again." | "Retry" button |
| Job failed | 200 (job status) | "Job failed: {error_message}" | "Retry" button (creates new job) |
| Validation error | 400 | Field-specific message | Fix input |
| Not found | 404 | "Campaign not found" | Navigate to list |
| Unauthorized | 401 | "Authentication required" | N/A |
| Rate limited | 429 | "Too many requests. Please wait before retrying." | Wait and retry |

#### Backend Error Response Format

```json
{
  "detail": "User-friendly message",
  "error_code": "OPTIONAL_ERROR_CODE",
  "retryable": true
}
```

#### Concrete API Response Examples

**Network unreachable (client-side, no HTTP):**
```typescript
// Frontend-generated error when fetch fails
{
  "detail": "Unable to connect. Please check your connection.",
  "error_code": "NETWORK_ERROR",
  "retryable": true
}
```

**API 500 error:**
```json
HTTP/1.1 500 Internal Server Error
{
  "detail": "Something went wrong. Please try again.",
  "error_code": "INTERNAL_ERROR",
  "retryable": true
}
```

**Job failed (returned in job status, not error response):**
```json
HTTP/1.1 200 OK
{
  "id": 42,
  "status": "FAILED",
  "error_message": "OCR provider returned invalid response",
  "error_code": "OCR_ERROR",
  "retryable": true
}
```

**Validation error (400):**
```json
HTTP/1.1 400 Bad Request
{
  "detail": "Email must be a valid email address",
  "error_code": "VALIDATION_ERROR",
  "retryable": false,
  "field": "email"
}
```

**Not found (404):**
```json
HTTP/1.1 404 Not Found
{
  "detail": "Campaign not found",
  "error_code": "NOT_FOUND",
  "retryable": false
}
```

**Rate limited (429):**
```json
HTTP/1.1 429 Too Many Requests
{
  "detail": "Too many requests. Please wait before retrying.",
  "error_code": "RATE_LIMITED",
  "retryable": true,
  "retry_after": 60
}
```

#### Global Exception Handler

```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong. Please try again.", "error_code": "INTERNAL_ERROR", "retryable": True},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )
```

---

## 6. Implementation Plan

### Phase 1: Stability (Week 1) - PARALLEL with Phase 3

| Task | Priority | Effort | Dependencies |
|------|----------|--------|--------------|
| Worker tests | HIGH | 4-6h | None |
| Dashboard metrics API | HIGH | 3-4h | None |
| Confidence donut component | HIGH | 2-3h | Metrics API |
| Error handling CORS | MEDIUM | 2-3h | None |

**BDD Scenarios:**
- Worker processes NOT_STARTED job → OCR results created → status transitions
- Dashboard shows real metrics with confidence breakdown
- API errors include CORS headers

### Phase 2: Polish (Week 2)

| Task | Priority | Effort | Dependencies |
|------|----------|--------|--------------|
| Keyboard navigation | MEDIUM | 3-4h | Phase 3 routes |
| E2E test suite | MEDIUM | 4-6h | Phase 3 routes |
| Documentation | LOW | 2-3h | All features |

**BDD Scenarios:**
- Tab through all interactive elements
- Full campaign workflow E2E test passes
- README reflects new routes

### Phase 3: Page Hierarchy (Week 2, PARALLEL with Phase 1)

| Task | Priority | Effort | Dependencies |
|------|----------|--------|--------------|
| Restructure routes | HIGH | 1-2 days | None |
| Campaign dashboard page | HIGH | 1 day | Routes |
| Campaign-scoped sidebar | HIGH | 1 day | Routes |
| Upload page with tabs | MEDIUM | 1 day | Routes |
| Demo mode integration | MEDIUM | 4h | Routes |
| Root landing placeholder | LOW | 2h | None |

**BDD Scenarios (Campaign-Scoped Navigation):**

```gherkin
Feature: Campaign-Scoped Navigation

  Scenario 1: Navigate to campaign dashboard
    Given a campaign with ID 123 exists
    When I navigate to /workspace/123
    Then I see the campaign dashboard
    And the sidebar shows campaign-scoped navigation
    And the campaign name is in the header

  Scenario 2: Jobs are scoped to campaign
    Given campaign 123 has 2 jobs
    And campaign 456 has 3 jobs
    When I navigate to /workspace/123/jobs
    Then I see only jobs for campaign 123
    And I see 2 jobs in the list

  Scenario 3: Campaign switcher navigates
    Given I am on /workspace/123/jobs
    When I use the campaign switcher to select campaign 456
    Then I navigate to /workspace/456/jobs
    And I see jobs for campaign 456

  Scenario 4: Results scoped to campaign
    Given campaign 123 has 50 match results
    When I navigate to /workspace/123/results
    Then I see results for campaign 123 only
    And pagination works within campaign scope

  Scenario 5: Upload scoped to campaign
    Given I am on /workspace/123/upload
    When I upload a voter list
    Then it is associated with campaign 123
    When I upload a petition
    Then it is associated with campaign 123

  Scenario 6: Root landing page exists
    When I navigate to /
    Then I see a landing page
    And I see a "Get Started" button
    And clicking it navigates to /workspace
```

**Test File:** `frontend-svelt/tests/e2e/navigation.spec.ts`

### Phase 4: New Features (Week 3-4) - ✅ COMPLETE

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| LLM provider config UI | HIGH | 2-3 days | ✅ Complete |
| Provider selection on job | MEDIUM | 1-2 days | ✅ Complete |
| Campaign list enhancement (US-018 partial) | LOW | 1-2 days | Deferred |

> **Note:** Campaign list enhancement includes status badges, progress bars, confidence display, and filtering. Basic campaign list is included in MVP; enhanced version is stretch.

### Phase 5: Post-MVP Enhancements - ✅ COMPLETE

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Configuration modes documentation | HIGH | 4h | ✅ Complete |
| OCR cache tracking (force_reprocess) | HIGH | 4h | ✅ Complete |
| Database cleanup utility | MEDIUM | 2h | ✅ Complete |
| Real OCR testing infrastructure | MEDIUM | 4h | ✅ Complete |
| Rate limiting retry logic | HIGH | 2h | ✅ Complete |

### Phase 6: Post-MVP Production Hardening - ✅ COMPLETE

| Task | Priority | Effort | Status | Notes |
|------|----------|--------|--------|-------|
| Session management fix | HIGH | 2h | ✅ Complete | Transaction rollback after errors |
| Batching integration | MEDIUM | 1-2 days | ✅ Complete | Batch API for payloads >10 crops |
| Worker hot-reload | LOW | 4h | Deferred | Process manager or file watcher |

---

## Post-MVP Phases (7-12)

### Phase 7: Quick Fixes & Cleanup (1-2 days)

**Goal:** Low-hanging fruit and cleanup

| ID | Task | Priority | Effort | Dependencies |
|----|------|----------|--------|--------------|
| UT-001 | Logo mode-aware destinations | HIGH | 2h | None |
| NF-001 | Hide login/signup on landing | HIGH | 1h | None |
| NF-002 | Mode-aware CTA button | HIGH | 2h | None |
| NF-003 | Landing page cleanup | MEDIUM | 2h | None |
| UF-011 | Sidebar reorder (Dashboard→Upload→Jobs→Results→Settings) | MEDIUM | 1h | None |
| DX-001 | Remove stale documents | MEDIUM | 1h | None |
| DX-004 | Fix critical TS errors | MEDIUM | 4h | None |

**BDD Scenarios:**
```gherkin
Feature: Mode-Aware Navigation

  Scenario 1: Logo navigation in production mode
    Given the app is in production mode
    When I click the logo
    Then I navigate to /workspace/campaigns

  Scenario 2: Logo in demo mode
    Given the app is in demo mode
    When I click the logo
    Then demo data resets
    And I stay on /workspace/demo

  Scenario 3: CTA button respects mode
    Given the app is in simulation mode
    When I click the CTA on landing page
    Then I navigate to /workspace/campaigns
```

### Phase 8: Campaign List & Dashboard (1 day)

**Goal:** Polish campaign management UI

| ID | Task | Priority | Effort | Dependencies |
|----|------|----------|--------|--------------|
| UF-003 | Sortable columns (Name, Year, Region, Updated, Created) | HIGH | 2h | None |
| UF-004 | Search (campaign name, region, year) | HIGH | 2h | None |
| UF-008 | N/A for empty metrics | HIGH | 1h | None |
| UF-009 | N/A when no data | HIGH | 1h | None |
| UF-010 | Hide "View Results" if empty | HIGH | 1h | None |

**Sort Configuration:**
```typescript
interface SortConfig {
  column: 'name' | 'region' | 'election_year' | 'updated_at' | 'created_at';
  direction: 'asc' | 'desc';
  default: { column: 'created_at', direction: 'desc' };
}
```

### Phase 9: Job Creation Flow (3-5 days)

**Goal:** New consolidated job creation experience

| ID | Task | Priority | Effort | Dependencies |
|----|------|----------|--------|--------------|
| UF-035 | /jobs/new route | HIGH | 4h | None |
| UF-036 | File selection (existing uploads) | HIGH | 4h | UF-013 |
| UF-037 | Inline upload | HIGH | 4h | UF-013 |
| UF-038 | Duplicate file handling | HIGH | 2h | UF-037 |
| UF-039 | Provider/model selection | HIGH | 2h | None |
| UF-040 | Save job (NOT_STARTED) | HIGH | 2h | None |
| UF-041 | Run immediately | HIGH | 2h | UF-040 |
| UF-042 | LLM validation | HIGH | 2h | None |
| UF-043 | Return to list | HIGH | 1h | UF-040, UF-041 |

**Route Design:**
```
/workspace/[id]/jobs/new
├── File Selection Section
│   ├── [Existing Files List] - checkboxes (shared UploadList component)
│   └── [Upload New] - inline FileUploader with duplicate handling
├── Provider Selection
│   ├── Provider dropdown (if configured)
│   ├── Model dropdown
│   └── [Configure LLM] link if none configured → /workspace/settings
├── Actions
│   ├── [Cancel] → return to job list
│   ├── [Save] → NOT_STARTED, return to list
│   └── [Run] → save + start, return to list with SSE
└── Pre-validation
    └── If no LLM: "Configure an LLM provider first" → /workspace/settings
```

**Job States:**
- NOT_STARTED (saved, not run) - visible in job list
- OCR_STARTED
- MATCHING
- MATCHING_COMPLETED
- FAILED

**Modal Coexistence:**
- Quick modal: Single file, immediate run, no save option
- Full page: Multi-file, save or run, provider selection

### Phase 10: Jobs List Enhancements (1 day)

**Goal:** Support new job creation flow

| ID | Task | Priority | Effort | Dependencies |
|----|------|----------|--------|--------------|
| UF-019 | Default sort by created date | HIGH | 1h | None |
| UF-020 | Show last updated timestamp | HIGH | 1h | None |
| UF-021 | Status dynamic update (SSE) | HIGH | 3h | None |
| UF-023 | Warn if no uploads | HIGH | 1h | None |
| UF-044 | Status filter (frontend-only) | HIGH | 2h | None |
| UF-045 | Keep quick modal for simple jobs | MEDIUM | 1h | Phase 9 |

**SSE Implementation:**
```typescript
// Job list subscribes to job status updates
const eventSource = new EventSource(`/api/campaigns/${campaignId}/jobs/events`);

eventSource.onmessage = (event) => {
  const update = JSON.parse(event.data);
  jobs.update(j => j.map(job =>
    job.id === update.job_id ? { ...job, status: update.status } : job
  ));
};
```

**Status Filter:**
```typescript
type JobStatusFilter = 'all' | 'not_started' | 'running' | 'completed' | 'failed';

// Frontend-only filter
$: filteredJobs = selectedFilter === 'all'
  ? jobs
  : jobs.filter(j => statusMatches(j.status, selectedFilter));
```

### Phase 11: Upload Enhancements (2-3 days)

**Goal:** Improve upload experience

| ID | Task | Priority | Effort | Dependencies |
|----|------|----------|--------|--------------|
| UF-013 | Show existing uploads (name, date, size, remove) | HIGH | 4h | None |
| UF-014 | Handle duplicates (override with confirmation) | HIGH | 2h | UF-013 |
| UF-015 | Upload queue (status for active/pending) | MEDIUM | 3h | None |
| UF-016 | Remove all files (with confirmation) | MEDIUM | 2h | UF-013 |
| UF-017 | Fix or remove unused progress bar | HIGH | 1h | None |
| UF-018 | Better remove icon (web/svg) | LOW | 1h | None |

**Shared Component:**
```svelte
<!-- UploadList.svelte - used by /upload and /jobs/new -->
<script lang="ts">
  interface Props {
    campaignId: string;
    type: 'voter_list' | 'petition';
    selectable?: boolean;  // true for /jobs/new, false for /upload
    onSelectionChange?: (selected: Upload[]) => void;
  }
</script>
```

**Duplicate Handling Flow:**
```
User uploads file with existing name
        │
        ▼
Show dialog: "File 'voters.csv' already exists. Override?"
        │
        ├── [Override] → Delete old, upload new
        └── [Cancel] → Keep existing, discard new
```

### Phase 12: Critical Fixes + Polish & Settings (2-3 days) - ✅ COMPLETE

**Goal:** Fix critical bugs discovered in walkthrough + final polish

#### Phase 12A: Critical Fixes (P0) - ✅ COMPLETE

| ID | Task | Priority | Effort | Dependencies | Status |
|----|------|----------|--------|--------------|--------|
| BUG-14 | Fix OCR duplicate results (add ocr_index, remove unique constraint) | 🔴 HIGH | 4-6h | None | ✅ |
| BUG-01 | Fix orphaned jobs after restart (expand cancelable states, orphan detection) | 🔴 HIGH | 3-4h | None | ✅ |
| BUG-15 | Fix metrics confidence deduplication | 🔴 HIGH | 2h | BUG-14 | ✅ |

#### Phase 12B: Quick UX Fixes (P1) - ✅ COMPLETE

| ID | Task | Priority | Effort | Dependencies | Status |
|----|------|----------|--------|--------------|--------|
| BUG-09 | Disable Create Job button when no uploads | 🟡 MEDIUM | 1h | None | ✅ |
| BUG-12 | Fix View Results button (use hasMatchResults not hasCrops) | 🟡 MEDIUM | 1h | None | ✅ |

#### Phase 12C: Original Polish Tasks (P2) - ✅ COMPLETE

| ID | Task | Priority | Effort | Dependencies | Status |
|----|------|----------|--------|--------------|--------|
| UF-024 | Job duration display | HIGH | 1h | None | ✅ |
| UF-025 | Job ended timestamp | HIGH | 1h | None | ✅ |
| UF-027 | View results conditional (success only) | HIGH | 1h | None | ✅ |
| UF-030 | Feature flags non-prod only | HIGH | 2h | None | ✅ |
| UF-031 | Settings: Reset Data | MEDIUM | 2h | None | ✅ |
| BUG-08 | Fix model selector dropdown clipped | MEDIUM | 1h | None | ✅ |
| BUG-17 | Commit uncommitted fixes | MEDIUM | 1h | None | ✅ |
| BUG-18 | Fix flaky provider test | LOW | 1h | None | ✅ |
| BUG-19 | Fix aggressive polling storm | MEDIUM | 1h | None | ✅ |

**Critical Bug Details:**

**BUG-14: OCR Duplicate Results**
- Current: UNIQUE constraint on `ocr_results.crop_id` causes 4/5 entries dropped
- Fix: Remove unique constraint, add `ocr_index` column (0-4 for 5 signatures per crop)
- Migration: `ALTER TABLE ocr_results ADD COLUMN ocr_index INTEGER;`
- Worker: Store all 5 entries with index

**BUG-01: Orphaned Jobs After Backend Restart**
- Current: Jobs stuck in MATCHING state, cannot cancel
- Fix Part 1: Expand cancelable states to include OCR_COMPLETED, MATCHING_PENDING, MATCHING
- Fix Part 2: Detect orphaned jobs on startup (no worker heartbeat)
- UX: Show "Resume" / "Delete" buttons for orphaned jobs

**Feature Flags Configuration:**
```typescript
// Only show in non-production modes
const showFeatureFlags = import.meta.env.MODE !== 'production';

// Available flags
interface FeatureFlags {
  enableSimulation: boolean;
  demoMode: boolean;
  debugTimezone: boolean;
}
```

### Critical Path

```
Phase 1-6 (MVP) ──────────────────────────────────────────► ✅ COMPLETE
                                                              │
                                                              ▼
Phase 7 (Quick Fixes) ──► Phase 8 (Campaign UI) ──► Phase 9 (Job Creation)
                                                              │
                                                              ▼
Phase 10 (Jobs List) ──► Phase 11 (Upload) ──► Phase 12 (Critical Fixes)
                                                              │
                                                              ▼
                                              Phase 13 (Voter List Tracking) ──► 📋 Planned
```

### Implementation Status

**MVP Phases (✅ Complete):**
- Phase 1: Stability - ✅ Complete
- Phase 2: Polish - ✅ Complete
- Phase 3: Page Hierarchy - ✅ Complete
- Phase 4: Stretch Features - ✅ Complete
- Phase 5: Post-MVP Enhancements - ✅ Complete
- Phase 6: Production Hardening - ✅ Complete

**Post-MVP Phases (✅ Complete):**
- Phase 7: Quick Fixes & Cleanup - ✅ Complete
- Phase 8: Campaign List & Dashboard - ✅ Complete
- Phase 9: Job Creation Flow - ✅ Complete
- Phase 10: Jobs List Enhancements - ✅ Complete
- Phase 11: Upload Enhancements - ✅ Complete
- Phase 12: Critical Fixes + Polish - ✅ Complete

**Enhancement Phases (📋 Planned):**
- Phase 13: Voter List Tracking + Dashboard Progress - ✅ Complete

### Phase Gate Criteria

Each phase has explicit entrance and exit criteria. No phase may proceed without meeting exit criteria.

#### Phase 1: Stability - ✅ COMPLETE

| Gate | Criteria | Status |
|------|----------|--------|
| **Entrance** | Development environment functional, existing tests pass | ✅ Met |
| **Exit** | - Worker tests pass (≥3 scenarios) <br> - Dashboard metrics API returns real data <br> - Confidence donut renders correctly <br> - Error responses include CORS headers | ✅ All Met |

#### Phase 2: Polish - ✅ COMPLETE

| Gate | Criteria | Status |
|------|----------|--------|
| **Entrance** | Phase 1 exit criteria met, Phase 3 routes exist | ✅ Met |
| **Exit** | - Keyboard navigation works (Tab through all pages) <br> - E2E full-flow test passes <br> - README updated with new routes <br> - No console errors in normal flows | ✅ All Met |

#### Phase 3: Page Hierarchy - ✅ COMPLETE

| Gate | Criteria | Status |
|------|----------|--------|
| **Entrance** | None (parallel with Phase 1) | ✅ Met |
| **Exit** | - All 6 navigation BDD scenarios pass <br> - Campaign-scoped routes work <br> - Campaign switcher preserves route segment <br> - Demo mode functional at /workspace/demo <br> - Root landing page exists | ✅ All Met |

#### Phase 4: Stretch Features - ✅ COMPLETE

| Gate | Criteria | Status |
|------|----------|--------|
| **Entrance** | Phase 1, 2, 3 complete | ✅ Met |
| **Exit** | - LLM provider config saves to DB <br> - Provider selection on job creation works <br> - Campaign list shows status badges | ✅ All Met |

#### Phase 5: Post-MVP Enhancements - ✅ COMPLETE

| Gate | Criteria | Status |
|------|----------|--------|
| **Entrance** | Phase 4 complete | ✅ Met |
| **Exit** | - Configuration modes documented <br> - OCR cache tracking works <br> - Database cleanup utility available <br> - Real OCR tested with rate limiting | ✅ All Met |

#### Phase 6: Production Hardening - ✅ COMPLETE

| Gate | Criteria | Status |
|------|----------|--------|
| **Entrance** | Phase 5 complete | ✅ Met |
| **Exit** | - Session management handles rollback <br> - Batching integrated for large payloads <br> - Worker hot-reload available | ✅ All Met |

#### Phase 7: Quick Fixes & Cleanup - ✅ COMPLETE

| Gate | Criteria | Status |
|------|----------|--------|
| **Entrance** | Phase 6 complete | ✅ Met |
| **Exit** | - Logo navigates correctly per mode <br> - Landing page CTA works per mode <br> - Sidebar order matches spec <br> - Stale documents removed | ✅ All Met |

#### Phase 8: Campaign List & Dashboard - ✅ COMPLETE

| Gate | Criteria | Status |
|------|----------|--------|
| **Entrance** | Phase 7 complete | ✅ Met |
| **Exit** | - Sortable columns work <br> - Search filters campaigns <br> - Empty states show N/A correctly | ✅ All Met |

#### Phase 9: Job Creation Flow - ✅ COMPLETE

| Gate | Criteria | Status |
|------|----------|--------|
| **Entrance** | Phase 8 complete | ✅ Met |
| **Exit** | - /jobs/new route renders <br> - File selection works (existing + inline upload) <br> - Save creates NOT_STARTED job <br> - Run starts processing <br> - LLM validation blocks if not configured | ✅ All Met |

#### Phase 10: Jobs List Enhancements - ✅ COMPLETE

| Gate | Criteria | Status |
|------|----------|--------|
| **Entrance** | Phase 9 complete | ✅ Met |
| **Exit** | - SSE updates job status in real-time <br> - Status filter works (frontend) <br> - Saved jobs visible in list | ✅ All Met |

#### Phase 11: Upload Enhancements - ✅ COMPLETE

| Gate | Criteria | Status |
|------|----------|--------|
| **Entrance** | Phase 10 complete | ✅ Met |
| **Exit** | - Upload list shows existing files <br> - Duplicate handling confirms override <br> - Progress bar functional or removed | ✅ All Met |

#### Phase 12: Critical Fixes + Polish & Settings - ✅ COMPLETE

| Gate | Criteria | Status |
|------|----------|--------|
| **Entrance** | Phase 11 complete | ✅ Met |
| **Exit** | - OCR stores all 5 entries per crop <br> - Orphaned jobs can be cancelled/resumed <br> - Job duration/timestamps display <br> - Feature flags only in non-prod <br> - Reset Data option available | ✅ All Met |

- Phase 13: Voter List Tracking + Dashboard Progress - ✅ COMPLETE

| Gate | Criteria | Status |
|------|----------|--------|
| **Entrance** | Phase 12 complete | ✅ Met |
| **Exit** | - Voter list uploads tracked with history <br> - Dashboard shows progress stepper <br> - Region schemas support configurable CSV parsing <br> - Merge/update logic handles duplicate voters | 📋 Pending |

**Phase 13 Scope (see `docs/plans/2026-03-18-voter-list-tracking-design.md`):**
- Issue #5: Voter list tab shows existing uploads
- Issue #10: Dashboard shows "uploads ready, no job run" state
- New tables: `voter_list_uploads`, `region_schemas`
- New tracking fields on `registered_voter`
- ProgressStepper component on dashboard
- Region schema admin UI

#### Phase Gate Verification

```bash
# Run before declaring phase complete
bun run test:unit && bun run test:e2e && bun run build

# All must pass with 0 failures
# Exit code 0 required to proceed
```

### Validation Protocol

All tasks must be validated through BDD/TDD before marking complete.

#### Test-First Requirements

1. **Write test first**: Before implementing any feature, write the failing test
2. **Implement minimum**: Write only enough code to make the test pass
3. **Refactor**: Clean up implementation while keeping tests green
4. **Document**: Update test file comments with any edge cases discovered

#### Test Coverage Requirements

| Test Type | Minimum Coverage | Phase Requirement |
|-----------|------------------|-------------------|
| Unit tests (backend) | 80% of new code | Mandatory |
| Integration tests (API) | All new endpoints | Mandatory |
| E2E tests | All user flows | Mandatory |
| Component tests | Deferred (Svelte 5 + jsdom incompatibility) | Post-MVP |

#### BDD Scenario Completion

Each BDD scenario must:
1. Have a corresponding test file
2. Pass independently
3. Pass when run with full suite
4. Be reviewed for edge cases

**Completion Checklist (per scenario):**
```
[ ] Scenario written in Gherkin
[ ] Test file created
[ ] Test passes in isolation
[ ] Test passes in full suite
[ ] Edge cases documented
[ ] Code reviewed
```

#### Verification Commands

```bash
# Backend unit tests
cd backend && uv run pytest tests/unit -v --cov=app --cov-report=term-missing

# Backend integration tests
cd backend && uv run pytest tests/integration -v

# Frontend E2E tests
cd frontend-svelt && bun run test:e2e

# All tests (pre-commit)
bun run test:all
```

### Progress Reporting

Developers must maintain a PROGRESS.md file with regular updates and record ADRs for notable decisions.

#### File Locations

| File | Purpose |
|------|---------|
| `.agent-workspace/problem/PROGRESS.md` | Implementation progress tracking |
| `openspec/adr/` | Architecture Decision Records |

#### PROGRESS.md Required Sections

```markdown
# Votecatcher Progress

**Last Updated:** YYYY-MM-DD HH:MM
**Current Phase:** [Phase X: Name]
**Overall Status:** [On Track / At Risk / Blocked]
**Health:** 🟢 Green / 🟡 Yellow / 🔴 Red

---

## Phase Status

| Phase | Status | Completion % | Notes |
|-------|--------|--------------|-------|
| Phase 7: Quick Fixes | [Not Started / In Progress / Complete] | X% | Brief note |
| Phase 8: Campaign UI | [Not Started / In Progress / Complete] | X% | Brief note |
| ... | ... | ... | ... |

---

## Current Work

**Task:** [ID] [Task name from SPEC]
**Started:** YYYY-MM-DD
**Status:** [In Progress / Blocked / Review / Testing]
**Effort:** [Xh spent / Yh estimated]

### Progress
- [ ] Subtask 1 - [status note]
- [ ] Subtask 2 - [status note]
- [x] Completed subtask

### Test Results
```
[Paste relevant test output]
```

---

## Blockers

| # | Task ID | Blocker | Impact | Owner | Status | Resolution |
|---|---------|---------|--------|-------|--------|------------|
| B1 | UF-035 | SSE endpoint returns 500 | Cannot proceed with UF-021 | Dev | Open | Investigating |
| B2 | UF-013 | API missing file size field | Partial implementation | Dev | Resolved | Added field to API |

---

## Questions & Concerns

| # | Type | Question/Concern | Context | Status | Answer/Resolution |
|---|------|------------------|---------|--------|-------------------|
| Q1 | Question | Should SSE reconnect on disconnect? | Phase 10 implementation | Answered | Yes, use exponential backoff |
| C1 | Concern | Upload component may be slow with 100+ files | Performance | Open | Consider pagination |
| Q2 | Clarification | What happens to NOT_STARTED jobs when campaign deleted? | Edge case | Pending | Need user input |

---

## SPEC Deviations

| Date | Section | Deviation | Reason | Impact | Approved By |
|------|---------|-----------|--------|--------|-------------|
| 2026-03-12 | §7.9 | Using backend filter instead of frontend | Performance concern for large lists | Minor API change | User |
| 2026-03-13 | Phase 9 | Deferred UF-038 to Phase 11 | Dependency on UF-014 | Reordered tasks | Architect |

---

## Decisions Log (ADRs)

| Date | ADR # | Decision | Rationale |
|------|-------|----------|-----------|
| 2026-03-12 | ADR-001 | SSE over WebSocket for job updates | Simpler, HTTP-compatible, existing pattern |
| 2026-03-13 | ADR-002 | Shared UploadList component | DRY, consistent UX |

> **Note:** Full ADRs documented in `openspec/adr/NNNN-title.md`

---

## Daily Log

### YYYY-MM-DD
- **Completed:** [list of task IDs]
- **In Progress:** [list of task IDs]
- **Blocked:** [list of task IDs with blocker ref]
- **Next:** [planned tasks for next session]
- **Time Spent:** Xh

### Session Notes
- [Notable observations, learnings, or context]
```

#### Update Cadence

| Event | Action |
|-------|--------|
| Start task | Update "Current Work" section |
| Complete subtask | Check off in "Progress" list |
| Test pass/fail | Update "Test Results" |
| Encounter blocker | Add to "Blockers" table immediately |
| Have question/concern | Add to "Questions & Concerns" table |
| Deviate from SPEC | Add to "SPEC Deviations", get approval |
| Make notable decision | Record in "Decisions Log", create ADR if significant |
| End of work session | Update "Phase Status" and "Daily Log" |
| Phase gate | Run verification, update "Phase Status" |

#### Issue Triage

When adding issues, classify by type:

| Type | Definition | Response Time | Escalation |
|------|------------|---------------|------------|
| **Blocker** | Cannot proceed without resolution | Immediate | Alert user same day |
| **Technical** | Implementation challenge | Same day | Escalate if unresolved 2 days |
| **Question** | Clarification on requirements/spec | Next session | Escalate if blocking |
| **Concern** | Potential risk or issue | Document | Review weekly |
| **Enhancement** | Nice-to-have, not blocking | Defer | Backlog |

#### ADR (Architecture Decision Record) Requirements

**When to create an ADR:**
- Changing a technical decision from the SPEC
- Introducing a new pattern or approach
- Choosing between alternatives with trade-offs
- Modifying data model or API contracts
- Any decision that affects other phases or future work

**ADR Template (`openspec/adr/NNNN-kebab-case-title.md`):**

```markdown
# ADR-NNNN: [Decision Title]

**Date:** YYYY-MM-DD
**Status:** [Proposed / Accepted / Deprecated / Superseded]
**Decision Makers:** [Who was involved]
**Supersedes:** [ADR-XXXX if applicable]

## Context

[What is the issue or problem being addressed? What constraints exist?]

## Decision

[What is the change or decision being made?]

## Alternatives Considered

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Option A | ... | ... | ... |
| Option B | ... | ... | ... |

## Consequences

**Positive:**
- [Benefits of this decision]

**Negative:**
- [Drawbacks or trade-offs]

**Risks:**
- [Potential issues to watch for]

## Implementation Notes

[Any specific guidance for implementing this decision]

## References

- Related SPEC section: §X.X
- Related requirements: [ID-001, ID-002]
- External references: [links]
```

**ADR Naming Convention:**
- Number sequentially: ADR-0001, ADR-0002, etc.
- Use kebab-case title: `0001-sse-for-job-updates.md`
- Location: `openspec/adr/`

**ADR Index:**
Maintain an index in `openspec/adr/README.md`:

```markdown
# Architecture Decision Records

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [0001](0001-sse-for-job-updates.md) | SSE for Job Updates | Accepted | 2026-03-12 |
| [0002](0002-shared-upload-component.md) | Shared UploadList Component | Accepted | 2026-03-13 |
```

---

## 7. Technical Decisions

### 7.1 Provider Storage: Snapshot Only

**Decision:** Jobs store `provider_name` and `provider_model` as text columns, no FK to `llm_provider_config`.

**Rationale:**
- Provider config may be deleted - job history preserved
- Simpler queries - no JOINs needed
- Matches requirements for "Provider removed" badge

**Alternatives Rejected:**
- FK with ON DELETE SET NULL - adds complexity, still need snapshot for display

### 7.2 Dashboard Updates: Polling

**Decision:** Dashboard uses 10-second polling for metrics.

**Rationale:**
- Aggregate metrics don't need sub-second updates
- 5 lines of code vs SSE connection management
- SSE retained for job progress page (already works)

### 7.3 Demo Mode: Virtual Campaign

**Decision:** Demo at `/workspace/demo` as in-memory virtual campaign.

**Rationale:**
- Preserves existing demo functionality
- Same route structure as real campaigns
- No database writes
- Always available (no campaign required)

#### Demo Route Structure

| Route | Behavior |
|-------|----------|
| `/workspace/demo` | Demo dashboard with pre-baked data |
| `/workspace/demo/jobs` | Demo jobs (in-memory) |
| `/workspace/demo/results` | Demo results (pre-baked) |
| `/workspace/demo/upload` | Disabled (demo uses sample data) |

#### In-Memory Data Structure

```typescript
// frontend-svelt/src/lib/stores/demoData.ts
import { writable } from 'svelte/store';

interface DemoData {
  campaign: {
    id: 'demo';
    name: 'Demo Campaign';
    region: 'DC';
    election_year: number;
  };
  jobs: DemoJob[];
  results: DemoMatchResult[];
}

const initialDemoData: DemoData = {
  campaign: { id: 'demo', name: 'Demo Campaign', region: 'DC', election_year: 2024 },
  jobs: [
    { id: 'demo-job-1', status: 'MATCHING_COMPLETED', provider_name: 'openai', provider_model: 'gpt-4o', ... }
  ],
  results: [...preBakedMatchResults], // ~50 sample results with H/M/L confidence
};

export const demoData = writable<DemoData>(structuredClone(initialDemoData));
```

#### Pre-Baked Fixtures

```typescript
// frontend-svelt/src/lib/data/demoFixtures.ts
export const preBakedMatchResults: DemoMatchResult[] = [
  // ~50 results with confidence distribution:
  // 35 High (≥0.8), 10 Medium (0.5-0.8), 5 Low (<0.5)
  { id: 1, petition_name: 'John Smith', confidence: 0.95, tier: 'HIGH', voter: {...} },
  { id: 2, petition_name: 'Jane Doe', confidence: 0.72, tier: 'MEDIUM', voter: {...} },
  { id: 3, petition_name: 'Bob Wilson', confidence: 0.35, tier: 'LOW', voter: null },
  // ... more results
];
```

#### Reset Flow

```
User clicks "Reset Demo"
       │
       ▼
Confirmation dialog: "This will clear all demo data. Continue?"
       │
       ▼ (Confirm)
demoData.set(structuredClone(initialDemoData))
       │
       ▼
UI refreshes to initial state
```

**Behavior:**
- `/workspace/demo/*` routes read from `demoData` store
- Reset button clears `demoData` back to initial state
- No API calls to backend (frontend-only)
- Data resets on page reload (no localStorage persistence)

### 7.4 Upload Page: Tabbed Interface

**Decision:** Single upload route with tabs for Voter List and Petitions.

**Route:** `/workspace/[id]/upload`

**Layout:**
```
┌─────────────────────────────────────┐
│  [Voter List]  [Petitions]          │  ← Tab navigation
├─────────────────────────────────────┤
│                                     │
│  Tab content here                   │
│  - Voter List: CSV upload           │
│  - Petitions: PDF upload            │
│                                     │
└─────────────────────────────────────┘
```

**Rationale:**
- Reduces navigation depth
- User often uploads both in sequence
- Tabs preserve campaign context

**State Management:**
- Active tab stored in component state
- Both tabs share campaign context from route param
- Upload success shows toast notification, stays on tab

### 7.5 Retry Flow: New Job Creation

**Decision:** Retry creates a NEW job (not restart same job).

**Rationale:**
- Clear audit trail (preserves failed job history)
- Failed job remains viewable for debugging
- New job can use different provider if original was deleted

**Flow:**
```
User clicks "Retry"
       │
       ▼
Job creation modal opens
       │
       ▼
Pre-filled with: same petition, same voter list
       │
       ▼
User can change provider (if original deleted or different choice)
       │
       ▼
Submit creates NEW job with parent_job_id reference
       │
       ▼
Original failed job preserved for audit
```

**Database:**
```sql
ALTER TABLE matcher_job ADD COLUMN parent_job_id INTEGER REFERENCES matcher_job(id);
```

**Modal Pre-fill Logic:**
```typescript
function openRetryModal(failedJob: Job) {
  const prefillData = {
    petition_id: failedJob.petition_id,
    voter_list_id: failedJob.voter_list_id,
    // Provider NOT pre-filled - user must select
    provider_name: null,
    provider_model: null,
    parent_job_id: failedJob.id,
  };
  // Open modal with prefillData
}
```

### 7.6 Campaign Switcher: Route Preservation

**Decision:** Switcher preserves current route segment when switching campaigns.

**Behavior Table:**

| Current Route | Switch to Campaign 456 | Result |
|---------------|------------------------|--------|
| `/workspace/123/jobs` | Campaign 456 | `/workspace/456/jobs` |
| `/workspace/123/results` | Campaign 456 | `/workspace/456/results` |
| `/workspace/123` (dashboard) | Campaign 456 | `/workspace/456` |
| `/workspace/123/upload` | Campaign 456 | `/workspace/456/upload` |

**Dropdown Contents:**
- All campaigns (sorted alphabetically)
- "Demo" option (if demo mode available)
- Current campaign highlighted with checkmark

**Implementation:**
```typescript
function switchCampaign(newCampaignId: string | number) {
  const currentPath = $page.url.pathname;
  const currentSegment = currentPath.replace(/^\/workspace\/\d+/, '');
  goto(`/workspace/${newCampaignId}${currentSegment}`);
}
```

### 7.7 Job Creation: Modal + Page Coexistence (Post-MVP)

**Decision:** Job creation modal and /jobs/new page coexist for different use cases.

**Rationale:**
- Modal: Quick single-file jobs, immediate run, minimal friction
- Full page: Multi-file selection, save for later, provider selection, inline upload

**When to use each:**
| Scenario | Use Modal | Use /jobs/new |
|----------|-----------|---------------|
| Single file, run now | ✅ | |
| Multi-file selection | | ✅ |
| Save job for later | | ✅ |
| Need to upload new file | | ✅ |
| Change provider from previous | | ✅ |

### 7.8 Job Status Sync: SSE (Post-MVP)

**Decision:** Job list uses Server-Sent Events for real-time status updates.

**Rationale:**
- Real-time UX for active jobs
- Consistent with existing job detail page SSE
- Lower overhead than polling for active campaigns

**Implementation:**
```typescript
// Subscribe to campaign job updates
const eventSource = new EventSource(`/api/campaigns/${campaignId}/jobs/events`);
eventSource.onmessage = (event) => {
  const update = JSON.parse(event.data);
  jobs.update(j => j.map(job =>
    job.id === update.job_id ? { ...job, ...update } : job
  ));
};
```

### 7.9 Status Filter: Frontend-Only (Post-MVP)

**Decision:** Job status filter implemented as frontend-only in-memory filtering.

**Rationale:**
- Typical job count per campaign < 100
- No backend changes needed
- Instant filter response

### 7.10 NOT_STARTED Jobs: No Expiration (Post-MVP)

**Decision:** Jobs in NOT_STARTED state live indefinitely with no automatic expiration.

**Rationale:**
- Users may save jobs for later execution
- No additional cleanup complexity
- Manual deletion if needed

### 7.11 Upload List: Shared Component (Post-MVP)

**Decision:** Upload list component shared between /upload page and /jobs/new page.

**Rationale:**
- Consistent UX across contexts
- Single source of truth for upload display logic
- Props control behavior (selectable vs view-only)

### 7.12 Duplicate Uploads: Override with Confirmation (Post-MVP)

**Decision:** Uploading a file with existing name shows confirmation dialog, then replaces.

**Rationale:**
- Prevents accidental data loss
- Clear user intent before action
- Matches common file manager patterns

### 7.13 Sidebar Order: Dashboard → Upload → Jobs → Results → Settings (Post-MVP)

**Decision:** Sidebar navigation order groups related actions together.

**Rationale:**
- Upload and Jobs are frequently used together
- Results follows Jobs as the output
- Settings at bottom (infrequent access)

---

## 8. Risks & Mitigations

| Risk | Impact | Probability | Mitigation | Status |
|------|--------|-------------|------------|--------|
| Phase 1/3 parallel conflicts | HIGH | MEDIUM | Clear file ownership, daily sync | ✅ Resolved |
| Worker test complexity | MEDIUM | MEDIUM | Start with happy path, add edge cases | ✅ Resolved |
| Route refactor breaks E2E | HIGH | HIGH | Update E2E tests as routes change | ✅ Resolved |
| Provider API validation fails | LOW | LOW | Graceful degradation, show validation error | ✅ Resolved |
| Dashboard polling performance | LOW | LOW | Debounce, cancel on unmount | ✅ Resolved |
| Rate limiting on real OCR | HIGH | HIGH | Exponential backoff retry logic | ✅ Resolved |
| Transaction rollback on error | HIGH | MEDIUM | Session management fix | ✅ Resolved |
| Large payload rate limits | MEDIUM | MEDIUM | Batch API for >10 crops | ✅ Resolved |
| SSE connection management | MEDIUM | MEDIUM | Reconnect logic, cleanup on unmount | 🔄 Phase 10 |
| Upload component complexity | LOW | LOW | Shared component with clear props | 🔄 Phase 11 |
| NOT_STARTED jobs accumulation | LOW | LOW | Manual cleanup, no auto-expiration | ✅ Accepted |
| Worker needs restart for changes | LOW | MEDIUM | Hot-reload or process manager | 📋 Backlog |

---

## 9. Open Questions

| Question | Status | Owner | Notes |
|----------|--------|-------|-------|
| Worker hot-reload strategy | Open | Developer | Process manager vs file watcher? |

### Post-MVP Implementation Notes

1. **SSE Connection Management**
   - Reconnect on disconnect with exponential backoff
   - Cleanup EventSource on component unmount
   - Handle multiple tab scenarios (broadcast channel?)

2. **Upload Component Props**
   ```typescript
   interface UploadListProps {
     campaignId: string;
     type: 'voter_list' | 'petition';
     selectable?: boolean;      // true for /jobs/new
     showActions?: boolean;     // remove, view details
     onSelectionChange?: (selected: Upload[]) => void;
   }
   ```

3. **Feature Flags Scope**
   - Only visible in non-production modes
   - Stored in localStorage for dev convenience
   - Reset on mode change

---

## 10. References

| Document | Status | Purpose |
|----------|--------|---------|
| `openspec/SPEC.md` | v1.5 (this file) | Technical specification |
| `openspec/PROGRESS.md` | Current | Implementation progress tracking |
| `openspec/adr/` | Active | Architecture Decision Records |
| `.agent-workspace/problem/PROGRESS.md` | Current | Daily progress, blockers, questions |
| `.agent-workspace/problem/REQUIREMENTS-NEXT-ITERATION-2026-03-12.md` | Complete | Post-MVP requirements |
| `.agent-workspace/problem/REQUIREMENTS-UPDATE-2026-03-11.md` | Complete | Original MVP requirements |
| `docs/configuration-modes.md` | Active | Configuration documentation |
| `docs/running-locally.md` | Active | Local development guide |
| `docs/demo-walkthrough.md` | Active | Demo mode guide |

---

## Appendix A: Code Examples

### Dashboard Polling (Svelte)

```svelte
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { page } from '$app/stores';

  let metrics = $state(null);
  let interval: number;

  onMount(async () => {
    await fetchMetrics();
    interval = setInterval(fetchMetrics, 10000);
  });

  onDestroy(() => clearInterval(interval));

  async function fetchMetrics() {
    const res = await fetch(`/api/campaigns/${$page.params.id}/metrics`);
    metrics = await res.json();
  }
</script>
```

### Provider Validation (Python)

```python
async def validate_provider_key(provider: str, api_key: str) -> tuple[bool, list[str]]:
    """Validate API key by calling list models endpoint."""
    if provider == "openai":
        client = OpenAI(api_key=api_key)
        models = client.models.list()
        return True, [m.id for m in models if "gpt" in m.id]
    # ... other providers
```

### Status Computation (Python)

```python
def compute_campaign_status(campaign_id: int, db: Session) -> CampaignStatus:
    jobs = db.query(MatcherJob).filter_by(campaign_id=campaign_id).order_by(MatcherJob.created_at).all()

    if not jobs and not has_uploads(campaign_id, db):
        return CampaignStatus.NOT_STARTED

    last_job = jobs[-1] if jobs else None
    results_count = db.query(MatchResult).filter_by(campaign_id=campaign_id).count()

    if last_job and last_job.status == JobStatus.FAILED and results_count == 0:
        return CampaignStatus.ERROR

    if last_job and last_job.status in [JobStatus.OCR_STARTED, JobStatus.MATCHING]:
        return CampaignStatus.IN_PROGRESS

    # ... additional logic
```

---

## Appendix B: Configuration

### Environment Variables

```bash
# LLM Provider Keys (fallback for testing)
LLM_KEYS={"openai":"sk-...","gemini":"...","mistral":"..."}

# Demo Mode
DEMO_MODE=false

# Simulation Mode (for development without real LLM API keys)
# When enabled, OCR returns mock data instead of calling LLM APIs
FEATURE_ENABLE_SIMULATION=1

# Polling Interval (seconds)
DASHBOARD_POLL_INTERVAL=10
```

### Static Configuration

```typescript
// frontend-svelt/src/lib/config/providers.ts
export const PROVIDERS = {
  openai: {
    name: 'OpenAI',
    models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4']
  },
  gemini: {
    name: 'Gemini',
    models: ['gemini-1.5-pro', 'gemini-1.5-flash']
  },
  mistral: {
    name: 'Mistral',
    models: ['mistral-large-latest', 'pixtral-12b-2409']
  }
};
```

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| Campaign | A petition verification project with voters and signatures |
| Job | A batch OCR + matching operation for a campaign |
| NOT_STARTED | Job state: saved but not yet executed (Post-MVP) |
| Provider | LLM service (OpenAI, Gemini, Mistral) used for OCR |
| Snapshot | Stored copy of provider name/model at job creation time |
| Confidence tier | High (≥0.8), Medium (0.5-0.8), Low (<0.5) match confidence |
| Virtual campaign | In-memory campaign for demo mode (not persisted) |
| SSE | Server-Sent Events for real-time updates |
| Upload List | Shared component showing uploaded files (Post-MVP) |
| Mode | Deployment context: Production, Demo, Simulation, Dev |

---

**Document Status:** v1.5 - MVP complete, Post-MVP Phases 7-12 planned
**Last Updated:** 2026-03-12

---

## Appendix D: MVP Enhancements (Complete)

### D.1 OCR Cache Tracking

**Feature:** Visibility into cached vs new OCR results during job processing.

**Status:** ✅ Complete

**Database Fields Added:**
```sql
ALTER TABLE matcher_job ADD COLUMN force_reprocess BOOLEAN DEFAULT FALSE;
ALTER TABLE matcher_job ADD COLUMN cached_ocr_count INTEGER DEFAULT 0;
ALTER TABLE matcher_job ADD COLUMN new_ocr_count INTEGER DEFAULT 0;
```

**UI Components:**
- "Re-process all crops" checkbox in job creation modal
- "X new · Y cached" indicator in job details page
- "re-processed" badge when force_reprocess was enabled

**Migration:** `20260312210000_add_ocr_cache_tracking_fields.py`

### D.2 Configuration Modes

**Feature:** Comprehensive configuration documentation for all deployment scenarios.

**Status:** ✅ Complete

**Modes Documented:**
1. Production (real LLM, persisted data)
2. Dev with Real LLM (local DB, real API)
3. Simulation (mock LLM, fast iteration)
4. Demo (in-memory, showcase mode)
5. Testing (isolated, deterministic)

**File:** `docs/configuration-modes.md`

**Environment Variables:**
```bash
FEATURE_ENABLE_SIMULATION=1  # Mock LLM for dev/testing
PUBLIC_DEMO_MODE=false       # Enable demo routes
ENV_FILE=.env.dev            # Backend env file selection
```

### D.3 Database Cleanup Utility

**Feature:** Purge old campaigns while keeping recent data.

**Status:** ✅ Complete

**Script:** `backend/scripts/purge_old_campaigns.py`

**Usage:**
```bash
python scripts/purge_old_campaigns.py --keep 10 [--dry-run]
```

**Result:** Removed 1,164 rows (201 old campaigns) in testing.

### D.4 Real OCR Infrastructure

**Feature:** Rate limiting retry logic for production OCR calls.

**Status:** ✅ Complete

**Implementation:**
- Exponential backoff retry (max 3 attempts, 5s base delay)
- `OCR_REAL_DELAY_SECONDS` increased from 0.5 → 2.0
- Debug logging for OCR responses

### D.5 Production Hardening

**Status:** ✅ Complete

| Item | Status | Description |
|------|--------|-------------|
| Session management | ✅ Complete | Transaction rollback after errors |
| Batching integration | ✅ Complete | Batch API for payloads >10 crops |
| Worker hot-reload | 📋 Backlog | Process manager or file watcher for dev UX |

---

## Appendix E: Post-MVP Requirements Summary (Phases 7-12)

### Phase 7: Quick Fixes & Cleanup

| ID | Requirement | Priority |
|----|-------------|----------|
| UT-001 | Logo mode-aware destinations | HIGH |
| NF-001 | Hide login/signup on landing | HIGH |
| NF-002 | Mode-aware CTA button | HIGH |
| NF-003 | Landing page cleanup | MEDIUM |
| UF-011 | Sidebar reorder | MEDIUM |
| DX-001 | Remove stale documents | MEDIUM |
| DX-004 | Fix critical TS errors | MEDIUM |

### Phase 8: Campaign List & Dashboard

| ID | Requirement | Priority |
|----|-------------|----------|
| UF-003 | Sortable columns | HIGH |
| UF-004 | Search | HIGH |
| UF-008 | N/A for empty metrics | HIGH |
| UF-009 | N/A when no data | HIGH |
| UF-010 | Hide "View Results" if empty | HIGH |

### Phase 9: Job Creation Flow

| ID | Requirement | Priority |
|----|-------------|----------|
| UF-035 | /jobs/new route | HIGH |
| UF-036 | File selection (existing) | HIGH |
| UF-037 | Inline upload | HIGH |
| UF-038 | Duplicate file handling | HIGH |
| UF-039 | Provider/model selection | HIGH |
| UF-040 | Save job (NOT_STARTED) | HIGH |
| UF-041 | Run immediately | HIGH |
| UF-042 | LLM validation | HIGH |
| UF-043 | Return to list | HIGH |

### Phase 10: Jobs List Enhancements

| ID | Requirement | Priority |
|----|-------------|----------|
| UF-019 | Default sort by created date | HIGH |
| UF-020 | Show last updated timestamp | HIGH |
| UF-021 | Status dynamic update (SSE) | HIGH |
| UF-023 | Warn if no uploads | HIGH |
| UF-044 | Status filter | HIGH |
| UF-045 | Keep quick modal | MEDIUM |

### Phase 11: Upload Enhancements

| ID | Requirement | Priority |
|----|-------------|----------|
| UF-013 | Show existing uploads | HIGH |
| UF-014 | Handle duplicates | HIGH |
| UF-015 | Upload queue | MEDIUM |
| UF-016 | Remove all files | MEDIUM |
| UF-017 | Fix progress bar | HIGH |
| UF-018 | Better remove icon | LOW |

### Phase 12: Polish & Settings

| ID | Requirement | Priority |
|----|-------------|----------|
| UF-024 | Job duration display | HIGH |
| UF-025 | Job ended timestamp | HIGH |
| UF-027 | View results conditional | HIGH |
| UF-028 | Progress animations | MEDIUM |
| UF-005 | Duplicate name warning | MEDIUM |
| UF-007 | New campaign on top | MEDIUM |
| UF-029 | Default model per vendor | MEDIUM |
| UF-030 | Feature flags non-prod | HIGH |
| UF-031 | Settings: Reset Data | MEDIUM |
| UF-001 | Timezone option | MEDIUM |
| DX-004 | Fix remaining TS errors | MEDIUM |

---

## Appendix F: Architecture Decision Records (ADRs)

### ADR Index

ADRs are stored in `openspec/adr/` and track notable technical decisions.

| ADR | Title | Status | Date | Phase |
|-----|-------|--------|------|-------|
| (None yet) | - | - | - | - |

### Creating New ADRs

When making decisions that:
- Change something from this SPEC
- Introduce new patterns or approaches
- Have significant trade-offs
- Affect multiple phases or future work

**Process:**
1. Create `openspec/adr/NNNN-kebab-title.md` using template in §6 (Progress Reporting)
2. Add entry to ADR index above
3. Reference in PROGRESS.md Decisions Log
4. Update SPEC if decision modifies existing content

### ADR Template Quick Reference

```markdown
# ADR-NNNN: [Title]

**Date:** YYYY-MM-DD
**Status:** [Proposed / Accepted / Deprecated / Superseded]

## Context
[Problem being addressed]

## Decision
[The change being made]

## Alternatives Considered
[Options evaluated]

## Consequences
[Positive, negative, risks]

## References
- SPEC section: §X.X
- Requirements: [IDs]
```
