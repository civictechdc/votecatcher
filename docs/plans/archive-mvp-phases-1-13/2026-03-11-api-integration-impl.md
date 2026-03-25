# Phase 3 Part C: API Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Connect frontend to backend API using generated OpenAPI client and Svelte stores

**Architecture:** Svelte stores wrap generated API client for state management. Pages subscribe to stores for reactive updates. LoadingState component handles async states.

**Tech Stack:** Svelte 5 runes, OpenAPI-generated TypeScript client, Vitest for testing, MSW for API mocking

---

## Phase 1: Foundation (Day 1 - ~4 hours)

### Task 1: API Client Wrapper

**Files:**
- Create: `frontend-svelt/src/lib/stores/api-client.ts`
- Test: `frontend-svelt/src/lib/stores/api-client.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-svelt/src/lib/stores/api-client.test.ts
import { describe, it, expect, vi } from 'vitest';
import { getApiClient } from './api-client';

describe('API Client', () => {
  it('creates client with default base URL', () => {
    const client = getApiClient();
    expect(client).toBeDefined();
  });

  it('uses PUBLIC_API_URL when available', () => {
    vi.stubGlobal('import.meta', {
      env: {
        PUBLIC_API_URL: 'http://custom-api:8000'
      }
    });

    const client = getApiClient();
    expect(client).toBeDefined();

    vi.unstubAllGlobals();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend-svelt && bun test src/lib/stores/api-client.test.ts -v`
Expected: FAIL - "Cannot find module './api-client'"

**Step 3: Write minimal implementation**

```typescript
// frontend-svelt/src/lib/stores/api-client.ts
import { DefaultApi } from '$lib/api/generated/apis/DefaultApi';
import { PUBLIC_API_URL } from '$env/static/public';

let client: DefaultApi | null = null;

export function getApiClient(): DefaultApi {
  if (!client) {
    const baseUrl = (PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');
    client = new DefaultApi({
      BASE: baseUrl
    });
  }
  return client;
}

export function resetApiClient() {
  client = null;
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend-svelt && bun test src/lib/stores/api-client.test.ts -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add frontend-svelt/src/lib/stores/api-client.ts frontend-svelt/src/lib/stores/api-client.test.ts
git commit -m "feat(frontend): add API client wrapper singleton"
```

---

### Task 2: Campaigns Store - Fetch All

**Files:**
- Create: `frontend-svelt/src/lib/stores/campaigns.ts`
- Create: `frontend-svelt/src/lib/stores/campaigns.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-svelt/src/lib/stores/campaigns.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import { campaigns, resetCampaignsStore } from './campaigns';
import { getApiClient } from './api-client';
import type { Campaign } from '$lib/api/generated';

vi.mock('./api-client');

describe('Campaigns Store', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    resetCampaignsStore();
  });

  describe('fetchAll', () => {
    it('starts with empty state', () => {
      const state = get(campaigns);
      expect(state.campaigns).toEqual([]);
      expect(state.loading).toBe(false);
      expect(state.error).toBeNull();
    });

    it('sets loading while fetching', async () => {
      const mockClient = {
        getCampaigns: vi.fn().mockResolvedValue([])
      };
      vi.mocked(getApiClient).mockReturnValue(mockClient as any);

      const promise = campaigns.fetchAll();

      let state = get(campaigns);
      expect(state.loading).toBe(true);

      await promise;

      state = get(campaigns);
      expect(state.loading).toBe(false);
    });

    it('stores fetched campaigns', async () => {
      const mockCampaigns: Campaign[] = [
        {
          id: 'uuid-1',
          name: 'Test Campaign',
          year: 2024,
          region: 'DC',
          status: 'active',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z'
        }
      ];

      const mockClient = {
        getCampaigns: vi.fn().mockResolvedValue(mockCampaigns)
      };
      vi.mocked(getApiClient).mockReturnValue(mockClient as any);

      await campaigns.fetchAll();

      const state = get(campaigns);
      expect(state.campaigns).toEqual(mockCampaigns);
      expect(state.error).toBeNull();
    });

    it('handles fetch errors', async () => {
      const mockClient = {
        getCampaigns: vi.fn().mockRejectedValue(new Error('Network error'))
      };
      vi.mocked(getApiClient).mockReturnValue(mockClient as any);

      await campaigns.fetchAll();

      const state = get(campaigns);
      expect(state.error).toBe('Network error');
      expect(state.campaigns).toEqual([]);
    });
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend-svelt && bun test src/lib/stores/campaigns.test.ts -v`
Expected: FAIL - "Cannot find module './campaigns'"

