import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { get } from 'svelte/store';

vi.mock('./api-client', () => ({
	getApiClient: vi.fn(() => ({
		basePath: 'http://localhost:8000/api'
	}))
}));

import { demo, resetDemoStore, isDemoModeEnabled, setDemoMode } from './demo';

global.fetch = vi.fn();

describe('Demo Store', () => {
	beforeEach(() => {
		resetDemoStore();
		setDemoMode(true);
		vi.clearAllMocks();
	});

	afterEach(() => {
		setDemoMode(false);
	});

	describe('initial state', () => {
		it('should start with reset confirmation false', () => {
			const state = get(demo);
			expect(state.showResetConfirmation).toBe(false);
			expect(state.resetting).toBe(false);
			expect(state.error).toBeNull();
		});
	});

	describe('isDemoModeEnabled', () => {
		it('should return a boolean', () => {
			expect(typeof isDemoModeEnabled()).toBe('boolean');
		});

		it('should return true when set', () => {
			setDemoMode(true);
			expect(isDemoModeEnabled()).toBe(true);
		});

		it('should return false when not set', () => {
			setDemoMode(false);
			expect(isDemoModeEnabled()).toBe(false);
		});
	});

	describe('confirmReset', () => {
		it('should show reset confirmation', () => {
			demo.confirmReset();
			const state = get(demo);
			expect(state.showResetConfirmation).toBe(true);
		});
	});

	describe('cancelReset', () => {
		it('should hide reset confirmation', () => {
			demo.confirmReset();
			demo.cancelReset();
			const state = get(demo);
			expect(state.showResetConfirmation).toBe(false);
		});
	});

	describe('resetData', () => {
		it('should call reset API and clear state', async () => {
			(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
				ok: true,
				json: async () => ({ success: true, message: 'Demo data reset' })
			});

			await demo.resetData();

			expect(global.fetch).toHaveBeenCalledWith(
				'http://localhost:8000/api/demo/reset',
				expect.objectContaining({ method: 'POST' })
			);

			const state = get(demo);
			expect(state.resetting).toBe(false);
			expect(state.showResetConfirmation).toBe(false);
		});

		it('should handle reset errors', async () => {
			(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
				ok: false,
				json: async () => ({ detail: 'Reset not allowed' })
			});

			await demo.resetData();

			const state = get(demo);
			expect(state.error).toBe('Reset not allowed');
			expect(state.resetting).toBe(false);
		});
	});

	describe('loadPrebaked', () => {
		it('should load pre-baked demo session', async () => {
			const mockSession = {
				id: 1,
				name: 'DC Demo 2024',
				session_type: 'DEMO',
				snapshot_data: { campaign_id: 'demo-campaign' }
			};

			(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
				ok: true,
				json: async () => mockSession
			});

			const result = await demo.loadPrebaked('dc-2024');

			expect(global.fetch).toHaveBeenCalledWith(
				'http://localhost:8000/api/demo/sessions/dc-2024/load',
				expect.objectContaining({ method: 'POST' })
			);
			expect(result).toEqual(mockSession);
		});

		it('should handle load errors', async () => {
			(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
				ok: false,
				json: async () => ({ detail: 'Session not found' })
			});

			await expect(demo.loadPrebaked('invalid')).rejects.toThrow('Session not found');
		});
	});

	describe('clearError', () => {
		it('should clear error state', () => {
			demo.clearError();
			const state = get(demo);
			expect(state.error).toBeNull();
		});
	});

	describe('resetDemoStore', () => {
		it('should reset store to initial state', () => {
			demo.confirmReset();
			resetDemoStore();
			const state = get(demo);
			expect(state).toEqual({
				showResetConfirmation: false,
				resetting: false,
				loading: false,
				error: null,
				prebakedSessions: []
			});
		});
	});
});
