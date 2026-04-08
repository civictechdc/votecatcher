import { test as base } from "@playwright/test";
import type { APIRequestContext } from "@playwright/test";

type TestFixtures = {
	apiContext: APIRequestContext;
	seededCampaign: { id: string; name: string };
};

const API_URL = process.env.PUBLIC_API_URL || "http://localhost:8080";

export const test = base.extend<TestFixtures>({
	apiContext: async ({ playwright }, use) => {
		const apiContext = await playwright.request.newContext({
			baseURL: API_URL,
		});
		await use(apiContext);
		await apiContext.dispose();
	},

	seededCampaign: async ({ apiContext }, use) => {
		const uniqueName = `test-campaign-${Date.now()}`;
		const response = await apiContext.post("/api/campaigns", {
			data: {
				name: uniqueName,
				year: 2024,
				region: "DC",
			},
		});

		if (!response.ok()) {
			throw new Error(`Failed to seed campaign: ${response.status()}`);
		}

		const campaign = await response.json();

		await use({ id: campaign.id, name: campaign.unique_name });

		await apiContext.delete(`/api/campaigns/${campaign.id}`).catch(() => {});
	},
});
