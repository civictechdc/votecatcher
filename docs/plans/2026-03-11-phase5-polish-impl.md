# Phase 5 Polish: Error Handling, Performance, Documentation

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete Phase 5 Parts B, C, and D - comprehensive error handling, Lighthouse score >80, and auto-generated API docs + user guides.

**Architecture:** TDD for error handling (tests first), incremental Lighthouse fixes, auto-generated docs with @redocly/cli.

**Tech Stack:** SvelteKit error boundaries, Lighthouse CLI, @redocly/cli, Markdown

---

## Part C: Performance (Lighthouse >80)

> Start here - quickest wins, identifies issues for other parts.

### Task 1: Install Lighthouse CLI and Run Initial Audit

**Step 1: Install Lighthouse globally**

Run:
```bash
npm install -g lighthouse
```

**Step 2: Start dev servers**

Terminal 1:
```bash
cd backend && uv run fastapi dev app/api.py
```

Terminal 2:
```bash
cd frontend-svelt && bun run dev
```

**Step 3: Run Lighthouse on key pages**

Run:
```bash
lighthouse http://localhost:5173/workspace --output=json --output-path=./lighthouse-workspace.json --chrome-flags="--headless"
lighthouse http://localhost:5173/workspace/campaigns --output=json --output-path=./lighthouse-campaigns.json --chrome-flags="--headless"
lighthouse http://localhost:5173/getting-started --output=json --output-path=./lighthouse-getting-started.json --chrome-flags="--headless"
```

Expected: JSON files with scores <80, identifying issues

**Step 4: Review scores**

Run:
```bash
cat lighthouse-workspace.json | grep -A5 '"score":'
```

Note: Record baseline scores in PROGRESS.md

---

### Task 2: Add Meta Tags to All Pages

**Files:**
- Modify: `frontend-svelt/src/routes/workspace/+page.svelte`
- Modify: `frontend-svelt/src/routes/workspace/campaigns/+page.svelte`
- Modify: `frontend-svelt/src/routes/workspace/jobs/+page.svelte`
- Modify: `frontend-svelt/src/routes/workspace/results/+page.svelte`
- Modify: `frontend-svelt/src/routes/workspace/upload/+page.svelte`
- Modify: `frontend-svelt/src/routes/workspace/sessions/+page.svelte`
- Modify: `frontend-svelt/src/routes/workspace/demo/+page.svelte`

**Step 1: Add meta tags to workspace dashboard**

In `frontend-svelt/src/routes/workspace/+page.svelte`, add after `<script>`:

```svelte
<svelte:head>
	<title>Dashboard — Votecatcher</title>
	<meta name="description" content="Votecatcher campaign signature verification dashboard. View campaigns, jobs, and matching results." />
</svelte:head>
```

**Step 2: Add meta tags to campaigns page**

In `frontend-svelt/src/routes/workspace/campaigns/+page.svelte`, add after `<script>`:

```svelte
<svelte:head>
	<title>Campaigns — Votecatcher</title>
	<meta name="description" content="Manage your campaigns. Create, view, and delete election campaigns." />
</svelte:head>
```

**Step 3: Add meta tags to jobs page**

In `frontend-svelt/src/routes/workspace/jobs/+page.svelte`, add after `<script>`:

```svelte
<svelte:head>
	<title>Jobs — Votecatcher</title>
	<meta name="description" content="View and manage OCR and matching jobs. Monitor job progress in real-time." />
</svelte:head>
```

**Step 4: Add meta tags to results page**

In `frontend-svelt/src/routes/workspace/results/+page.svelte`, add after `<script>`:

```svelte
<svelte:head>
	<title>Results — Votecatcher</title>
	<meta name="description" content="View signature matching results. Filter by confidence, export to CSV." />
</svelte:head>
```

**Step 5: Add meta tags to upload page**

In `frontend-svelt/src/routes/workspace/upload/+page.svelte`, add after `<script>`:

```svelte
<svelte:head>
	<title>Upload Files — Votecatcher</title>
	<meta name="description" content="Upload voter registration lists and petition PDFs for signature verification." />
</svelte:head>
```

**Step 6: Add meta tags to sessions page**

In `frontend-svelt/src/routes/workspace/sessions/+page.svelte`, add after `<script>`:

```svelte
<svelte:head>
	<title>Sessions — Votecatcher</title>
	<meta name="description" content="Save, load, and export workspace sessions. Preserve your work state." />
</svelte:head>
```

**Step 7: Add meta tags to demo page**

In `frontend-svelt/src/routes/workspace/demo/+page.svelte`, add after `<script>`:

```svelte
<svelte:head>
	<title>Demo Mode — Votecatcher</title>
	<meta name="description" content="Try Votecatcher with sample data. Reset workspace and load pre-baked sessions." />
</svelte:head>
```

**Step 8: Commit meta tags**

Run:
```bash
cd frontend-svelt
git add src/routes/workspace/**/+page.svelte
git commit -m "feat(frontend): add meta tags to workspace pages for SEO"
```

---

### Task 3: Fix Deprecated Event Handlers in Getting-Started

**Files:**
- Modify: `frontend-svelt/src/routes/getting-started/+page.svelte`

**Step 1: Fix on:change to onchange for provider select**

In `frontend-svelt/src/routes/getting-started/+page.svelte:189`, change:

```svelte
<!-- Before -->
<select
	id="provider"
	class="select"
	bind:value={selectedProvider}
	on:change={onOcrProviderSelected}
>

<!-- After -->
<select
	id="provider"
	class="select"
	bind:value={selectedProvider}
	onchange={onOcrProviderSelected}
>
```

**Step 2: Fix on:input to oninput for API key field**

In `frontend-svelt/src/routes/getting-started/+page.svelte:214`, change:

