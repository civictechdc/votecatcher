import { describe, it, expect, vi } from "vitest";

/**
 * Job-existence guard on `workspace/[id]/jobs/[job_id]/+page.server.ts`
 * (spec: error-pages).
 *
 * The backend (`GET {PUBLIC_API_URL}/jobs/{id}`) answers 404 for an unknown
 * id and 422 for a non-numeric id; the page load maps both to `error(404)`
 * before any page data is produced, and sends exactly one request while
 * doing so.
 */
async function freshPageLoad() {
	vi.resetModules();
	const mod = await import("../../../src/routes/(app)/workspace/[id]/jobs/[job_id]/+page.server");
	return mod.load;
}

function makeEvent(jobId: string, fetchSpy: ReturnType<typeof vi.fn>) {
	return {
		fetch: fetchSpy,
		params: { job_id: jobId },
		url: new URL(`http://localhost:5173/workspace/x/jobs/${jobId}`),
	} as unknown as Parameters<Awaited<ReturnType<typeof freshPageLoad>>>[0];
}

describe("workspace/[id]/jobs/[job_id] page server load — unknown-job 404 guard", () => {
	it("throws 404 for an unknown job id and sends no further requests", async () => {
		const load = await freshPageLoad();
		const fetchSpy = vi.fn(async () => ({ ok: false, status: 404 }));
		const jobId = "999999";

		await expect(load(makeEvent(jobId, fetchSpy))).rejects.toMatchObject({
			status: 404,
			body: { message: expect.stringContaining("not found") },
		});
		expect(fetchSpy).toHaveBeenCalledTimes(1);
		expect((fetchSpy.mock.calls[0] as unknown[])[0]).toBe(`http://localhost:8080/jobs/${jobId}`);
	});

	it("maps a backend 422 (non-numeric id) to 404 as well", async () => {
		const load = await freshPageLoad();
		const fetchSpy = vi.fn(async () => ({ ok: false, status: 422 }));

		await expect(load(makeEvent("not-a-job", fetchSpy))).rejects.toMatchObject({
			status: 404,
		});
		expect(fetchSpy).toHaveBeenCalledTimes(1);
	});

	it("resolves with empty data for a known job id", async () => {
		const load = await freshPageLoad();
		const fetchSpy = vi.fn(async () => ({ ok: true, status: 200 }));

		await expect(load(makeEvent("42", fetchSpy))).resolves.toEqual({});
		expect(fetchSpy).toHaveBeenCalledTimes(1);
	});

	it("leaves other failures untouched instead of mapping them to 404", async () => {
		const load = await freshPageLoad();
		const fetchSpy = vi.fn(async () => ({ ok: false, status: 500 }));

		await expect(load(makeEvent("42", fetchSpy))).resolves.toEqual({});
		expect(fetchSpy).toHaveBeenCalledTimes(1);
	});
});
