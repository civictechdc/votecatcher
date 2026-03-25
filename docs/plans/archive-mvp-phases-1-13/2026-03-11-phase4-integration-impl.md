# Phase 4: Integration & E2E Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete file uploads, SSE job tracking, results visualization, and E2E tests

**Architecture:** Svelte stores for state, SSE for real-time updates, Playwright for E2E

**Tech Stack:** Svelte 5 runes, EventSource API, XHR upload progress, Playwright

---

## Part A: File Upload Pages (Day 1 - ~4 hours)

### Task 1: File Upload Store

**Files:**
- Create: `frontend-svelt/src/lib/stores/uploads.ts`
- Create: `frontend-svelt/src/lib/stores/uploads.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-svelt/src/lib/stores/uploads.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import { uploads, resetUploadsStore } from './uploads';
import { getApiClient } from './api-client';

vi.mock('./api-client');

describe('Uploads Store', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    resetUploadsStore();
  });

  describe('uploadVoterList', () => {
    it('starts with empty state', () => {
      const state = get(uploads);
      expect(state.voterListUploading).toBe(false);
      expect(state.voterListProgress).toBe(0);
      expect(state.voterListError).toBeNull();
    });

    it('sets uploading state and progress', async () => {
      const mockClient = {
        uploadVoterList: vi.fn().mockImplementation(() => {
          return new Promise((resolve) => {
            setTimeout(() => resolve({ success: true }), 100);
          });
        })
      };
      vi.mocked(getApiClient).mockReturnValue(mockClient as any);

      const promise = uploads.uploadVoterList(new File(['data'], 'voters.csv'));

      let state = get(uploads);
      expect(state.voterListUploading).toBe(true);

      await promise;

      state = get(uploads);
      expect(state.voterListUploading).toBe(false);
      expect(state.voterListProgress).toBe(100);
    });

    it('handles upload errors', async () => {
      const mockClient = {
        uploadVoterList: vi.fn().mockRejectedValue(new Error('Invalid CSV format'))
      };
      vi.mocked(getApiClient).mockReturnValue(mockClient as any);

      await uploads.uploadVoterList(new File(['bad'], 'bad.csv'));

      const state = get(uploads);
      expect(state.voterListError).toBe('Invalid CSV format');
    });
  });

  describe('uploadPetition', () => {
    it('uploads petition with progress tracking', async () => {
      const mockClient = {
        uploadPetition: vi.fn().mockResolvedValue({
          scan_id: 'scan-1',
          crop_count: 10
        })
      };
      vi.mocked(getApiClient).mockReturnValue(mockClient as any);

      const result = await uploads.uploadPetition(
        new File(['pdf'], 'petition.pdf'),
        'campaign-1'
      );

      expect(result.scan_id).toBe('scan-1');
      expect(result.crop_count).toBe(10);

      const state = get(uploads);
      expect(state.petitionUploading).toBe(false);
    });
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend-svelt && bun test src/lib/stores/uploads.test.ts -v`
Expected: FAIL - "Cannot find module './uploads'"

**Step 3: Write minimal implementation**

