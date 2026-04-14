import { Configuration, request } from "./runtime";
import type { RegionListResponse } from "./models/Region";

export class RegionsApi {
	private config: Configuration;

	constructor(config: Configuration) {
		this.config = config;
	}

	async listRegions(): Promise<RegionListResponse> {
		return request<RegionListResponse>(this.config, "GET", "/regions");
	}
}
