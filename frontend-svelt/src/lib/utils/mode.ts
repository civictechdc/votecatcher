import { browser } from '$app/environment';
import { PUBLIC_DEMO_MODE } from '$env/static/public';
import { get } from 'svelte/store';
import { featureFlags } from '$lib/stores/featureFlags';

export type AppMode = 'production' | 'demo' | 'simulation' | 'dev';

export function getAppMode(): AppMode {
	if (browser && import.meta.env.DEV) {
		return 'dev';
	}
	if (isDemoMode()) {
		return 'demo';
	}
	if (isSimulationMode()) {
		return 'simulation';
	}
	return 'production';
}

export function isDemoMode(): boolean {
	return PUBLIC_DEMO_MODE === 'true';
}

export function isSimulationMode(): boolean {
	if (!browser) return false;
	return get(featureFlags).simulationMode;
}

export function isDevMode(): boolean {
	return import.meta.env.DEV;
}

export function getLogoDestination(): string {
	const mode = getAppMode();
	switch (mode) {
		case 'demo':
			return '/workspace/demo';
		case 'simulation':
		case 'dev':
		case 'production':
		default:
			return '/workspace/campaigns';
	}
}

export function getCTADestination(): string {
	const mode = getAppMode();
	switch (mode) {
		case 'demo':
			return '/workspace/demo';
		case 'simulation':
		case 'dev':
		case 'production':
		default:
			return '/workspace/campaigns';
	}
}
