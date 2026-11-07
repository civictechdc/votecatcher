import { expect } from "@playwright/test";

import { test } from "./fixtures";

import type { APIRequestContext } from "@playwright/test";
import type { Page } from "@playwright/test";

/**
 * Characterization suite for the sidebar campaign switcher
 * (`src/lib/components/layout/CampaignSidebar.svelte`) and the campaign
 * SSE connection marker (`src/lib/stores/events.ts`).
 *
 * These tests PIN current SvelteKit 2 behavior as a tripwire for the
 * SvelteKit 3 upgrade.
 */

const SSE_CONNECTED_MARKER = "[SSE] Connected to campaign event stream";

async function createCampaign(
	apiContext: APIRequestContext,
	name: string,
): Promise<{ id: string; name: string }> {
	const response = await apiContext.post("/api/campaigns", {
		data: { name, year: 2024, region: "DC" },
	});
	if (!response.ok()) {
		throw new Error(`Failed to seed campaign ${name}: ${response.status()}`);
	}
	const campaign = await response.json();
	return { id: campaign.id, name: campaign.uniqueName };
}

/** Open the sidebar campaign switcher and return its panel list. */
async function openSwitcher(page: Page, currentCampaignName: string) {
	const toggle = page.locator("aside button[aria-expanded]");
	await expect(toggle).toBeVisible();
	// the switcher label renders the campaign name only after the campaigns
	// store fetch resolves (a pulse placeholder before that)
	await expect(toggle).toContainText(currentCampaignName, { timeout: 15_000 });
	await toggle.click();
	// the switcher panel is the first <ul> in the aside (nav lists follow it)
	const panel = page.locator("aside ul").first();
	await expect(panel).toBeVisible();
	return panel;
}

test.describe("Sidebar Campaign Switcher (characterization)", () => {
	test("switcher navigates to the target campaign", async ({
		page,
		apiContext,
		seededCampaign,
	}) => {
		const beta = await createCampaign(apiContext, `test-campaign-beta-${Date.now()}`);

		try {
			await page.goto(`/workspace/${seededCampaign.id}`);
			await page.waitForLoadState("domcontentloaded");

			const panel = await openSwitcher(page, seededCampaign.name);
			await panel.getByRole("button", { name: beta.name }).click();

			await page.waitForURL(new RegExp(`/workspace/${beta.id}$`), { timeout: 10_000 });
			await expect(page).toHaveURL(new RegExp(`/workspace/${beta.id}$`));
		} finally {
			await apiContext.delete(`/api/campaigns/${beta.id}`).catch(() => {});
		}
	});

	test("switcher preserves the current sub-path", async ({ page, apiContext, seededCampaign }) => {
		const beta = await createCampaign(apiContext, `test-campaign-beta-${Date.now()}`);

		try {
			await page.goto(`/workspace/${seededCampaign.id}/jobs`);
			await page.waitForLoadState("domcontentloaded");
			await expect(page.locator("h1").first()).toBeVisible();

			const panel = await openSwitcher(page, seededCampaign.name);
			await panel.getByRole("button", { name: beta.name }).click();

			await page.waitForURL(new RegExp(`/workspace/${beta.id}/jobs`), { timeout: 10_000 });
			await expect(page).toHaveURL(new RegExp(`/workspace/${beta.id}/jobs`));
		} finally {
			await apiContext.delete(`/api/campaigns/${beta.id}`).catch(() => {});
		}
	});

	test("full-page reload persists the switched campaign context", async ({
		page,
		apiContext,
		seededCampaign,
	}) => {
		const beta = await createCampaign(apiContext, `test-campaign-beta-${Date.now()}`);

		try {
			await page.goto(`/workspace/${seededCampaign.id}`);
			await page.waitForLoadState("domcontentloaded");

			const panel = await openSwitcher(page, seededCampaign.name);
			await panel.getByRole("button", { name: beta.name }).click();
			await page.waitForURL(new RegExp(`/workspace/${beta.id}$`), { timeout: 10_000 });

			await page.reload();
			await page.waitForLoadState("domcontentloaded");

			await expect(page).toHaveURL(new RegExp(`/workspace/${beta.id}$`));
			// the sidebar switcher shows the active campaign's name after reload
			await expect(page.locator("aside button[aria-expanded]")).toContainText(beta.name, {
				timeout: 15_000,
			});
		} finally {
			await apiContext.delete(`/api/campaigns/${beta.id}`).catch(() => {});
		}
	});

	test("campaign view logs the SSE connected console marker", async ({ page, seededCampaign }) => {
		const consoleMessages: string[] = [];
		page.on("console", (message) => {
			consoleMessages.push(message.text());
		});

		await page.goto(`/workspace/${seededCampaign.id}`);
		await page.waitForLoadState("domcontentloaded");

		await expect
			.poll(() => consoleMessages.some((text) => text === SSE_CONNECTED_MARKER), {
				timeout: 15_000,
				message: `expected console marker "${SSE_CONNECTED_MARKER}"`,
			})
			.toBe(true);
	});
});
