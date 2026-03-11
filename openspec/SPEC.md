# Votecatcher MVP Technical Specification

**Status:** Draft
**Version:** 1.2
**Last Updated:** 2026-03-11
**Author:** Solutions Architect Agent

---

## Executive Summary

This specification defines the technical implementation for Votecatcher MVP completion, focusing on stability, page hierarchy redesign, and LLM provider configuration. The MVP targets a 3-4 week timeline with clear phase gates. Key architectural decisions include: campaign-scoped navigation with numeric IDs, snapshot-based provider storage (no foreign keys), on-demand status computation, and polling-based dashboard updates. Phase 1 (Stability) and Phase 3 (Page Hierarchy) can proceed in parallel.

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
/                             → Marketing landing (placeholder)
/workspace                    → Redirect to /workspace/campaigns
/workspace/campaigns          → Campaign list (enhanced table)
/workspace/[id]               → Campaign dashboard
/workspace/[id]/jobs          → Jobs scoped to campaign
/workspace/[id]/jobs/[job_id] → Job details
/workspace/[id]/results       → Results scoped to campaign
/workspace/[id]/upload        → Upload page with tabs (Voter List / Petitions)
/workspace/settings           → Global settings + LLM providers
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

| Component | Location | Purpose | MVP Status |
|-----------|----------|---------|------------|
| `CampaignDashboard` | `/workspace/[id]` | Metrics cards, donut chart, recent jobs | Required |
| `CampaignSidebar` | Layout | Campaign-scoped nav + switcher | Required |
| `UploadTabs` | `/workspace/[id]/upload` | Tabbed voter/petition upload | Required |
| `ProviderSettings` | `/workspace/settings` | LLM provider configuration | Stretch |
| `ConfidenceDonut` | Dashboard | High/Medium/Low distribution | Required |
| `StatusBadge` | Shared | Campaign/job status indicators | Required |
| `CampaignList` | `/workspace/campaigns` | Enhanced table with status, filtering | **Phase 4 Stretch** |

> **Note:** Enhanced CampaignList (US-018 partial) is deferred to Phase 4. MVP includes basic campaign list only.

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

#### Modified Table: `matcher_job`

```sql
ALTER TABLE matcher_job ADD COLUMN provider_name TEXT;    -- Snapshot: 'openai'
ALTER TABLE matcher_job ADD COLUMN provider_model TEXT;   -- Snapshot: 'gpt-4o'
ALTER TABLE matcher_job ADD COLUMN parent_job_id INTEGER REFERENCES matcher_job(id);
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

### Phase 4: New Features (Week 3-4) - STRETCH

| Task | Priority | Effort | Dependencies |
|------|----------|--------|--------------|
| LLM provider config UI | HIGH | 2-3 days | Phase 1-3 |
| Provider selection on job | MEDIUM | 1-2 days | Provider config |
| Campaign list enhancement (US-018 partial) | LOW | 1-2 days | Phase 3 |

> **Note:** Campaign list enhancement includes status badges, progress bars, confidence display, and filtering. Basic campaign list is included in MVP; enhanced version is stretch.

### Critical Path

```
Phase 1 (Stability) ────────┐
                             ├──▶ Phase 2 (Polish) ──▶ MVP Ready
Phase 3 (Page Hierarchy) ───┘
```

### Phase Gate Criteria

Each phase has explicit entrance and exit criteria. No phase may proceed without meeting exit criteria.

#### Phase 1: Stability

| Gate | Criteria |
|------|----------|
| **Entrance** | Development environment functional, existing tests pass |
| **Exit** | - Worker tests pass (≥3 scenarios) <br> - Dashboard metrics API returns real data <br> - Confidence donut renders correctly <br> - Error responses include CORS headers |

#### Phase 2: Polish

| Gate | Criteria |
|------|----------|
| **Entrance** | Phase 1 exit criteria met, Phase 3 routes exist |
| **Exit** | - Keyboard navigation works (Tab through all pages) <br> - E2E full-flow test passes <br> - README updated with new routes <br> - No console errors in normal flows |

#### Phase 3: Page Hierarchy

| Gate | Criteria |
|------|----------|
| **Entrance** | None (parallel with Phase 1) |
| **Exit** | - All 6 navigation BDD scenarios pass <br> - Campaign-scoped routes work <br> - Campaign switcher preserves route segment <br> - Demo mode functional at /workspace/demo <br> - Root landing page exists |

#### Phase 4: Stretch Features

| Gate | Criteria |
|------|----------|
| **Entrance** | Phase 1, 2, 3 complete |
| **Exit** | - LLM provider config saves to DB <br> - Provider selection on job creation works <br> - Campaign list shows status badges |

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

Developers must maintain a PROGRESS.md file with regular updates.

#### File Location

`.agent-workspace/problem/PROGRESS.md`

#### Required Sections

```markdown
# Votecatcher MVP Progress

