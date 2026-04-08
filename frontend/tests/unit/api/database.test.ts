import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("$env/static/public", () => ({
	PUBLIC_API_URL: "http://localhost:8000",
}));

describe("api.database", () => {
	beforeEach(() => {
		vi.resetModules();
		global.fetch = vi.fn();
	});

	function mockFetchResponse(body: unknown, ok = true, status = 200) {
		(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
			ok,
			status,
			statusText: ok ? "OK" : "Internal Server Error",
			headers: { get: () => "application/json" },
			json: () => Promise.resolve(body),
		});
	}

	it("getStatus returns DatabaseStatus on success", async () => {
		const mockStatus = {
			configured: true,
			type: "sqlite",
			connected: true,
			message: "SQLite connected",
		};
		mockFetchResponse(mockStatus);

		const { api } = await import("$lib/api/client");
		const result = await api.database.getStatus();
		expect(result.ok).toBe(true);
		if (result.ok) {
			expect(result.data.type).toBe("sqlite");
			expect(result.data.connected).toBe(true);
		}
	});

	it("getStatus returns error on failure", async () => {
		mockFetchResponse({}, false, 500);

		const { api } = await import("$lib/api/client");
		const result = await api.database.getStatus();
		expect(result.ok).toBe(false);
		if (!result.ok) {
			expect(result.error).toBeTruthy();
		}
	});

	it("testSupabase sends credentials and returns result", async () => {
		const mockResult = {
			success: true,
			message: "Connected",
			project_ref: "abc",
		};
		mockFetchResponse(mockResult);

		const { api } = await import("$lib/api/client");
		const result = await api.database.testSupabase({
			project_url: "https://test.supabase.co",
			service_key: "sk_test_1234567890123456789012345678901234567890", // pragma: allowlist secret
			db_password: "password", // pragma: allowlist secret
		});
		expect(result.ok).toBe(true);
		if (result.ok) {
			expect(result.data.success).toBe(true);
			expect(result.data.project_ref).toBe("abc");
		}
	});

	it("testSupabase sends POST to correct endpoint", async () => {
		mockFetchResponse({ success: true, message: "OK" });

		const { api } = await import("$lib/api/client");
		await api.database.testSupabase({
			project_url: "https://test.supabase.co",
			service_key: "sk_test_key", // pragma: allowlist secret
			db_password: "pass", // pragma: allowlist secret
		});

		expect(global.fetch).toHaveBeenCalledWith(
			expect.stringContaining("/database/supabase/test"),
			expect.objectContaining({ method: "POST" }),
		);
	});

	it("provisionSupabase sends credentials and returns result", async () => {
		const mockResult = {
			success: true,
			message: "Provisioned",
			tables_created: ["voters"],
		};
		mockFetchResponse(mockResult);

		const { api } = await import("$lib/api/client");
		const result = await api.database.provisionSupabase({
			project_url: "https://test.supabase.co",
			service_key: "sk_test_1234567890123456789012345678901234567890", // pragma: allowlist secret
			db_password: "password", // pragma: allowlist secret
		});
		expect(result.ok).toBe(true);
		if (result.ok) {
			expect(result.data.tables_created).toContain("voters");
		}
	});

	it("provisionSupabase sends POST to provision endpoint", async () => {
		mockFetchResponse({ success: true, message: "OK" });

		const { api } = await import("$lib/api/client");
		await api.database.provisionSupabase({
			project_url: "https://test.supabase.co",
			service_key: "key", // pragma: allowlist secret
			db_password: "pass", // pragma: allowlist secret
		});

		expect(global.fetch).toHaveBeenCalledWith(
			expect.stringContaining("/database/supabase/provision"),
			expect.objectContaining({ method: "POST" }),
		);
	});

	it("disconnectSupabase sends DELETE and returns result", async () => {
		mockFetchResponse({ success: true });

		const { api } = await import("$lib/api/client");
		const result = await api.database.disconnectSupabase();
		expect(result.ok).toBe(true);

		expect(global.fetch).toHaveBeenCalledWith(
			expect.stringContaining("/database/supabase"),
			expect.objectContaining({ method: "DELETE" }),
		);
	});
});
