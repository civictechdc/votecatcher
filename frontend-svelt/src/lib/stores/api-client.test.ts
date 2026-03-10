import { describe, it, expect, beforeEach, vi } from 'vitest';
import { Configuration } from '$lib/api/generated/runtime';

describe('API Client', () => {
	beforeEach(() => {
		vi.resetModules();
	});

	it('creates client with default base URL', async () => {
		const { getApiClient } = await import('./api-client');
		const client = getApiClient();
		expect(client).toBeDefined();
		expect(client.basePath).toBeDefined();
		expect(typeof client.basePath).toBe('string');
	});

	it('uses PUBLIC_API_URL when available', async () => {
		const { getApiClient } = await import('./api-client');
		const client = getApiClient();
		expect(client).toBeDefined();
		expect(client.basePath).toBe('http://localhost:8000');
	});

	it('returns singleton instance', async () => {
		const { getApiClient } = await import('./api-client');
		const client1 = getApiClient();
		const client2 = getApiClient();
		expect(client1).toBe(client2);
	});

	it('resetApiClient creates new instance on next call', async () => {
		const { getApiClient, resetApiClient } = await import('./api-client');
		const client1 = getApiClient();
		resetApiClient();
		const client2 = getApiClient();
		expect(client1).not.toBe(client2);
	});
});
