import { Configuration, request } from "./runtime";
import type { JobResponse, JobListResponse, CreateJobRequest } from "./models/Job";

export class JobsApi {
	private config: Configuration;

	constructor(config: Configuration) {
		this.config = config;
	}

	async listJobsJobsGet(params: { offset?: number; limit?: number }): Promise<JobListResponse> {
		const query: Record<string, unknown> = {};
		if (params.offset !== undefined) query["offset"] = params.offset;
		if (params.limit !== undefined) query["limit"] = params.limit;
		const qs = new URLSearchParams(
			Object.entries(query).map(([k, v]) => [k, String(v)]),
		).toString();
		return request<JobListResponse>(this.config, "GET", `/jobs${qs ? `?${qs}` : ""}`);
	}

	async createJobJobsPost(params: { createJobRequest: CreateJobRequest }): Promise<JobResponse> {
		return request<JobResponse>(this.config, "POST", "/jobs", params.createJobRequest);
	}

	async getJobJobsJobIdGet(params: { jobId: number }): Promise<JobResponse> {
		return request<JobResponse>(this.config, "GET", `/jobs/${params.jobId}`);
	}

	async cancelJobJobsJobIdCancelPost(params: { jobId: number }): Promise<JobResponse> {
		return request<JobResponse>(this.config, "POST", `/jobs/${params.jobId}/cancel`);
	}
}
