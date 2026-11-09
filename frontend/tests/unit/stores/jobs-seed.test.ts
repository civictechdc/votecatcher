import { describe, it, expect, vi, beforeEach } from "vitest";
import { get } from "svelte/store";
import { jobs, resetJobsStore } from "#lib/stores/jobs.ts";
import type { JobResponse } from "#lib/api/generated/index.ts";

/**
 * Server-data seeding on the jobs store: the job page
 * load returns `{ job }` and the page seeds the store with it, skipping the
 * initial client-side GET.
 */
const makeJob = (over: Partial<JobResponse> = {}): JobResponse => ({
	jobId: 42,
	status: "OCR_PENDING",
	campaignId: "11111111-1111-4111-8111-111111111111",
	...over,
});

describe("jobs store — server-data seeding", () => {
	beforeEach(() => {
		resetJobsStore();
	});

	it("seeds currentJob from server data without any client-side fetch", () => {
		const fetchSpy = vi
			.spyOn(jobs, "fetch")
			.mockRejectedValue(new Error("client fetch must not run"));

		jobs.seed(makeJob({ jobId: 7, status: "MATCHING" }));

		const state = get(jobs);
		expect(state.currentJob).toEqual(makeJob({ jobId: 7, status: "MATCHING" }));
		expect(state.loading).toBe(false);
		expect(state.error).toBeNull();
		expect(fetchSpy).not.toHaveBeenCalled();
		fetchSpy.mockRestore();
	});

	it("replaces a previously seeded job (navigating between job pages)", () => {
		jobs.seed(makeJob({ jobId: 1 }));
		jobs.seed(makeJob({ jobId: 2, status: "OCR_STARTED" }));

		expect(get(jobs).currentJob?.jobId).toBe(2);
		expect(get(jobs).currentJob?.status).toBe("OCR_STARTED");
	});
});