```svelte
<!-- Before -->
<input
	id="api-key"
	class="input"
	type="password"
	placeholder="sk-..."
	bind:value={state.answers.ocrProviderApiKey}
	on:input={(e) =>
		onboard.setAnswer('ocrProviderApiKey', (e.target as HTMLInputElement).value)}
	aria-describedby="api-hint"
/>

<!-- After -->
<input
	id="api-key"
	class="input"
	type="password"
	placeholder="sk-..."
	bind:value={state.answers.ocrProviderApiKey}
	oninput={(e) =>
		onboard.setAnswer('ocrProviderApiKey', (e.target as HTMLInputElement).value)}
	aria-describedby="api-hint"
/>
```

**Step 3: Fix on:input to oninput for campaign name**

In `frontend-svelt/src/routes/getting-started/+page.svelte:233`, change:

```svelte
<!-- Before -->
<input
	id="campaign-name"
	class="input"
	placeholder="e.g., Smith for Mayor"
	bind:value={state.answers.campaign_name}
	on:input={(e) =>
		onboard.setAnswer('campaign_name', (e.target as HTMLInputElement).value)}
/>

<!-- After -->
<input
	id="campaign-name"
	class="input"
	placeholder="e.g., Smith for Mayor"
	bind:value={state.answers.campaign_name}
	oninput={(e) =>
		onboard.setAnswer('campaign_name', (e.target as HTMLInputElement).value)}
/>
```

**Step 4: Run typecheck**

Run:
```bash
cd frontend-svelt && bun run typecheck
```

Expected: No errors

**Step 5: Commit deprecated handler fixes**

Run:
```bash
cd frontend-svelt
git add src/routes/getting-started/+page.svelte
git commit -m "refactor(frontend): replace deprecated on: event handlers with on attributes"
```

---

### Task 4: Re-run Lighthouse and Verify Scores

**Step 1: Run Lighthouse again**

Run:
```bash
lighthouse http://localhost:5173/workspace --output=json --output-path=./lighthouse-workspace-after.json --chrome-flags="--headless"
```

**Step 2: Check scores**

Run:
```bash
node -e "const fs = require('fs'); const data = JSON.parse(fs.readFileSync('./lighthouse-workspace-after.json')); console.log('Performance:', data.categories.performance.score); console.log('Accessibility:', data.categories.accessibility.score); console.log('Best Practices:', data.categories['best-practices'].score); console.log('SEO:', data.categories.seo.score);"
```

Expected: All scores >0.80 (80%)

**Step 3: If scores <80, identify remaining issues**

Run:
```bash
node -e "const fs = require('fs'); const data = JSON.parse(fs.readFileSync('./lighthouse-workspace-after.json')); const failed = data.categories.performance.auditRefs.filter(a => a.result.score !== null && a.result.score < 0.9); failed.forEach(f => console.log(f.result.title, ':', f.result.score));"
```

**Step 4: Document scores in PROGRESS.md**

Add to `openspec/PROGRESS.md` under Part C:

```markdown
**Lighthouse Scores (2026-03-11):**
- Workspace Dashboard: Performance XX%, Accessibility XX%, Best Practices XX%, SEO XX%
- Campaigns: Performance XX%, Accessibility XX%, Best Practices XX%, SEO XX%
- Getting Started: Performance XX%, Accessibility XX%, Best Practices XX%, SEO XX%
```

**Step 5: Commit progress update**

Run:
```bash
git add openspec/PROGRESS.md
git commit -m "docs: record Lighthouse scores for Phase 5 Part C"
```

---

## Part B: Error Handling

> TDD approach - write tests first.

### Task 5: Create API Error Integration Tests

**Files:**
- Create: `frontend-svelt/tests/integration/errors/test_api_errors.ts`
- Create: `frontend-svelt/tests/integration/errors/helpers.ts`

**Step 1: Create test helpers**

Create `frontend-svelt/tests/integration/errors/helpers.ts`:

```typescript
export function mockFetchError(status: number, message: string) {
	return jest.fn().mockResolvedValue({
		ok: false,
		status,
		json: async () => ({ error: message })
	});
}

export function mockNetworkError() {
	return jest.fn().mockRejectedValue(new Error('Network error'));
}

export function mockTimeout() {
	return jest.fn().mockImplementation(
		() =>
			new Promise((_, reject) =>
				setTimeout(() => reject(new Error('Timeout')), 100)
			)
	);
}
```

**Step 2: Write test for network error**

Create `frontend-svelt/tests/integration/errors/test_api_errors.ts`:

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { campaigns } from '$lib/stores/campaigns';
import { mockNetworkError } from './helpers';

describe('API Error Handling', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	describe('Network errors', () => {
		it('shows error message when network fails', async () => {
			global.fetch = mockNetworkError();

			await campaigns.fetchAll();

			const state = campaigns.subscribe;
			expect(state.error).toBe('Unable to connect to server');
			expect(state.loading).toBe(false);
		});

		it('shows retry button on network error', async () => {
			global.fetch = mockNetworkError();

			await campaigns.fetchAll();

			// Verify error state includes retry capability
			expect(campaigns.hasError).toBe(true);
			expect(campaigns.canRetry).toBe(true);
		});
	});

	describe('HTTP errors', () => {
		it('shows 404 message for not found', async () => {
			global.fetch = mockFetchError(404, 'Campaign not found');

			await campaigns.fetchAll();

			expect(campaigns.error).toBe('Campaign not found');
		});

		it('shows generic message for 500 error', async () => {
			global.fetch = mockFetchError(500, 'Internal server error');

			await campaigns.fetchAll();

			expect(campaigns.error).toBe('Server error. Please try again later.');
		});

		it('shows validation message for 422 error', async () => {
			global.fetch = mockFetchError(422, 'Invalid campaign name');

			await campaigns.create({ name: '', year: 2024 });

			expect(campaigns.error).toBe('Invalid campaign name');
		});
	});

	describe('Timeout handling', () => {
		it('shows timeout message after 30s', async () => {
			global.fetch = mockTimeout();

			await campaigns.fetchAll();

			expect(campaigns.error).toBe('Request timed out. Please try again.');
		});
	});
});
```

**Step 3: Run test to verify it fails**

Run:
```bash
cd frontend-svelt && bun run test tests/integration/errors/test_api_errors.ts
```

Expected: FAIL - tests don't pass yet

**Step 4: Commit failing tests (TDD)**

Run:
```bash
cd frontend-svelt
git add tests/integration/errors/
git commit -m "test(frontend): add API error handling tests (failing)"
```

---

### Task 6: Enhance Error Page Component

**Files:**
- Modify: `frontend-svelt/src/routes/+error.svelte`

**Step 1: Write test for enhanced error page**

Create `frontend-svelt/src/routes/+error.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import ErrorPage from './+error.svelte';

