import { writable } from "svelte/store";
import { PUBLIC_API_URL } from "$env/static/public";

const BASE_URL = PUBLIC_API_URL ?? "http://localhost:8000/api";

export interface FeatureFlags {
	simulationMode: boolean;
	betaFeatures: boolean;
	debugMode: boolean;
	demoMode: boolean;
	demoReset: boolean;
}

export interface Settings {
	ocr_provider: string | null;
	ocr_model: string | null;
	features: FeatureFlags;
}

interface SettingsState {
	initialized: boolean;
	loading: boolean;
	error: string | null;
	settings: Settings | null;
}

function createSettingsStore() {
	const { subscribe, set, update } = writable<SettingsState>({
		initialized: false,
		loading: false,
		error: null,
		settings: null,
	});

	async function fetchSettings(): Promise<void> {
		update((s) => ({ ...s, loading: true, error: null }));

		try {
			const response = await fetch(`${BASE_URL}/config/settings`);
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}`);
			}
			const settings: Settings = await response.json();
			update((s) => ({ ...s, initialized: true, loading: false, settings }));
		} catch (error) {
			const message = error instanceof Error ? error.message : "Unknown error";
			update((s) => ({ ...s, initialized: true, error: message, loading: false }));
		}
	}

	function clearError() {
		update((s) => ({ ...s, error: null }));
	}

	function resetStore() {
		set({
			initialized: false,
			loading: false,
			error: null,
			settings: null,
		});
	}

	return {
		subscribe,
		fetchSettings,
		clearError,
		resetStore,
	};
}

export const settings = createSettingsStore();
export { createSettingsStore };