```typescript
// frontend-svelt/src/lib/stores/uploads.ts
import { writable } from 'svelte/store';
import { getApiClient } from './api-client';

interface UploadsState {
  voterListUploading: boolean;
  voterListProgress: number;
  voterListError: string | null;
  petitionUploading: boolean;
  petitionProgress: number;
  petitionError: string | null;
  lastUploadResult: { scan_id: string; crop_count: number } | null;
}

function createUploadsStore() {
  const { subscribe, set, update } = writable<UploadsState>({
    voterListUploading: false,
    voterListProgress: 0,
    voterListError: null,
    petitionUploading: false,
    petitionProgress: 0,
    petitionError: null,
    lastUploadResult: null
  });

  return {
    subscribe,

    async uploadVoterList(file: File) {
      update(s => ({
        ...s,
        voterListUploading: true,
        voterListProgress: 0,
        voterListError: null
      }));

      try {
        const client = getApiClient();
        const formData = new FormData();
        formData.append('file', file);

        // Note: Real implementation would use XHR for progress
        await client.uploadVoterList(formData);

        update(s => ({
          ...s,
          voterListUploading: false,
          voterListProgress: 100
        }));
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unknown error';
        update(s => ({
          ...s,
          voterListUploading: false,
          voterListError: message
        }));
      }
    },

    async uploadPetition(file: File, campaignId: string) {
      update(s => ({
        ...s,
        petitionUploading: true,
        petitionProgress: 0,
        petitionError: null
      }));

      try {
        const client = getApiClient();
        const formData = new FormData();
        formData.append('file', file);
        formData.append('campaign_id', campaignId);

        const result = await client.uploadPetition(formData);

        update(s => ({
          ...s,
          petitionUploading: false,
          petitionProgress: 100,
          lastUploadResult: result as any
        }));

        return result;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unknown error';
        update(s => ({
          ...s,
          petitionUploading: false,
          petitionError: message
        }));
        throw error;
      }
    },

    clearErrors() {
      update(s => ({
        ...s,
        voterListError: null,
        petitionError: null
      }));
    },

    reset() {
      set({
        voterListUploading: false,
        voterListProgress: 0,
        voterListError: null,
        petitionUploading: false,
        petitionProgress: 0,
        petitionError: null,
        lastUploadResult: null
      });
    }
  };
}

export const uploads = createUploadsStore();

export function resetUploadsStore() {
  uploads.reset();
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend-svelt && bun test src/lib/stores/uploads.test.ts -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add frontend-svelt/src/lib/stores/uploads.ts frontend-svelt/src/lib/stores/uploads.test.ts
git commit -m "feat(frontend): add uploads store with progress tracking"
```

---

### Task 2: Voter List Upload Page

**Files:**
- Modify: `frontend-svelt/src/routes/workspace/upload/voters/+page.svelte`
- Create: `frontend-svelt/src/routes/workspace/upload/voters/+page.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-svelt/src/routes/workspace/upload/voters/+page.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import Page from './+page.svelte';
import { uploads } from '$lib/stores/uploads';

vi.mock('$lib/stores/uploads');

describe('Voter List Upload Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(uploads.subscribe).mockImplementation((fn) => {
      fn({
        voterListUploading: false,
        voterListProgress: 0,
        voterListError: null,
        petitionUploading: false,
        petitionProgress: 0,
        petitionError: null,
        lastUploadResult: null
      });
      return () => {};
    });
  });

  it('displays upload form', () => {
    render(Page);
    expect(screen.getByText(/upload voter list/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/file/i)).toBeInTheDocument();
  });

  it('shows drag and drop zone', () => {
    render(Page);
    expect(screen.getByText(/drag and drop|drop files here/i)).toBeInTheDocument();
  });

  it('calls uploadVoterList when file selected', async () => {
    vi.mocked(uploads.uploadVoterList).mockResolvedValue(undefined);

    render(Page);

    const file = new File(['name,email,voter_id\nJohn,john@test.com,1'], 'voters.csv', {
      type: 'text/csv'
    });

    const input = screen.getByLabelText(/file/i) as HTMLInputElement;
    await fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(uploads.uploadVoterList).toHaveBeenCalledWith(file);
    });
  });

  it('shows progress during upload', async () => {
    let subscriber: any;
    vi.mocked(uploads.subscribe).mockImplementation((fn) => {
      subscriber = fn;
      fn({
        voterListUploading: true,
        voterListProgress: 50,
        voterListError: null,
        petitionUploading: false,
        petitionProgress: 0,
        petitionError: null,
        lastUploadResult: null
      });
      return () => {};
    });

    render(Page);

    expect(screen.getByText('50%')).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend-svelt && bun test src/routes/workspace/upload/voters/+page.test.ts -v`
Expected: FAIL - Page doesn't exist or missing elements

**Step 3: Write minimal implementation**

