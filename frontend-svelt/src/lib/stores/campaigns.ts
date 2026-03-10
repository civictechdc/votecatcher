import { writable } from 'svelte/store';
import { CampaignsApi } from '$lib/api/generated';
import { getApiClient } from './api-client';
import type { Campaign } from '$lib/api/generated';

interface CampaignsState {
	campaigns: Campaign[];
	loading: boolean;
	error: string | null;
}

function createCampaignsStore() {
	const { subscribe, set, update } = writable<CampaignsState>({
		campaigns: [],
		loading: false,
		error: null
	});

	return {
		subscribe,

		async fetchAll() {
			update((s) => ({ ...s, loading: true, error: null }));

			try {
				const client = getApiClient();
				const api = new CampaignsApi(client);
				const result = await api.listCampaigns({});
				update((s) => ({ ...s, campaigns: result.items, loading: false }));
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

		async create(data: { name: string; year: number; regionId: number }): Promise<Campaign> {
			update((s) => ({ ...s, loading: true, error: null }));

			try {
				const client = getApiClient();
				const api = new CampaignsApi(client);
				const newCampaign = await api.createCampaign({ createCampaign: data });
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

		async delete(id: number): Promise<void> {
			update((s) => ({ ...s, loading: true, error: null }));

			try {
				// TODO: Backend delete endpoint not yet available
				// When backend adds DELETE /campaigns/{id}, update this to:
				// const client = getApiClient();
				// const api = new CampaignsApi(client);
				// await api.deleteCampaign({ campaignId: id });

				// For now, just remove from local store
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
