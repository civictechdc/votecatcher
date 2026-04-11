// Server-side simulated matching endpoint.
// Accepts JSON { demo?: boolean }, returns mocked matches.
// Replace implementation with FastAPI backend later.

import type { RequestHandler } from "@sveltejs/kit";
import { json } from "@sveltejs/kit";
import type { MatchRow, ConfidenceThresholds, MatchResults } from "$lib/workspace-types";
import { MatchColumn } from "$lib/workspace-types";
import { faker } from "@faker-js/faker";
import { api, type ApiResult } from "$lib/api/client";
import { OCR_PROVIDER_API_KEY, OCR_PROVIDER_NAME, OCR_PROVIDER_MODEL } from "$env/static/private";
import { DEMO_MODE } from "$env/static/private";
import type { MatchingProgressResponse } from "$lib/api/response-types";

const SERVER_DEMO = DEMO_MODE === "true";

const MATCH_TABLE_COLUMNS: MatchColumn[] = [
	new MatchColumn("Registration Name", function (first: MatchRow, second: MatchRow) {
		return String(first["registeredName"] ?? "").localeCompare(
			String(second["registeredName"] ?? ""),
		);
	}),
	new MatchColumn("Matched Name"),
	new MatchColumn("Confidence", function (first, second) {
		const a = Number(first["predictionScore"]) || 0;
		const b = Number(second["predictionScore"]) || 0;
		if (a > b) return 1;
		if (a < b) return -1;
		return 0;
	}),
	new MatchColumn("Name distance"),
	new MatchColumn("Registered Address"),
	new MatchColumn("Address Distance"),
	new MatchColumn("Matched Address", function (first, second) {
		return String(first["predictedAddress"] ?? "").localeCompare(
			String(second["predictedAddress"] ?? ""),
		);
	}),
	new MatchColumn("Ward", function (first, second) {
		return String(first["ward"] ?? "").localeCompare(String(second["ward"] ?? ""));
	}),
	new MatchColumn("Page", function (first, second) {
		const a = Number(first["petitionPageNumber"]) || 0;
		const b = Number(second["petitionPageNumber"]) || 0;
		if (a > b) return 1;
		if (a < b) return -1;
		return 0;
	}),
	new MatchColumn("Row", function (first, second) {
		const a = Number(first["petitionRowNumber"]) || 0;
		const b = Number(second["petitionRowNumber"]) || 0;
		if (a > b) return 1;
		if (a < b) return -1;
		return 0;
	}),
	new MatchColumn("Match Rank", function (first, second) {
		const a = Number(first["matchRank"]) || 0;
		const b = Number(second["matchRank"]) || 0;
		if (a > b) return 1;
		if (a < b) return -1;
		return 0;
	}),
];

function createRandomMatch(thresholds: ConfidenceThresholds, rowIdx: number): MatchRow {
	const randomScore = parseFloat(Math.random().toFixed(2));

	const person = faker.person;
	const location = faker.location;
	const registeredAddress = location.streetAddress();
	const firstName = person.firstName();
	const middleName = person.middleName();
	const lastName = person.lastName();

	let fullName = "";
	let fullAddress = "";
	if (randomScore >= thresholds.high) {
		fullName = firstName + " " + lastName;
		fullAddress = registeredAddress;
	} else if (randomScore >= thresholds.medium) {
		fullName = firstName + " " + middleName.charAt(0) + ". " + lastName;
		fullAddress = registeredAddress;
	} else {
		const randomMix = Math.floor(Math.random() * 3);

		if (randomMix == 0) {
			fullName = faker.person.fullName();
			fullAddress = faker.location.streetAddress();
		} else if (randomMix == 1) {
			fullName = faker.person.fullName({ firstName: firstName });
			fullAddress = faker.location.secondaryAddress();
		} else {
			fullName = faker.person.fullName({ lastName: lastName });
			fullAddress = faker.location.streetAddress();
		}
	}

	const ward = Math.floor(Math.random() * 7) + 1;

	return {
		row_idx: rowIdx,
		voterId: faker.string.uuid(),
		registeredName: firstName + " " + lastName,
		ocrPredictedName: fullName,
		predictionScore: randomScore,
		registeredAddress: registeredAddress,
		predictedAddress: fullAddress,
		nameDistance: 1,
		addressDistance: 2,
		ward: ward.toString(),
		petitionPageNumber: 2,
		petitionRowNumber: 14,
		matchRank: 1,
	};
}

function mockMatches(thresholds: ConfidenceThresholds): MatchRow[] {
	const matches: MatchRow[] = [];

	for (let i = 0; i <= 50; i++) {
		matches.push(createRandomMatch(thresholds, i));
	}

	return matches;
}

export const POST: RequestHandler = async ({ request }) => {
	const body = await request.json().catch(() => ({}));
	const demoRequested = body?.demo === true || SERVER_DEMO;

	const batchEnabled = body?.batchEnabled === true;

	if (batchEnabled) {
		const batchResponse: ApiResult = await api.demoStartOcrRequest({
			provider_name: OCR_PROVIDER_NAME,
			provider_model: OCR_PROVIDER_MODEL,
			api_key: OCR_PROVIDER_API_KEY,
		});

		if (!batchResponse.ok) {
			return json({ batchResponse }, { status: 400 });
		}

		const matchStatus: MatchingProgressResponse = batchResponse.data as MatchingProgressResponse;
		console.log(`Batch response is ${JSON.stringify(matchStatus)}`);
		return json({ matchStatus }, { status: 200 });
	}
	const threshold: ConfidenceThresholds = body?.thresholds;

	// Simulate processing time on server
	await new Promise((r) => setTimeout(r, demoRequested ? 800 : 400));

	let matches: MatchRow[] = [];
	if (demoRequested) {
		matches = mockMatches(threshold ?? { high: 0.8, medium: 0.5 });
	}

	const matchResults: MatchResults = {
		matchColumns: MATCH_TABLE_COLUMNS,
		matchRecords: matches,
		timestamp: new Date().toISOString(),
	};

	return json({ matchResults }, { status: 200 });
};
