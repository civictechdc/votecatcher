import { writable } from "svelte/store";
import { ResultsApi } from "$lib/api/generated";
import { getApiClient } from "./api-client";
import type { ResultResponse } from "$lib/api/generated";

interface ResultsState {
	results: ResultResponse[];
	total: number;
	page: number;
	pageSize: number;
	confidence?: string;
	loading: boolean;
	error: string | null;
}

interface FetchOptions {
	page?: number;
	pageSize?: number;
	confidence?: string;
}

function createResultsStore() {
	const { subscribe, set, update } = writable<ResultsState>({
		results: [],
		total: 0,
		page: 1,
		pageSize: 50,
		confidence: undefined,
		loading: false,
		error: null,
	});

	return {
		subscribe,

		async fetchResults(jobId: number, options: FetchOptions = {}) {
			const page = options.page ?? 1;
			const pageSize = options.pageSize ?? 50;
			const confidence = options.confidence as "HIGH" | "MEDIUM" | "LOW" | undefined;

			update((s) => ({
				...s,
				loading: true,
				error: null,
				page,
				pageSize,
				confidence,
			}));

			try {
				const client = getApiClient();
				const api = new ResultsApi(client);
				const response = await api.getResultsJobsJobIdResultsGet({
					jobId,
					page,
					pageSize,
					confidence: confidence ?? null,
				});

				update((s) => ({
					...s,
					results: response.results,
					total: response.total,
					loading: false,
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

		async exportCSV(jobId: number, confidence?: string): Promise<void> {
			const client = getApiClient();
			const api = new ResultsApi(client);

			const response = await api.exportResultsCsvJobsJobIdResultsExportGet({
				jobId,
				confidence: (confidence as "HIGH" | "MEDIUM" | "LOW" | null) ?? null,
			});

			const blob = new Blob([response], { type: "text/csv" });
			const url = URL.createObjectURL(blob);
			const a = document.createElement("a");
			a.href = url;
			a.download = `results-job-${jobId}.csv`;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			URL.revokeObjectURL(url);
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
				error: null,
			});
		},
	};
}

export const results = createResultsStore();

export function resetResultsStore() {
	results.reset();
}
