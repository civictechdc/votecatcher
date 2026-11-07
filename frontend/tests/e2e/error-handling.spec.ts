import { expect, test } from "@playwright/test";

test.describe("Error Handling", () => {
	test("error page displays on 404", async ({ page }) => {
		await page.goto("/workspace/nonexistent-page-12345");

		await expect(page.locator("h1").first()).toBeVisible({ timeout: 5000 });
	});

	test("error page has navigation options", async ({ page }) => {
		await page.goto("/workspace/nonexistent-page-12345");
		await page.waitForLoadState("domcontentloaded");

		const hasButton = (await page.locator("button").count()) > 0;
		const hasLink = (await page.locator("a").count()) > 0;

		expect(hasButton || hasLink).toBeTruthy();
	});

	test("campaigns page handles loading state", async ({ page }) => {
		await page.goto("/workspace/campaigns");

		await expect(page.locator("h1")).toContainText("Campaigns");
	});

	test("workspace redirects to campaigns", async ({ page }) => {
		await page.goto("/workspace");

		await page.waitForURL(/.*campaigns/, { timeout: 5000 }).catch(() => {});

		await expect(page).toHaveURL(/.*campaigns/);
	});

	test("demo page shows heading", async ({ page }) => {
		await page.goto("/workspace/demo");

		await expect(page.locator("h1")).toContainText("Demo Mode");
	});

	test("settings page loads", async ({ page }) => {
		await page.goto("/workspace/settings");

		await expect(page.locator("h1").first()).toBeVisible();
	});

	test("unmatched route answers HTTP 404 with the workspace error boundary", async ({ page }) => {
		// CHARACTERIZATION: no route in the app throws error(404), so the root
		// +error.svelte "404 — Page Not Found" mapping is unreachable. For an
		// unrouted URL SvelteKit renders the ROOT +error.svelte (the root error
		// node) with an undefined status prop: EMPTY h1, title
		// "— Error — Votecatcher". The HTTP response status is the only place
		// "404" appears. Pin as-is; Kit 3 may change error-boundary resolution.
		const response = await page.goto("/no-such-route-characterization");
		expect(response?.status()).toBe(404);

		await page.waitForLoadState("domcontentloaded");
		await expect(page.locator("h1").first()).toHaveText("", { timeout: 5000 });
		// The static SSR <title>Votecatcher</title> from app.html comes first
		// in <head>; Svelte appends the error page's svelte:head title after
		// it. This pin still passes because client hydration writes
		// document.title directly (Svelte 5 title effect mutates the first
		// title element), and toHaveTitle auto-retries through that hydration
		// step — so what is asserted is the post-hydration title.
		await expect(page).toHaveTitle("— Error — Votecatcher");
		await expect(page.getByRole("button", { name: "Try Again" })).toBeVisible();
	});

	test("unknown campaign id renders the dashboard skeleton, not an error page", async ({
		page,
	}) => {
		// CHARACTERIZATION: /workspace/<id> matches the [id] route for ANY id,
		// so unknown campaign ids do NOT produce an error page — the dashboard
		// renders with the fallback "Campaign" heading. The pre-existing
		// "error page displays on 404" tests above pass vacuously for this
		// reason (they only assert an h1 is visible).
		const response = await page.goto("/workspace/nonexistent-page-12345");
		await page.waitForLoadState("domcontentloaded");

		// the dashboard skeleton answers HTTP 200 (a matched, non-error route)
		expect(response?.status()).toBe(200);

		await expect(page.locator("h1").first()).toHaveText("Campaign", { timeout: 5000 });
	});

	test("campaign API failure surfaces an error alert on the campaigns page", async ({ page }) => {
		// force a deterministic client-side fetch failure: abort every call to
		// the API origin (the generated client calls /campaigns, not
		// /api/campaigns, so origin-scoping also avoids hitting the page URL)
		const apiUrl = process.env["PUBLIC_API_URL"] || "http://localhost:8080";
		const apiOrigin = new URL(apiUrl).origin;
		await page.route(
			(url) => url.origin === apiOrigin,
			(route) => route.abort(),
		);

		await page.goto("/workspace/campaigns");
		await page.waitForLoadState("domcontentloaded");

		// the page renders ErrorDisplay (role="alert", red panel) when the
		// campaigns store fetch throws — pinned as-is; Kit 3 must keep this
		// surface. "Failed to fetch" is Chromium's engine string for an
		// aborted fetch — an engine-coupled pin, safe only because the suite
		// is chromium-only.
		const alert = page.locator('[role="alert"]');
		await expect(alert).toBeVisible({ timeout: 10_000 });
		await expect(alert).toContainText("Failed to fetch");
	});
});
