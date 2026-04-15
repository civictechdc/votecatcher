import { writable } from "svelte/store";
const PUBLIC_API_URL: string = import.meta.env["PUBLIC_API_URL"] || "";

interface CampaignMatchPrediction {
	rank: number;
	voterName: string;
	voterAddress: string;
	similarityScore: number;
	confidence: string;
}

export interface CampaignResultResponse {
	ocrResultId: number;
	extractedName: string;
	extractedAddress: string;
	cropId: number;
	jobId: number;
	thumbnailUrl: string;
	predictions: CampaignMatchPrediction[];
}

interface CampaignResultsState {
	results: CampaignResultResponse[];
	total: number;
	page: number;
	pageSize: number;
	confidence?: string;
	loading: boolean;
	initialized: boolean;
	error: string | null;
}

interface FetchOptions {
	page?: number;
	pageSize?: number;
	confidence?: string;
}

function getBaseUrl(): string {
	return (PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");
}

function createCampaignResultsStore() {
	const { subscribe, set, update } = writable<CampaignResultsState>({
		results: [],
		total: 0,
		page: 1,
		pageSize: 50,
		confidence: undefined,
		loading: false,
		initialized: false,
		error: null,
	});

	return {
		subscribe,

		async fetchResults(campaignId: string, options: FetchOptions = {}) {
			const page = options.page ?? 1;
			const pageSize = options.pageSize ?? 50;
			const confidence = options.confidence;

			update((s) => ({
				...s,
				loading: true,
				error: null,
				page,
				pageSize,
				confidence,
			}));

			try {
				const params = new URLSearchParams({
					page: String(page),
					page_size: String(pageSize),
				});
				if (confidence) {
					params.append("confidence", confidence);
				}

				const response = await fetch(
					`${getBaseUrl()}/api/campaigns/${campaignId}/results?${params.toString()}`,
				);

				if (!response.ok) {
					throw new Error(`HTTP ${response.status}: ${response.statusText}`);
				}

				const data = await response.json();

				update((s) => ({
					...s,
					results: data.results,
					total: data.total,
					loading: false,
					initialized: true,
				}));
			} catch (error) {
				const message = error instanceof Error ? error.message : "Unknown error";
				update((s) => ({
					...s,
					loading: false,
					error: message,
				}));
			}
		},

		clearError() {
			update((s) => ({ ...s, error: null }));
		},

		reset() {
			set({
				results: [],
				total: 0,
				page: 1,
				pageSize: 50,
				confidence: undefined,
				loading: false,
				initialized: false,
				error: null,
			});
		},
	};
}

export const campaignResults = createCampaignResultsStore();

export function resetCampaignResultsStore() {
	campaignResults.reset();
}

export function renderThumbnailCell(thumbnailUrl: string): string {
	if (!thumbnailUrl) return '<span class="text-slate-400">—</span>';
	return `<img src="${thumbnailUrl}" loading="lazy" width="60" height="40" alt="Crop thumbnail" class="rounded object-cover" />`;
}

export function sortResults(
	results: CampaignResultResponse[],
	config: { key: string; direction: "asc" | "desc" } | null,
): CampaignResultResponse[] {
	if (!config) return results;

	return [...results].sort((a, b) => {
		let aVal: string | number;
		let bVal: string | number;

		const topA = a.predictions[0];
		const topB = b.predictions[0];

		switch (config.key) {
			case "extracted_name":
				aVal = a.extractedName.toLowerCase();
				bVal = b.extractedName.toLowerCase();
				break;
			case "extracted_address":
				aVal = a.extractedAddress.toLowerCase();
				bVal = b.extractedAddress.toLowerCase();
				break;
			case "matched_name":
				aVal = (topA?.voterName ?? "").toLowerCase();
				bVal = (topB?.voterName ?? "").toLowerCase();
				break;
			case "matched_address":
				aVal = (topA?.voterAddress ?? "").toLowerCase();
				bVal = (topB?.voterAddress ?? "").toLowerCase();
				break;
			case "confidence":
				aVal = topA?.confidence ?? "";
				bVal = topB?.confidence ?? "";
				break;
			case "score":
				aVal = topA?.similarityScore ?? 0;
				bVal = topB?.similarityScore ?? 0;
				break;
			default:
				return 0;
		}

		if (aVal < bVal) return config.direction === "asc" ? -1 : 1;
		if (aVal > bVal) return config.direction === "asc" ? 1 : -1;
		return 0;
	});
}
