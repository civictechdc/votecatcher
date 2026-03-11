import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { get } from 'svelte/store';

vi.mock('$env/static/public', () => ({
	PUBLIC_API_URL: 'http://localhost:8000/api'
}));

vi.mock('$app/environment', () => ({
	browser: false
}));

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('featureFlags store', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	describe('URL construction', () => {
		it('should not double /api/api/ in URL', async () => {
			vi.resetModules();
			const { featureFlags } = await import('$lib/stores/featureFlags');

			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve({
					simulationMode: false,
					betaFeatures: false,
					debugMode: false
				})
			});

			await featureFlags.load();

			const fetchCall = mockFetch.mock.calls[0];
			const urlUsed = fetchCall[0];

			expect(urlUsed).not.toContain('/api/api/');
			expect(urlUsed).toBe('http://localhost:8000/api/config/features');
		});

		it('should construct URL correctly from PUBLIC_API_URL', async () => {
			vi.resetModules();
			const { featureFlags } = await import('$lib/stores/featureFlags');

			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve({
					simulationMode: false,
					betaFeatures: false,
					debugMode: false
				})
			});

			await featureFlags.load();

			expect(mockFetch).toHaveBeenCalledWith(
				'http://localhost:8000/api/config/features'
			);
		});
	});

	describe('load', () => {
		it('should update store with server flags on successful fetch', async () => {
			vi.resetModules();
			const { featureFlags } = await import('$lib/stores/featureFlags');

			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve({
					simulationMode: true,
					betaFeatures: true,
					debugMode: false
				})
			});

			await featureFlags.load();

			const state = get(featureFlags);
			expect(state.simulationMode).toBe(true);
			expect(state.betaFeatures).toBe(true);
			expect(state.debugMode).toBe(false);
		});

		it('should use default flags on fetch error', async () => {
			vi.resetModules();
			const { featureFlags } = await import('$lib/stores/featureFlags');

			mockFetch.mockRejectedValueOnce(new Error('Network error'));

			await featureFlags.load();

			const state = get(featureFlags);
			expect(state.simulationMode).toBe(false);
			expect(state.betaFeatures).toBe(false);
			expect(state.debugMode).toBe(false);
		});

		it('should use default flags on HTTP error', async () => {
			vi.resetModules();
			const { featureFlags } = await import('$lib/stores/featureFlags');

			mockFetch.mockResolvedValueOnce({
				ok: false,
				status: 500
			});

			await featureFlags.load();

			const state = get(featureFlags);
			expect(state.simulationMode).toBe(false);
		});
	});
});
