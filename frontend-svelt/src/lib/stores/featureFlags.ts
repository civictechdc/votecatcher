import { browser } from '$app/environment';
import { writable, derived } from 'svelte/store';

export interface FeatureFlags {
	simulationMode: boolean;
	betaFeatures: boolean;
	debugMode: boolean;
}

interface FeatureFlagOverrides {
	[key: string]: boolean | undefined;
}

const DEFAULT_FLAGS: FeatureFlags = {
	simulationMode: false,
	betaFeatures: false,
	debugMode: false,
};

const STORAGE_KEY = 'featureFlags_overrides';

function loadOverrides(): FeatureFlagOverrides {
	if (!browser) return {};

	try {
		const stored = localStorage.getItem(STORAGE_KEY);
		return stored ? JSON.parse(stored) : {};
	} catch {
		return {};
	}
}

function saveOverrides(overrides: FeatureFlagOverrides): void {
	if (!browser) return;

	try {
		localStorage.setItem(STORAGE_KEY, JSON.stringify(overrides));
	} catch (error) {
		console.error('Failed to save feature flag overrides:', error);
	}
}

function mergeFlags(
	serverFlags: FeatureFlags,
	overrides: FeatureFlagOverrides
): FeatureFlags {
	return {
		simulationMode: overrides.simulationMode ?? serverFlags.simulationMode,
		betaFeatures: overrides.betaFeatures ?? serverFlags.betaFeatures,
		debugMode: overrides.debugMode ?? serverFlags.debugMode,
	};
}

function createFeatureFlagStore() {
	const { subscribe, set, update } = writable<FeatureFlags>(DEFAULT_FLAGS);

	let overrides: FeatureFlagOverrides = loadOverrides();
	let serverFlags: FeatureFlags = DEFAULT_FLAGS;

	return {
		subscribe,

		async load(): Promise<void> {
			try {
				const response = await fetch('/api/config/features');
				if (response.ok) {
					serverFlags = await response.json();
					const merged = mergeFlags(serverFlags, overrides);
					set(merged);
				}
			} catch (error) {
				console.error('Failed to load feature flags:', error);
				set(mergeFlags(DEFAULT_FLAGS, overrides));
			}
		},

		toggle(flag: keyof FeatureFlags): void {
			update((current) => {
				const newValue = !current[flag];
				overrides[flag] = newValue;
				saveOverrides(overrides);
				return { ...current, [flag]: newValue };
			});
		},

		setFlag(flag: keyof FeatureFlags, value: boolean): void {
			update((current) => {
				overrides[flag] = value;
				saveOverrides(overrides);
				return { ...current, [flag]: value };
			});
		},

		reset(flag: keyof FeatureFlags): void {
			update((current) => {
				delete overrides[flag];
				saveOverrides(overrides);
				return { ...current, [flag]: serverFlags[flag] };
			});
		},

		resetAll(): void {
			overrides = {};
			saveOverrides(overrides);
			set(serverFlags);
		},

		getOverrides(): FeatureFlagOverrides {
			return { ...overrides };
		},

		getServerFlags(): FeatureFlags {
			return { ...serverFlags };
		},
	};
}

export const featureFlags = createFeatureFlagStore();

export const hasOverrides = derived(featureFlags, ($flags, set) => {
	const overrides = loadOverrides();
	set(Object.keys(overrides).length > 0);
});