```svelte
<!-- frontend-svelt/src/routes/workspace/upload/voters/+page.svelte -->
<script lang="ts">
  import { uploads } from '$lib/stores/uploads';
  import { Button, LoadingSpinner } from '$lib/components/ui';
  import { Upload } from 'lucide-svelte';

  let selectedFile: File | null = $state(null);

  function handleFileSelect(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      selectedFile = input.files[0];
      uploads.uploadVoterList(selectedFile);
    }
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault();
    if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
      selectedFile = event.dataTransfer.files[0];
      uploads.uploadVoterList(selectedFile);
    }
  }
</script>

<div class="space-y-6">
  <div>
    <h1 class="text-3xl font-bold text-slate-900">Upload Voter List</h1>
    <p class="mt-2 text-slate-600">Upload a CSV or Excel file with voter registration data</p>
  </div>

  {#if $uploads.voterListError}
    <div class="rounded-lg bg-red-50 p-4">
      <p class="text-red-800">{$uploads.voterListError}</p>
      <Button variant="secondary" onclick={() => uploads.clearErrors()}>
        Try Again
      </Button>
    </div>
  {:else if $uploads.voterListUploading}
    <div class="rounded-lg border border-slate-200 bg-white p-6">
      <div class="flex items-center gap-4">
        <LoadingSpinner />
        <div class="flex-1">
          <p class="font-medium text-slate-900">Uploading...</p>
          <div class="mt-2 h-2 w-full rounded-full bg-slate-200">
            <div
              class="h-full rounded-full bg-blue-600 transition-all"
              style="width: {$uploads.voterListProgress}%"
            ></div>
          </div>
          <p class="mt-1 text-sm text-slate-600">{$uploads.voterListProgress}%</p>
        </div>
      </div>
    </div>
  {:else if $uploads.voterListProgress === 100}
    <div class="rounded-lg bg-green-50 p-4">
      <p class="text-green-800">Voter list uploaded successfully!</p>
    </div>
  {:else}
    <div
      class="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 p-12 text-center"
      ondrop={handleDrop}
      ondragover={(e) => e.preventDefault()}
      role="button"
      tabindex="0"
    >
      <Upload class="mx-auto h-12 w-12 text-slate-400" />
      <p class="mt-4 text-lg font-medium text-slate-900">Drag and drop your file here</p>
      <p class="mt-2 text-sm text-slate-600">or click to browse</p>

      <input
        type="file"
        accept=".csv,.xlsx,.xls"
        onchange={handleFileSelect}
        class="mt-4"
        aria-label="File"
      />

      <p class="mt-4 text-xs text-slate-500">
        Supported formats: CSV, Excel (.xlsx, .xls)
      </p>
    </div>
  {/if}
</div>
```

**Step 4: Run test to verify it passes**

Run: `cd frontend-svelt && bun test src/routes/workspace/upload/voters/+page.test.ts -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add frontend-svelt/src/routes/workspace/upload/
git commit -m "feat(frontend): add voter list upload page with drag-drop"
```

---

### Task 3: Petition Upload Page

