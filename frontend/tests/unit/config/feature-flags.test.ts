import { describe, it, expect, vi } from "vitest";

// Guards for retained helper behavior. featureFlags reads VITE_FEATURES at module load,
// so each scenario stubs the env and re-imports the module (resetModules).

async function freshFeatureFlags(viteFeatures: string) {
	vi.stubEnv("VITE_FEATURES", viteFeatures);
	vi.resetModules();
	const mod = await import("../../../src/lib/config/featureFlags");
	return mod.featureFlags;
}

describe("featureFlags helper (retained behavior)", () => {
	it("isEnabled honors VITE_FEATURES", async () => {
		const ff = await freshFeatureFlags("mockApi,2fa");

		expect(ff.isEnabled("mockApi")).toBe(true);
		expect(ff.isEnabled("2fa")).toBe(true);
		expect(ff.isEnabled("mockAuth")).toBe(false);
	});

	it("list() returns the union of env flags and persisted vc:flags", async () => {
		localStorage.setItem("vc:flags", "mock:session:loggedIn");
		const ff = await freshFeatureFlags("mockApi");

		const flags = ff.list();
		expect(flags).toContain("mockApi");
		expect(flags).toContain("mock:session:loggedIn");
		expect(ff.isEnabled("mock:session:loggedIn")).toBe(true);
	});

	it("a seeded vc:flags keeps mockApi gating wired (helper only)", async () => {
		localStorage.setItem("vc:flags", "mockApi");
		const ff = await freshFeatureFlags("");

		// The mock worker engages off the same helper read (see mocks/init.ts).
		expect(ff.isEnabled("mockApi")).toBe(true);
		expect(ff.list()).toEqual(["mockApi"]);
	});
});
