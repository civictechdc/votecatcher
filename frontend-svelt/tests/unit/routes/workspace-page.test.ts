import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, waitFor } from '@testing-library/svelte';
import Page from '../../../src/routes/workspace/+page.svelte';
import { campaigns } from '$lib/stores/campaigns';

vi.mock('$lib/stores/campaigns', () => ({
	campaigns: {
		subscribe: vi.fn(),
		fetchAll: vi.fn(),
		clearError: vi.fn()
	}
}));

describe('Dashboard Page', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('displays campaign count from store', async () => {
		const mockCampaigns = [
			{ id: 1, name: 'Campaign 1', year: 2024, regionId: 1, createdAt: new Date() },
			{ id: 2, name: 'Campaign 2', year: 2024, regionId: 1, createdAt: new Date() },
			{ id: 3, name: 'Campaign 3', year: 2024, regionId: 1, createdAt: new Date() }
		];

		vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
			fn({ campaigns: mockCampaigns, loading: false, error: null });
			return () => {};
		});

		const { getByText } = render(Page);

		await waitFor(() => {
			const countElement = getByText('3');
			expect(countElement).toBeTruthy();
		});
	});

	it('calls fetchAll on mount', () => {
		vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
			fn({ campaigns: [], loading: false, error: null });
			return () => {};
		});

		render(Page);

		expect(campaigns.fetchAll).toHaveBeenCalled();
	});
});
