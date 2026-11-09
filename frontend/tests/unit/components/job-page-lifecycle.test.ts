import { describe, it, expect, vi, beforeEach } from "vitest";
import { render } from "@testing-library/svelte";
import { tick } from "svelte";
import { get } from "svelte/store";
import type { JobResponse } from "#lib/api/generated/index.ts";
import { jobs } from "#lib/stores/jobs.ts";

/**
 * Job-page lifecycle behavior: the job binding (server-data seed, client
 * fetch fallback, SSE stream) is keyed on the route's job id and server
 * data — not on mount — so client-side navigation between job pages re-binds
 * everything and closes the previous job's stream, with no duplicate work on
 * the initial mount. Also covers the client-fallback campaign match: a job
 * returned for a different campaign is treated as not found.
 */

// Call recorder shared with the store mocks (plain arrays, no vitest
// handles inside vi.hoisted).
const calls = vi.hoisted(() => ({
	fetchAll: [] as unknown[][],
	seed: [] as unknown[][],
	fetch: [] as unknown[][],
	connectToJob: [] as unknown[][],
	disconnect: [] as unknown[][],
	reset: [] as unknown[][],
	// Resolved value of the client-side fetch (null mimics a failed fetch).
	fetchResult: null as unknown,
	// When set, the fetch's resolution is deferred to this factory — used to
	// hold a fetch in flight across navigation.
	fetchDeferred: null as null | (() => Promise<unknown>),
}));

vi.mock("#lib/stores/jobs.ts", async () => {
	const { writable } = await import("svelte/store");
	const store = writable<{
		jobs: unknown[];
		currentJob: unknown;
		loading: boolean;
		error: string | null;
		sse: { connected: boolean; reconnectAttempts: number; error: string | null };
	}>({
		jobs: [],
		currentJob: null,
		loading: false,
		error: null,
		sse: { connected: false, reconnectAttempts: 0, error: null },
	});
	return {
		jobs: {
			subscribe: store.subscribe,
			fetchAll: () => {
				calls.fetchAll.push([]);
			},
			fetch: async (...args: unknown[]) => {
				calls.fetch.push(args);
				const job = calls.fetchDeferred ? await calls.fetchDeferred() : calls.fetchResult;
				// Mimic the real store: fetch writes `currentJob`
				// unconditionally when it resolves — guarding against stale
				// resolutions is the component's job.
				if (job != null) {
					store.update((s) => ({ ...s, currentJob: job, loading: false }));
				}
				return job;
			},
			seed: (job: unknown) => {
				calls.seed.push([job]);
				store.update((s) => ({ ...s, currentJob: job, loading: false, error: null }));
			},
			connectToJob: (id: unknown) => {
				calls.connectToJob.push([id]);
			},
			disconnect: () => {
				calls.disconnect.push([]);
			},
			reset: () => {
				calls.reset.push([]);
				store.set({
					jobs: [],
					currentJob: null,
					loading: false,
					error: null,
					sse: { connected: false, reconnectAttempts: 0, error: null },
				});
			},
			cancel: async () => undefined,
			clearError: () => {},
		},
		resetJobsStore: () => {},
	};
});

vi.mock("#lib/stores/campaigns.ts", async () => {
	const { writable } = await import("svelte/store");
	const store = writable({ campaigns: [], loading: false, error: null });
	return {
		campaigns: {
			subscribe: store.subscribe,
			fetchAll: () => {
				calls.fetchAll.push([]);
			},
		},
	};
});

// Per-file $app/state override: the shared mock exposes a reactive page
// object that tests mutate to drive param changes.
vi.mock("$app/state", async () => {
	return await import("../../../tests/__mocks__/$app/state.svelte.ts");
});
const { page: pageState } = await import("../../../tests/__mocks__/$app/state.svelte.ts");

import Page from "../../../src/routes/(app)/workspace/[id]/jobs/[job_id]/+page.svelte";

const campaignId = "11111111-1111-4111-8111-111111111111";
const otherCampaignId = "22222222-2222-4222-8222-222222222222";

function makeJob(jobId: number, campaign = campaignId): JobResponse {
	return { jobId, status: "OCR_PENDING", campaignId: campaign };
}

async function flush() {
	await tick();
	await new Promise((resolve) => setTimeout(resolve, 0));
}

beforeEach(() => {
	for (const list of [
		calls.fetchAll,
		calls.seed,
		calls.fetch,
		calls.connectToJob,
		calls.disconnect,
		calls.reset,
	]) {
		list.splice(0);
	}
	calls.fetchResult = null;
	calls.fetchDeferred = null;
	Object.assign(pageState, {
		params: { id: campaignId, job_id: "42" },
		url: new URL(`http://localhost:5173/workspace/${campaignId}/jobs/42`),
	});
});

// PageProps requires params/form even though the page reads params from
// $app/state; pass data plus the type-required placeholders.
function renderJobPage(job: JobResponse | null) {
	return render(Page, {
		data: { job },
		params: { id: campaignId, job_id: String(job?.jobId ?? 42) },
		form: null,
	});
}