**Step 3: Write minimal implementation**

```typescript
// frontend-svelt/src/lib/stores/campaigns.ts
import { writable } from 'svelte/store';
import { getApiClient } from './api-client';
import type { Campaign } from '$lib/api/generated';

interface CampaignsState {
  campaigns: Campaign[];
  loading: boolean;
  error: string | null;
}

function createCampaignsStore() {
  const { subscribe, set, update } = writable<CampaignsState>({
    campaigns: [],
    loading: false,
    error: null
  });

  return {
    subscribe,

    async fetchAll() {
      update(s => ({ ...s, loading: true, error: null }));

      try {
        const client = getApiClient();
        const campaigns = await client.getCampaigns();
        update(s => ({ ...s, campaigns, loading: false }));
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unknown error';
        update(s => ({ ...s, error: message, loading: false, campaigns: [] }));
      }
    },

    clearError() {
      update(s => ({ ...s, error: null }));
    },

    reset() {
      set({ campaigns: [], loading: false, error: null });
    }
  };
}

export const campaigns = createCampaignsStore();

export function resetCampaignsStore() {
  campaigns.reset();
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend-svelt && bun test src/lib/stores/campaigns.test.ts -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add frontend-svelt/src/lib/stores/campaigns.ts frontend-svelt/src/lib/stores/campaigns.test.ts
git commit -m "feat(frontend): add campaigns store with fetchAll"
```

---

### Task 3: Campaigns Store - CRUD Operations

**Files:**
- Modify: `frontend-svelt/src/lib/stores/campaigns.ts`
- Modify: `frontend-svelt/src/lib/stores/campaigns.test.ts`

**Step 1: Write the failing tests**

```typescript
// Add to frontend-svelt/src/lib/stores/campaigns.test.ts

  describe('create', () => {
    it('creates a new campaign', async () => {
      const newCampaign: Campaign = {
        id: 'uuid-new',
        name: 'New Campaign',
        year: 2024,
        region: 'DC',
        status: 'active',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      };

      const mockClient = {
        getCampaigns: vi.fn().mockResolvedValue([]),
        createCampaign: vi.fn().mockResolvedValue(newCampaign)
      };
      vi.mocked(getApiClient).mockReturnValue(mockClient as any);

      await campaigns.create({ name: 'New Campaign', year: 2024, region: 'DC' });

      const state = get(campaigns);
      expect(state.campaigns).toContainEqual(newCampaign);
    });

    it('handles create errors', async () => {
      const mockClient = {
        getCampaigns: vi.fn().mockResolvedValue([]),
        createCampaign: vi.fn().mockRejectedValue(new Error('Validation failed'))
      };
      vi.mocked(getApiClient).mockReturnValue(mockClient as any);

      await campaigns.create({ name: '', year: 2024, region: 'DC' });

      const state = get(campaigns);
      expect(state.error).toBe('Validation failed');
    });
  });

  describe('delete', () => {
    it('removes campaign from store', async () => {
      const existingCampaign: Campaign = {
        id: 'uuid-1',
        name: 'Test',
        year: 2024,
        region: 'DC',
        status: 'active',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      };

      const mockClient = {
        getCampaigns: vi.fn().mockResolvedValue([existingCampaign]),
        deleteCampaign: vi.fn().mockResolvedValue(undefined)
      };
      vi.mocked(getApiClient).mockReturnValue(mockClient as any);

      await campaigns.fetchAll();
      await campaigns.delete('uuid-1');

      const state = get(campaigns);
      expect(state.campaigns).not.toContainEqual(existingCampaign);
    });
  });
```

**Step 2: Run test to verify it fails**

Run: `cd frontend-svelt && bun test src/lib/stores/campaigns.test.ts -v`
Expected: FAIL - "campaigns.create is not a function"

**Step 3: Write minimal implementation**

