# Phase 4: Integration & E2E Design

**Date:** 2026-03-11
**Status:** Draft
**Author:** Developer Agent

## Overview

Complete the core user workflow by implementing file uploads, job status tracking with SSE, results visualization, and comprehensive E2E testing.

## Architecture

### Current State (End of Phase 3)

```
Frontend Foundation:
├── Base UI Components (136 tests) ✅
├── Layout & Navigation (13 tests) ✅
├── Loading/Error Components (28 tests) ✅
├── API Integration (42 tests) ✅
│   ├── API client wrapper
│   ├── Campaigns store (CRUD)
│   ├── Jobs store (create/fetch/cancel)
│   ├── Dashboard integration
│   └── Campaigns list page
└── Total: 219 tests passing
```

### Phase 4 Scope

```
Phase 4: Integration & E2E
├── Part A: File Upload Pages (~4 hours)
│   ├── Voter list upload
│   ├── Petition upload with pre-crop
│   └── Upload progress tracking
├── Part B: Job Status & SSE (~3 hours)
│   ├── SSE connection in jobs store
│   ├── Job status page with live updates
│   └── Cancel job functionality
├── Part C: Results Visualization (~3 hours)
│   ├── Results store (paginated, filtered)
│   ├── Results table with confidence badges
│   └── CSV export
├── Part D: Session Management (~2 hours)
│   ├── Session save/load
│   └── Session export (ZIP)
└── Part E: E2E Testing (~4 hours)
    ├── Full workflow test
    ├── Error scenarios
    └── Accessibility audit
```

## Implementation Plan

### Part A: File Upload Pages (~4 hours)

#### Task 1: File Upload Store

**Files:**
- Create: `src/lib/stores/uploads.ts`
- Create: `src/lib/stores/uploads.test.ts`

**Features:**
- Voter list upload (CSV/Excel validation)
- Petition upload (PDF with pre-crop)
- Progress tracking (%)
- Error handling

**API Endpoints Used:**
- `POST /api/upload/voter-list`
- `POST /api/upload/petition`

#### Task 2: Voter List Upload Page

**Files:**
- Modify: `src/routes/workspace/upload/voters/+page.svelte`
- Create: `src/routes/workspace/upload/voters/+page.test.ts`

**Features:**
- Drag-and-drop file upload
- CSV/Excel validation (required columns)
- Preview first 5 rows
- Progress indicator
- Success/error states

#### Task 3: Petition Upload Page

**Files:**
- Modify: `src/routes/workspace/upload/petitions/+page.svelte`
- Create: `src/routes/workspace/upload/petitions/+page.test.ts`

**Features:**
- PDF file upload
- Crop region selection (DC preset for MVP)
- Progress indicator
- Crop preview thumbnails
- Job creation trigger

---

### Part B: Job Status & SSE (~3 hours)

#### Task 4: SSE Integration in Jobs Store

**Files:**
- Modify: `src/lib/stores/jobs.ts`
- Modify: `src/lib/stores/jobs.test.ts`

**Features:**
- `connectToJob(id)` - Open SSE connection
- `disconnect()` - Close connection
- Auto-reconnect (3 retries with backoff)
- Connection state tracking
- Event handlers: status_update, matching_progress, job_complete, job_error

**SSE Events (from SPEC.md §5.3):**
```typescript
{ "event": "status_update", "data": { "status": "OCR_STARTED", ... } }
{ "event": "matching_progress", "data": { "processed": 50, "total": 100 } }
{ "event": "job_complete", "data": { "status": "MATCHING_COMPLETED", "summary": {...} } }
{ "event": "job_error", "data": { "error": "...", "status": "OCR_FAILED" } }
```

#### Task 5: Job Status Page

**Files:**
- Modify: `src/routes/workspace/jobs/+page.svelte`
- Create: `src/routes/workspace/jobs/[id]/+page.svelte`
- Create: `src/routes/workspace/jobs/[id]/+page.test.ts`

**Features:**
- Real-time status updates via SSE
- Progress bar for OCR/matching
- Status badges (NOT_STARTED → OCR_PENDING → ... → MATCHING_COMPLETED)
- Cancel button (with confirmation)
- Error display with retry
- Results link when complete

---

### Part C: Results Visualization (~3 hours)

#### Task 6: Dashboard Store

**Files:**
- Create: `src/lib/stores/dashboard.ts`
- Create: `src/lib/stores/dashboard.test.ts`

**Features:**
- Fetch campaign metrics from API (not hardcoded)
- Real-time updates via SSE on job_complete event
- Loading/error states

**API Endpoints Used:**
- `GET /api/campaigns/{id}/metrics` - Total signatures, confidence breakdown
- `GET /api/jobs?campaign_id={id}` - Active/recent jobs

