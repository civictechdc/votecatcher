import { Configuration } from "./runtime";
import type { VoterListUploadResponse, PetitionUploadResponse } from "./models/Upload";

export class UploadApi {
	private config: Configuration;

	constructor(config: Configuration) {
		this.config = config;
	}

	async uploadVoterListUploadVoterListPost(params: {
		file: File;
		campaign_id: string;
	}): Promise<VoterListUploadResponse> {
		const formData = new FormData();
		formData.append("file", params.file);
		formData.append("campaign_id", String(params.campaign_id));
		const fetchApi = this.config.fetchApi || fetch;
		const response = await fetchApi(`${this.config.basePath}/upload/voter-list`, {
			method: "POST",
			body: formData,
		});
		if (!response.ok) throw new Error(await response.text());
		return response.json();
	}

	async uploadPetitionUploadPetitionPost(params: {
		file: File;
		campaign_id: number;
	}): Promise<PetitionUploadResponse> {
		const formData = new FormData();
		formData.append("file", params.file);
		formData.append("campaign_id", String(params.campaign_id));
		const fetchApi = this.config.fetchApi || fetch;
		const response = await fetchApi(`${this.config.basePath}/upload/petition`, {
			method: "POST",
			body: formData,
		});
		if (!response.ok) throw new Error(await response.text());
		return response.json();
	}
}