```typescript
// Add to frontend-svelt/src/lib/stores/campaigns.ts in createCampaignsStore()

    async create(data: { name: string; year: number; region: string }) {
      update(s => ({ ...s, loading: true, error: null }));

      try {
        const client = getApiClient();
        const newCampaign = await client.createCampaign(data);
        update(s => ({
          ...s,
          campaigns: [...s.campaigns, newCampaign],
          loading: false
        }));
        return newCampaign;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unknown error';
        update(s => ({ ...s, error: message, loading: false }));
        throw error;
      }
    },

    async delete(id: string) {
      update(s => ({ ...s, loading: true, error: null }));

      try {
        const client = getApiClient();
        await client.deleteCampaign(id);
        update(s => ({
          ...s,
          campaigns: s.campaigns.filter(c => c.id !== id),
          loading: false
        }));
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unknown error';
        update(s => ({ ...s, error: message, loading: false }));
        throw error;
      }
    },
```

**Step 4: Run test to verify it passes**

Run: `cd frontend-svelt && bun test src/lib/stores/campaigns.test.ts -v`
Expected: PASS (7 tests)

**Step 5: Commit**

```bash
git add frontend-svelt/src/lib/stores/campaigns.ts frontend-svelt/src/lib/stores/campaigns.test.ts
git commit -m "feat(frontend): add create and delete to campaigns store"
```

---

### Task 4: Dashboard - Load Campaign Count

**Files:**
- Modify: `frontend-svelt/src/routes/workspace/+page.svelte`
- Create: `frontend-svelt/src/routes/workspace/+page.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-svelt/src/routes/workspace/+page.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/svelte';
import Page from './+page.svelte';
import { campaigns } from '$lib/stores/campaigns';

vi.mock('$lib/stores/campaigns', () => ({
  campaigns: {
    subscribe: vi.fn(),
    fetchAll: vi.fn(),
    clearError: vi.fn()
  }
}));

describe('Dashboard Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays campaign count from store', async () => {
    const mockCampaigns = [
      { id: '1', name: 'Campaign 1' },
      { id: '2', name: 'Campaign 2' },
      { id: '3', name: 'Campaign 3' }
    ];

    let subscriber: any;
    vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
      subscriber = fn;
      fn({ campaigns: mockCampaigns, loading: false, error: null });
      return () => {};
    });

    render(Page);

    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument();
    });
  });

  it('calls fetchAll on mount', () => {
    vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
      fn({ campaigns: [], loading: false, error: null });
      return () => {};
    });

    render(Page);

    expect(campaigns.fetchAll).toHaveBeenCalled();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend-svelt && bun test src/routes/workspace/+page.test.ts -v`
Expected: FAIL - Dashboard shows hardcoded "0"

**Step 3: Write minimal implementation**

```svelte
<!-- frontend-svelt/src/routes/workspace/+page.svelte -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { campaigns } from '$lib/stores/campaigns';
	import { Button, LoadingState } from '$lib/components/ui';
	import { Home, FolderOpen, Activity, CheckCircle, Settings } from 'lucide-svelte';

	let { data } = $props();

	onMount(() => {
		campaigns.fetchAll();
	});
</script>

{#if $campaigns.loading}
	<LoadingState loading={true} />
{:else if $campaigns.error}
	<LoadingState error={$campaigns.error} onRetry={() => campaigns.fetchAll()} />
{:else}
	<div class="space-y-6">
		<div>
			<h1 class="text-3xl font-bold text-slate-900">Dashboard</h1>
			<p class="mt-2 text-slate-600">Welcome to your workspace</p>
		</div>

		<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
			<div class="rounded-lg border border-slate-200 bg-white p-6">
				<h3 class="text-sm font-medium text-slate-600">Active Campaigns</h3>
				<p class="mt-2 text-3xl font-bold text-slate-900">{$campaigns.campaigns.length}</p>
			</div>
		</div>

		<div class="rounded-lg border border-slate-200 bg-white p-6">
			<h2 class="text-lg font-semibold text-slate-900">Quick Actions</h2>
			<div class="mt-4 flex gap-4">
				<Button variant="primary" onclick={() => window.location.href = '/workspace/campaigns'}>
					Create Campaign
				</Button>
				<Button variant="secondary" onclick={() => window.location.href = '/workspace/jobs'}>
					View Jobs
				</Button>
			</div>
		</div>
	</div>
{/if}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend-svelt && bun test src/routes/workspace/+page.test.ts -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add frontend-svelt/src/routes/workspace/+page.svelte frontend-svelt/src/routes/workspace/+page.test.ts
git commit -m "feat(frontend): load campaign count from API in dashboard"
```