**Files:**
- Modify: `frontend-svelt/src/routes/workspace/upload/petitions/+page.svelte`
- Create: `frontend-svelt/src/routes/workspace/upload/petitions/+page.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-svelt/src/routes/workspace/upload/petitions/+page.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import Page from './+page.svelte';
import { uploads } from '$lib/stores/uploads';
import { campaigns } from '$lib/stores/campaigns';

vi.mock('$lib/stores/uploads');
vi.mock('$lib/stores/campaigns');

describe('Petition Upload Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(uploads.subscribe).mockImplementation((fn) => {
      fn({
        voterListUploading: false,
        voterListProgress: 0,
        voterListError: null,
        petitionUploading: false,
        petitionProgress: 0,
        petitionError: null,
        lastUploadResult: null
      });
      return () => {};
    });

    vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
      fn({
        campaigns: [{ id: 'camp-1', name: 'DC 2024' }],
        loading: false,
        error: null
      });
      return () => {};
    });
  });

  it('displays campaign selector', () => {
    render(Page);
    expect(screen.getByLabelText(/campaign/i)).toBeInTheDocument();
  });

  it('calls uploadPetition with campaign ID', async () => {
    vi.mocked(uploads.uploadPetition).mockResolvedValue({
      scan_id: 'scan-1',
      crop_count: 10
    } as any);

    render(Page);

    const file = new File(['pdf content'], 'petition.pdf', { type: 'application/pdf' });
    const input = screen.getByLabelText(/file/i) as HTMLInputElement;

    await fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(uploads.uploadPetition).toHaveBeenCalledWith(file, 'camp-1');
    });
  });

  it('shows crop count after upload', async () => {
    vi.mocked(uploads.subscribe).mockImplementation((fn) => {
      fn({
        voterListUploading: false,
        voterListProgress: 0,
        voterListError: null,
        petitionUploading: false,
        petitionProgress: 100,
        petitionError: null,
        lastUploadResult: { scan_id: 'scan-1', crop_count: 10 }
      });
      return () => {};
    });

    render(Page);

    expect(screen.getByText(/10 signatures detected/i)).toBeInTheDocument();
  });
});
```

**Step 2-5: Follow same pattern as Task 2**

---

## Part B: Job Status & SSE (Day 2 - ~3 hours)

### Task 4: SSE Integration in Jobs Store

**Files:**
- Modify: `frontend-svelt/src/lib/stores/jobs.ts`
- Modify: `frontend-svelt/src/lib/stores/jobs.test.ts`

**Step 1: Write the failing tests**

```typescript
// Add to frontend-svelt/src/lib/stores/jobs.test.ts

  describe('SSE Integration', () => {
    it('connects to job status stream', () => {
      const mockEventSource = {
        close: vi.fn(),
        onopen: null,
        onmessage: null,
        onerror: null
      };

      vi.stubGlobal('EventSource', vi.fn(() => mockEventSource));

      jobs.connectToJob('job-1');

      expect(EventSource).toHaveBeenCalledWith(
        expect.stringContaining('/api/jobs/job-1/status')
      );

      vi.unstubAllGlobals();
    });

    it('updates job state on SSE message', async () => {
      const mockEventSource = {
        close: vi.fn(),
        onopen: null,
        onmessage: null,
        onerror: null
      };

      vi.stubGlobal('EventSource', vi.fn(() => mockEventSource));

      jobs.connectToJob('job-1');

      // Simulate SSE message
      const messageEvent = new MessageEvent('message', {
        data: JSON.stringify({
          event: 'status_update',
          data: { status: 'OCR_STARTED', progress: 25 }
        })
      });

      mockEventSource.onmessage(messageEvent);

      const state = get(jobs);
      expect(state.currentJob?.status).toBe('OCR_STARTED');

      vi.unstubAllGlobals();
    });

    it('reconnects on connection error', async () => {
      const mockEventSource = {
        close: vi.fn(),
        onopen: null,
        onmessage: null,
        onerror: null
      };

      vi.stubGlobal('EventSource', vi.fn(() => mockEventSource));
      vi.useFakeTimers();

      jobs.connectToJob('job-1');

      // First connection attempt
      expect(EventSource).toHaveBeenCalledTimes(1);

      // Simulate error
      mockEventSource.onerror(new Event('error'));

      // Fast-forward to reconnect
      await vi.advanceTimersByTimeAsync(2000);

      // Should have reconnected
      expect(EventSource).toHaveBeenCalledTimes(2);

      vi.useRealTimers();
      vi.unstubAllGlobals();
    });

    it('disconnects cleanly', () => {
      const mockEventSource = {
        close: vi.fn()
      };

      vi.stubGlobal('EventSource', vi.fn(() => mockEventSource));

      jobs.connectToJob('job-1');
      jobs.disconnect();

      expect(mockEventSource.close).toHaveBeenCalled();

      vi.unstubAllGlobals();
    });
  });
```

**Step 2: Run test to verify it fails**

Run: `cd frontend-svelt && bun test src/lib/stores/jobs.test.ts -v`
Expected: FAIL - "jobs.connectToJob is not a function"

