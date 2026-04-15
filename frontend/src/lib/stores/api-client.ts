import { Configuration } from "$lib/api/generated/runtime";
const PUBLIC_API_URL: string = import.meta.env["PUBLIC_API_URL"] || "";

let config: Configuration | null = null;

export function getApiClient(): Configuration {
	if (!config) {
		const baseUrl = (PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");
		config = new Configuration({
			basePath: baseUrl,
		});
	}
	return config;
}

export function resetApiClient() {
	config = null;
}
