import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/svelte";
import Page from "../../../src/routes/(app)/auth/+page.svelte";

// Overrides the repo-wide dev:true $app/env mock (tests/setup.ts) — the per-file factory wins — so this file runs in production mode.
vi.mock("$app/env", () => ({
	browser: true,
	dev: false,
	building: false,
	version: "test",
}));

vi.mock("#lib/stores/auth.ts", () => ({
	auth: {
		subscribe: vi.fn((fn: (s: unknown) => void) => {
			fn({ twoFactorRequired: false, user: null, initialized: true });
			return () => {};
		}),
		initSession: vi.fn(async () => {}),
		signIn: vi.fn(),
		signUp: vi.fn(),
		start2fa: vi.fn(),
		verify2fa: vi.fn(),
	},
}));

vi.mock("#lib/config/featureFlags.ts", () => ({
	featureFlags: {
		isEnabled: vi.fn(() => false),
		toggleLocal: vi.fn(),
		list: vi.fn(() => []),
	},
}));

describe("Auth page in production mode", () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it("renders no dev flags panel or flag controls", () => {
		render(Page);

		expect(screen.queryByText("Dev Flags")).toBeNull();
		expect(screen.queryByRole("button", { name: /flags/i })).toBeNull();
		// Mock handlers' flag keys must never surface as UI rows
		expect(screen.queryByText("mockApi")).toBeNull();
		expect(screen.queryByText("mock:session:loggedIn")).toBeNull();
		expect(screen.queryByText("mock:createCampaign:missingFields")).toBeNull();
	});
});
