export interface RegionSummary {
	key: string;
	name: string;
	id: string;
}

export interface RegionListResponse {
	regions: RegionSummary[];
}
