import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

/**
 * Job-existence guard on `workspace/[id]/jobs/[job_id]/+page.server.ts`
 * (spec: error-pages).
 *
 * The guard hits the campaign-scoped endpoint
 * (`GET {PUBLIC_API_URL}/campaigns/{campaign_id}/jobs/{job_id}`), which
 * answers 404 for an unknown job, unknown campaign, or campaign/job mismatch
 * and 422 for a non-uuid campaign id / non-numeric job id — both map to
 * `error(404)` before any page data is produced, exactly one request is sent,
 * a 200 body is returned as `{ job }` for store seeding, and deadline/outage
 * failures fall through with `job: null` so the page's client-side handling
 * takes over.
 */
async function freshPageLoad() {
	vi.resetModules();
	const mod = await import("../../../src/routes/(app)/workspace/[id]/jobs/[job_id]/+page.server");
	return mod.load;
}

function makeEvent(campaignId: string, jobId: string, fetchSpy: ReturnType<typeof vi.fn>) {
	return {
		fetch: fetchSpy,
		params: { id: campaignId, job_id: jobId },
		url: new URL(`http://localhost:5173/workspace/${campaignId}/jobs/${jobId}`),
	} as unknown as Parameters<Awaited<ReturnType<typeof freshPageLoad>>>[0];
}

const campaignId = "11111111-1111-4111-8111-111111111111";
const jobId = "42";

// jsdom's AbortSignal.timeout schedules real timers that would keep the test
// worker alive past teardown; stub it with unref'd timers instead.
const realAbortSignalTimeout = AbortSignal.timeout;
beforeEach(() => {
	AbortSignal.timeout = ((ms: number) => {
		const controller = new AbortController();
		const t = setTimeout(
			() => controller.abort(new DOMException("The operation timed out.", "TimeoutError")),
			ms,
		) as ReturnType<typeof setTimeout> & { unref?: () => void };
		t.unref?.();
		return controller.signal;
	}) as typeof AbortSignal.timeout;
});
afterEach(() => {
	AbortSignal.timeout = realAbortSignalTimeout;
});

describe("workspace/[id]/jobs/[job_id] page server load — campaign-scoped job guard", () => {
	it("fetches the campaign-scoped endpoint with a deadline signal", async () => {
		const load = await freshPageLoad();
		const fetchSpy = vi.fn(async () => ({
			ok: true,
			status: 200,
			json: async () => ({ jobId: 42, status: "OCR_PENDING", campaignId }),
		}));

		await load(makeEvent(campaignId, jobId, fetchSpy));
		expect(fetchSpy).toHaveBeenCalledTimes(1);
		expect((fetchSpy.mock.calls[0] as unknown[])[0]).toBe(
			`http://localhost:8080/campaigns/${campaignId}/jobs/${jobId}`,
		);
		const init = (fetchSpy.mock.calls[0] as unknown[])[1] as RequestInit;
		expect(init?.signal).toBeInstanceOf(AbortSignal);
	});

	it("throws 404 for an unknown job id (backend 404 also covers unknown campaign and mismatch)", async () => {
		const load = await freshPageLoad();
		const fetchSpy = vi.fn(async () => ({ ok: false, status: 404 }));

		await expect(load(makeEvent(campaignId, jobId, fetchSpy))).rejects.toMatchObject({
			status: 404,
			body: { message: expect.stringContaining("not found") },
		});
		expect(fetchSpy).toHaveBeenCalledTimes(1);
	});

	it("maps a backend 422 (non-numeric job id) to 404 as well", async () => {
		const load = await freshPageLoad();
		const fetchSpy = vi.fn(async () => ({ ok: false, status: 422 }));

		await expect(load(makeEvent(campaignId, "not-a-job", fetchSpy))).rejects.toMatchObject({
			status: 404,
		});
		expect(fetchSpy).toHaveBeenCalledTimes(1);
	});

	it("returns the parsed job body as { job } for a known job", async () => {
		const load = await freshPageLoad();
		const job = { jobId: 42, status: "OCR_PENDING", campaignId };
		const fetchSpy = vi.fn(async () => ({ ok: true, status: 200, json: async () => job }));

		await expect(load(makeEvent(campaignId, jobId, fetchSpy))).resolves.toEqual({ job });
		expect(fetchSpy).toHaveBeenCalledTimes(1);
	});

	it("falls through with job: null when a 200 body stalls past the deadline", async () => {
		const load = await freshPageLoad();
		const fetchSpy = vi.fn(async () => ({
			ok: true,
			status: 200,
			json: async () => {
				throw new DOMException("The operation timed out.", "TimeoutError");
			},
		}));

		await expect(load(makeEvent(campaignId, jobId, fetchSpy))).resolves.toEqual({ job: null });
	});

	it("falls through with job: null when the 200 body is not parseable JSON", async () => {
		const load = await freshPageLoad();
		const fetchSpy = vi.fn(async () => ({
			ok: true,
			status: 200,
			json: async () => {
				throw new SyntaxError("Unexpected token in JSON");
			},
		}));

		await expect(load(makeEvent(campaignId, jobId, fetchSpy))).resolves.toEqual({ job: null });
	});

	it("still surfaces unexpected fetch rejection types instead of swallowing them", async () => {
		const load = await freshPageLoad();
		const fetchSpy = vi.fn(async () => {
			throw new SyntaxError("unexpected");
		});

		await expect(load(makeEvent(campaignId, jobId, fetchSpy))).rejects.toThrow(SyntaxError);
	});

	it("falls through with job: null on a fetch timeout (TimeoutError)", async () => {
		const load = await freshPageLoad();
		const fetchSpy = vi.fn(async () => {
			throw new DOMException("The operation timed out.", "TimeoutError");
		});

		await expect(load(makeEvent(campaignId, jobId, fetchSpy))).resolves.toEqual({ job: null });
	});

	it("falls through with job: null on an abort (AbortError)", async () => {
		const load = await freshPageLoad();
		const fetchSpy = vi.fn(async () => {
			throw new DOMException("This operation was aborted", "AbortError");
		});

		await expect(load(makeEvent(campaignId, jobId, fetchSpy))).resolves.toEqual({ job: null });
	});

	it("leaves other backend failures untouched (job: null, not 404)", async () => {
		const load = await freshPageLoad();
		const fetchSpy = vi.fn(async () => ({ ok: false, status: 500 }));

		await expect(load(makeEvent(campaignId, jobId, fetchSpy))).resolves.toEqual({ job: null });
		expect(fetchSpy).toHaveBeenCalledTimes(1);
	});
});