---

### Task 5: Campaigns List Page

**Files:**
- Modify: `frontend-svelt/src/routes/workspace/campaigns/+page.svelte`
- Create: `frontend-svelt/src/routes/workspace/campaigns/+page.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-svelt/src/routes/workspace/campaigns/+page.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import Page from './+page.svelte';
import { campaigns } from '$lib/stores/campaigns';

vi.mock('$lib/stores/campaigns');

describe('Campaigns List Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
      fn({ campaigns: [], loading: false, error: null });
      return () => {};
    });
  });

  it('displays campaigns table', async () => {
    const mockCampaigns = [
      { id: '1', name: 'Campaign 1', year: 2024, region: 'DC', status: 'active' },
      { id: '2', name: 'Campaign 2', year: 2024, region: 'MD', status: 'active' }
    ];

    vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
      fn({ campaigns: mockCampaigns, loading: false, error: null });
      return () => {};
    });

    render(Page);

    await waitFor(() => {
      expect(screen.getByText('Campaign 1')).toBeInTheDocument();
      expect(screen.getByText('Campaign 2')).toBeInTheDocument();
    });
  });

  it('shows loading state', () => {
    vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
      fn({ campaigns: [], loading: true, error: null });
      return () => {};
    });

    render(Page);

    expect(screen.getByRole('status')).toBeInTheDocument(); // Loading spinner
  });

  it('calls delete on button click', async () => {
    const mockCampaigns = [
      { id: '1', name: 'Campaign 1', year: 2024, region: 'DC', status: 'active' }
    ];

    vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
      fn({ campaigns: mockCampaigns, loading: false, error: null });
      return () => {};
    });
    vi.mocked(campaigns.delete).mockResolvedValue(undefined);

    render(Page);

    const deleteButton = screen.getByText('Delete');
    await fireEvent.click(deleteButton);

    expect(campaigns.delete).toHaveBeenCalledWith('1');
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend-svelt && bun test src/routes/workspace/campaigns/+page.test.ts -v`
Expected: FAIL - Page is placeholder

**Step 3: Write minimal implementation**

