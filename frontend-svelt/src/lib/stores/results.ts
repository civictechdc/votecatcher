import { writable } from 'svelte/store';
import { ResultsApi } from '$lib/api/generated';
import { getApiClient } from './api-client';

interface MatchResult {
	id: number;
	ocr_result_id: number;
	prediction_1_name: string;
	prediction_1_score: number;
	confidence_level: 'HIGH' | 'MEDIUM' | 'LOW';
	[key: string]: any;
}

interface ResultsState {
	results: MatchResult[];
	total: number;
	offset: number;
	limit: number;
	confidence?: 'HIGH' | 'MEDIUM' | 'LOW';
	loading: boolean;
	error: string | null;
}

interface FetchOptions {
	offset?: number;
	limit?: number;
	confidence?: 'HIGH' | 'MEDIUM' | 'LOW';
}

function createResultsStore() {
	const { subscribe, set, update } = writable<ResultsState>({
		results: [],
		total: 0,
		offset: 0,
		limit: 50,
		confidence: undefined,
		loading: false,
		error: null
	});

	return {
		subscribe,

		async fetchResults(jobId: number, options: FetchOptions = {}) {
			const offset = options.offset ?? 0;
			const limit = options.limit ?? 50;
			const confidence = options.confidence;

			update((s) => ({
				...s,
				loading: true,
				error: null,
				offset,
				limit,
				confidence
			}));

			try {
				const client = getApiClient();
				const api = new ResultsApi(client);
				const response = await api.getResults({
					jobId,
					offset,
					limit,
					confidence
				});

				update((s) => ({
					...s,
					results: (response as any).items || [],
					total: (response as any).total || 0,
					loading: false
				}));
			} catch (error) {
				const message = error instanceof Error ? error.message : 'Unknown error';
				update((s) => ({
					...s,
					loading: false,
					error: message
				}));
			}
		},

		async exportCSV(jobId: number): Promise<string> {
			const client = getApiClient();
			const api = new ResultsApi(client);
			return await api.exportResults({ jobId });
		},

		clearError() {
			update((s) => ({ ...s, error: null }));
		},

		reset() {
			set({
				results: [],
				total: 0,
				offset: 0,
				limit: 50,
				confidence: undefined,
				loading: false,
				error: null
			});
		}
	};
}

export const results = createResultsStore();

export function resetResultsStore() {
	results.reset();
}
