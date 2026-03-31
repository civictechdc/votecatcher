import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { get } from 'svelte/store';

// Mock environment variables before importing
vi.mock('$env/static/public', () => ({
	PUBLIC_API_URL: 'http://localhost:8000/api',
}));

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('settings store', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	describe('initialized flag', () => {
		it('starts with initialized as false', async () => {
			// Import fresh store instance
			vi.resetModules();
			const { settings } = await import('$lib/stores/settings');

			// Reset to get initial state
			settings.resetStore();

			const state = get(settings);
			expect(state.initialized).toBe(false);
		});

		it('sets initialized to true after successful fetch', async () => {
			vi.resetModules();
			const { settings } = await import('$lib/stores/settings');
			settings.resetStore();

			const mockSettings = {
				ocr_provider: 'open_ai',
				ocr_model: 'gpt-4o-mini',
				features: {
					simulationMode: false,
					betaFeatures: false,
					debugMode: true,
					demoMode: true,
					demoReset: true,
				},
			};

			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve(mockSettings),
			});

			await settings.fetchSettings();

			const state = get(settings);
			expect(state.initialized).toBe(true);
			expect(state.settings).toEqual(mockSettings);
			expect(state.loading).toBe(false);
			expect(state.error).toBeNull();
		});

		it('sets initialized to true even after network error', async () => {
			vi.resetModules();
			const { settings } = await import('$lib/stores/settings');
			settings.resetStore();

			mockFetch.mockRejectedValueOnce(new Error('Network error'));

			await settings.fetchSettings();

			const state = get(settings);
			expect(state.initialized).toBe(true);
			expect(state.error).toBe('Network error');
			expect(state.loading).toBe(false);
		});

		it('sets initialized to true after HTTP error', async () => {
			vi.resetModules();
			const { settings } = await import('$lib/stores/settings');
			settings.resetStore();

			mockFetch.mockResolvedValueOnce({
				ok: false,
				status: 500,
			});

			await settings.fetchSettings();

			const state = get(settings);
			expect(state.initialized).toBe(true);
			expect(state.error).toBe('HTTP 500');
		});
	});

	describe('loading state', () => {
		it('sets loading to true during fetch', async () => {
			vi.resetModules();
			const { settings } = await import('$lib/stores/settings');
			settings.resetStore();

			let resolveFetch: (value: unknown) => void;
			const fetchPromise = new Promise((resolve) => {
				resolveFetch = resolve;
			});

			mockFetch.mockReturnValueOnce(fetchPromise);

			const fetchPromiseResult = settings.fetchSettings();

			// Check loading state during fetch
			const stateDuringFetch = get(settings);
			expect(stateDuringFetch.loading).toBe(true);

			// Resolve the fetch
			resolveFetch!({
				ok: true,
				json: () => Promise.resolve({ ocr_provider: null, ocr_model: null, features: {} }),
			});

			await fetchPromiseResult;

			const stateAfterFetch = get(settings);
			expect(stateAfterFetch.loading).toBe(false);
		});
	});

	describe('clearError', () => {
		it('clears error state', async () => {
			vi.resetModules();
			const { settings } = await import('$lib/stores/settings');
			settings.resetStore();

			mockFetch.mockRejectedValueOnce(new Error('Test error'));
			await settings.fetchSettings();

			let state = get(settings);
			expect(state.error).toBe('Test error');

			settings.clearError();

			state = get(settings);
			expect(state.error).toBeNull();
		});
	});
});