```svelte
<!-- frontend-svelt/src/routes/workspace/campaigns/+page.svelte -->
<script lang="ts">
	import { onMount } from 'svelte';
	import { campaigns } from '$lib/stores/campaigns';
	import { Button, Table, LoadingState, Modal } from '$lib/components/ui';
	import { Plus, Trash2, Edit } from 'lucide-svelte';
	import type { Campaign } from '$lib/api/generated';

	let { data } = $props();
	let showCreateModal = $state(false);
	let newCampaignName = $state('');
	let newCampaignYear = $state(2024);
	let newCampaignRegion = $state('DC');

	onMount(() => {
		campaigns.fetchAll();
	});

	const columns = [
		{ key: 'name', label: 'Name', sortable: true },
		{ key: 'year', label: 'Year', sortable: true },
		{ key: 'region', label: 'Region', sortable: true },
		{ key: 'status', label: 'Status', sortable: true },
		{ key: 'actions', label: 'Actions', sortable: false }
	];

	async function handleCreate() {
		await campaigns.create({
			name: newCampaignName,
			year: newCampaignYear,
			region: newCampaignRegion
		});
		showCreateModal = false;
		newCampaignName = '';
	}

	async function handleDelete(id: string) {
		if (confirm('Are you sure you want to delete this campaign?')) {
			await campaigns.delete(id);
		}
	}

	function renderCell(campaign: Campaign, key: string) {
		if (key === 'actions') {
			return `
				<div class="flex gap-2">
					<button onclick="handleDelete('${campaign.id}')" class="text-red-600 hover:text-red-800">Delete</button>
				</div>
			`;
		}
		return campaign[key as keyof Campaign];
	}
</script>

{#if $campaigns.loading}
	<LoadingState loading={true} />
{:else if $campaigns.error}
	<LoadingState error={$campaigns.error} onRetry={() => campaigns.fetchAll()} />
{:else}
	<div class="space-y-6">
		<div class="flex items-center justify-between">
			<h1 class="text-3xl font-bold text-slate-900">Campaigns</h1>
			<Button variant="primary" onclick={() => showCreateModal = true}>
				<Plus class="h-4 w-4 mr-2" />
				Create Campaign
			</Button>
		</div>

		<Table
			data={$campaigns.campaigns}
			{columns}
			{renderCell}
			emptyMessage="No campaigns yet. Create your first campaign to get started."
		/>
	</div>
{/if}

<Modal open={showCreateModal} onclose={() => showCreateModal = false} title="Create Campaign">
	<form onsubmit={(e) => { e.preventDefault(); handleCreate(); }} class="space-y-4">
		<div>
			<label for="name" class="block text-sm font-medium text-slate-700">Name</label>
			<input
				type="text"
				id="name"
				bind:value={newCampaignName}
				class="mt-1 block w-full rounded-md border-slate-300 shadow-sm"
				required
			/>
		</div>

		<div>
			<label for="year" class="block text-sm font-medium text-slate-700">Year</label>
			<input
				type="number"
				id="year"
				bind:value={newCampaignYear}
				class="mt-1 block w-full rounded-md border-slate-300 shadow-sm"
				required
			/>
		</div>

		<div>
			<label for="region" class="block text-sm font-medium text-slate-700">Region</label>
			<input
				type="text"
				id="region"
				bind:value={newCampaignRegion}
				class="mt-1 block w-full rounded-md border-slate-300 shadow-sm"
				required
			/>
		</div>

		<div class="flex justify-end gap-2">
			<Button variant="secondary" onclick={() => showCreateModal = false}>Cancel</Button>
			<Button variant="primary" type="submit">Create</Button>
		</div>
	</form>
</Modal>
```

**Step 4: Run test to verify it passes**

Run: `cd frontend-svelt && bun test src/routes/workspace/campaigns/+page.test.ts -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add frontend-svelt/src/routes/workspace/campaigns/+page.svelte frontend-svelt/src/routes/workspace/campaigns/+page.test.ts
git commit -m "feat(frontend): add campaigns list page with CRUD"
```

---

## Verification: Phase 1 Complete

Run all Phase 1 tests:
```bash
cd frontend-svelt && bun test src/lib/stores/ src/routes/workspace/ -v
```

Expected: All tests passing

---

## Phase 2: File Operations (Day 2 - ~3 hours)

### Task 6: Jobs Store - Basic Operations

**Files:**
- Create: `frontend-svelt/src/lib/stores/jobs.ts`
- Create: `frontend-svelt/src/lib/stores/jobs.test.ts`

**Step 1: Write the failing tests**

```typescript
// frontend-svelt/src/lib/stores/jobs.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import { jobs, resetJobsStore } from './jobs';
import { getApiClient } from './api-client';

vi.mock('./api-client');

describe('Jobs Store', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    resetJobsStore();
  });

  describe('create', () => {
    it('creates a new job', async () => {
      const mockJob = {
        id: 'job-1',
        status: 'NOT_STARTED',
        created_at: '2024-01-01T00:00:00Z'
      };

      const mockClient = {
        createJob: vi.fn().mockResolvedValue(mockJob)
      };
      vi.mocked(getApiClient).mockReturnValue(mockClient as any);

      const result = await jobs.create({
        campaign_id: 'camp-1',
        scan_ids: ['scan-1'],
        provider: 'openai'
      });

      expect(result).toEqual(mockJob);
    });

    it('handles creation errors', async () => {
      const mockClient = {
        createJob: vi.fn().mockRejectedValue(new Error('Invalid campaign'))
      };
      vi.mocked(getApiClient).mockReturnValue(mockClient as any);

      await expect(jobs.create({
        campaign_id: 'invalid',
        scan_ids: [],
        provider: 'openai'
      })).rejects.toThrow('Invalid campaign');
    });
  });

  describe('fetch', () => {
    it('fetches job status', async () => {
      const mockJob = {
        id: 'job-1',
        status: 'OCR_STARTED',
        progress: 50
      };

      const mockClient = {
        getJob: vi.fn().mockResolvedValue(mockJob)
      };
      vi.mocked(getApiClient).mockReturnValue(mockClient as any);

      await jobs.fetch('job-1');

      const state = get(jobs);
      expect(state.currentJob).toEqual(mockJob);
    });
  });

  describe('cancel', () => {
    it('cancels a running job', async () => {
      const mockClient = {
        cancelJob: vi.fn().mockResolvedValue({ status: 'CANCELLED' })
      };
      vi.mocked(getApiClient).mockReturnValue(mockClient as any);

      await jobs.cancel('job-1');

      expect(mockClient.cancelJob).toHaveBeenCalledWith('job-1');
    });
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend-svelt && bun test src/lib/stores/jobs.test.ts -v`
Expected: FAIL - "Cannot find module './jobs'"