**Step 3: Write minimal implementation**

```typescript
// Add to frontend-svelt/src/lib/stores/jobs.ts

interface SSEState {
  connected: boolean;
  reconnectAttempts: number;
  error: string | null;
}

interface JobsState {
  currentJob: Job | null;
  loading: boolean;
  error: string | null;
  sse: SSEState;
}

function createJobsStore() {
  const { subscribe, set, update } = writable<JobsState>({
    currentJob: null,
    loading: false,
    error: null,
    sse: { connected: false, reconnectAttempts: 0, error: null }
  });

  let eventSource: EventSource | null = null;
  const maxRetries = 3;
  const baseRetryDelay = 1000;

  function handleSSEEvent(data: { event: string; data: any }) {
    switch (data.event) {
      case 'status_update':
        update(s => ({
          ...s,
          currentJob: { ...s.currentJob, ...data.data } as Job
        }));
        break;

      case 'matching_progress':
        update(s => ({
          ...s,
          currentJob: {
            ...s.currentJob,
            progress: data.data.processed / data.data.total * 100
          } as Job
        }));
        break;

      case 'job_complete':
        update(s => ({
          ...s,
          currentJob: { ...s.currentJob, status: 'MATCHING_COMPLETED' } as Job
        }));
        disconnect();
        break;

      case 'job_error':
        update(s => ({
          ...s,
          currentJob: { ...s.currentJob, status: data.data.status } as Job,
          sse: { ...s.sse, error: data.data.error }
        }));
        disconnect();
        break;
    }
  }

  function connectToJob(jobId: string) {
    if (eventSource) {
      eventSource.close();
    }

    const baseUrl = PUBLIC_API_URL || 'http://localhost:8000';
    eventSource = new EventSource(`${baseUrl}/api/jobs/${jobId}/status`);

    eventSource.onopen = () => {
      update(s => ({
        ...s,
        sse: { connected: true, reconnectAttempts: 0, error: null }
      }));
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleSSEEvent(data);
      } catch (e) {
        console.error('Failed to parse SSE message:', e);
      }
    };

    eventSource.onerror = () => {
      update(s => {
        const attempts = s.sse.reconnectAttempts + 1;

        if (attempts < maxRetries) {
          const delay = baseRetryDelay * Math.pow(2, attempts);
          setTimeout(() => connectToJob(jobId), delay);
          return { ...s, sse: { ...s.sse, reconnectAttempts: attempts } };
        } else {
          return { ...s, sse: { connected: false, reconnectAttempts: attempts, error: 'Connection lost' } };
        }
      });
    };
  }

  function disconnect() {
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
    update(s => ({ ...s, sse: { connected: false, reconnectAttempts: 0, error: null } }));
  }

  return {
    subscribe,
    create: /* existing */,
    fetch: /* existing */,
    cancel: /* existing */,
    connectToJob,
    disconnect,
    clearError: /* existing */,
    reset: /* existing */
  };
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend-svelt && bun test src/lib/stores/jobs.test.ts -v`
Expected: All tests passing

**Step 5: Commit**

```bash
git add frontend-svelt/src/lib/stores/jobs.ts frontend-svelt/src/lib/stores/jobs.test.ts
git commit -m "feat(frontend): add SSE integration to jobs store"
```

---

### Task 5: Job Status Page

**Files:**
- Create: `frontend-svelt/src/routes/workspace/jobs/[id]/+page.svelte`
- Create: `frontend-svelt/src/routes/workspace/jobs/[id]/+page.test.ts`

**Test and implementation follow same pattern - shows job status, progress bar, cancel button, connects to SSE on mount**

---

## Part C-E: Continue with similar TDD pattern...

---

## Final Verification

**Run all frontend tests:**
```bash
cd frontend-svelt && bun test -v
```

**Expected:** All tests passing, coverage >80% for new code

**Run E2E tests:**
```bash
cd frontend-svelt && bun run test:e2e
```

