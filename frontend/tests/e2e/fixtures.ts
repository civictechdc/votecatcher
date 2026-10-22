import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { test as base } from "@playwright/test";
import type { APIRequestContext } from "@playwright/test";

type TestFixtures = {
	apiContext: APIRequestContext;
	seededCampaign: { id: string; name: string };
	campaignWithJobInputs: { id: string; name: string };
};

const API_URL = process.env["PUBLIC_API_URL"] || "http://localhost:8080";

const VOTER_LIST_CSV = [
	"First_Name,Last_Name,Street_Number,Street_Name",
	"Alice,Smith,123,Main St",
	"Bob,Jones,456,Oak Ave",
	"Carol,White,789,Pine Rd",
].join("\n");

/**
 * Upload the inputs required before a job can be created for a campaign:
 * petition scans, an active voter list for the campaign's region, and an
 * OCR provider config (the backend runs with simulated OCR in e2e, so the
 * fake key is never used for network calls).
 */
export async function seedJobInputs(
	apiContext: APIRequestContext,
	campaignId: string,
): Promise<void> {
	const petition = await apiContext.post("/api/upload/petition", {
		multipart: {
			campaign_id: campaignId,
			region: "DC",
			file: {
				name: "fake_signed_petitions_1-10.pdf",
				mimeType: "application/pdf",
				buffer: readFileSync(
					fileURLToPath(
						new URL("../../../samples/dc/fake_signed_petitions_1-10.pdf", import.meta.url),
					),
				),
			},
		},
	});
	if (!petition.ok()) {
		throw new Error(
			`Failed to seed petition upload: ${petition.status()} ${await petition.text()}`,
		);
	}

	const voterList = await apiContext.post("/api/upload/voter-list", {
		multipart: {
			campaign_id: campaignId,
			file: {
				name: "voters.csv",
				mimeType: "text/csv",
				buffer: Buffer.from(VOTER_LIST_CSV, "utf8"),
			},
		},
	});
	if (!voterList.ok()) {
		throw new Error(
			`Failed to seed voter list upload: ${voterList.status()} ${await voterList.text()}`,
		);
	}

	const provider = await apiContext.post("/api/settings/providers/openai", {
		data: {
			api_key: "test-key", // pragma: allowlist secret
			model: "gpt-4o-mini",
		},
	});
	if (!provider.ok()) {
		throw new Error(
			`Failed to seed OCR provider config: ${provider.status()} ${await provider.text()}`,
		);
	}
}

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

		await use({ id: campaign.id, name: campaign.uniqueName });

		await apiContext.delete(`/api/campaigns/${campaign.id}`).catch(() => {});
	},

	campaignWithJobInputs: async ({ apiContext, seededCampaign }, use, testInfo) => {
		// Seeding uploads the sample petition PDF and can exceed the 30s default.
		testInfo.setTimeout(120_000);

		// The provider config row is global app state (not campaign-scoped).
		// Note: the api_key is write-only (never returned by the API), so the
		// original key, if any, is destroyed by the seeding upsert — teardown
		// removes the seeded row rather than leaving a fake key bound to the
		// prior model.
		await seedJobInputs(apiContext, seededCampaign.id);
		await use(seededCampaign);

		await apiContext.delete("/api/settings/providers/openai").catch(() => {});
	},
});
