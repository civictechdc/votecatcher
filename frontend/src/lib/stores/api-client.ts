import { Configuration } from '$lib/api/generated/runtime';
import { PUBLIC_API_URL } from '$env/static/public';

let config: Configuration | null = null;

export function getApiClient(): Configuration {
	if (!config) {
		const baseUrl = (PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');
		config = new Configuration({
			basePath: baseUrl,
		});
	}
	return config;
}

export function resetApiClient() {
	config = null;
}
