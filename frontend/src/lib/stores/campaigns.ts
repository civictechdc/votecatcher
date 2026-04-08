import { writable } from "svelte/store";
import { CampaignsApi } from "$lib/api/generated";
import { getApiClient } from "./api-client";
import type { CampaignResponse } from "$lib/api/generated";

interface CampaignsState {
	campaigns: CampaignResponse[];
	loading: boolean;
	loaded: boolean;
	error: string | null;
	metrics: {
		[campaignId: string]: {
			total_signatures: number;
			processed: number;
			high_confidence: number;
		};
	};
}

function createCampaignsStore() {
	const { subscribe, set, update } = writable<CampaignsState>({
		campaigns: [],
		loading: false,
		loaded: false,
		error: null,
		metrics: {},
	});

	return {
		subscribe,

		async fetchAll() {
			update((s) => ({ ...s, loading: true, error: null }));

			try {
				const client = getApiClient();
				const api = new CampaignsApi(client);
				const result = await api.listCampaignsCampaignsGet({});
				update((s) => ({ ...s, campaigns: result.campaigns, loading: false, loaded: true }));
			} catch (error) {
				const message = error instanceof Error ? error.message : "Unknown error";
				update((s) => ({ ...s, error: message, loading: false, campaigns: [] }));
			}
		},

		clearError() {
			update((s) => ({ ...s, error: null }));
		},

		reset() {
			set({ campaigns: [], loading: false, loaded: false, error: null, metrics: {} });
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
					loading: false,
				}));
				return newCampaign;
			} catch (error) {
				const message = error instanceof Error ? error.message : "Unknown error";
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
					loading: false,
				}));
			} catch (error) {
				const message = error instanceof Error ? error.message : "Unknown error";
				update((s) => ({ ...s, error: message, loading: false }));
				throw error;
			}
		},

		handleMetricsEvent(event: {
			campaign_id: string;
			total_signatures: number;
			processed: number;
			high_confidence: number;
		}) {
			if (!event.campaign_id) return;

			update((s) => ({
				...s,
				metrics: {
					...s.metrics,
					[event.campaign_id]: {
						total_signatures: event.total_signatures,
						processed: event.processed,
						high_confidence: event.high_confidence,
					},
				},
			}));
		},
	};
}

export const campaigns = createCampaignsStore();

export function resetCampaignsStore() {
	campaigns.reset();
}
