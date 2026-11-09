import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { existsSync } from "node:fs";
import path from "node:path";

/**
 * Campaign-existence guard on `workspace/[id]/+layout.server.ts`
 * (spec: error-pages).
 *
 * The backend (`GET {PUBLIC_API_URL}/campaigns/{id}`) answers 404 for an
 * unknown uuid id and 422 for a non-uuid id; the layout load maps both to
 * `error(404)` before any page data is produced, sends exactly one request
 * while doing so, and falls through with empty data on deadline/outage
 * failures so the page's client-side handling takes over.
 */
async function freshLayoutLoad() {
	vi.resetModules();
	const mod = await import("../../../src/routes/(app)/workspace/[id]/+layout.server");
	return mod.load;
}

function makeEvent(id: string, fetchSpy: ReturnType<typeof vi.fn>) {
	return {
		fetch: fetchSpy,
		params: { id },
		url: new URL(`http://localhost:5173/workspace/${id}`),
	} as unknown as Parameters<Awaited<ReturnType<typeof freshLayoutLoad>>>[0];
}

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

describe("workspace/[id] layout server load — unknown-campaign 404 guard", () => {
	it("throws 404 for an unknown uuid id and sends no further requests", async () => {
		const load = await freshLayoutLoad();
		const fetchSpy = vi.fn(async () => ({ ok: false, status: 404 }));
		const id = "00000000-0000-4000-8000-000000000000";

		await expect(load(makeEvent(id, fetchSpy))).rejects.toMatchObject({
			status: 404,
			body: { message: expect.stringContaining("not found") },
		});
		expect(fetchSpy).toHaveBeenCalledTimes(1);
		expect((fetchSpy.mock.calls[0] as unknown[])[0]).toBe(`http://localhost:8080/campaigns/${id}`);
	});

	it("maps a backend 422 (non-uuid id) to 404 as well", async () => {
		const load = await freshLayoutLoad();
		const fetchSpy = vi.fn(async () => ({ ok: false, status: 422 }));

		await expect(load(makeEvent("not-a-uuid", fetchSpy))).rejects.toMatchObject({
			status: 404,
		});
		expect(fetchSpy).toHaveBeenCalledTimes(1);
	});

	it("resolves with empty data for a known campaign id", async () => {
		const load = await freshLayoutLoad();
		const fetchSpy = vi.fn(async () => ({ ok: true, status: 200 }));

		await expect(
			load(makeEvent("11111111-1111-4111-8111-111111111111", fetchSpy)),
		).resolves.toEqual({});
		expect(fetchSpy).toHaveBeenCalledTimes(1);
	});

	it("bounds the guard fetch with a deadline signal", async () => {
		const load = await freshLayoutLoad();
		const fetchSpy = vi.fn(async () => ({ ok: true, status: 200 }));

		await load(makeEvent("11111111-1111-4111-8111-111111111111", fetchSpy));
		const init = (fetchSpy.mock.calls[0] as unknown[])[1] as RequestInit;
		expect(init?.signal).toBeInstanceOf(AbortSignal);
	});

	it("falls through with empty data on a fetch timeout (TimeoutError)", async () => {
		const load = await freshLayoutLoad();
		const fetchSpy = vi.fn(async () => {
			throw new DOMException("The operation timed out.", "TimeoutError");
		});

		await expect(
			load(makeEvent("11111111-1111-4111-8111-111111111111", fetchSpy)),
		).resolves.toEqual({});
	});

	it("falls through with empty data on an abort (AbortError)", async () => {
		const load = await freshLayoutLoad();
		const fetchSpy = vi.fn(async () => {
			throw new DOMException("This operation was aborted", "AbortError");
		});

		await expect(
			load(makeEvent("11111111-1111-4111-8111-111111111111", fetchSpy)),
		).resolves.toEqual({});
	});

	it("falls through with empty data on a plain network failure (TypeError)", async () => {
		const load = await freshLayoutLoad();
		const fetchSpy = vi.fn(async () => {
			throw new TypeError("fetch failed");
		});

		await expect(
			load(makeEvent("11111111-1111-4111-8111-111111111111", fetchSpy)),
		).resolves.toEqual({});
	});

	it("still surfaces unexpected rejection types instead of swallowing them", async () => {
		const load = await freshLayoutLoad();
		const fetchSpy = vi.fn(async () => {
			throw new SyntaxError("unexpected");
		});

		await expect(load(makeEvent("11111111-1111-4111-8111-111111111111", fetchSpy))).rejects.toThrow(
			SyntaxError,
		);
	});

	it("leaves /workspace/demo to its static route (never matched by [id])", async () => {
		// SvelteKit prefers static segments over dynamic ones, so
		// /workspace/demo resolves to workspace/demo/+page.svelte and the
		// [id] layout guard never runs for it. Pin the static route's
		// existence so this stays true.
		const demoPage = path.resolve(process.cwd(), "src/routes/(app)/workspace/demo/+page.svelte");
		expect(existsSync(demoPage)).toBe(true);
	});
});
