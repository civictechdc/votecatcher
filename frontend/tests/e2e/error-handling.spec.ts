import { expect, test } from "@playwright/test";

test.describe("Error Handling", () => {
	test("unknown campaign id answers 404 with the error page and retry affordances", async ({
		page,
	}) => {
		// CONTRACT (spec: error-pages): a workspace URL whose campaign id
		// does not exist answers HTTP 404 with the workspace error boundary —
		// not the dashboard skeleton. Non-uuid ids can never name a campaign
		// (the backend rejects them with 422); the layout guard maps both
		// unknown-id shapes to 404.
		const response = await page.goto("/workspace/nonexistent-page-12345");

		expect(response?.status()).toBe(404);

		await expect(page.locator("h1").first()).toHaveText("404", { timeout: 5000 });
		await expect(page.locator("body")).toContainText("not found");
		await expect(page.getByRole("button", { name: "Try Again" })).toBeVisible();
		await expect(page.getByRole("button", { name: "Go Back" })).toBeVisible();
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

	test("unmatched route answers HTTP 404 with the rendered error page", async ({ page }) => {
		// CONTRACT (spec: error-pages): an unrouted URL answers 404 and the
		// root error boundary renders the actual status ("404" h1, "Page Not
		// Found" title map entry). Kit 3 hands the boundary an `error` prop;
		// the component derives the status from it, so the heading is never
		// empty (this replaces the Kit-2-era empty-h1 characterization pin).
		const response = await page.goto("/no-such-route-characterization");
		expect(response?.status()).toBe(404);

		await page.waitForLoadState("domcontentloaded");
		await expect(page.locator("h1").first()).toHaveText("404", { timeout: 5000 });
		await expect(page.locator("h2").first()).toHaveText("Page Not Found");
		// The static SSR <title>Votecatcher</title> from app.html comes first
		// in <head>; Svelte appends the error page's svelte:head title after
		// it. This pin passes because client hydration writes document.title
		// directly (Svelte 5 title effect mutates the first title element),
		// and toHaveTitle auto-retries through that hydration step — so what
		// is asserted is the post-hydration title.
		await expect(page).toHaveTitle("404 — Page Not Found — Votecatcher");
		await expect(page.getByRole("button", { name: "Try Again" })).toBeVisible();
	});

	test("unknown uuid campaign id answers 404 with the error page, not the skeleton", async ({
		page,
	}) => {
		// CONTRACT (spec: error-pages): uuid-shaped unknown ids are validated
		// server-side by workspace/[id]/+layout.server.ts (backend 404 →
		// error(404)) — the former skeleton-with-200 behavior is gone.
		const unknownId = "00000000-0000-4000-8000-000000000000";
		const response = await page.goto(`/workspace/${unknownId}`);

		expect(response?.status()).toBe(404);

		await expect(page.locator("h1").first()).toHaveText("404", { timeout: 5000 });
		await expect(page.locator("body")).toContainText(`Campaign "${unknownId}" not found.`);
	});

	test("unknown campaign child route answers 404 with the error page", async ({ page }) => {
		// CONTRACT (spec: error-pages): the [id] layout guard covers every
		// child route (here …/jobs), so deep links to unknown campaigns 404
		// too — not a half-rendered jobs dashboard.
		const response = await page.goto(
			"/workspace/00000000-0000-4000-8000-000000000000/jobs",
		);

		expect(response?.status()).toBe(404);

		await expect(page.locator("h1").first()).toHaveText("404", { timeout: 5000 });
		await expect(page.locator("body")).toContainText("not found");
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
