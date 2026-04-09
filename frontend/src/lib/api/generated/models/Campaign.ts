export interface CampaignResponse {
	id: string;
	unique_name: string;
	title: string;
	year: string;
	region: string | null;
	region_id: string | null;
	created_at: string | Date | null;
	updated_at: string | Date | null;
}

export interface CampaignListResponse {
	campaigns: CampaignResponse[];
	total: number;
}

export interface CreateCampaignRequest {
	name: string;
	year: number;
	region?: string;
}