#### Task 7: Results Store

**Files:**
- Create: `src/lib/stores/results.ts`
- Create: `src/lib/stores/results.test.ts`

**Features:**
- Paginated fetching (page, page_size)
- Confidence filtering (HIGH, MEDIUM, LOW, ALL)
- Loading/error states
- Summary stats
- CSV export functionality

**API Endpoints Used:**
- `GET /api/jobs/{job_id}/results?page=1&page_size=20&confidence=HIGH`
- `GET /api/jobs/{job_id}/results/export` (CSV download)

#### Task 8: Results Table Component

**Files:**
- Create: `src/lib/components/results/ResultsTable.svelte`
- Create: `src/lib/components/results/ResultsTable.test.ts`
- Create: `src/lib/components/results/ConfidenceBadge.svelte`
- Create: `src/lib/components/results/CsvExportButton.svelte`

**Features:**
- Columns: Crop Image, OCR Text, Top Match, Confidence, Actions
- ConfidenceBadge component (HIGH=green, MEDIUM=yellow, LOW=red)
- Pagination controls
- Confidence filter tabs
- Lazy-loaded crop images
- CSV export button with download trigger

#### Task 9: Dashboard Page

**Files:**
- Modify: `src/routes/workspace/dashboard/+page.svelte`
- Create: `src/routes/workspace/dashboard/+page.test.ts`

**Features:**
- Display total signatures processed
- Confidence distribution (pie/bar chart or stats)
- Progress toward target (if configured)
- Recent jobs list
- Update on SSE job_complete event

---

### Part D: Session Management (~2 hours)

#### Task 10: Session Store

**Files:**
- Create: `src/lib/stores/sessions.ts`
- Create: `src/lib/stores/sessions.test.ts`

**Features:**
- `save(name)` - Save current workspace state
- `load(id)` - Load saved session
- `export(id)` - Download as ZIP
- `list()` - List saved sessions
- Loading/error states

**API Endpoints (Phase 4 scope - NOT deferred):**
- `POST /api/sessions` - Save session
- `GET /api/sessions/{id}` - Load session
- `GET /api/sessions/{id}/export` - Export as ZIP
- `GET /api/sessions` - List sessions

#### Task 11: Session UI

**Files:**
- Create: `src/routes/workspace/sessions/+page.svelte`
- Create: `src/routes/workspace/sessions/+page.test.ts`
- Add to sidebar: Sessions nav item

**Features:**
- Save session modal with name input
- Load session dropdown with confirmation
- Export button (ZIP download)
- Session list with metadata (date, campaign, status)

---

### Part E: Demo Mode (~2 hours)

#### Task 12: Demo Store

**Files:**
- Create: `src/lib/stores/demo.ts`
- Create: `src/lib/stores/demo.test.ts`

**Features:**
- `isDemoMode` - Check feature flag
- `reset()` - Clear all user data
- `loadPrebaked(sessionName)` - Load demo session
- Confirmation dialog state

**API Endpoints Used:**
- `POST /api/demo/reset` - Reset demo data
- `GET /api/demo/sessions` - List pre-baked demo sessions

#### Task 13: Demo UI

**Files:**
- Create: `src/routes/workspace/demo/+page.svelte`
- Create: `src/routes/workspace/demo/+page.test.ts`
- Add to workspace layout (conditional, behind feature flag)

**Features:**
- Demo mode banner (visible when demo_mode=true)
- Reset Demo button with confirmation dialog
- Load Pre-baked Session dropdown
- Feature flag visibility check

---

### Part F: E2E Testing (~4 hours)

#### Task 14: E2E Test Setup

**Files:**
- Create: `tests/e2e/setup.ts`
- Create: `tests/e2e/fixtures.ts`
- Create: `playwright.config.ts`

**Setup:**
- Backend running on port 8000
- Frontend running on port 5173
- Test database isolation
- Authentication mock (if needed)

#### Task 12: Full Workflow E2E Test

**Files:**
- Create: `tests/e2e/full-workflow.spec.ts`

**Test Scenario:**
```gherkin
Feature: Full petition verification workflow

  Scenario: Happy path
    Given I am on the workspace dashboard
    When I create a campaign "DC 2024"
    And I upload the voter list "fake_voter_records.csv"
    And I upload a petition "fake_signed_petitions.pdf"
    And I create a matcher job
    Then I see job status "OCR_STARTED" in real-time
    And I see progress updates
    When the job completes
    Then I see "MATCHING_COMPLETED" status
    And I navigate to results
    And I see match results with confidence badges
    And I can filter by "HIGH" confidence
    And I can export results as CSV
```

