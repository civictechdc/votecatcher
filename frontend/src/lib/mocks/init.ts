import { featureFlags } from "$lib/config/featureFlags";

// Initialize MSW worker if the mockApi feature flag is enabled.
// This file is safe to import (it is lazy-started via initMocks in onMount).
export async function initMocks() {
	if (typeof window === "undefined") return;
	// Only start worker when the top-level flag is enabled to avoid surprising behavior
	if (!featureFlags.isEnabled("mockApi")) return;

	try {
		const { worker } = await import("./browser");
		// allow real network requests that are not handled
		await worker.start({ onUnhandledRequest: "bypass" });
		console.info("MSW worker started (mockApi enabled)");
	} catch (err) {
		console.error("Failed to start MSW worker", err);
	}
}
