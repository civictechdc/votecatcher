import { describe, it, expect, beforeEach, vi } from "vitest";
import { API_BASE_URL } from "$lib/api/base-url";

describe("API Client", () => {
	beforeEach(() => {
		vi.resetModules();
	});

	it("creates client with default base URL", async () => {
		const { getApiClient } = await import("./api-client");
		const client = getApiClient();
		expect(client).toBeDefined();
		expect(client.basePath).toBeDefined();
		expect(typeof client.basePath).toBe("string");
	});

	it("uses API_BASE_URL", async () => {
		const { getApiClient } = await import("./api-client");
		const client = getApiClient();
		expect(client).toBeDefined();
		expect(client.basePath).toBe(API_BASE_URL);
	});

	it("returns singleton instance", async () => {
		const { getApiClient } = await import("./api-client");
		const client1 = getApiClient();
		const client2 = getApiClient();
		expect(client1).toBe(client2);
	});

	it("resetApiClient creates new instance on next call", async () => {
		const { getApiClient, resetApiClient } = await import("./api-client");
		const client1 = getApiClient();
		resetApiClient();
		const client2 = getApiClient();
		expect(client1).not.toBe(client2);
	});
});
