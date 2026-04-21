import { Configuration, request, requestBlob } from "./runtime";
import type { ResultsListResponse } from "./models/Result";
export class ResultsApi {
	private config: Configuration;

	constructor(config: Configuration) {
		this.config = config;
	}

	async getResultsJobsJobIdResultsGet(params: {
		jobId: number;
		cursor?: number | null;
		pageSize?: number;
		confidence?: string | null;
	}): Promise<ResultsListResponse> {
		const query: Record<string, unknown> = {};
		if (params.cursor) query["cursor"] = params.cursor;
		if (params.pageSize !== undefined) query["page_size"] = params.pageSize;
		if (params.confidence) query["confidence"] = params.confidence;
		const qs = new URLSearchParams(
			Object.entries(query).map(([k, v]) => [k, String(v)]),
		).toString();
		return request<ResultsListResponse>(
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
		if (params.confidence) query["confidence"] = params.confidence;
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
