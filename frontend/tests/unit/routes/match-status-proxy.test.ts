import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { MATCH_STATUS_CONNECT_TIMEOUT_MS } from "#lib/api/fetch-deadline.ts";

/**
 * match-status SSE proxy (`/workspace/api/match-status/[job_id]`): upstream
 * statuses are forwarded (bodyless ones normalized to 502), the initial fetch
 * is bounded by a
 * deadline that is cleared before the streamed response is returned (so the
 * SSE body is never aborted mid-flight), a deadline timeout answers 504, and
 * a client disconnect during the connect phase aborts the upstream request.
 */
const fetchMock = vi.fn();
global.fetch = fetchMock;

async function freshGet() {
	vi.resetModules();
	const mod = await import("../../../src/routes/(app)/workspace/api/match-status/[job_id]/+server");
	return mod.GET;
}

type GetEvent = Parameters<Awaited<ReturnType<typeof freshGet>>>[0];

function makeEvent(jobId: string, requestSignal?: AbortSignal): GetEvent {
	return {
		params: { job_id: jobId },
		request: { signal: requestSignal ?? new AbortController().signal },
	} as unknown as GetEvent;
}

function sseResponse(status: number, statusText: string, chunk?: string) {
	const body = new ReadableStream<Uint8Array>({
		start(controller) {
			if (chunk) controller.enqueue(new TextEncoder().encode(chunk));
			controller.close();
		},
	});
	return { ok: status >= 200 && status < 300, status, statusText, body };
}

describe("workspace/api/match-status/[job_id] SSE proxy", () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});
	afterEach(() => {
		vi.useRealTimers();
	});

	it("returns a 200 SSE response streaming the upstream body", async () => {
		const GET = await freshGet();
		fetchMock.mockResolvedValueOnce(sseResponse(200, "OK", "data: hello\n\n"));

		const res = await GET(makeEvent("7"));
		expect(res.status).toBe(200);
		expect(res.headers.get("content-type")).toBe("text/event-stream");
		await expect(res.text()).resolves.toContain("data: hello");
	});

	it("forwards an upstream 404 status", async () => {
		const GET = await freshGet();
		fetchMock.mockResolvedValueOnce({
			ok: false,
			status: 404,
			statusText: "Not Found",
			body: null,
		});

		const res = await GET(makeEvent("7"));
		expect(res.status).toBe(404);
		await expect(res.text()).resolves.toContain("Upstream error");
	});

	it("answers 502 when the upstream 200 has no body to stream", async () => {
		const GET = await freshGet();
		fetchMock.mockResolvedValueOnce({ ok: true, status: 200, statusText: "OK", body: null });

		const res = await GET(makeEvent("7"));
		expect(res.status).toBe(502);
	});

	it("answers 504 when the upstream headers never arrive (deadline)", async () => {
		vi.useFakeTimers();
		const GET = await freshGet();
		// Mimic fetch: stay pending until the deadline signal aborts.
		fetchMock.mockImplementation(
			(_url: unknown, init?: { signal?: AbortSignal }) =>
				new Promise((_resolve, reject) => {
					init?.signal?.addEventListener("abort", () => reject(init.signal?.reason));
				}),
		);

		const pending = GET(makeEvent("7"));
		await vi.advanceTimersByTimeAsync(MATCH_STATUS_CONNECT_TIMEOUT_MS);
		const res = await pending;
		expect(res.status).toBe(504);
		await expect(res.text()).resolves.toContain("timed out");
	});

	it("normalizes bodyless upstream statuses (204/205/304) to 502 instead of crashing", async () => {
		const GET = await freshGet();
		for (const status of [204, 205, 304]) {
			fetchMock.mockResolvedValueOnce({
				ok: status >= 200 && status < 300,
				status,
				statusText: "bodyless",
				body: null,
			});

			const res = await GET(makeEvent("7"));
			expect(res.status).toBe(502);
			await expect(res.text()).resolves.toContain("empty body");
		}
		expect(fetchMock).toHaveBeenCalledTimes(3);
	});

	it("aborts the upstream request and answers 500 when the client disconnects while connecting", async () => {
		const GET = await freshGet();
		const client = new AbortController();
		let upstreamSignal: AbortSignal | undefined;
		// Mimic fetch: stay pending until its own signal aborts.
		fetchMock.mockImplementation(
			(_url: unknown, init?: { signal?: AbortSignal }) =>
				new Promise((_resolve, reject) => {
					upstreamSignal = init?.signal;
					init?.signal?.addEventListener("abort", () => reject(init.signal?.reason));
				}),
		);

		const pending = GET(makeEvent("7", client.signal));
		client.abort(new DOMException("client went away", "AbortError"));
		const res = await pending;
		expect(res.status).toBe(500);
		await expect(res.text()).resolves.toContain("Cannot connect");
		expect(upstreamSignal?.aborted).toBe(true);
	});

	it("does not treat a client disconnect as a deadline timeout (listener removed after connect)", async () => {
		const GET = await freshGet();
		const client = new AbortController();
		fetchMock.mockResolvedValueOnce(sseResponse(200, "OK", "data: hello\n\n"));

		// Disconnect while the handler is awaiting the (already resolved) fetch.
		const pending = GET(makeEvent("7", client.signal));
		client.abort(new DOMException("client went away", "AbortError"));
		const res = await pending;
		expect(res.status).toBe(200);
		await expect(res.text()).resolves.toContain("data: hello");
	});

	it("clears the deadline once headers arrive so the stream is never aborted mid-flight", async () => {
		// Only fake setTimeout: clearTimeout stays real so the proxy's cleanup
		// call is observable.
		vi.useFakeTimers({ toFake: ["setTimeout"] });
		const clearTimeoutSpy = vi.spyOn(global, "clearTimeout");
		const GET = await freshGet();
		fetchMock.mockResolvedValueOnce(sseResponse(200, "OK"));

		const res = await GET(makeEvent("7"));
		expect(res.status).toBe(200);
		expect(clearTimeoutSpy).toHaveBeenCalled();
	});
});
