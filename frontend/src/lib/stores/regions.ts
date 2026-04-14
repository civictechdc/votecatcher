import { writable } from "svelte/store";
import { RegionsApi } from "$lib/api/generated/RegionsApi";
import { getApiClient } from "./api-client";
import type { RegionSummary } from "$lib/api/generated/models/Region";

interface RegionsState {
	regions: RegionSummary[];
	loading: boolean;
	loaded: boolean;
	error: string | null;
}

function createRegionsStore() {
	const { subscribe, set, update } = writable<RegionsState>({
		regions: [],
		loading: false,
		loaded: false,
		error: null,
	});

	return {
		subscribe,

		async fetchAll() {
			update((s) => ({ ...s, loading: true, error: null }));

			try {
				const client = getApiClient();
				const api = new RegionsApi(client);
				const result = await api.listRegions();
				update((s) => ({
					...s,
					regions: result.regions,
					loading: false,
					loaded: true,
				}));
			} catch (error) {
				const message = error instanceof Error ? error.message : "Unknown error";
				update((s) => ({ ...s, error: message, loading: false, regions: [] }));
			}
		},

		reset() {
			set({ regions: [], loading: false, loaded: false, error: null });
		},
	};
}

export const regions = createRegionsStore();
