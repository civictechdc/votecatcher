import { describe, it, expect } from "vitest";
import { sortResults } from "./campaign-results";
import type { CampaignResultResponse } from "./campaign-results";

function makeResult(overrides: Partial<CampaignResultResponse> & { ocrResultId: number }): CampaignResultResponse {
	return {
		extractedName: "",
		extractedAddress: "",
		cropId: 0,
		jobId: 0,
		predictions: [],
		...overrides,
	};
}

const testResults: CampaignResultResponse[] = [
	makeResult({
		ocrResultId: 1,
		extractedName: "Alice Smith",
		extractedAddress: "123 Main St",
		predictions: [{ rank: 1, voterName: "Bob Jones", voterAddress: "456 Oak Ave", similarityScore: 0.95, confidence: "HIGH" }],
	}),
	makeResult({
		ocrResultId: 2,
		extractedName: "Charlie Brown",
		extractedAddress: "789 Pine Rd",
		predictions: [{ rank: 1, voterName: "Alice White", voterAddress: "321 Elm Blvd", similarityScore: 0.72, confidence: "MEDIUM" }],
	}),
	makeResult({
		ocrResultId: 3,
		extractedName: "Diana Prince",
		extractedAddress: "555 Cedar Ln",
		predictions: [{ rank: 1, voterName: "Charlie Green", voterAddress: "888 Maple Dr", similarityScore: 0.45, confidence: "LOW" }],
	}),
];

describe("sortResults", () => {
	it("returns same order when config is null", () => {
		const sorted = sortResults(testResults, null);
		expect(sorted.map((r) => r.ocrResultId)).toEqual([1, 2, 3]);
	});

	it("sorts by extracted_name ascending", () => {
		const sorted = sortResults(testResults, { key: "extracted_name", direction: "asc" });
		expect(sorted.map((r) => r.ocrResultId)).toEqual([1, 2, 3]);
	});

	it("sorts by extracted_name descending", () => {
		const sorted = sortResults(testResults, { key: "extracted_name", direction: "desc" });
		expect(sorted.map((r) => r.ocrResultId)).toEqual([3, 2, 1]);
	});

	it("sorts by matched_name ascending", () => {
		const sorted = sortResults(testResults, { key: "matched_name", direction: "asc" });
		expect(sorted.map((r) => r.ocrResultId)).toEqual([2, 1, 3]);
	});

	it("sorts by confidence ascending (alphabetical)", () => {
		const sorted = sortResults(testResults, { key: "confidence", direction: "asc" });
		expect(sorted.map((r) => r.ocrResultId)).toEqual([1, 3, 2]);
	});

	it("sorts by score ascending (numeric)", () => {
		const sorted = sortResults(testResults, { key: "score", direction: "asc" });
		expect(sorted.map((r) => r.ocrResultId)).toEqual([3, 2, 1]);
	});

	it("sorts by score descending", () => {
		const sorted = sortResults(testResults, { key: "score", direction: "desc" });
		expect(sorted.map((r) => r.ocrResultId)).toEqual([1, 2, 3]);
	});

	it("sorts by extracted_address ascending", () => {
		const sorted = sortResults(testResults, { key: "extracted_address", direction: "asc" });
		expect(sorted.map((r) => r.ocrResultId)).toEqual([1, 3, 2]);
	});

	it("sorts by matched_address ascending", () => {
		const sorted = sortResults(testResults, { key: "matched_address", direction: "asc" });
		expect(sorted.map((r) => r.ocrResultId)).toEqual([2, 1, 3]);
	});

	it("handles results with no predictions", () => {
		const noPredictionResult = makeResult({ ocrResultId: 4, extractedName: "Zara" });
		const sorted = sortResults(
			[noPredictionResult, testResults[0]!],
			{ key: "score", direction: "asc" },
		);
		expect(sorted[0]!.ocrResultId).toBe(4);
	});

	it("is stable — equal keys preserve original order", () => {
		const sameScore = [
			makeResult({ ocrResultId: 1, predictions: [{ rank: 1, voterName: "A", voterAddress: "", similarityScore: 0.8, confidence: "HIGH" }] }),
			makeResult({ ocrResultId: 2, predictions: [{ rank: 1, voterName: "B", voterAddress: "", similarityScore: 0.8, confidence: "HIGH" }] }),
			makeResult({ ocrResultId: 3, predictions: [{ rank: 1, voterName: "C", voterAddress: "", similarityScore: 0.8, confidence: "HIGH" }] }),
		];
		const sorted = sortResults(sameScore, { key: "score", direction: "asc" });
		expect(sorted.map((r) => r.ocrResultId)).toEqual([1, 2, 3]);
	});

	it("returns new array without mutating input", () => {
		const original = [...testResults];
		sortResults(testResults, { key: "score", direction: "desc" });
		expect(testResults.map((r) => r.ocrResultId)).toEqual(original.map((r) => r.ocrResultId));
	});

	it("returns empty array unchanged", () => {
		const sorted = sortResults([], { key: "score", direction: "asc" });
		expect(sorted).toEqual([]);
	});

	it("returns unknown column key unchanged", () => {
		const sorted = sortResults(testResults, { key: "unknown_column", direction: "asc" });
		expect(sorted.map((r) => r.ocrResultId)).toEqual([1, 2, 3]);
	});
});
