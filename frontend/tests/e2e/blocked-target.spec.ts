import { expect, test } from "@playwright/test";

/**
 * Trusted-origin blocked-target behavior (spec: trusted-origins
 * "Untrusted target failure behavior").
 *
 * Runs ONLY under playwright.blocked.config.ts (`bun run test:e2e:blocked`):
 * that config boots the dev server with
 * TRUSTED_ORIGINS=https://canonical.example.com while ORIGIN stays
 * http://localhost:5173 (frontend/.env), so every server-side relative
 * fetch resolves against an untrusted base and must fail fast — never a
 * hang, never a silent fallback.
 *
 * The root +error.svelte now derives status/message from the Kit 3 `error`
 * prop (spec: error-pages), so the 502 page surfaces the real status and
 * the actionable message text ("Rejected untrusted server fetch base …
 * TRUSTED_ORIGINS …") — asserted here at e2e level, not just unit level.
 */
test.describe("Blocked server fetch targets (untrusted TRUSTED_ORIGINS matrix)", () => {
	test("auth load: fails fast with 502 and the root error boundary, not a hang", async ({
		page,
	}) => {
		const response = await page.goto("/auth");

		expect(response?.status()).toBe(502);

		// the load rejected before any fetch was sent; the root error
		// boundary renders the real status + actionable message instead of
		// hanging or silently degrading
		await expect(page.locator("h1").first()).toHaveText("502", { timeout: 10_000 });
		await expect(page.locator("h2").first()).toHaveText("Bad Gateway");
		await expect(page.getByRole("button", { name: "Try Again" })).toBeVisible();
		await expect(page.locator("body")).toContainText("Rejected untrusted server fetch base");
		await expect(page.locator("body")).toContainText("TRUSTED_ORIGINS");
	});

	test("getting-started load: same fail-fast rejection with surfaced status", async ({ page }) => {
		const response = await page.goto("/getting-started");

		expect(response?.status()).toBe(502);
		await expect(page.locator("h1").first()).toHaveText("502", { timeout: 10_000 });
		await expect(page.getByRole("button", { name: "Try Again" })).toBeVisible();
	});
});