describe('Error Page', () => {
	describe('Rendering', () => {
		it('shows 404 message for not found', () => {
			render(ErrorPage, { error: { message: 'Not found' }, status: 404 });

			expect(screen.getByRole('heading', { name: '404' })).toBeInTheDocument();
			expect(screen.getByText(/page you're looking for/i)).toBeInTheDocument();
		});

		it('shows 500 message for server error', () => {
			render(ErrorPage, { error: { message: 'Server error' }, status: 500 });

			expect(screen.getByRole('heading', { name: '500' })).toBeInTheDocument();
			expect(screen.getByText(/server error/i)).toBeInTheDocument();
		});

		it('shows generic message for unknown error', () => {
			render(ErrorPage, { error: { message: 'Unknown' }, status: 418 });

			expect(screen.getByRole('heading', { name: '418' })).toBeInTheDocument();
			expect(screen.getByText(/unexpected error/i)).toBeInTheDocument();
		});
	});

	describe('Navigation', () => {
		it('shows return home link', () => {
			render(ErrorPage, { error: { message: 'Error' }, status: 500 });

			expect(screen.getByRole('link', { name: /return home/i })).toHaveAttribute('href', '/');
		});

		it('shows go back button', () => {
			render(ErrorPage, { error: { message: 'Error' }, status: 500 });

			expect(screen.getByRole('button', { name: /go back/i })).toBeInTheDocument();
		});
	});

	describe('Accessibility', () => {
		it('has role="alert"', () => {
			render(ErrorPage, { error: { message: 'Error' }, status: 500 });

			expect(screen.getByRole('alert')).toBeInTheDocument();
		});

		it('has aria-live="assertive"', () => {
			const { container } = render(ErrorPage, { error: { message: 'Error' }, status: 500 });

			expect(container.querySelector('[aria-live="assertive"]')).toBeInTheDocument();
		});
	});
});
```

**Step 2: Run test to verify it fails**

Run:
```bash
cd frontend-svelt && bun run test src/routes/+error.test.ts
```

Expected: FAIL - current implementation doesn't match

**Step 3: Implement enhanced error page**

Replace `frontend-svelt/src/routes/+error.svelte`:

```svelte
<script lang="ts">
	import { goto } from '$app/navigation';
	import { Button } from '$lib/components/ui';

	let { error, status } = $props<{
		error: { message?: string } | null;
		status: number;
	}>();

	const errorMessages: Record<number, { title: string; description: string }> = {
		404: {
			title: 'Page Not Found',
			description: "The page you're looking for doesn't exist or has been moved."
		},
		500: {
			title: 'Server Error',
			description: "Something went wrong on our end. Please try again later."
		},
		403: {
			title: 'Access Denied',
			description: "You don't have permission to access this resource."
		},
		422: {
			title: 'Validation Error',
			description: 'The request could not be processed due to invalid data.'
		}
	};

	const errorInfo = errorMessages[status] || {
		title: 'Unexpected Error',
		description: error?.message || 'An unexpected error occurred.'
	};

	const goBack = () => {
		if (typeof window !== 'undefined' && window.history.length > 1) {
			window.history.back();
		} else {
			goto('/');
		}
	};
</script>

<svelte:head>
	<title>{status} — {errorInfo.title} — Votecatcher</title>
</svelte:head>

<div class="error-container" role="alert" aria-live="assertive">
	<div class="error-card">
		<div class="error-code">{status}</div>
		<h1 class="error-title">{errorInfo.title}</h1>
		<p class="error-description">{errorInfo.description}</p>
		<div class="error-actions">
			<Button variant="secondary" onclick={goBack}>Go Back</Button>
			<Button variant="primary" href="/">Return Home</Button>
		</div>
	</div>
</div>

<style>
	.error-container {
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 60vh;
		padding: 2rem;
	}

	.error-card {
		max-width: 32rem;
		text-align: center;
		padding: 2rem;
		background: var(--card-bg, white);
		border-radius: 0.5rem;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}

	.error-code {
		font-size: 6rem;
		font-weight: bold;
		color: var(--text-muted, #6b7280);
		line-height: 1;
		margin-bottom: 1rem;
	}

	.error-title {
		font-size: 1.5rem;
		font-weight: 600;
		margin-bottom: 0.5rem;
		color: var(--text-primary, #111827);
	}

	.error-description {
		color: var(--text-muted, #6b7280);
		margin-bottom: 2rem;
	}

	.error-actions {
		display: flex;
		gap: 1rem;
		justify-content: center;
	}
</style>
```

**Step 4: Run test to verify it passes**

Run:
```bash
cd frontend-svelt && bun run test src/routes/+error.test.ts
```

Expected: PASS - all tests pass

**Step 5: Commit enhanced error page**

Run:
```bash
cd frontend-svelt
git add src/routes/+error.svelte src/routes/+error.test.ts
git commit -m "feat(frontend): enhance error page with status-specific messages"
```

---

### Task 7: Add SSE Connection Error Handling

**Files:**
- Modify: `frontend-svelt/src/lib/stores/jobs.ts`
- Modify: `frontend-svelt/src/routes/workspace/jobs/+page.svelte`

**Step 1: Write test for SSE errors**

Add to `frontend-svelt/src/lib/stores/jobs.test.ts`:

```typescript
describe('SSE Error Handling', () => {
	it('shows error when connection fails', async () => {
		// Mock EventSource to fail on connection
		const mockEventSource = vi.fn().mockImplementation(() => {
			const es = new EventTarget();
			setTimeout(() => es.dispatchEvent(new Event('error')), 10);
			return Object.assign(es, { close: vi.fn(), readyState: 0 });
		});

		vi.stubGlobal('EventSource', mockEventSource);

		await jobs.connectToJobSSE('job-123');

		expect(jobs.sseError).toBe('Connection failed. Retrying...');
	});

	it('reconnects with exponential backoff', async () => {
		vi.useFakeTimers();

		const closeMock = vi.fn();
		let connectionAttempts = 0;

		const mockEventSource = vi.fn().mockImplementation(() => {
			const es = new EventTarget();
			connectionAttempts++;

			if (connectionAttempts < 3) {
				// Fail first 2 attempts
				setTimeout(() => es.dispatchEvent(new Event('error')), 10);
			} else {
				// Succeed on 3rd attempt
				setTimeout(() => {
					es.dispatchEvent(new MessageEvent('message', { data: JSON.stringify({ status: 'OCR_STARTED' }) }));
				}, 10);
			}

			return Object.assign(es, { close: closeMock, readyState: 0 });
		});

		vi.stubGlobal('EventSource', mockEventSource);

		await jobs.connectToJobSSE('job-123');

		// First retry after 1s
		await vi.advanceTimersByTimeAsync(1000);
		expect(connectionAttempts).toBe(2);

		// Second retry after 2s
		await vi.advanceTimersByTimeAsync(2000);
		expect(connectionAttempts).toBe(3);

		// Connection successful
		expect(jobs.sseError).toBeNull();

		vi.useRealTimers();
	});

	it('shows permanent error after max retries', async () => {
		vi.useFakeTimers();

		const mockEventSource = vi.fn().mockImplementation(() => {
			const es = new EventTarget();
			setTimeout(() => es.dispatchEvent(new Event('error')), 10);
			return Object.assign(es, { close: vi.fn(), readyState: 0 });
		});

		vi.stubGlobal('EventSource', mockEventSource);

		await jobs.connectToJobSSE('job-123');

		// Exhaust retries (1s, 2s, 4s, 8s = 15s total)
		await vi.advanceTimersByTimeAsync(15000);

		expect(jobs.sseError).toBe('Unable to reconnect. Please refresh the page.');
		expect(jobs.sseRetries).toBe(4);

		vi.useRealTimers();
	});
});
```

**Step 2: Run test to verify it fails**

Run:
```bash
cd frontend-svelt && bun run test src/lib/stores/jobs.test.ts -t "SSE Error"
```

Expected: FAIL - SSE error handling not implemented

**Step 3: Implement SSE error handling in jobs store**

Update `frontend-svelt/src/lib/stores/jobs.ts` to add error handling:

```typescript
// Add to store state
interface JobsState {
	// ... existing fields
	sseError: string | null;
	sseRetries: number;
	sseMaxRetries: number;
}

// Add to initial state
const initialState: JobsState = {
	// ... existing
	sseError: null,
	sseRetries: 0,
	sseMaxRetries: 4
};

// Add SSE connection with retry
function connectToJobSSE(jobId: string) {
	const { subscribe, set, update } = writable(initialState);

	const connect = (retryDelay = 0) => {
		setTimeout(() => {
			const eventSource = new EventSource(`/api/jobs/${jobId}/status`);

			eventSource.onerror = () => {
				eventSource.close();

				update((state) => {
					const newRetries = state.sseRetries + 1;

					if (newRetries >= state.sseMaxRetries) {
						return {
							...state,
							sseError: 'Unable to reconnect. Please refresh the page.',
							sseRetries: newRetries
						};
					}

					// Exponential backoff: 1s, 2s, 4s, 8s
					const nextDelay = Math.pow(2, newRetries - 1) * 1000;
					setTimeout(() => connect(nextDelay), nextDelay);

					return {
						...state,
						sseError: 'Connection lost. Retrying...',
						sseRetries: newRetries
					};
				});
			};

			eventSource.onopen = () => {
				update((state) => ({
					...state,
					sseError: null,
					sseRetries: 0
				}));
			};

			eventSource.onmessage = (event) => {
				const data = JSON.parse(event.data);
				update((state) => ({
					...state,
					currentJob: data,
					sseError: null
				}));
			};
		}, retryDelay);
	};

	connect();

	return { subscribe };
}
```

**Step 4: Run test to verify it passes**

Run:
```bash
cd frontend-svelt && bun run test src/lib/stores/jobs.test.ts -t "SSE Error"
```

Expected: PASS - all SSE error tests pass

**Step 5: Commit SSE error handling**

Run:
```bash
cd frontend-svelt
git add src/lib/stores/jobs.ts src/lib/stores/jobs.test.ts
git commit -m "feat(frontend): add SSE connection error handling with retry"
```

---

### Task 8: Add Getting-Started Error Handling

**Files:**
- Modify: `frontend-svelt/src/routes/getting-started/+page.svelte`
- Create: `frontend-svelt/src/routes/getting-started/+page.test.ts`

**Step 1: Write test for getting-started errors**

Create `frontend-svelt/src/routes/getting-started/+page.test.ts`:

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import GettingStartedPage from './+page.svelte';

describe('Getting Started Error Handling', () => {
	describe('Provider Selection', () => {
		it('shows error for invalid API key format', async () => {
			render(GettingStartedPage, {
				data: {
					user: { id: '1' },
					steps: [{ id: 'provider', title: 'Provider', description: '' }],
					years: ['2024']
				}
			});

			// Select provider
			const select = screen.getByLabelText(/ai provider/i);
			await fireEvent.change(select, { target: { value: 'open_ai' } });

			// Enter invalid key
			const input = screen.getByLabelText(/api key/i);
			await fireEvent.input(input, { target: { value: 'invalid-key' } });

			// Click next
			const nextButton = screen.getByRole('button', { name: /next/i });
			await fireEvent.click(nextButton);

			await waitFor(() => {
				expect(screen.getByRole('alert')).toHaveTextContent(/invalid api key format/i);
			});
		});

		it('shows error when API key validation fails', async () => {
			vi.mock('$lib/api/client', () => ({
				api: {
					storeApiKey: vi.fn().mockResolvedValue({ ok: false, error: 'Unable to verify API key' })
				}
			}));

			render(GettingStartedPage, {
				data: {
					user: { id: '1' },
					steps: [{ id: 'provider', title: 'Provider', description: '' }],
					years: ['2024']
				}
			});

			// Fill valid-looking form
			const select = screen.getByLabelText(/ai provider/i);
			await fireEvent.change(select, { target: { value: 'open_ai' } });

			const input = screen.getByLabelText(/api key/i);
			await fireEvent.input(input, { target: { value: 'sk-valid-key-format' } });

			const nextButton = screen.getByRole('button', { name: /next/i });
			await fireEvent.click(nextButton);

			await waitFor(() => {
				expect(screen.getByRole('alert')).toHaveTextContent(/unable to verify/i);
			});
		});
	});

	describe('Campaign Creation', () => {
		it('shows error for duplicate campaign name', async () => {
			vi.mock('$lib/api/client', () => ({
				api: {
					createCampaign: vi.fn().mockResolvedValue({ ok: false, error: 'Campaign name already exists' })
				}
			}));

			render(GettingStartedPage, {
				data: {
					user: { id: '1' },
					steps: [{ id: 'campaign', title: 'Campaign', description: '' }],
					years: ['2024']
				}
			});

			// Fill form
			const nameInput = screen.getByLabelText(/campaign name/i);
			await fireEvent.input(nameInput, { target: { value: 'Existing Campaign' } });

			const yearSelect = screen.getByLabelText(/election year/i);
			await fireEvent.change(yearSelect, { target: { value: '2024' } });

			const nextButton = screen.getByRole('button', { name: /next/i });
			await fireEvent.click(nextButton);

			await waitFor(() => {
				expect(screen.getByRole('alert')).toHaveTextContent(/already exists/i);
			});
		});
	});
});
```

**Step 2: Run test to verify it fails**

Run:
```bash
cd frontend-svelt && bun run test src/routes/getting-started/+page.test.ts
```

Expected: FAIL - error display not implemented

**Step 3: Update getting-started page to use ErrorDisplay component**

In `frontend-svelt/src/routes/getting-started/+page.svelte`, replace the error div:

```svelte
<!-- Replace this -->
{#if errorMsg}
	<div role="alert" style="color:var(--vc-danger)" class="small">{errorMsg}</div>
{/if}

<!-- With this -->
{#if errorMsg}
	<ErrorDisplay
		variant="error"
		message={errorMsg}
		onRetry={canRetry ? () => next() : undefined}
	/>
{/if}
```

Add import at top:

```svelte
import { ErrorDisplay } from '$lib/components/ui';
```

**Step 4: Run test to verify it passes**

Run:
```bash
cd frontend-svelt && bun run test src/routes/getting-started/+page.test.ts
```

Expected: PASS - all tests pass

**Step 5: Commit getting-started error handling**

Run:
```bash
cd frontend-svelt
git add src/routes/getting-started/
git commit -m "feat(frontend): improve getting-started error handling with ErrorDisplay"
```

---

## Part D: Documentation

### Task 9: Generate Auto-Generated API Docs

**Step 1: Install @redocly/cli**

Run:
```bash
npm install -g @redocly/cli
```

**Step 2: Create output directory**

Run:
```bash
mkdir -p docs/api
```

**Step 3: Generate API docs**

Run:
```bash
cd /Users/kurian/01 - Projects/votecatcher
redocly build-doc backend/openapi.yaml -o docs/api/index.html
```

Expected: `docs/api/index.html` created

**Step 4: Verify generated docs**

Run:
```bash
open docs/api/index.html
```

Expected: Beautiful API documentation in browser

**Step 5: Add docs build script to package.json**

In `package.json` (root), add:

```json
{
	"scripts": {
		"docs:api": "redocly build-doc backend/openapi.yaml -o docs/api/index.html"
	}
}
```

**Step 6: Commit API docs**

Run:
```bash
git add docs/api/ package.json
git commit -m "docs: add auto-generated API documentation"
```

---

### Task 10: Create User Guide Directory Structure

**Step 1: Create directory**

Run:
```bash
mkdir -p docs/user-guide
```

**Step 2: Create main README**

Create `docs/user-guide/README.md`:

```markdown
# VoteCatcher User Guide

Welcome to VoteCatcher! This guide will help you get started with campaign signature verification.

## Quick Links

- **[Getting Started](./getting-started.md)** - Set up your first campaign
- **[Uploading Data](./uploading-data.md)** - Upload voter lists and petitions
- **[Running Jobs](./running-jobs.md)** - Create and monitor OCR/matching jobs
- **[Viewing Results](./viewing-results.md)** - Analyze matching results
- **[Sessions](./sessions.md)** - Save and restore workspace state
- **[Demo Mode](./demo-mode.md)** - Try VoteCatcher with sample data

## Overview

VoteCatcher automates the verification of petition signatures using AI-powered OCR and fuzzy matching. Upload your voter registration list and petition PDFs, and VoteCatcher will extract handwritten text and match it against your voter database.

## Typical Workflow

1. **Choose an AI provider** - Select OpenAI, Gemini, or Mistral for OCR
2. **Create a campaign** - Name your campaign and select the election year
3. **Upload data** - Add voter registration list and petition PDFs
4. **Run a job** - Start OCR processing and signature matching
5. **Review results** - View matches with confidence scores
6. **Export** - Download results as CSV for further analysis

## Need Help?

- **API Documentation:** [API Reference](../api/index.html)
- **Running Locally:** [Local Setup Guide](../running-locally.md)
- **Architecture:** [Technical Overview](../architecture/README.md)
```

**Step 3: Commit structure**

Run:
```bash
git add docs/user-guide/README.md
git commit -m "docs: create user guide directory and main README"
```

---

### Task 11: Create Getting Started Guide

**Create `docs/user-guide/getting-started.md`:**

```markdown
# Getting Started

## Overview

This guide walks you through setting up VoteCatcher for the first time. You'll choose an AI provider, create a campaign, and upload your first voter registration file.

## Prerequisites

- VoteCatcher installed and running
- API key for at least one LLM provider:
  - [OpenAI API key](https://platform.openai.com/api-keys)
  - [Google Gemini API key](https://ai.google.dev/tutorials/setup)
  - [Mistral API key](https://console.mistral.ai/)
- Voter registration file (CSV, Excel, or JSON)

## Steps

### Step 1: Access VoteCatcher

1. Open your browser to `http://localhost:5173`
2. You'll be redirected to the Getting Started wizard

### Step 2: Choose AI Provider

1. Select your preferred OCR provider from the dropdown
2. Paste your API key in the field provided
3. Click **Next** to validate your key

**Provider Comparison:**

| Provider | Speed | Accuracy | Cost |
|----------|-------|----------|------|
| OpenAI GPT-4o-mini | Fast | High | Low |
| Gemini Flash | Fastest | High | Lowest |
| Mistral Pixtral | Fast | Medium | Low |

### Step 3: Create Campaign

1. Enter a **Campaign Name** (e.g., "Smith for Mayor 2024")
2. Select the **Election Year**
3. Optionally add a **Description**
4. Click **Next**

**Note:** Campaign name must be at least 3 characters.

### Step 4: Upload Voter Registration File

1. Click **Choose File**
2. Select your voter registration file (CSV, Excel, or JSON)
3. Verify the file name and size display correctly
4. Click **Complete**

**Supported Formats:**
- CSV (comma-separated values)
- Excel (.xlsx, .xls)
- JSON (array of objects)

### Step 5: Navigate to Workspace

After completion, you'll be redirected to the workspace dashboard where you can:
- View your campaign
- Upload petition PDFs
- Start OCR/matching jobs

## Troubleshooting

### "Invalid API key format"

**Problem:** API key validation failed.
**Solution:**
- Ensure you copied the entire key (no extra spaces)
- OpenAI keys start with `sk-`
- Check your provider's dashboard to regenerate if needed

### "Campaign name already exists"

**Problem:** You're trying to create a campaign with a duplicate name.
**Solution:**
- Use a unique name (e.g., "Smith for Mayor 2024 - Attempt 2")
- Or delete the existing campaign first

### "Unsupported file type"

**Problem:** Uploaded file is not CSV, Excel, or JSON.
**Solution:**
- Convert your file to one of the supported formats
- Ensure file extension matches content (.csv, .xlsx, .json)

## Next Steps

- [Upload petition PDFs](./uploading-data.md)
- [Run your first job](./running-jobs.md)
```

**Commit:**

```bash
git add docs/user-guide/getting-started.md
git commit -m "docs: add getting started user guide"
```

---

### Task 12: Create Uploading Data Guide

**Create `docs/user-guide/uploading-data.md`:**

```markdown
# Uploading Data

## Overview

VoteCatcher processes two types of data: voter registration lists and petition PDFs. This guide explains how to upload and validate both.

## Prerequisites

- Campaign created (see [Getting Started](./getting-started.md))
- Voter registration file ready
- Petition PDFs ready (if processing signatures)

## Voter Registration Lists

### Supported Formats

- **CSV** - Recommended for most cases
- **Excel** (.xlsx, .xls) - Good for data from spreadsheets
- **JSON** - Array of objects with voter data

### Required Fields

Your voter registration file should include:

| Field | Description | Example |
|-------|-------------|---------|
| `first_name` | Voter's first name | "John" |
| `last_name` | Voter's last name | "Smith" |
| `address` | Street address | "123 Main St" |
| `city` | City name | "Washington" |
| `state` | State abbreviation | "DC" |
| `zipcode` | ZIP code | "20001" |

### Upload Steps

1. Navigate to **Workspace** → **Upload**
2. Select **Voter List** tab
3. Click **Choose File** or drag-and-drop
4. Select your voter registration file
5. Review validation results
6. Click **Upload**

### Validation

VoteCatcher validates:
- File format is supported
- Required columns exist
- Data is properly formatted
- No duplicate records

## Petition PDFs

### Supported Formats

- **PDF** - Standard PDF files

### Upload Steps

1. Navigate to **Workspace** → **Upload**
2. Select **Petition** tab
3. Click **Choose File** or drag-and-drop
4. Select your petition PDF
5. Review pre-crop preview
6. Click **Upload**

### Pre-Cropping

VoteCatcher automatically pre-crops petition PDFs into individual signature entries. This improves OCR accuracy.

**Note:** For DC region, default crop coordinates are used. Other regions may require manual configuration.

## Troubleshooting

### "Missing required columns"

**Problem:** CSV/Excel missing required fields.
**Solution:**
- Ensure column headers match exactly (case-sensitive)
- Check for extra spaces in column names
- Map columns in your spreadsheet to match required names

### "Duplicate records detected"

**Problem:** Same voter appears multiple times.
**Solution:**
- Remove duplicates in your source file
- VoteCatcher uses a hash to detect exact duplicates

### "PDF processing failed"

**Problem:** Petition PDF could not be processed.
**Solution:**
- Ensure PDF is not password-protected
- Check PDF is not corrupted (open in PDF reader)
- Try re-saving PDF from original source

## Next Steps

- [Run your first job](./running-jobs.md)
- [View results](./viewing-results.md)
```

**Commit:**

```bash
git add docs/user-guide/uploading-data.md
git commit -m "docs: add uploading data user guide"
```

---

### Task 13: Create Remaining User Guides

**Create `docs/user-guide/running-jobs.md`:**

```markdown
# Running Jobs

## Overview

Jobs in VoteCatcher orchestrate the full signature verification pipeline: OCR extraction followed by fuzzy matching against your voter registration list.

## Prerequisites

- Campaign created
- Voter registration list uploaded
- At least one petition PDF uploaded

## Create a Job

### Step 1: Navigate to Jobs

1. Go to **Workspace** → **Jobs**
2. Click **Create New Job**

### Step 2: Select Campaign

1. Choose the campaign from the dropdown
2. Click **Next**

### Step 3: Select Petition Scans

1. Check the boxes next to petition scans to process
2. Click **Create Job**

### Step 4: Monitor Progress

The job status page shows real-time updates:

- **NOT_STARTED** - Job created, waiting to start
- **OCR_PENDING** - OCR batch submitted
- **OCR_STARTED** - OCR processing in progress
- **OCR_COMPLETED** - OCR finished, ready for matching
- **MATCHING** - Fuzzy matching in progress
- **MATCHING_COMPLETED** - Job complete, results available

### Real-Time Updates

Job status updates automatically via Server-Sent Events (SSE). No page refresh needed.

## Cancel a Job

1. Go to **Workspace** → **Jobs**
2. Click on the running job
3. Click **Cancel Job**
4. Confirm cancellation

**Note:** Cancelled jobs cannot be resumed. Start a new job if needed.

## Job States

| State | Description | Can Cancel? |
|-------|-------------|-------------|
| NOT_STARTED | Created, not started | Yes |
| OCR_PENDING | Batch submitted to LLM | Yes |
| OCR_STARTED | Processing OCR | No |
| OCR_COMPLETED | OCR done, matching queued | No |
| MATCHING | Fuzzy matching | No |
| MATCHING_COMPLETED | Complete | No |
| CANCELLED | User cancelled | No |
| FAILED | Error occurred | No |

## Troubleshooting

### "No petition scans available"

**Problem:** No scans to select when creating job.
**Solution:**
- Upload at least one petition PDF first
- Check that scans are associated with the correct campaign

### "Job stuck in OCR_PENDING"

**Problem:** Job hasn't progressed past pending state.
**Solution:**
- LLM batch APIs can take 1-5 minutes to start
- Check your API provider's status page
- Wait 5 minutes before assuming failure

### "Connection lost" error

**Problem:** Real-time updates stopped.
**Solution:**
- VoteCatcher auto-reconnects with exponential backoff
- If error persists after 15 seconds, refresh the page
- Check backend is still running

## Next Steps

- [View results](./viewing-results.md)
```

**Create `docs/user-guide/viewing-results.md`:**

```markdown
# Viewing Results

## Overview

After a job completes, view matching results to verify petition signatures against your voter registration list.

## Prerequisites

- Job with status **MATCHING_COMPLETED**

## Access Results

1. Go to **Workspace** → **Results**
2. Select the job from the dropdown
3. Results table loads automatically

## Results Table

### Columns

| Column | Description |
|--------|-------------|
| **Crop Image** | Pre-cropped signature from petition |
| **OCR Text** | Extracted name and address |
| **Top Match** | Best matching voter record |
| **Confidence** | Match quality (HIGH, MEDIUM, LOW) |
| **Score** | Similarity percentage (0-100) |

### Filtering

Filter results by confidence level:

- **All** - Show all results
- **HIGH** - Score ≥85%
- **MEDIUM** - Score 60-84%
- **LOW** - Score <60%

### Pagination

- Default: 25 results per page
- Navigate with Previous/Next buttons
- Jump to specific page with page number input

## Export to CSV

1. Click **Export CSV** button
2. File downloads automatically
3. Open in Excel, Google Sheets, or text editor

### CSV Format

The exported CSV includes:

```csv
crop_id,ocr_name,ocr_address,match_name,match_address,confidence,score
1,John Smith,123 Main St,John A Smith,123 Main St Washington DC,HIGH,92.5
```

## Confidence Scores

### HIGH (≥85%)

Strong match. OCR text closely matches voter record. High confidence this is a valid signature.

### MEDIUM (60-84%)

Moderate match. Some discrepancies. Manual review recommended.

### LOW (<60%)

Weak match. Significant differences. Likely requires manual verification.

## Troubleshooting

### "No results available"

**Problem:** Results page shows empty.
**Solution:**
- Ensure job completed successfully
- Check job status is MATCHING_COMPLETED
- Refresh the page

### "CSV export failed"

**Problem:** Export button doesn't download file.
**Solution:**
- Check browser popup blocker
- Try different browser
- Check backend logs for errors

## Next Steps

- [Manage sessions](./sessions.md)
```

**Create `docs/user-guide/sessions.md`:**

```markdown
# Sessions

## Overview

Sessions allow you to save and restore your workspace state. Useful for:
- Pausing work and resuming later
- Backing up your progress
- Sharing configurations with team members

## Prerequisites

- At least one campaign created
- Data uploaded or jobs run

## Save Session

### Step 1: Navigate to Sessions

1. Go to **Workspace** → **Sessions**

### Step 2: Save Current State

1. Click **Save Session**
2. Enter a session name (e.g., "DC 2024 - March 11")
3. Click **Save**

Session stores references to:
- Campaigns
- Uploaded files
- Jobs
- Results

**Note:** Sessions store references (IDs), not full data. Deleting data makes sessions invalid.

## Load Session

### Step 1: Select Session

1. Go to **Workspace** → **Sessions**
2. Click on a saved session

### Step 2: Load

1. Click **Load Session**
2. Confirm loading (overwrites current workspace)
3. Workspace updates with session state

## Export Session

Export creates a ZIP file with all session data:

1. Click **Export** on a session
2. ZIP file downloads automatically
3. Contains JSON metadata + file references

### Export Contents

```
session-export.zip
├── session.json         # Session metadata
├── campaigns.json       # Campaign data
├── jobs.json            # Job data
└── results/             # Results exports
```

## Delete Session

1. Click **Delete** on a session
2. Confirm deletion
3. Session removed from list

**Note:** Deleting a session does NOT delete the underlying campaigns, jobs, or data.

## Troubleshooting

### "Session load failed"

**Problem:** Session cannot be loaded.
**Solution:**
- Check that referenced campaigns/jobs still exist
- If data was deleted, session is invalid
- Create a new session instead

### "Export incomplete"

**Problem:** ZIP file missing expected data.
**Solution:**
- Some data may have been deleted
- Check session.json for references
- Re-save session with current data

## Next Steps

- [Try demo mode](./demo-mode.md)
```

**Create `docs/user-guide/demo-mode.md`:**

```markdown
# Demo Mode

## Overview

Demo mode lets you try VoteCatcher with pre-configured sample data. Perfect for:
- Learning the workflow
- Testing features
- Demonstrating to stakeholders

## Prerequisites

- VoteCatcher running locally
- Demo mode enabled (check feature flags)

## Access Demo Mode

1. Go to **Workspace** → **Demo**
2. Demo page loads with available options

## Load Pre-Baked Session

### Step 1: Click Load Demo

1. Click **Load Demo Session**
2. Wait for loading to complete

### Step 2: Explore

The pre-baked session includes:
- Sample campaign (DC 2024)
- 10 sample petition scans
- OCR results with matches
- Results ready to view

### Step 3: Navigate

1. Go to **Results** to see sample matches
2. Explore confidence levels
3. Try filtering and CSV export

## Reset Workspace

### Step 1: Click Reset

1. Click **Reset Workspace**
2. Confirm reset

### Step 2: Clean Slate

Reset removes:
- All campaigns
- All uploaded files
- All jobs and results
- All saved sessions

**Warning:** Reset is irreversible. Use with caution.

## Demo Data Details

### Sample Campaign

- **Name:** DC 2024 Demo
- **Year:** 2024
- **Region:** Washington, DC

### Sample Petitions

- 10 pre-cropped signature entries
- Simulated handwriting variations
- Matches against fake voter list

### Fake Voter List

- 100,000 synthetic voter records
- Realistic DC addresses
- No real person data

## Troubleshooting

### "Demo mode disabled"

**Problem:** Demo page shows "Feature disabled".
**Solution:**
- Check feature flags in backend config
- Ensure `FEATURE_DEMO_MODE=true`
- Restart backend server

### "Reset failed"

**Problem:** Workspace reset incomplete.
**Solution:**
- Check backend logs for errors
- Manually delete database and re-run migrations
- Restart both frontend and backend

## Next Steps

- [Start real workflow](./getting-started.md)
```

**Commit all guides:**

```bash
git add docs/user-guide/
git commit -m "docs: add complete user guide documentation"
```

---

### Task 14: Update README Links

**Step 1: Add documentation links to README**

In `README.md`, update Documentation section:

```markdown
## Documentation

### For Users

- **[User Guide](docs/user-guide/)** - Complete workflow guides
  - [Getting Started](docs/user-guide/getting-started.md)
  - [Uploading Data](docs/user-guide/uploading-data.md)
  - [Running Jobs](docs/user-guide/running-jobs.md)
  - [Viewing Results](docs/user-guide/viewing-results.md)
- **[API Documentation](docs/api/index.html)** - Auto-generated API reference
- **[Running Locally](docs/running-locally.md)** - Detailed setup and configuration

### For Developers

- **[Architecture Overview](docs/architecture/README.md)** - System design
- **[C4 Diagrams](docs/architecture/)** - Context, containers, components
- **[Architecture Decisions](docs/architecture/decisions/)** - ADRs
- **[API Specification](backend/openapi.yaml)** - OpenAPI 3.1 spec
```

**Step 2: Commit README update**

```bash
git add README.md
git commit -m "docs: update README with links to user guide and API docs"
```

---

### Task 15: Update PROGRESS.md

**Step 1: Document completion**

Add to `openspec/PROGRESS.md`:

```markdown
### Part B: Error Handling ✅ **COMPLETE**
- [x] API error integration tests
- [x] Enhanced error page component
- [x] SSE connection error handling
- [x] Getting-started error handling
- [x] All error scenarios tested

### Part C: Performance ✅ **COMPLETE**
- [x] Lighthouse CLI installed
- [x] Meta tags added to all pages
- [x] Deprecated event handlers fixed
- [x] All pages score >80 on Lighthouse
- [x] Scores documented

**Lighthouse Scores (2026-03-11):**
- Workspace Dashboard: Performance XX%, Accessibility XX%, Best Practices XX%, SEO XX%
- Campaigns: Performance XX%, Accessibility XX%, Best Practices XX%, SEO XX%
- Getting Started: Performance XX%, Accessibility XX%, Best Practices XX%, SEO XX%

### Part D: Documentation ✅ **COMPLETE**
- [x] API docs auto-generated with @redocly/cli
- [x] User guide directory created
- [x] Getting started guide
- [x] Uploading data guide
- [x] Running jobs guide
- [x] Viewing results guide
- [x] Sessions guide
- [x] Demo mode guide
- [x] README updated with links
```

**Step 2: Commit progress**

```bash
git add openspec/PROGRESS.md
git commit -m "docs: record Phase 5 Parts B, C, D completion in PROGRESS.md"
```

---

## Summary

**Tasks Completed:** 15

**Estimated Time:** 9-12 hours

**Files Created:**
- 7 test files (error handling)
- 6 user guide documents
- 1 API docs (auto-generated)

**Files Modified:**
- 7 pages (meta tags)
- 1 error page (enhanced)
- 3 stores (error handling)
- 1 README (links)

**Success Criteria:**
- [ ] All Lighthouse scores >80
- [ ] All error scenarios tested
- [ ] API docs accessible at docs/api/index.html
- [ ] User guide covers all workflows
- [ ] PROGRESS.md updated
