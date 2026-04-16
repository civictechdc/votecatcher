import { describe, it, expect } from "vitest";
import {
	sortResults,
	renderThumbnailCell,
	toggleAccordion,
	renderPredictionsTable,
	renderExpandedCropImage,
	escapeHtml,
} from "./campaign-results";
import type { CampaignResultResponse, CampaignMatchPrediction } from "./campaign-results";

function makeResult(
	overrides: Partial<CampaignResultResponse> & { ocrResultId: number },
): CampaignResultResponse {
	return {
		extractedName: "",
		extractedAddress: "",
		cropId: 0,
		jobId: 0,
		thumbnailUrl: "",
		predictions: [],
		...overrides,
	};
}

const testResults: CampaignResultResponse[] = [
	makeResult({
		ocrResultId: 1,
		extractedName: "Alice Smith",
		extractedAddress: "123 Main St",
		predictions: [
			{
				rank: 1,
				voterName: "Bob Jones",
				voterAddress: "456 Oak Ave",
				similarityScore: 0.95,
				confidence: "HIGH",
			},
		],
	}),
	makeResult({
		ocrResultId: 2,
		extractedName: "Charlie Brown",
		extractedAddress: "789 Pine Rd",
		predictions: [
			{
				rank: 1,
				voterName: "Alice White",
				voterAddress: "321 Elm Blvd",
				similarityScore: 0.72,
				confidence: "MEDIUM",
			},
		],
	}),
	makeResult({
		ocrResultId: 3,
		extractedName: "Diana Prince",
		extractedAddress: "555 Cedar Ln",
		predictions: [
			{
				rank: 1,
				voterName: "Charlie Green",
				voterAddress: "888 Maple Dr",
				similarityScore: 0.45,
				confidence: "LOW",
			},
		],
	}),
];

describe("CampaignResultResponse", () => {
	it("includes thumbnailUrl field", () => {
		const result = makeResult({
			ocrResultId: 1,
			thumbnailUrl: "/api/crops/42/image",
		});
		expect(result.thumbnailUrl).toBe("/api/crops/42/image");
	});

	it("defaults thumbnailUrl to empty string", () => {
		const result = makeResult({ ocrResultId: 1 });
		expect(result.thumbnailUrl).toBe("");
	});
});

describe("renderThumbnailCell", () => {
	it("renders img with correct attributes for valid URL", () => {
		const html = renderThumbnailCell("/api/crops/1/image");
		expect(html).toContain('src="http://localhost:8080/api/crops/1/image"');
		expect(html).toContain('loading="lazy"');
		expect(html).toContain('width="60"');
		expect(html).toContain('height="40"');
		expect(html).toContain('alt="Crop thumbnail"');
	});

	it("renders placeholder for empty URL", () => {
		const html = renderThumbnailCell("");
		expect(html).toContain("—");
		expect(html).not.toContain("<img");
	});

	it("escapes malicious URL in thumbnail", () => {
		const html = renderThumbnailCell('" onerror="alert(1)');
		expect(html).toContain("&quot;");
		expect(html).not.toContain('onerror="alert');
	});
});

describe("toggleAccordion", () => {
	it("expands unexpanded row", () => {
		expect(toggleAccordion(null, 1)).toBe(1);
	});

	it("collapses expanded row on re-click", () => {
		expect(toggleAccordion(1, 1)).toBeNull();
	});

	it("switches to different row", () => {
		expect(toggleAccordion(1, 2)).toBe(2);
	});

	it("expands from number to different number", () => {
		expect(toggleAccordion(42, 7)).toBe(7);
	});
});

function makePrediction(
	overrides: Partial<CampaignMatchPrediction> & { rank: number },
): CampaignMatchPrediction {
	return {
		voterName: "Test Voter",
		voterAddress: "123 Test St",
		similarityScore: 0.85,
		confidence: "HIGH",
		...overrides,
	};
}

describe("renderExpandedCropImage", () => {
	it("renders large image for valid URL", () => {
		const html = renderExpandedCropImage("/api/crops/42/image");
		expect(html).toContain('src="http://localhost:8080/api/crops/42/image"');
		expect(html).toContain("max-width");
		expect(html).toContain("max-height");
	});

	it("renders nothing for empty URL", () => {
		const html = renderExpandedCropImage("");
		expect(html).toBe("");
	});

	it("includes data-crop-url for lightbox click delegation", () => {
		const html = renderExpandedCropImage("/api/crops/42/image");
		expect(html).toContain('data-crop-url="http://localhost:8080/api/crops/42/image"');
	});

	it("includes cursor pointer for click affordance", () => {
		const html = renderExpandedCropImage("/api/crops/42/image");
		expect(html).toContain("cursor-pointer");
	});

	it("escapes malicious URL in expanded crop", () => {
		const html = renderExpandedCropImage('" onmouseover="alert(1)');
		expect(html).toContain("&quot;");
		expect(html).not.toContain('onmouseover="alert');
	});
});

