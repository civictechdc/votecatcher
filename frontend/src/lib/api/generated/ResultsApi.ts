import { Configuration, request, requestBlob } from "./runtime";
import type { ResultResponse, ResultListResponse } from "./models/Result";

export class ResultsApi {
	private config: Configuration;

	constructor(config: Configuration) {
		this.config = config;
	}

	async getResultsJobsJobIdResultsGet(params: {
		jobId: number;
		page?: number;
		pageSize?: number;
		confidence?: string | null;
	}): Promise<ResultListResponse> {
		const query: Record<string, unknown> = {};
		if (params.page !== undefined) query.page = params.page;
		if (params.pageSize !== undefined) query.page_size = params.pageSize;
		if (params.confidence) query.confidence = params.confidence;
		const qs = new URLSearchParams(
			Object.entries(query).map(([k, v]) => [k, String(v)]),
		).toString();
		return request<ResultListResponse>(
			this.config,
			"GET",
			`/jobs/${params.jobId}/results${qs ? `?${qs}` : ""}`,
		);
	}

	async exportResultsCsvJobsJobIdResultsExportGet(params: {
		jobId: number;
		confidence?: string | null;
	}): Promise<Blob> {
		const query: Record<string, unknown> = {};
		if (params.confidence) query.confidence = params.confidence;
		const qs = new URLSearchParams(
			Object.entries(query).map(([k, v]) => [k, String(v)]),
		).toString();
		return requestBlob(
			this.config,
			"GET",
			`/jobs/${params.jobId}/results/export${qs ? `?${qs}` : ""}`,
		);
	}
}
