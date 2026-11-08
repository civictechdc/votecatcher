import { describe, it, expect, vi } from "vitest";
import { setPrivateEnv } from "../../helpers/env-mocks";

/** Structural check for Kit `error()` throws (HttpError is type-only at runtime). */
function expectHttpError(err: unknown, status: number, messagePart: string): void {
	const httpError = err as { status?: number; body?: { message?: string } };
	expect(httpError.status).toBe(status);
	expect(httpError.body?.message).toContain(messagePart);
}

/**
 * Trusted-origin helper unit tests (task 3.5; spec: trusted-origins).
 *
 * The helper snapshots `$app/env/private` at module load, so each scenario
 * seeds the mock env (setPrivateEnv), resets modules, and re-imports. The
 * wired scenarios at the bottom drive the real `auth/+page.server.ts` load
 * to prove the request is actually sent to the trusted origin — and NOT sent
 * for an untrusted one.
 */
async function freshHelper() {
	vi.resetModules();
	return await import("../../../src/lib/server/trusted-origins");
}

async function freshAuthLoad() {
	vi.resetModules();
	const mod = await import("../../../src/routes/(app)/auth/+page.server");
	return mod.load;
}

describe("resolveTrustedBase", () => {
	it("prefers the canonical ORIGIN when it is trusted", async () => {
		setPrivateEnv({
			ORIGIN: "https://app.example.com",
			TRUSTED_ORIGINS: ["https://app.example.com", "https://staging.example.com"],
		});
		const { resolveTrustedBase } = await freshHelper();
		expect(resolveTrustedBase("https://whatever.example.net")).toBe("https://app.example.com");
	});

	it("falls back to the event-derived origin when ORIGIN is unset", async () => {
		setPrivateEnv({
			ORIGIN: undefined,
			TRUSTED_ORIGINS: ["http://localhost:5173"],
		});
		const { resolveTrustedBase } = await freshHelper();
		expect(resolveTrustedBase("http://localhost:5173")).toBe("http://localhost:5173");
	});

	it("rejects an untrusted ORIGIN with an actionable 502 naming the target", async () => {
		setPrivateEnv({
			ORIGIN: "http://localhost:5173",
			TRUSTED_ORIGINS: ["https://canonical.example.com"],
		});
		const { resolveTrustedBase } = await freshHelper();
		try {
			resolveTrustedBase("https://canonical.example.com");
			expect.unreachable("should have thrown");
		} catch (err) {
			expectHttpError(err, 502, "http://localhost:5173");
			expectHttpError(err, 502, "TRUSTED_ORIGINS");
		}
	});

	it("rejects everything when the allowlist is empty (fail closed)", async () => {
		setPrivateEnv({ ORIGIN: undefined, TRUSTED_ORIGINS: undefined });
		const { resolveTrustedBase } = await freshHelper();
		try {
			resolveTrustedBase("http://localhost:5173");
			expect.unreachable("should have thrown");
		} catch (err) {
			expectHttpError(err, 502, "TRUSTED_ORIGINS");
		}
	});
});

describe("trustedFetchUrl", () => {
	it("resolves a relative target against the trusted base (spec: proceeds)", async () => {
		setPrivateEnv({
			ORIGIN: "http://localhost:5173",
			TRUSTED_ORIGINS: ["http://localhost:5173"],
		});
		const { trustedFetchUrl } = await freshHelper();
		expect(trustedFetchUrl("/api/session", "http://localhost:5173")).toBe(
			"http://localhost:5173/api/session",
		);
	});

	it("rejects non-root-relative paths", async () => {
		setPrivateEnv({ ORIGIN: "http://localhost:5173", TRUSTED_ORIGINS: ["http://localhost:5173"] });
		const { trustedFetchUrl } = await freshHelper();
		expect(() => trustedFetchUrl("api/session", "http://localhost:5173")).toThrowError();
	});
});

describe("wired through auth/+page.server.ts load", () => {
	it("sends the request to the resolved trusted origin (spec: proceeds)", async () => {
		setPrivateEnv({
			ORIGIN: "http://localhost:5173",
			TRUSTED_ORIGINS: ["http://localhost:5173"],
		});
		const load = await freshAuthLoad();
		const fetchSpy = vi.fn(async () => ({ ok: false, json: async () => ({}) }));
		const event = {
			fetch: fetchSpy,
			url: new URL("http://localhost:5173/auth"),
		} as unknown as Parameters<typeof load>[0];

		await load(event);

		expect(fetchSpy).toHaveBeenCalledTimes(1);
		expect((fetchSpy.mock.calls[0] as unknown[])[0]).toBe("http://localhost:5173/auth/session");
	});

	it("sends NO request for an untrusted target and fails with the actionable error (spec)", async () => {
		setPrivateEnv({
			ORIGIN: "http://localhost:5173",
			TRUSTED_ORIGINS: ["https://canonical.example.com"],
		});
		const load = await freshAuthLoad();
		const fetchSpy = vi.fn();
		const event = {
			fetch: fetchSpy,
			url: new URL("http://localhost:5173/auth"),
		} as unknown as Parameters<typeof load>[0];

		await expect(load(event)).rejects.toMatchObject({
			status: 502,
			body: { message: expect.stringContaining("TRUSTED_ORIGINS") },
		});
		expect(fetchSpy).not.toHaveBeenCalled();
	});
});
