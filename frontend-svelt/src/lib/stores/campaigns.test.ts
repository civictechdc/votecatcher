import { describe, it, expect, vi, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import { campaigns, resetCampaignsStore } from './campaigns';
import type { CampaignResponse } from '$lib/api/generated';

const mockListCampaigns = vi.fn();
const mockCreateCampaign = vi.fn();
const mockDeleteCampaign = vi.fn();

vi.mock('$lib/api/generated', () => {
	return {
		CampaignsApi: class {
			listCampaignsCampaignsGet = mockListCampaigns;
			createCampaignCampaignsPost = mockCreateCampaign;
			deleteCampaignCampaignsCampaignIdDelete = mockDeleteCampaign;
		}
	};
});

describe('Campaigns Store', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockListCampaigns.mockReset();
		mockCreateCampaign.mockReset();
		mockDeleteCampaign.mockReset();
		resetCampaignsStore();
	});

	describe('fetchAll', () => {
		it('starts with empty state and loaded=false', () => {
			const state = get(campaigns);
			expect(state.campaigns).toEqual([]);
			expect(state.loading).toBe(false);
			expect(state.loaded).toBe(false);
			expect(state.error).toBeNull();
		});

		it('sets loaded=true after successful fetch', async () => {
			mockListCampaigns.mockResolvedValue({ campaigns: [] });

			await campaigns.fetchAll();

			const state = get(campaigns);
			expect(state.loaded).toBe(true);
			expect(state.loading).toBe(false);
		});

		it('sets loading while fetching', async () => {
			mockListCampaigns.mockResolvedValue({ campaigns: [] });

			const promise = campaigns.fetchAll();

			let state = get(campaigns);
			expect(state.loading).toBe(true);
			expect(state.loaded).toBe(false);

			await promise;

			state = get(campaigns);
			expect(state.loading).toBe(false);
			expect(state.loaded).toBe(true);
		});

		it('stores fetched campaigns', async () => {
			const mockCampaigns: CampaignResponse[] = [
				{
					id: '1',
					unique_name: 'test-campaign',
					title: 'Test Campaign',
					year: '2024',
					region: 'DC',
					region_id: '1',
					created_at: new Date('2024-01-01T00:00:00Z'),
					updated_at: null
				}
			];

			mockListCampaigns.mockResolvedValue({ campaigns: mockCampaigns });

			await campaigns.fetchAll();

			const state = get(campaigns);
			expect(state.campaigns).toEqual(mockCampaigns);
			expect(state.loaded).toBe(true);
			expect(state.error).toBeNull();
		});

		it('handles fetch errors and keeps loaded=false', async () => {
			mockListCampaigns.mockRejectedValue(new Error('Network error'));

			await campaigns.fetchAll();

			const state = get(campaigns);
			expect(state.error).toBe('Network error');
			expect(state.campaigns).toEqual([]);
			expect(state.loaded).toBe(false);
		});
	});

	describe('create', () => {
		it('creates a new campaign', async () => {
			const newCampaign: CampaignResponse = {
				id: '2',
				unique_name: 'new-campaign',
				title: 'New Campaign',
				year: '2024',
				region: 'DC',
				region_id: '1',
				created_at: new Date('2024-01-01T00:00:00Z'),
				updated_at: null
			};

			mockListCampaigns.mockResolvedValue({ campaigns: [] });
			mockCreateCampaign.mockResolvedValue(newCampaign);

			await campaigns.fetchAll();
			const result = await campaigns.create({ name: 'New Campaign', year: 2024, region: 'DC' });

			const state = get(campaigns);
			expect(state.campaigns).toContainEqual(newCampaign);
			expect(result).toEqual(newCampaign);
		});

		it('handles create errors', async () => {
			mockCreateCampaign.mockRejectedValue(new Error('Validation failed'));

			await expect(
				campaigns.create({ name: '', year: 2024 })
			).rejects.toThrow('Validation failed');

			const state = get(campaigns);
			expect(state.error).toBe('Validation failed');
		});
	});

	describe('delete', () => {
		it('removes campaign from store', async () => {
			const existingCampaign: CampaignResponse = {
				id: '1',
				unique_name: 'test',
				title: 'Test',
				year: '2024',
				region: 'DC',
				region_id: '1',
				created_at: new Date('2024-01-01T00:00:00Z'),
				updated_at: null
			};

			mockListCampaigns.mockResolvedValue({ campaigns: [existingCampaign] });
			mockDeleteCampaign.mockResolvedValue(undefined);

			await campaigns.fetchAll();
			await campaigns.delete('1');

			const state = get(campaigns);
			expect(state.campaigns).not.toContainEqual(existingCampaign);
			expect(state.campaigns).toHaveLength(0);
		});

		it('handles delete when campaign does not exist', async () => {
			const existingCampaign: CampaignResponse = {
				id: '1',
				unique_name: 'test',
				title: 'Test',
				year: '2024',
				region: 'DC',
				region_id: '1',
				created_at: new Date('2024-01-01T00:00:00Z'),
				updated_at: null
			};

			mockListCampaigns.mockResolvedValue({ campaigns: [existingCampaign] });
			mockDeleteCampaign.mockResolvedValue(undefined);

			await campaigns.fetchAll();
			await campaigns.delete('999');

			const state = get(campaigns);
			expect(state.campaigns).toHaveLength(1);
			expect(state.campaigns[0]).toEqual(existingCampaign);
		});
	});
});