describe("job page lifecycle", () => {
	it("seeds and connects exactly once on initial mount (no duplicate work)", async () => {
		const job = makeJob(42);
		renderJobPage(job);
		await flush();

		expect(calls.seed).toEqual([[job]]);
		expect(calls.fetch).toEqual([]);
		expect(calls.connectToJob).toEqual([["42"]]);
		expect(calls.disconnect).toEqual([]);
	});

	it("re-seeds and reconnects when navigating to a different job id", async () => {
		const job1 = makeJob(1);
		const job2 = makeJob(2);
		const { rerender } = renderJobPage(job1);
		await flush();

		Object.assign(pageState, {
			params: { id: campaignId, job_id: "2" },
			url: new URL(`http://localhost:5173/workspace/${campaignId}/jobs/2`),
		});
		await rerender({ data: { job: job2 } });
		await flush();

		// The previous job's stream was closed before/at the re-bind, and the
		// final seed + stream both target the new job id.
		expect(calls.disconnect.length).toBeGreaterThanOrEqual(1);
		expect(calls.seed.at(-1)).toEqual([job2]);
		expect(calls.connectToJob.at(-1)).toEqual(["2"]);
	});

	it("falls back to a client fetch when the server load produced no job", async () => {
		const job = makeJob(42);
		calls.fetchResult = job;
		renderJobPage(null);
		await flush();

		expect(calls.fetch).toEqual([[42]]);
		expect(calls.seed).toEqual([]);
		expect(calls.reset).toEqual([]);
		expect(calls.connectToJob).toEqual([["42"]]);
	});

	it("treats a client-fetched job from another campaign as not found", async () => {
		calls.fetchResult = makeJob(42, otherCampaignId);
		renderJobPage(null);
		await flush();

		expect(calls.fetch).toEqual([[42]]);
		expect(calls.reset.length).toBe(1);
		expect(calls.disconnect.length).toBe(1);
		expect(calls.seed).toEqual([]);
	});

	it("disconnects the stream on unmount", async () => {
		const { unmount } = renderJobPage(makeJob(42));
		await flush();
		calls.disconnect.splice(0);

		unmount();
		await flush();

		expect(calls.disconnect.length).toBe(1);
	});

	it("discards a stale fallback fetch that resolves after navigating to another job", async () => {
		const deferred = { resolve: undefined as undefined | ((job: JobResponse | null) => void) };
		calls.fetchDeferred = () =>
			new Promise<JobResponse | null>((resolve) => {
				deferred.resolve = resolve;
			});
		Object.assign(pageState, {
			params: { id: campaignId, job_id: "1" },
			url: new URL(`http://localhost:5173/workspace/${campaignId}/jobs/1`),
		});

		// Job 1's server guard timed out: no server data, the fallback fetch
		// starts and stays pending.
		const { rerender } = renderJobPage(null);
		await flush();
		expect(calls.fetch).toEqual([[1]]);

		// Navigate to job 2, whose server load did produce the job.
		const job2 = makeJob(2);
		Object.assign(pageState, {
			params: { id: campaignId, job_id: "2" },
			url: new URL(`http://localhost:5173/workspace/${campaignId}/jobs/2`),
		});
		await rerender({ data: { job: job2 } });
		await flush();
		expect(calls.seed.at(-1)).toEqual([job2]);

		// Job 1's fetch finally resolves — same campaign, so only the stale
		// guard (not the campaign-mismatch guard) can keep job 1's data from
		// clobbering job 2 (the store itself writes currentJob unconditionally).
		deferred.resolve?.(makeJob(1));
		await flush();

		expect(get(jobs).currentJob?.jobId).toBe(2);
		expect(calls.reset).toEqual([]);
		expect(calls.seed.at(-1)).toEqual([job2]);
	});

	it("does not touch the store when a fallback fetch resolves after unmount", async () => {
		const deferred = { resolve: undefined as undefined | ((job: JobResponse | null) => void) };
		calls.fetchDeferred = () =>
			new Promise<JobResponse | null>((resolve) => {
				deferred.resolve = resolve;
			});
		Object.assign(pageState, {
			params: { id: campaignId, job_id: "1" },
			url: new URL(`http://localhost:5173/workspace/${campaignId}/jobs/1`),
		});

		const { unmount } = renderJobPage(null);
		await flush();
		expect(calls.fetch).toEqual([[1]]);

		unmount();
		await flush();

		// A cross-campaign job resolving after unmount would trip the
		// campaign-mismatch path (reset) if the component still acted on it;
		// after unmount it must not touch the store at all.
		deferred.resolve?.(makeJob(1, otherCampaignId));
		await flush();

		expect(calls.reset).toEqual([]);
		expect(calls.seed).toEqual([]);
		expect(calls.disconnect.length).toBe(1);
	});
});