describe("escapeHtml", () => {
	it("escapes ampersands", () => {
		expect(escapeHtml("a&b")).toBe("a&amp;b");
	});

	it("escapes angle brackets", () => {
		expect(escapeHtml("<script>alert(1)</script>")).toBe("&lt;script&gt;alert(1)&lt;/script&gt;");
	});

	it("escapes double quotes", () => {
		expect(escapeHtml('val="x"')).toBe("val=&quot;x&quot;");
	});

	it("escapes single quotes", () => {
		expect(escapeHtml("it's")).toBe("it&#39;s");
	});

	it("returns empty string unchanged", () => {
		expect(escapeHtml("")).toBe("");
	});

	it("returns safe text unchanged", () => {
		expect(escapeHtml("Alice Smith")).toBe("Alice Smith");
	});
});

describe("renderPredictionsTable", () => {
	it("renders table with prediction rows", () => {
		const predictions = [
			makePrediction({
				rank: 1,
				voterName: "Alice Smith",
				similarityScore: 0.95,
				confidence: "HIGH",
			}),
			makePrediction({
				rank: 2,
				voterName: "Bob Jones",
				similarityScore: 0.72,
				confidence: "MEDIUM",
			}),
		];
		const html = renderPredictionsTable(predictions);
		expect(html).toContain("Alice Smith");
		expect(html).toContain("Bob Jones");
		expect(html).toContain("<table");
		expect(html).toContain("<tr");
	});

	it("renders score as percentage", () => {
		const predictions = [makePrediction({ rank: 1, similarityScore: 0.856 })];
		const html = renderPredictionsTable(predictions);
		expect(html).toContain("85.6%");
	});

	it("renders confidence badge with color class", () => {
		const predictions = [makePrediction({ rank: 1, confidence: "HIGH" })];
		const html = renderPredictionsTable(predictions);
		expect(html).toContain("bg-green-100");
		expect(html).toContain("text-green-800");
	});

	it("renders empty message for empty predictions", () => {
		const html = renderPredictionsTable([]);
		expect(html).toContain("No predictions");
	});

	it("limits to 5 predictions", () => {
		const predictions = Array.from({ length: 7 }, (_, i) =>
			makePrediction({ rank: i + 1, voterName: `Voter ${i + 1}` }),
		);
		const html = renderPredictionsTable(predictions);
		expect(html).toContain("Voter 5");
		expect(html).not.toContain("Voter 6");
		expect(html).not.toContain("Voter 7");
	});

	it("escapes XSS in voterName", () => {
		const predictions = [makePrediction({ rank: 1, voterName: '<script>alert("xss")</script>' })];
		const html = renderPredictionsTable(predictions);
		expect(html).not.toContain("<script>");
		expect(html).toContain("&lt;script&gt;");
	});

	it("escapes XSS in voterAddress", () => {
		const predictions = [makePrediction({ rank: 1, voterAddress: "<img src=x onerror=alert(1)>" })];
		const html = renderPredictionsTable(predictions);
		expect(html).not.toContain("<img");
		expect(html).toContain("&lt;img");
	});
});

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
		const sorted = sortResults([noPredictionResult, testResults[0]!], {
			key: "score",
			direction: "asc",
		});
		expect(sorted[0]!.ocrResultId).toBe(4);
	});

	it("is stable — equal keys preserve original order", () => {
		const sameScore = [
			makeResult({
				ocrResultId: 1,
				predictions: [
					{ rank: 1, voterName: "A", voterAddress: "", similarityScore: 0.8, confidence: "HIGH" },
				],
			}),
			makeResult({
				ocrResultId: 2,
				predictions: [
					{ rank: 1, voterName: "B", voterAddress: "", similarityScore: 0.8, confidence: "HIGH" },
				],
			}),
			makeResult({
				ocrResultId: 3,
				predictions: [
					{ rank: 1, voterName: "C", voterAddress: "", similarityScore: 0.8, confidence: "HIGH" },
				],
			}),
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
