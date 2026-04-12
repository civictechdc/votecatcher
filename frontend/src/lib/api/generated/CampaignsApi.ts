import { Configuration, request } from "./runtime";
import type {
	CampaignResponse,
	CampaignListResponse,
	CreateCampaignRequest,
} from "./models/Campaign";

export class CampaignsApi {
	private config: Configuration;

	constructor(config: Configuration) {
		this.config = config;
	}

	async listCampaignsCampaignsGet(params: {
		offset?: number;
		limit?: number;
	}): Promise<CampaignListResponse> {
		const query: Record<string, unknown> = {};
		if (params.offset !== undefined) query["offset"] = params.offset;
		if (params.limit !== undefined) query["limit"] = params.limit;
		const qs = new URLSearchParams(
			Object.entries(query).map(([k, v]) => [k, String(v)]),
		).toString();
		return request<CampaignListResponse>(this.config, "GET", `/campaigns${qs ? `?${qs}` : ""}`);
	}

	async createCampaignCampaignsPost(params: {
		createCampaignRequest: CreateCampaignRequest;
	}): Promise<CampaignResponse> {
		return request<CampaignResponse>(
			this.config,
			"POST",
			"/campaigns",
			params.createCampaignRequest,
		);
	}

	async deleteCampaignCampaignsCampaignIdDelete(params: { campaignId: string }): Promise<void> {
		return request<void>(this.config, "DELETE", `/campaigns/${params.campaignId}`);
	}
}
