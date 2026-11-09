import { describe, it, expect, vi, beforeEach } from "vitest";
import { request } from "#lib/api/client.ts";

/**
 * Error-status fidelity through `ApiResult`: the error
 * variant carries the upstream HTTP status, `0` when the request never got a
 * response, and `fetchWithRetry` never retries an abort/deadline.
 */
const fetchMock = vi.fn();
global.fetch = fetchMock;

function jsonResponse(status: number, body: unknown, statusText = "") {
	return {
		ok: status >= 200 && status < 300,
		status,
		statusText,
		headers: new Headers({ "content-type": "application/json" }),
		json: () => Promise.resolve(body),
	};
}

describe("api client request() — error status fidelity", () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it("reports the upstream HTTP status on error responses", async () => {
		fetchMock.mockResolvedValueOnce(jsonResponse(404, { error: "Job not found" }, "Not Found"));

		await expect(request("/jobs/1")).resolves.toEqual({
			ok: false,
			error: "Job not found",
			status: 404,
		});
	});

	it("reports status 0 when the request never got a response", async () => {
		fetchMock.mockImplementation(async () => {
			throw new TypeError("fetch failed");
		});

		await expect(request("/jobs/1")).resolves.toEqual({
			ok: false,
			error: "fetch failed",
			status: 0,
		});
		// Plain network failures are still retried once (unchanged behavior).
		expect(fetchMock).toHaveBeenCalledTimes(2);
	});

	it("does not retry an aborted request (AbortError is a deadline, not transient)", async () => {
		fetchMock.mockImplementation(async () => {
			throw new DOMException("This operation was aborted", "AbortError");
		});

		const res = await request("/jobs/1");
		expect(res.ok).toBe(false);
		expect(fetchMock).toHaveBeenCalledTimes(1);
	});

	it("does not retry a timed-out request (TimeoutError)", async () => {
		fetchMock.mockImplementation(async () => {
			throw new DOMException("The operation was aborted due to timeout", "TimeoutError");
		});

		const res = await request("/jobs/1");
		expect(res.ok).toBe(false);
		expect(fetchMock).toHaveBeenCalledTimes(1);
	});

	it("still retries a 5xx response once", async () => {
		fetchMock
			.mockResolvedValueOnce(jsonResponse(500, { error: "boom" }, "Internal Server Error"))
			.mockResolvedValueOnce(jsonResponse(200, { fine: true }));

		await expect(request("/jobs/1")).resolves.toEqual({ ok: true, data: { fine: true } });
		expect(fetchMock).toHaveBeenCalledTimes(2);
	});
});
