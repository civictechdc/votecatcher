import { expect, test } from "@playwright/test";

/**
 * Trusted-origin blocked-target behavior (task 3.6; spec: trusted-origins
 * "Untrusted target failure behavior").
 *
 * Runs ONLY under playwright.blocked.config.ts (`bun run test:e2e:blocked`):
 * that config boots the dev server with
 * TRUSTED_ORIGINS=https://canonical.example.com while ORIGIN stays
 * http://localhost:5173 (frontend/.env), so every server-side relative
 * fetch resolves against an untrusted base and must fail fast — never a
 * hang, never a silent fallback.
 *
 * The actionable message text ("Rejected untrusted server fetch base …
 * TRUSTED_ORIGINS …") is asserted at the unit level
 * (tests/unit/server/trusted-origins.test.ts). It cannot be asserted here:
 * Kit 3 passes `+error.svelte` an `error` object prop, while the app's root
 * +error.svelte still reads Kit 2 flat `status`/`message` props — so error
 * pages render the generic fallback regardless of the thrown message. That
 * degraded error page is pre-existing and pinned as-is (issue #193 tracks
 * the fix; task 3.6 keeps #193/#194 pins unchanged).
 */
test.describe("Blocked server fetch targets (untrusted TRUSTED_ORIGINS matrix)", () => {
	test("auth load: fails fast with 502 and the root error boundary, not a hang", async ({
		page,
	}) => {
		const response = await page.goto("/auth");

		expect(response?.status()).toBe(502);

		// the load rejected before any fetch was sent; the root error
		// boundary renders instead of the page hanging or silently degrading
		await expect(page.getByRole("button", { name: "Try Again" })).toBeVisible({
			timeout: 10_000,
		});
		await expect(page.locator("h2")).toContainText("Error");
	});

	test("getting-started load: same fail-fast rejection", async ({ page }) => {
		const response = await page.goto("/getting-started");

		expect(response?.status()).toBe(502);
		await expect(page.getByRole("button", { name: "Try Again" })).toBeVisible({
			timeout: 10_000,
		});
	});
});
