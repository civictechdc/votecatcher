import {
	Configuration,
	CampaignsApi,
	UploadApi,
	JobsApi,
	ResultsApi,
	SessionsApi,
} from "./generated";
import { API_BASE_URL } from "./base-url";

const config = new Configuration({
	basePath: `${API_BASE_URL}/api`,
});

export const campaignsApi = new CampaignsApi(config);
export const uploadApi = new UploadApi(config);
export const jobsApi = new JobsApi(config);
export const resultsApi = new ResultsApi(config);
export const sessionsApi = new SessionsApi(config);

export * from "./generated";