**Manual verification:**
1. Upload voter list (CSV) - validates and uploads
2. Upload petition (PDF) - creates crops
3. Create job - starts OCR
4. Watch job status - real-time updates via SSE
5. View results - paginated, filtered
6. Export results - CSV download
7. Cancel job - stops running job

---

## Notes for Implementation

**TDD Discipline:**
- Write test first, verify it fails
- Write minimal code to pass
- Refactor if needed
- Commit after each task

**SSE Testing:**
- Mock EventSource with vi.stubGlobal
- Test reconnection logic
- Test event handlers
- Test cleanup on unmount

**File Upload Testing:**
- Mock File API
- Test progress callbacks
- Test error handling
- Test validation

**Accessibility:**
- Progress bars have aria-valuenow
- Upload zones are keyboard accessible
- Status updates announced to screen readers
- Error messages have role="alert"

---

## Part C: Results & Dashboard (~4 hours)

### Task 6: Dashboard Store

**Files:**
- Create: `frontend-svelt/src/lib/stores/dashboard.ts`
- Create: `frontend-svelt/src/lib/stores/dashboard.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-svelt/src/lib/stores/dashboard.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import { dashboard, resetDashboardStore } from './dashboard';
import { getApiClient } from './api-client';

vi.mock('./api-client');

describe('Dashboard Store', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    resetDashboardStore();
  });

  it('starts with empty metrics', () => {
    const state = get(dashboard);
    expect(state.totalSignatures).toBe(0);
    expect(state.confidenceBreakdown).toEqual({ HIGH: 0, MEDIUM: 0, LOW: 0 });
    expect(state.loading).toBe(false);
  });

  it('fetches metrics from API', async () => {
    const mockClient = {
      getCampaignMetrics: vi.fn().mockResolvedValue({
        total_signatures: 150,
        confidence_breakdown: { HIGH: 80, MEDIUM: 50, LOW: 20 },
        jobs_active: 1,
        jobs_completed: 5
      })
    };
    vi.mocked(getApiClient).mockReturnValue(mockClient as any);

    await dashboard.fetchMetrics('campaign-1');

    const state = get(dashboard);
    expect(state.totalSignatures).toBe(150);
    expect(state.confidenceBreakdown.HIGH).toBe(80);
  });

  it('handles fetch errors', async () => {
    const mockClient = {
      getCampaignMetrics: vi.fn().mockRejectedValue(new Error('API error'))
      };
    vi.mocked(getApiClient).mockReturnValue(mockClient as any);

    await dashboard.fetchMetrics('campaign-1');

    const state = get(dashboard);
    expect(state.error).toBe('API error');
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend-svelt && bun test src/lib/stores/dashboard.test.ts -v`
Expected: FAIL - "Cannot find module './dashboard'"

**Step 3: Write minimal implementation**

```typescript
// frontend-svelt/src/lib/stores/dashboard.ts
import { writable } from 'svelte/store';
import { getApiClient } from './api-client';

interface ConfidenceBreakdown {
  HIGH: number;
  MEDIUM: number;
  LOW: number;
}

interface DashboardState {
  totalSignatures: number;
  confidenceBreakdown: ConfidenceBreakdown;
  jobsActive: number;
  jobsCompleted: number;
  targetTotal: number | null;
  loading: boolean;
  error: string | null;
}

function createDashboardStore() {
  const { subscribe, set, update } = writable<DashboardState>({
    totalSignatures: 0,
    confidenceBreakdown: { HIGH: 0, MEDIUM: 0, LOW: 0 },
    jobsActive: 0,
    jobsCompleted: 0,
    targetTotal: null,
    loading: false,
    error: null
  });

  return {
    subscribe,

    async fetchMetrics(campaignId: string) {
    update(s => ({ ...s, loading: true, error: null }));

    try {
      const client = getApiClient();
      const response = await client.getCampaignMetrics(campaignId);

      update(s => ({
        ...s,
        totalSignatures: response.total_signatures,
        confidenceBreakdown: response.confidence_breakdown,
        jobsActive: response.jobs_active,
        jobsCompleted: response.jobs_completed,
        targetTotal: response.target_total ?? null,
        loading: false
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      update(s => ({ ...s, loading: false, error: message }));
    }
  },

    reset() {
    set({
      totalSignatures: 0,
      confidenceBreakdown: { HIGH: 0, MEDIUM: 0, LOW: 0 },
      jobsActive: 0,
      jobsCompleted: 0,
      targetTotal: null,
      loading: false,
      error: null
    });
  }
  };
}

export const dashboard = createDashboardStore();

export function resetDashboardStore() {
  dashboard.reset();
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend-svelt && bun test src/lib/stores/dashboard.test.ts -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add frontend-svelt/src/lib/stores/dashboard.ts frontend-svelt/src/lib/stores/dashboard.test.ts
git commit -m "feat(frontend): add dashboard store with real API calls"
```

