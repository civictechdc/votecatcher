import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { MATCH_RESULT_TIMEOUT_MS } from "#lib/api/fetch-deadline.ts";

/**
 * match-result proxy (`/workspace/api/match-result/[job_id]`): upstream
 * error statuses are forwarded (clamped to 4xx–5xx, 5xx with a generic
 * message), a
 * deadline timeout surfaces as 504, and the upstream call is bounded by a
 * deadline signal. The `#lib/api/client.ts` module is mocked.
 */
const { demoGetMatchingResults } = vi.hoisted(() => ({ demoGetMatchingResults: vi.fn() }));

vi.mock("#lib/api/client.ts", () => ({
	api: { demoGetMatchingResults },
}));

async function freshGet() {
	vi.resetModules();
	const mod = await import("../../../src/routes/(app)/workspace/api/match-result/[job_id]/+server");
	return mod.GET;
}

type GetEvent = Parameters<Awaited<ReturnType<typeof freshGet>>>[0];

function makeEvent(jobId: string): GetEvent {
	return { params: { job_id: jobId } } as unknown as GetEvent;
}

describe("workspace/api/match-result/[job_id] proxy", () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});
	afterEach(() => {
		vi.useRealTimers();
	});

	it("forwards an upstream 404 as error(404)", async () => {
		const GET = await freshGet();
		demoGetMatchingResults.mockResolvedValueOnce({
			ok: false,
			error: "Job not found",
			status: 404,
		});

		await expect(GET(makeEvent("7"))).rejects.toMatchObject({
			status: 404,
			body: { message: expect.stringContaining("Job not found") },
		});
	});

	it("forwards an upstream 500 as error(500) with a generic message, logging upstream details", async () => {
		const GET = await freshGet();
		const consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
		try {
			demoGetMatchingResults.mockResolvedValueOnce({
				ok: false,
				error: "boom: internal stack details",
				status: 500,
			});

			await expect(GET(makeEvent("7"))).rejects.toMatchObject({
				status: 500,
				body: { message: "Upstream match results unavailable." },
			});
			expect(consoleErrorSpy).toHaveBeenCalledWith(
				expect.stringContaining("boom: internal stack details"),
			);
		} finally {
			consoleErrorSpy.mockRestore();
		}
	});

	it("clamps a non-HTTP failure (status 0 without timeout) to 500", async () => {
		const GET = await freshGet();
		demoGetMatchingResults.mockResolvedValueOnce({
			ok: false,
			error: "fetch failed",
			status: 0,
		});

		await expect(GET(makeEvent("7"))).rejects.toMatchObject({ status: 500 });
	});

	it("passes a deadline signal to the upstream client call", async () => {
		const GET = await freshGet();
		demoGetMatchingResults.mockResolvedValueOnce({
			ok: true,
			data: { results: { column_data: [], result_data: [] } },
		});

		await GET(makeEvent("7"));
		const init = (demoGetMatchingResults.mock.calls[0] as unknown[])[1] as {
			signal?: AbortSignal;
		};
		expect(init?.signal).toBeInstanceOf(AbortSignal);
	});

	it("maps a deadline timeout to 504", async () => {
		vi.useFakeTimers();
		const GET = await freshGet();
		// Mimic fetch: stay pending until the deadline signal aborts, then
		// resolve with the abort surfaced as a no-response ApiResult.
		demoGetMatchingResults.mockImplementation(
			(_jobId: string, opts?: { signal?: AbortSignal }) =>
				new Promise((resolve) => {
					opts?.signal?.addEventListener("abort", () =>
						resolve({ ok: false, error: "The operation was aborted.", status: 0 }),
					);
				}),
		);

		const pending = GET(makeEvent("7"));
		// Attach the rejection expectation before advancing timers: the proxy
		// rejects during advanceTimersByTimeAsync and an unhandled rejection
		// would otherwise be recorded one tick earlier.
		const expectation = expect(pending).rejects.toMatchObject({ status: 504 });
		await vi.advanceTimersByTimeAsync(MATCH_RESULT_TIMEOUT_MS);
		await expectation;
	});

	it("returns transformed results with 200 on success", async () => {
		const GET = await freshGet();
		demoGetMatchingResults.mockResolvedValueOnce({
			ok: true,
			data: {
				results: {
					column_data: [{ name: "Match Score", data_type: "float", position_idx: 0 }],
					result_data: [{ row_idx: 0, values: [{ value: "0.97" }] }],
				},
			},
		});

		const res = await GET(makeEvent("7"));
		expect(res.status).toBe(200);
		const payload = (await res.json()) as {
			matchResults: { matchColumns: { name: string }[]; matchRecords: Record<string, unknown>[] };
		};
		expect(payload.matchResults.matchColumns).toEqual([{ name: "Match Score", isSortable: false }]);
		expect(payload.matchResults.matchRecords).toHaveLength(1);
	});
});
