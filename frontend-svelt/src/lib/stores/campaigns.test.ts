import { describe, it, expect, vi, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import { campaigns, resetCampaignsStore } from './campaigns';
import type { Campaign } from '$lib/api/generated';

const mockListCampaigns = vi.fn();

vi.mock('$lib/api/generated', () => {
	return {
		CampaignsApi: class {
			listCampaigns = mockListCampaigns;
		}
	};
});

describe('Campaigns Store', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockListCampaigns.mockReset();
		resetCampaignsStore();
	});

	describe('fetchAll', () => {
		it('starts with empty state', () => {
			const state = get(campaigns);
			expect(state.campaigns).toEqual([]);
			expect(state.loading).toBe(false);
			expect(state.error).toBeNull();
		});

		it('sets loading while fetching', async () => {
			mockListCampaigns.mockResolvedValue({ items: [], total: 0 });

			const promise = campaigns.fetchAll();

			let state = get(campaigns);
			expect(state.loading).toBe(true);

			await promise;

			state = get(campaigns);
			expect(state.loading).toBe(false);
		});

		it('stores fetched campaigns', async () => {
			const mockCampaigns: Campaign[] = [
				{
					id: 1,
					name: 'Test Campaign',
					year: 2024,
					regionId: 1,
					createdAt: new Date('2024-01-01T00:00:00Z')
				}
			];

			mockListCampaigns.mockResolvedValue({ items: mockCampaigns, total: 1 });

			await campaigns.fetchAll();

			const state = get(campaigns);
			expect(state.campaigns).toEqual(mockCampaigns);
			expect(state.error).toBeNull();
		});

		it('handles fetch errors', async () => {
			mockListCampaigns.mockRejectedValue(new Error('Network error'));

			await campaigns.fetchAll();

			const state = get(campaigns);
			expect(state.error).toBe('Network error');
			expect(state.campaigns).toEqual([]);
		});
	});
});