#### Task 13: Error Scenario E2E Tests

**Files:**
- Create: `tests/e2e/errors.spec.ts`

**Scenarios:**
- Invalid file format upload
- Network error during job
- Job cancellation
- Session timeout

#### Task 14: Accessibility E2E Test

**Files:**
- Create: `tests/e2e/accessibility.spec.ts`

**Tests:**
- Keyboard navigation (Tab through all pages)
- Screen reader announcements (status updates)
- Focus management (modal open/close)
- Color contrast verification

---

### Part G: User Documentation (~3 hours)

#### Task 18: Update README.md

**Files:**
- Modify: `README.md`

**Content:**
- Quick start guide (5-minute setup)
- Prerequisites (Python 3.12+, Node 20+, Docker)
- Environment variables reference
- Development setup (`docker-compose up`)
- Production deployment basics

#### Task 19: Deployment Guide

**Files:**
- Create: `docs/deployment.md`

**Content:**
- Single VPS deployment (DigitalOcean, Hetzner)
- Docker Compose production setup
- Environment configuration
- Database setup (PostgreSQL/SQLite)
- HTTPS with Caddy/nginx
- Backup strategy
- Troubleshooting common issues

#### Task 20: User Guide

**Files:**
- Create: `docs/user-guide.md`

**Content:**
- Campaign creation and configuration
- Uploading voter lists (CSV/Excel format requirements)
- Uploading petitions (PDF requirements, DC preset)
- Understanding job status and progress
- Interpreting match results and confidence levels
- Filtering and exporting results
- Session save/load/export
- Demo mode usage

#### Task 21: Configuration Reference

**Files:**
- Create: `docs/configuration.md`

**Content:**
- All environment variables with descriptions
- Feature flags reference
- OCR provider configuration (OpenAI, Gemini, Mistral)
- Database options (PostgreSQL, SQLite)
- File storage configuration
- Performance tuning options

#### Task 22: API Documentation

**Files:**
- Verify: OpenAPI spec at `openapi.yaml`
- Create: `docs/api-usage.md` (optional - for API consumers)

**Content:**
- Link to interactive API docs (Swagger UI)
- Authentication (if implemented)
- Common API patterns
- Rate limits and best practices

---

## Technical Patterns

### SSE Connection Management

```typescript
// src/lib/stores/jobs.ts
interface SSEState {
  connected: boolean;
  reconnectAttempts: number;
  error: string | null;
}

function createJobsStore() {
  let eventSource: EventSource | null = null;
  const maxRetries = 3;
  const retryDelay = 1000; // ms, exponential backoff

  return {
    // ... existing methods ...

    connectToJob(jobId: string) {
      if (eventSource) {
        eventSource.close();
      }

      const url = `${PUBLIC_API_URL}/api/jobs/${jobId}/status`;
      eventSource = new EventSource(url);

      eventSource.onopen = () => {
        update(s => ({ ...s, sse: { connected: true, reconnectAttempts: 0, error: null } }));
      };

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleSSEEvent(data);
      };

      eventSource.onerror = () => {
        const attempts = get(currentState).sse.reconnectAttempts + 1;
        
        if (attempts < maxRetries) {
          setTimeout(() => this.connectToJob(jobId), retryDelay * Math.pow(2, attempts));
        } else {
          update(s => ({ 
            ...s, 
            sse: { connected: false, reconnectAttempts: attempts, error: 'Connection lost' } 
          }));
        }
      };
    },

    disconnect() {
      eventSource?.close();
      eventSource = null;
      update(s => ({ ...s, sse: { connected: false, reconnectAttempts: 0, error: null } }));
    }
  };
}
```

### File Upload with Progress

```typescript
// src/lib/stores/uploads.ts
interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

async function uploadWithProgress(
  file: File,
  endpoint: string,
  onProgress: (progress: UploadProgress) => void
): Promise<Response> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        onProgress({
          loaded: e.loaded,
          total: e.total,
          percentage: Math.round((e.loaded / e.total) * 100)
        });
      }
    });

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.response));
      } else {
        reject(new Error(`Upload failed: ${xhr.statusText}`));
      }
    });

    xhr.addEventListener('error', () => reject(new Error('Network error')));

    const formData = new FormData();
    formData.append('file', file);

    xhr.open('POST', endpoint);
    xhr.send(formData);
  });
}
```

### Results Pagination