---

### Task 7: CSV Export Component

**Files:**
- Create: `frontend-svelt/src/lib/components/results/CsvExportButton.svelte`
- Create: `frontend-svelt/src/lib/components/results/CsvExportButton.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-svelt/src/lib/components/results/CsvExportButton.test.ts
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import CsvExportButton from './CsvExportButton.svelte';
import { jobs } from '$lib/stores/jobs';

vi.mock('$lib/stores/jobs');

describe('CsvExportButton', () => {
  it('renders export button', () => {
    vi.mocked(jobs.subscribe).mockImplementation((fn: any) => {
    fn({ currentJob: { id: 'job-1' }, loading: false, error: null, sse: { connected: false, reconnectAttempts: 0, error: null } });
    return () => {};
  });

    render(CsvExportButton, { jobId: 'job-1' });
    expect(screen.getByRole('button', { name: /export.*csv/i })).toBeInTheDocument();
  });

  it('triggers download on click', async () => {
    const mockAnchor = vi.fn();
    vi.stubGlobal('URL', { createObjectURL: mockAnchor.mockReturnValue('blob:url') });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      blob: () => new Blob(['csv,data'], { type: 'text/csv' })
    }));

    vi.mocked(jobs.subscribe).mockImplementation((fn: any) => {
    fn({ currentJob: { id: 'job-1' }, loading: false, error: null, sse: { connected: false, reconnectAttempts: 4, error: null } });
    return () => {};
  });

    render(CsvExportButton, { jobId: 'job-1' });

    const button = screen.getByRole('button', { name: /export.*csv/i });
    await fireEvent.click(button);

    await waitFor(() => {
      expect(mockAnchor).toHaveBeenCalled();
    });
  });
});
```

**Step 2-5: Follow same pattern - implement, test, commit**

---

## Part D: Session Management (~2 hours)

> **NOTE:** Session API endpoints are NOT deferred - they are Phase 4 scope.

### Task 8: Session Store

**Files:**
- Create: `frontend-svelt/src/lib/stores/sessions.ts`
- Create: `frontend-svelt/src/lib/stores/sessions.test.ts`

**Features:**
- `save(name)` - Save current workspace state
- `load(id)` - Load saved session
- `exportSession(id)` - Download as ZIP
- `list()` - List saved sessions

**API Endpoints (Phase 4 scope):**
- `POST /api/sessions` - Save session
- `GET /api/sessions/{id}` - Load session
- `GET /api/sessions/{id}/export` - Export as ZIP
- `GET /api/sessions` - List sessions

---

### Task 9: Session UI

**Files:**
- Create: `frontend-svelt/src/routes/workspace/sessions/+page.svelte`
- Create: `frontend-svelt/src/routes/workspace/sessions/+page.test.ts`

**Features:**
- Save session modal with name input
- Load session dropdown with confirmation
- Export button (ZIP download)
- Session list with metadata

---

## Part E: Demo Mode (~2 hours)

### Task 10: Demo Store

**Files:**
- Create: `frontend-svelt/src/lib/stores/demo.ts`
- Create: `frontend-svelt/src/lib/stores/demo.test.ts`

