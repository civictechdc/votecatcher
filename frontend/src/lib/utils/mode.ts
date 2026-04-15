import { browser, dev } from "$app/environment";
import { get } from "svelte/store";
import { featureFlags } from "$lib/stores/featureFlags";

const PUBLIC_DEMO_MODE: string = import.meta.env["PUBLIC_DEMO_MODE"] || "";

export type AppMode = "production" | "demo" | "simulation" | "dev";

const IS_DEV = dev;
export { IS_DEV };

export function getAppMode(): AppMode {
	if (browser && IS_DEV) {
		return "dev";
	}
	if (isDemoMode()) {
		return "demo";
	}
	if (isSimulationMode()) {
		return "simulation";
	}
	return "production";
}

export function isDemoMode(): boolean {
	return PUBLIC_DEMO_MODE === "true";
}

export function isSimulationMode(): boolean {
	if (!browser) return false;
	return get(featureFlags).simulationMode;
}

export function isDevMode(): boolean {
	return IS_DEV;
}

export function getLogoDestination(): string {
	const mode = getAppMode();
	switch (mode) {
		case "demo":
			return "/workspace/demo";
		case "simulation":
		case "dev":
		case "production":
		default:
			return "/workspace/campaigns";
	}
}

export function getCTADestination(): string {
	const mode = getAppMode();
	switch (mode) {
		case "demo":
			return "/workspace/demo";
		case "simulation":
		case "dev":
		case "production":
		default:
			return "/workspace/campaigns";
	}
}
