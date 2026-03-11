import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { get } from 'svelte/store';

vi.mock('$env/static/public', () => ({
	PUBLIC_DEMO_MODE: 'true'
}));

vi.mock('$lib/stores/api-client', () => ({
	getApiClient: () => ({
		basePath: 'http://localhost:8000/api'
	})
}));

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('demo store', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	describe('initialized flag', () => {
		it('starts with initialized as false', async () => {
			vi.resetModules();
			const { demo } = await import('$lib/stores/demo');
			demo.resetStore();

			const state = get(demo);
			expect(state.initialized).toBe(false);
		});

		it('sets initialized to true after successful fetchPrebakedSessions', async () => {
			vi.resetModules();
			const { demo } = await import('$lib/stores/demo');
			demo.resetStore();

			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve({ sessions: [] })
			});

			await demo.fetchPrebakedSessions();

			const state = get(demo);
			expect(state.initialized).toBe(true);
		});

		it('sets initialized to true even after network error', async () => {
			vi.resetModules();
			const { demo } = await import('$lib/stores/demo');
			demo.resetStore();

			mockFetch.mockRejectedValueOnce(new Error('Network error'));

			await demo.fetchPrebakedSessions();

			const state = get(demo);
			expect(state.initialized).toBe(true);
			expect(state.error).toBe('Network error');
		});
	});

	describe('fetchPrebakedSessions', () => {
		it('fetches sessions from correct endpoint', async () => {
			vi.resetModules();
			const { demo } = await import('$lib/stores/demo');
			demo.resetStore();

			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve({ sessions: [] })
			});

			await demo.fetchPrebakedSessions();

			expect(mockFetch).toHaveBeenCalledWith(
				'http://localhost:8000/api/demo/sessions',
				expect.objectContaining({
					headers: expect.objectContaining({
						'Content-Type': 'application/json'
					})
				})
			);
		});

		it('stores prebaked sessions in state', async () => {
			vi.resetModules();
			const { demo } = await import('$lib/stores/demo');
			demo.resetStore();

			const mockSessions = [
				{ id: 'session-1', name: 'Demo 1', description: 'Test session' }
			];

			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve({ sessions: mockSessions })
			});

			await demo.fetchPrebakedSessions();

			const state = get(demo);
			expect(state.prebakedSessions).toEqual(mockSessions);
			expect(state.loading).toBe(false);
		});

		it('handles empty sessions array', async () => {
			vi.resetModules();
			const { demo } = await import('$lib/stores/demo');
			demo.resetStore();

			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve({})
			});

			await demo.fetchPrebakedSessions();

			const state = get(demo);
			expect(state.prebakedSessions).toEqual([]);
		});
	});

	describe('loadPrebaked', () => {
		it('calls correct endpoint with session ID', async () => {
			vi.resetModules();
			const { demo } = await import('$lib/stores/demo');
			demo.resetStore();

			const mockResponse = {
				success: true,
				session_id: 'minimal',
				message: 'Session loaded',
				campaign_id: '1',
				voters_count: 10,
				match_results_count: 50
			};

			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			await demo.loadPrebaked('minimal');

			expect(mockFetch).toHaveBeenCalledWith(
				'http://localhost:8000/api/demo/sessions/minimal/load',
				expect.objectContaining({
					method: 'POST'
				})
			);
		});

		it('stores loaded session info in state', async () => {
			vi.resetModules();
			const { demo } = await import('$lib/stores/demo');
			demo.resetStore();

			const mockResponse = {
				success: true,
				session_id: 'minimal',
				message: 'Session loaded',
				campaign_id: '1',
				voters_count: 10,
				match_results_count: 50
			};

			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			await demo.loadPrebaked('minimal');

			const state = get(demo);
			expect(state.loadedSession).toEqual(mockResponse);
			expect(state.loading).toBe(false);
		});

		it('sets error on load failure', async () => {
			vi.resetModules();
			const { demo } = await import('$lib/stores/demo');
			demo.resetStore();

			mockFetch.mockResolvedValueOnce({
				ok: false,
				json: () => Promise.resolve({ detail: 'Load failed' })
			});

			await expect(demo.loadPrebaked('minimal')).rejects.toThrow('Load failed');

			const state = get(demo);
			expect(state.error).toBe('Load failed');
			expect(state.loading).toBe(false);
		});
	});

	describe('resetData', () => {
		it('calls reset endpoint with POST method', async () => {
			vi.resetModules();
			const { demo } = await import('$lib/stores/demo');
			demo.resetStore();

			mockFetch.mockResolvedValueOnce({
				ok: true
			});

			await demo.resetData();

			expect(mockFetch).toHaveBeenCalledWith(
				'http://localhost:8000/api/demo/reset',
				expect.objectContaining({
					method: 'POST'
				})
			);
		});

		it('hides reset confirmation after successful reset', async () => {
			vi.resetModules();
			const { demo } = await import('$lib/stores/demo');
			demo.resetStore();
			demo.confirmReset();

			expect(get(demo).showResetConfirmation).toBe(true);

			mockFetch.mockResolvedValueOnce({
				ok: true
			});

			await demo.resetData();

			const state = get(demo);
			expect(state.showResetConfirmation).toBe(false);
			expect(state.resetting).toBe(false);
		});

		it('sets error on reset failure', async () => {
			vi.resetModules();
			const { demo } = await import('$lib/stores/demo');
			demo.resetStore();

			mockFetch.mockResolvedValueOnce({
				ok: false,
				json: () => Promise.resolve({ detail: 'Reset failed' })
			});

			await demo.resetData();

			const state = get(demo);
			expect(state.error).toBe('Reset failed');
			expect(state.resetting).toBe(false);
		});
	});

	describe('confirmReset/cancelReset', () => {
		it('shows confirmation modal when confirmReset called', async () => {
			vi.resetModules();
			const { demo } = await import('$lib/stores/demo');
			demo.resetStore();

			demo.confirmReset();

			expect(get(demo).showResetConfirmation).toBe(true);
		});

		it('hides confirmation modal when cancelReset called', async () => {
			vi.resetModules();
			const { demo } = await import('$lib/stores/demo');
			demo.resetStore();
			demo.confirmReset();

			demo.cancelReset();

			expect(get(demo).showResetConfirmation).toBe(false);
		});
	});

	describe('clearError', () => {
		it('clears error state', async () => {
			vi.resetModules();
			const { demo } = await import('$lib/stores/demo');
			demo.resetStore();

			mockFetch.mockRejectedValueOnce(new Error('Test error'));
			await demo.fetchPrebakedSessions();

			expect(get(demo).error).toBe('Test error');

			demo.clearError();

			expect(get(demo).error).toBeNull();
		});
	});

	describe('resetStore', () => {
		it('resets store to initial state', async () => {
			vi.resetModules();
			const { demo } = await import('$lib/stores/demo');

			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve({
					sessions: [{ id: '1', name: 'Test', description: '' }]
				})
			});

			await demo.fetchPrebakedSessions();
			demo.confirmReset();

			expect(get(demo).initialized).toBe(true);
			expect(get(demo).prebakedSessions.length).toBe(1);
			expect(get(demo).showResetConfirmation).toBe(true);

			demo.resetStore();

			const state = get(demo);
			expect(state).toEqual({
				initialized: false,
				showResetConfirmation: false,
				resetting: false,
				loading: false,
				error: null,
				prebakedSessions: [],
				loadedSession: null
			});
		});
	});
});