**Features:**
- `isDemoMode` - Check feature flag from settings
- `reset()` - Call `POST /api/demo/reset`
- `loadPrebaked(sessionName)` - Load demo session
- Confirmation dialog state

---

### Task 11: Demo UI

**Files:**
- Create: `frontend-svelt/src/routes/workspace/demo/+page.svelte`
- Create: `frontend-svelt/src/routes/workspace/demo/+page.test.ts`

**Features:**
- Demo mode banner (visible when feature flag enabled)
- Reset button with confirmation dialog
- Pre-baked session selector

---

## Part F: E2E Testing (~4 hours)

> Follow existing plan structure for Tasks 11-14

---

## Part G: Documentation (~3 hours)

### Task 15: Update README.md

**Files:**
- Modify: `README.md`

**Content to Add:**
```markdown
## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.12+ (for local dev)
- Node.js 20+ / Bun (for local dev)

### Development Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and configure
3. Run `docker-compose up`
4. Open http://localhost:5173

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for OCR | Yes* |
| `DATABASE_URL` | PostgreSQL connection string | No (SQLite default) |

*At least one OCR provider required
```

**Step 1: Write test**
**Step 2: Verify current README exists**
**Step 3: Update with new content**
**Step 4: Commit**

---

### Task 16: Create Deployment Guide

**Files:**
- Create: `docs/deployment.md`

**Content:**
```markdown
# Deployment Guide

## Single VPS Deployment (Recommended)

### Option A: DigitalOcean Droplet ($6-12/mo)

1. Create Droplet (Ubuntu 22.04, 1GB RAM minimum)
2. Install Docker: `curl -fsSL https://get.docker.com | sh`
3. Clone repository
4. Configure environment
5. Run: `docker-compose -f docker-compose.prod.yml up -d`

### Environment Configuration

Create `.env` file:
\`\`\`bash
DATABASE_URL=postgresql://user:pass@localhost/votecatcher
OPENAI_API_KEY=sk-...
FEATURE_DEMO_MODE=false
\`\`\`

### HTTPS Setup

Use Caddy for automatic Let's Encrypt:
\`\`\`bash
# Add Caddy to docker-compose.prod.yml
\`\`\`

### Backup Strategy

Daily PostgreSQL dump:
\`\`\`bash
docker exec postgres pg_dump -U user votecatcher > backup_$(date +%Y%m%d).sql
\`\`\`
```

**Commit after creating**

---

### Task 17: Create User Guide

**Files:**
- Create: `docs/user-guide.md`

**Content sections:**
1. Creating a Campaign
2. Uploading Voter Lists (format requirements)
3. Uploading Petitions (PDF requirements, DC preset)
4. Running Jobs (OCR + Matching)
5. Understanding Results (confidence levels)
6. Filtering and Exporting
7. Session Management
8. Demo Mode

---

### Task 18: Create Configuration Reference

**Files:**
- Create: `docs/configuration.md`

**Content:**
All environment variables with descriptions, defaults, and examples

---

## Final Verification

**Run all frontend tests:**
```bash
cd frontend-svelt && bun test -v
```

**Expected:** All tests passing, coverage >80% for new code

**Run E2E tests:**
```bash
cd frontend-svelt && bun run test:e2e
```

**Manual verification:**
1. Upload voter list (CSV) - validates and uploads
2. Upload petition (PDF) - creates crops
3. Create job - starts OCR
4. Watch job status - real-time updates via SSE
5. View results - paginated, filtered
6. Export results - CSV download
7. Cancel job - stops running job
8. Save session - workspace state persisted
9. Load session - state restored
10. Demo reset - clears data
11. Verify README quick start works
12. Verify deployment guide is accurate

---

## Summary of New Tasks Added

| Part | Task | Description |
|------|------|-------------|
| C | 6 | Dashboard Store (real API calls, not hardcoded) |
| C | 7 | CSV Export Component |
| D | 8-9 | Session Management (API endpoints NOT deferred) |
| E | 10-11 | Demo Mode Store & UI |
| G | 15-18 | Documentation (README, deployment, user guide, config) |
