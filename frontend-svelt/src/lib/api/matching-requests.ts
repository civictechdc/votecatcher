import { request } from "$lib/api/client";
import type { MatchResponse, MatchResultResponse } from "./response-types";

export interface MatchMetaDataResponse {
	campaign_id: string;
	started_at: Date;
	completed_at?: Date;
	region: string;
	ocr_provider: string;
}

export const matchApi = {
	getMatchResults: (payload: {
		campaign_id: string;
		job_id: string;
		page_number?: number;
		results_per_page?: number;
	}) => {
		return request<MatchResultResponse>({
			opts: { method: "GET", headers: { "Content-Type": "application/json" } },
			path: ["api", payload.campaign_id, "matching", "result", payload.job_id],
			query: {
				id: payload.job_id,
				page: payload.page_number?.toString() ?? String(0),
				results_per_page: payload.results_per_page?.toString() ?? String(20),
			},
		});
	},

	simulateOcrResults: (task_id: string) => {
		return request<MatchResponse>({
			opts: { method: "GET", headers: { "Content-Type": "application/json" } },
			path: ["workspace", "ocr", "simulate", task_id],
		});
	},
};