```typescript
// src/lib/stores/results.ts
interface ResultsState {
  results: MatchResult[];
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
  filter: 'ALL' | 'HIGH' | 'MEDIUM' | 'LOW';
  loading: boolean;
  error: string | null;
}

async fetchResults(jobId: string, page: number = 1) {
  update(s => ({ ...s, loading: true, error: null }));

  try {
    const client = getApiClient();
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: '20',
      ...(state.filter !== 'ALL' && { confidence: state.filter })
    });

    const response = await client.getJobResults(jobId, params);
    
    update(s => ({
      ...s,
      results: response.results,
      pagination: {
        page: response.page,
        pageSize: response.page_size,
        total: response.total,
        totalPages: Math.ceil(response.total / response.page_size)
      },
      loading: false
    }));
  } catch (error) {
    // error handling
  }
}
```

---

## Testing Strategy

### Unit Tests (Vitest)
- Stores: Mock API client, test state transitions
- Components: Test rendering, events, accessibility
- Target: >80% coverage for new code

### Integration Tests (MSW)
- Page components with mocked API handlers
- SSE events simulated with mock EventSource
- File upload with mock XMLHttpRequest

### E2E Tests (Playwright)
- Full workflow with real backend
- Browser automation for UI testing
- Screenshot comparisons (optional)

---

## Exit Criteria

### Part A: File Upload Pages
- [ ] Voter list upload validates CSV/Excel
- [ ] Petition upload creates crops
- [ ] Progress indicators show percentage
- [ ] Error states display retry options

### Part B: Job Status & SSE
- [ ] SSE connection opens/closes correctly
- [ ] Job status updates in real-time
- [ ] Cancel button stops job
- [ ] Reconnection works after network drop

### Part C: Results Visualization
- [ ] Dashboard shows real metrics from API (not hardcoded)
- [ ] Results table paginates correctly
- [ ] Confidence filters work
- [ ] CSV export downloads file
- [ ] Crop images lazy-load

### Part D: Session Management
- [ ] Save session stores workspace state
- [ ] Load session restores state
- [ ] Export creates valid ZIP
- [ ] Session API endpoints implemented (NOT deferred)

### Part E: Demo Mode
- [ ] Demo reset clears user data
- [ ] Pre-baked session loads correctly
- [ ] Feature flag controls visibility
- [ ] Confirmation dialog works

### Part F: E2E Testing
- [ ] Full workflow test passes
- [ ] Error scenarios handled gracefully
- [ ] Accessibility audit passes

### Part G: Documentation
- [ ] README updated with quick start
- [ ] Deployment guide complete
- [ ] User guide covers all features
- [ ] Configuration reference accurate
- [ ] API docs accessible

---

## Timeline

| Day | Tasks | Duration | Cumulative |
|-----|-------|----------|------------|
| 1 | Part A: File Upload | 4h | 4h |
| 2 | Part B: SSE + Job Status | 3h | 7h |
| 3 | Part C: Results + Dashboard | 4h | 11h |
| 4 | Part D: Sessions | 2h | 13h |
| 5 | Part E: Demo Mode | 2h | 15h |
| 6 | Part F: E2E Tests | 4h | 19h |
| 7 | Part G: Documentation | 3h | 22h |

**Total Estimated:** 22 hours (6-7 days)

---

### Backend APIs (All Ready ✅)

**Core Workflow:**
- POST /api/upload/voter-list
- POST /api/upload/petition
- POST /api/jobs
- GET /api/jobs/{id}
- GET /api/jobs/{id}/status (SSE)
- POST /api/jobs/{id}/cancel
- GET /api/jobs/{job_id}/results
- GET /api/jobs/{job_id}/results/export

**Session Management (Phase 4 scope - implement now):**
- POST /api/sessions
- GET /api/sessions/{id}
- GET /api/sessions/{id}/export
- GET /api/sessions

**Demo Mode:**
- GET /api/config/feature-flags
- POST /api/demo/reset
- GET /api/demo/sessions

**Dashboard Metrics:**
- GET /api/campaigns/{id}/metrics
- GET /api/jobs?campaign_id={id}

### Sample Data (Available ✅)
- `samples/dc/fake_voter_records.csv` (100K voters)
- `samples/dc/fake_signed_petitions.pdf`
- `samples/dc/fake_signed_petitions_1-10.pdf`

---

## Success Criteria

1. **User can complete full workflow:** Create campaign → Upload files → Start job → View results
2. **Real-time updates work:** SSE delivers job status without refresh
3. **Results are actionable:** User can filter, paginate, and export
4. **Error handling is graceful:** Clear messages, retry options
5. **Accessibility is maintained:** WCAG 2.2 AA compliance
6. **E2E tests pass:** Full workflow automated

---

## Next Steps

1. Review and approve this plan
2. Create detailed implementation plan with `writing-plans` skill
3. Begin Part A: File Upload Pages with TDD
4. Update PROGRESS.md after each part
