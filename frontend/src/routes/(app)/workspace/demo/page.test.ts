import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/svelte";
import { writable } from "svelte/store";
import Page from "./+page.svelte";

const createMockDemoStore = () => {
	const state = {
		initialized: true,
		showResetConfirmation: false,
		resetting: false,
		loading: false,
		error: null as string | null,
		prebakedSessions: [
			{ id: "dc-2024", name: "DC Demo 2024", description: "Sample DC petition data" },
		],
		loadedSession: null as any,
	};

	const store = writable(state);

	return {
		subscribe: store.subscribe,
		confirmReset: vi.fn(() => store.update((s) => ({ ...s, showResetConfirmation: true }))),
		cancelReset: vi.fn(() => store.update((s) => ({ ...s, showResetConfirmation: false }))),
		resetData: vi.fn(async () => {
			store.update((s) => ({ ...s, resetting: true }));
			store.update((s) => ({
				...s,
				resetting: false,
				showResetConfirmation: false,
			}));
		}),
		loadPrebaked: vi.fn(async (id: string) => ({ id, loaded: true })),
		clearError: vi.fn(() => store.update((s) => ({ ...s, error: null }))),
		fetchPrebakedSessions: vi.fn(),
	};
};

let mockStore: ReturnType<typeof createMockDemoStore>;

vi.mock("$lib/stores/demo", () => ({
	get demo() {
		return mockStore;
	},
	isDemoModeEnabled: () => true,
	setDemoMode: vi.fn(),
}));

describe("Demo Page", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockStore = createMockDemoStore();
	});

	it("should display demo page title", () => {
		render(Page);
		expect(screen.getByText(/demo mode/i)).toBeTruthy();
	});

	it("should show reset button", () => {
		render(Page);
		const btn = screen.getByRole("button", { name: /reset demo/i });
		expect(btn).toBeTruthy();
	});

	it("should show available pre-baked sessions", async () => {
		render(Page);
		await waitFor(() => {
			expect(screen.getByText("DC Demo 2024")).toBeTruthy();
		});
	});
});
