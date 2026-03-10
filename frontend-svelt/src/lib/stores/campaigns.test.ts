import { describe, it, expect, vi, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import { campaigns, resetCampaignsStore } from './campaigns';
import type { Campaign } from '$lib/api/generated';

const mockListCampaigns = vi.fn();
const mockCreateCampaign = vi.fn();
const mockDeleteCampaign = vi.fn();

vi.mock('$lib/api/generated', () => {
	return {
		CampaignsApi: class {
			listCampaigns = mockListCampaigns;
			createCampaign = mockCreateCampaign;
			deleteCampaign = mockDeleteCampaign;
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

	describe('create', () => {
		it('creates a new campaign', async () => {
			const newCampaign: Campaign = {
				id: 2,
				name: 'New Campaign',
				year: 2024,
				regionId: 1,
				createdAt: new Date('2024-01-01T00:00:00Z')
			};

			mockListCampaigns.mockResolvedValue({ items: [], total: 0 });
			mockCreateCampaign.mockResolvedValue(newCampaign);

			await campaigns.fetchAll();
			const result = await campaigns.create({ name: 'New Campaign', year: 2024, regionId: 1 });

			const state = get(campaigns);
			expect(state.campaigns).toContainEqual(newCampaign);
			expect(result).toEqual(newCampaign);
		});

		it('handles create errors', async () => {
			mockCreateCampaign.mockRejectedValue(new Error('Validation failed'));

			await expect(
				campaigns.create({ name: '', year: 2024, regionId: 1 })
			).rejects.toThrow('Validation failed');

			const state = get(campaigns);
			expect(state.error).toBe('Validation failed');
		});
	});

	describe('delete', () => {
		it('removes campaign from store', async () => {
			const existingCampaign: Campaign = {
				id: 1,
				name: 'Test',
				year: 2024,
				regionId: 1,
				createdAt: new Date('2024-01-01T00:00:00Z')
			};

			mockListCampaigns.mockResolvedValue({ items: [existingCampaign], total: 1 });

			await campaigns.fetchAll();
			await campaigns.delete(1);

			const state = get(campaigns);
			expect(state.campaigns).not.toContainEqual(existingCampaign);
			expect(state.campaigns).toHaveLength(0);
		});

		it('handles delete when campaign does not exist', async () => {
			const existingCampaign: Campaign = {
				id: 1,
				name: 'Test',
				year: 2024,
				regionId: 1,
				createdAt: new Date('2024-01-01T00:00:00Z')
			};

			mockListCampaigns.mockResolvedValue({ items: [existingCampaign], total: 1 });

			await campaigns.fetchAll();
			await campaigns.delete(999);

			const state = get(campaigns);
			expect(state.campaigns).toHaveLength(1);
			expect(state.campaigns[0]).toEqual(existingCampaign);
		});
	});
});
