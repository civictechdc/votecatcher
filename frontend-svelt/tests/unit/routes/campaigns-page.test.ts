import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import Page from '../../../src/routes/workspace/campaigns/+page.svelte';
import type { CampaignResponse } from '$lib/api/generated';

vi.mock('$lib/stores/campaigns', () => ({
	campaigns: {
		subscribe: vi.fn(),
		create: vi.fn(),
		delete: vi.fn(),
		fetchAll: vi.fn(),
		clearError: vi.fn(),
		reset: vi.fn(),
		handleMetricsEvent: vi.fn(),
	},
}));

import { campaigns } from '$lib/stores/campaigns';

describe('Campaigns List Page', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
			fn({ campaigns: [], loading: false, loaded: true, error: null, metrics: {} });
			return () => {};
		});
	});

	describe('Display', () => {
		it('shows campaigns table', async () => {
			const testCampaigns: CampaignResponse[] = [
				{
					id: '1',
					unique_name: 'c1',
					title: 'Campaign 1',
					year: '2024',
					region: 'Region 1',
					region_id: '1',
					created_at: new Date(),
					updated_at: null,
				},
				{
					id: '2',
					unique_name: 'c2',
					title: 'Campaign 2',
					year: '2024',
					region: 'Region 2',
					region_id: '2',
					created_at: new Date(),
					updated_at: null,
				},
			];

			vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
				fn({ campaigns: testCampaigns, loading: false, loaded: true, error: null, metrics: {} });
				return () => {};
			});

			render(Page);

			await waitFor(() => {
				expect(screen.getByText('Campaign 1')).toBeTruthy();
				expect(screen.getByText('Campaign 2')).toBeTruthy();
			});
		});

		it('shows empty state when no campaigns', async () => {
			vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
				fn({ campaigns: [], loading: false, loaded: true, error: null, metrics: {} });
				return () => {};
			});

			render(Page);

			await waitFor(() => {
				expect(screen.getByText(/no campaigns yet/i)).toBeTruthy();
			});
		});

		it('shows loading spinner while loading', () => {
			vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
				fn({ campaigns: [], loading: true, loaded: false, error: null, metrics: {} });
				return () => {};
			});

			render(Page);

			expect(screen.getByRole('status')).toBeTruthy();
		});
	});

	describe('Create', () => {
		it('opens create modal on button click', async () => {
			render(Page);

			const createButton = screen.getByRole('button', { name: /create campaign/i });
			await fireEvent.click(createButton);

			await waitFor(() => {
				expect(screen.getByRole('dialog')).toBeTruthy();
				expect(screen.getByLabelText(/name/i)).toBeTruthy();
			});
		});

		it('calls create with form data', async () => {
			vi.mocked(campaigns.create).mockResolvedValue({} as CampaignResponse);

			render(Page);

			await fireEvent.click(screen.getByRole('button', { name: /create campaign/i }));
			await fireEvent.input(screen.getByLabelText(/name/i), { target: { value: 'New Campaign' } });
			await fireEvent.input(screen.getByLabelText(/year/i), { target: { value: '2024' } });
			await fireEvent.input(screen.getByLabelText(/region/i), { target: { value: 'DC' } });
			await fireEvent.click(screen.getByRole('button', { name: /^create$/i }));

			await waitFor(() => {
				expect(campaigns.create).toHaveBeenCalledWith({
					name: 'New Campaign',
					year: 2024,
					region: 'DC',
				});
			});
		});
	});

	describe('Delete', () => {
		it('calls delete on button click', async () => {
			vi.mocked(campaigns.delete).mockResolvedValue(undefined);
			vi.spyOn(window, 'confirm').mockReturnValue(true);

			const testCampaigns: CampaignResponse[] = [
				{
					id: '1',
					unique_name: 'c1',
					title: 'Campaign 1',
					year: '2024',
					region: 'Region 1',
					region_id: '1',
					created_at: new Date(),
					updated_at: null,
				},
			];

			vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
				fn({ campaigns: testCampaigns, loading: false, loaded: true, error: null, metrics: {} });
				return () => {};
			});

			render(Page);

			const deleteButton = await screen.findByText(/delete/i);
			await fireEvent.click(deleteButton);

			expect(campaigns.delete).toHaveBeenCalledWith('1');
		});

		it('does not delete if user cancels', async () => {
			vi.spyOn(window, 'confirm').mockReturnValue(false);

			const testCampaigns: CampaignResponse[] = [
				{
					id: '1',
					unique_name: 'c1',
					title: 'Campaign 1',
					year: '2024',
					region: 'Region 1',
					region_id: '1',
					created_at: new Date(),
					updated_at: null,
				},
			];

			vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
				fn({ campaigns: testCampaigns, loading: false, loaded: true, error: null, metrics: {} });
				return () => {};
			});

			render(Page);

			const deleteButton = await screen.findByText(/delete/i);
			await fireEvent.click(deleteButton);

			expect(campaigns.delete).not.toHaveBeenCalled();
		});
	});
});