**Step 3: Write minimal implementation**

```typescript
// frontend-svelt/src/lib/stores/jobs.ts
import { writable } from 'svelte/store';
import { getApiClient } from './api-client';
import type { Job } from '$lib/api/generated';

interface JobsState {
  currentJob: Job | null;
  loading: boolean;
  error: string | null;
}

function createJobsStore() {
  const { subscribe, set, update } = writable<JobsState>({
    currentJob: null,
    loading: false,
    error: null
  });

  return {
    subscribe,

    async create(data: { campaign_id: string; scan_ids: string[]; provider: string }) {
      update(s => ({ ...s, loading: true, error: null }));

      try {
        const client = getApiClient();
        const job = await client.createJob(data);
        update(s => ({ ...s, currentJob: job, loading: false }));
        return job;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unknown error';
        update(s => ({ ...s, error: message, loading: false }));
        throw error;
      }
    },

    async fetch(id: string) {
      update(s => ({ ...s, loading: true, error: null }));

      try {
        const client = getApiClient();
        const job = await client.getJob(id);
        update(s => ({ ...s, currentJob: job, loading: false }));
        return job;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unknown error';
        update(s => ({ ...s, error: message, loading: false }));
        throw error;
      }
    },

    async cancel(id: string) {
      update(s => ({ ...s, loading: true, error: null }));

      try {
        const client = getApiClient();
        await client.cancelJob(id);
        update(s => ({ ...s, loading: false }));
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unknown error';
        update(s => ({ ...s, error: message, loading: false }));
        throw error;
      }
    },

    clearError() {
      update(s => ({ ...s, error: null }));
    },

    reset() {
      set({ currentJob: null, loading: false, error: null });
    }
  };
}

export const jobs = createJobsStore();

export function resetJobsStore() {
  jobs.reset();
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend-svelt && bun test src/lib/stores/jobs.test.ts -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add frontend-svelt/src/lib/stores/jobs.ts frontend-svelt/src/lib/stores/jobs.test.ts
git commit -m "feat(frontend): add jobs store with create/fetch/cancel"
```

---

## Phase 3: Real-time & Results (Day 3 - ~4 hours)

### Task 7-10: [Similar pattern for SSE, Job Status Page, Results Store, Results Page]

[Continue with similar task structure...]

---

## Final Verification

**Run all frontend tests:**
```bash
cd frontend-svelt && bun test -v
```

**Expected:** All tests passing, >80% coverage for stores

**Start dev server:**
```bash
cd frontend-svelt && bun run dev
```

**Manual verification:**
1. Dashboard loads campaign count
2. Campaigns list shows data from API
3. Create campaign works
4. Delete campaign works
5. Loading states display correctly
6. Error states show retry button

---

## Notes for Implementation

**TDD Discipline:**
- Write test first, verify it fails
- Write minimal code to pass
- Refactor if needed
- Commit after each task

**Testing Mocks:**
- Use Vitest `vi.mock()` for store tests
- Use MSW for integration tests (optional for MVP)
- Real backend for E2E tests

**Error Handling:**
- All API errors caught in stores
- User-friendly messages displayed
- Retry buttons on error states

**Accessibility:**
- All buttons have aria-labels
- Modals have focus trap
- Loading spinners have role="status"

**Performance:**
- Stores are singletons (avoid duplicate API calls)
- Loading states prevent UI jank
- Pagination for large result sets
