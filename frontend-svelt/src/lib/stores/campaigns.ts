import { writable } from 'svelte/store';
import { CampaignsApi } from '$lib/api/generated';
import { getApiClient } from './api-client';
import type { CampaignResponse } from '$lib/api/generated';

interface CampaignsState {
	campaigns: CampaignResponse[];
	loading: boolean;
	error: string | null;
}

function createCampaignsStore() {
	const { subscribe, set, update } = writable<CampaignsState>({
		campaigns: [],
		loading: true,
		error: null
	});

	return {
		subscribe,

		async fetchAll() {
			update((s) => ({ ...s, loading: true, error: null }));

			try {
				const client = getApiClient();
				const api = new CampaignsApi(client);
				const result = await api.listCampaignsCampaignsGet({});
				update((s) => ({ ...s, campaigns: result.campaigns, loading: false }));
			} catch (error) {
				const message = error instanceof Error ? error.message : 'Unknown error';
				update((s) => ({ ...s, error: message, loading: false, campaigns: [] }));
			}
		},

		clearError() {
			update((s) => ({ ...s, error: null }));
		},

		reset() {
			set({ campaigns: [], loading: false, error: null });
		},

		async create(data: { name: string; year: number; region?: string }): Promise<CampaignResponse> {
			update((s) => ({ ...s, loading: true, error: null }));

			try {
				const client = getApiClient();
				const api = new CampaignsApi(client);
				const newCampaign = await api.createCampaignCampaignsPost({ createCampaignRequest: data });
				update((s) => ({
					...s,
					campaigns: [...s.campaigns, newCampaign],
					loading: false
				}));
				return newCampaign;
			} catch (error) {
				const message = error instanceof Error ? error.message : 'Unknown error';
				update((s) => ({ ...s, error: message, loading: false }));
				throw error;
			}
		},

		async delete(id: string): Promise<void> {
			update((s) => ({ ...s, loading: true, error: null }));

			try {
				const client = getApiClient();
				const api = new CampaignsApi(client);
				await api.deleteCampaignCampaignsCampaignIdDelete({ campaignId: id });
				update((s) => ({
					...s,
					campaigns: s.campaigns.filter((c) => c.id !== id),
					loading: false
				}));
			} catch (error) {
				const message = error instanceof Error ? error.message : 'Unknown error';
				update((s) => ({ ...s, error: message, loading: false }));
				throw error;
			}
		}
	};
}

export const campaigns = createCampaignsStore();

export function resetCampaignsStore() {
	campaigns.reset();
}
