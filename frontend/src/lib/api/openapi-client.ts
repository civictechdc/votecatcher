import {
	Configuration,
	CampaignsApi,
	UploadApi,
	JobsApi,
	ResultsApi,
	SessionsApi,
} from "./generated";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080/api";

const config = new Configuration({
	basePath: API_BASE_URL,
});

export const campaignsApi = new CampaignsApi(config);
export const uploadApi = new UploadApi(config);
export const jobsApi = new JobsApi(config);
export const resultsApi = new ResultsApi(config);
export const sessionsApi = new SessionsApi(config);

export * from "./generated";
