import { expect } from "@playwright/test";

import { test as base } from "./fixtures";

import type { APIRequestContext, Page } from "@playwright/test";

/**
 * Production smoke suite: walks the 7 baseline routes against the
 * adapter-node build (booted by playwright.prod.config.ts) and asserts the
 * README invariant — every route renders <main>, every page-API call
 * answers 2xx/3xx, and the console stays error-free.
 *
 * Run with: `bun run test:e2e:prod` (Postgres must already be up).
 */

const API_URL = process.env["PUBLIC_API_URL"] || "http://localhost:8080";

type CampaignHandle = { id: string; name: string };

type ProdWorkerFixtures = {
	alphaCampaign: CampaignHandle;
	betaCampaign: CampaignHandle;
};

async function seedCampaign(ctx: APIRequestContext, name: string): Promise<CampaignHandle> {
	const response = await ctx.post("/api/campaigns", {
		data: { name, year: 2024, region: "DC" },
	});
	if (!response.ok()) {
		throw new Error(`Failed to seed prod-smoke campaign ${name}: ${response.status()}`);
	}
	const campaign = await response.json();
	return { id: campaign.id, name: campaign.uniqueName };
}

const test = base.extend<object, ProdWorkerFixtures>({
	alphaCampaign: [
		async ({ playwright }, use) => {
			const ctx = await playwright.request.newContext({ baseURL: API_URL });
			const campaign = await seedCampaign(ctx, `prod-smoke-alpha-${Date.now()}`);
			await use(campaign);
			await ctx.delete(`/api/campaigns/${campaign.id}`).catch(() => {});
			await ctx.dispose();
		},
		{ scope: "worker" },
	],
	betaCampaign: [
		async ({ playwright }, use) => {
			const ctx = await playwright.request.newContext({ baseURL: API_URL });
			const campaign = await seedCampaign(ctx, `prod-smoke-beta-${Date.now()}`);
			await use(campaign);
			await ctx.delete(`/api/campaigns/${campaign.id}`).catch(() => {});
			await ctx.dispose();
		},
		{ scope: "worker" },
	],
});

/**
 * Collect console errors / page errors / failed API-origin responses for
 * the routes visited by one test.
 */
function watchPage(page: Page) {
	const consoleErrors: string[] = [];
	const failedApiCalls: string[] = [];
	const apiOrigin = new URL(API_URL).origin;

	page.on("console", (message) => {
		if (message.type() === "error") {
			consoleErrors.push(message.text());
		}
	});
	page.on("pageerror", (error) => {
		consoleErrors.push(`pageerror: ${error.message}`);
	});
	page.on("response", (response) => {
		if (new URL(response.url()).origin === apiOrigin && response.status() >= 400) {
			failedApiCalls.push(`${response.status()} ${response.request().method()} ${response.url()}`);
		}
	});

	return { consoleErrors, failedApiCalls };
}

async function assertRouteHealthy(page: Page, path: string, watched: ReturnType<typeof watchPage>) {
	const response = await page.goto(path);
	await page.waitForLoadState("domcontentloaded");

	expect(response?.status(), `page ${path} responded ${response?.status()}`).toBeLessThan(400);
	// exactly one <main> landmark per page (#194): root (app) layout owns it
	await expect(page.locator("main"), `route ${path} renders exactly one <main>`).toHaveCount(1);

	// settle for onMount fetches (hydration + store loads) before judging
	// the console / API-call invariants
	await page.waitForTimeout(1500);

	expect(watched.failedApiCalls, `route ${path} API failures`).toEqual([]);
	expect(watched.consoleErrors, `route ${path} console errors`).toEqual([]);
}

test.describe("Production smoke (adapter-node build)", () => {
	test("landing page /", async ({ page }) => {
		const watched = watchPage(page);
		await assertRouteHealthy(page, "/", watched);
	});

	test("/workspace redirects to /workspace/campaigns", async ({ page }) => {
		const watched = watchPage(page);
		await page.goto("/workspace");
		await page.waitForURL(/\/workspace\/campaigns/, { timeout: 10_000 });
		await expect(page).toHaveURL(/\/workspace\/campaigns/);
		await expect(page.locator("main")).toHaveCount(1);
		await page.waitForTimeout(1500);
		expect(watched.failedApiCalls, "API failures on /workspace redirect").toEqual([]);
		expect(watched.consoleErrors, "console errors on /workspace redirect").toEqual([]);
	});

	test("campaign dashboard /workspace/<alpha>", async ({ page, alphaCampaign }) => {
		const watched = watchPage(page);
		await assertRouteHealthy(page, `/workspace/${alphaCampaign.id}`, watched);
	});

	test("upload page /workspace/<alpha>/upload", async ({ page, alphaCampaign }) => {
		const watched = watchPage(page);
		await assertRouteHealthy(page, `/workspace/${alphaCampaign.id}/upload`, watched);
	});

	test("jobs page /workspace/<alpha>/jobs", async ({ page, alphaCampaign }) => {
		const watched = watchPage(page);
		await assertRouteHealthy(page, `/workspace/${alphaCampaign.id}/jobs`, watched);
	});

	test("results page /workspace/<alpha>/results", async ({ page, alphaCampaign }) => {
		const watched = watchPage(page);
		await assertRouteHealthy(page, `/workspace/${alphaCampaign.id}/results`, watched);
	});

	test("empty campaign /workspace/<beta>", async ({ page, betaCampaign }) => {
		const watched = watchPage(page);
		await assertRouteHealthy(page, `/workspace/${betaCampaign.id}`, watched);
	});
});
