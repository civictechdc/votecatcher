import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/svelte";
import Page from "../../../src/routes/(app)/auth/+page.svelte";

vi.mock("$app/environment", () => ({
	browser: true,
	dev: false,
	prerendering: false,
	SSR: false,
}));

vi.mock("$lib/stores/auth", () => ({
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

vi.mock("$lib/config/featureFlags", () => ({
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
