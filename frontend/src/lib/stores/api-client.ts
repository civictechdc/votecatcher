import { Configuration } from "$lib/api/generated/runtime";
import { API_BASE_URL } from "$lib/api/base-url";

let config: Configuration | null = null;

export function getApiClient(): Configuration {
	if (!config) {
		const baseUrl = API_BASE_URL;
		config = new Configuration({
			basePath: baseUrl,
		});
	}
	return config;
}

export function resetApiClient() {
	config = null;
}
