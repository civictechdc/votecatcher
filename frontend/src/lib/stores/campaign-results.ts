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