**Last Updated:** YYYY-MM-DD HH:MM
**Current Phase:** [Phase X]
**Overall Status:** [On Track / At Risk / Blocked]

---

## Phase Status

| Phase | Status | Completion % | Notes |
|-------|--------|--------------|-------|
| Phase 1: Stability | [Not Started / In Progress / Complete] | X% | Brief note |
| Phase 2: Polish | [Not Started / In Progress / Complete] | X% | Brief note |
| Phase 3: Page Hierarchy | [Not Started / In Progress / Complete] | X% | Brief note |
| Phase 4: Stretch | [Not Started / In Progress / Complete] | X% | Brief note |

---

## Current Work

**Task:** [Task name from SPEC]
**Started:** YYYY-MM-DD
**Status:** [In Progress / Blocked / Review]

### Progress
- [ ] Subtask 1
- [ ] Subtask 2
- [x] Completed subtask

### Test Results
```
[Paste relevant test output]
```

---

## Issues & Questions

| # | Type | Description | Status | Resolution |
|---|------|-------------|--------|------------|
| 1 | Blocker | Description of issue | Open/Resolved | How resolved or proposed solution |
| 2 | Question | Clarification needed | Pending/Answered | Answer or awaiting input |

---

## SPEC Deviations

| Date | Section | Deviation | Reason | Approved By |
|------|---------|-----------|--------|-------------|
| YYYY-MM-DD | §X.X | What changed | Why | [User/Architect] |

---

## Daily Log

### YYYY-MM-DD
- Completed: [list]
- In Progress: [list]
- Blocked: [list]
- Next: [list]
```

#### Update Cadence

| Event | Action |
|-------|--------|
| Start task | Update "Current Work" section |
| Complete subtask | Check off in "Progress" list |
| Test pass/fail | Update "Test Results" |
| Encounter issue | Add to "Issues & Questions" |
| Deviate from SPEC | Add to "SPEC Deviations", get approval |
| End of work session | Update "Phase Status" and "Daily Log" |
| Phase gate | Run verification, update "Phase Status" |

#### Issue Triage

When adding issues, classify by type:

| Type | Definition | Response Time |
|------|------------|---------------|
| **Blocker** | Cannot proceed without resolution | Immediate |
| **Technical** | Implementation challenge | Same day |
| **Question** | Clarification on requirements/spec | Next session |
| **Enhancement** | Nice-to-have, not blocking | Defer |

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

---

## 8. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Phase 1/3 parallel conflicts | HIGH | MEDIUM | Clear file ownership, daily sync |
| Worker test complexity | MEDIUM | MEDIUM | Start with happy path, add edge cases |
| Route refactor breaks E2E | HIGH | HIGH | Update E2E tests as routes change |
| Provider API validation fails | LOW | LOW | Graceful degradation, show validation error |
| Dashboard polling performance | LOW | LOW | Debounce, cancel on unmount |

---

## 9. Open Questions

| Question | Status | Owner |
|----------|--------|-------|
| None outstanding | Resolved | - |

---

## 10. References

- Requirements: `.agent-workspace/problem/REQUIREMENTS-UPDATE-2026-03-11.md`
- Diagrams: `.agent-workspace/problem/diagrams/`
- Existing codebase: FastAPI + SvelteKit + SQLModel/Drizzle

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
| Provider | LLM service (OpenAI, Gemini, Mistral) used for OCR |
| Snapshot | Stored copy of provider name/model at job creation time |
| Confidence tier | High (≥0.8), Medium (0.5-0.8), Low (<0.5) match confidence |
| Virtual campaign | In-memory campaign for demo mode (not persisted) |

---

**Document Status:** Draft v1.2 - Added phase gate criteria, BDD/TDD validation protocol, PROGRESS.md reporting requirements
**Last Updated:** 2026-03-11
