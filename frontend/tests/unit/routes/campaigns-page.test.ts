import { describe, it, expect, vi, beforeEach, beforeAll } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/svelte";
import Page from "../../../src/routes/(app)/workspace/campaigns/+page.svelte";
import type { CampaignResponse } from "$lib/api/generated";
import Table from "$lib/components/ui/Table.svelte";

vi.mock("$lib/stores/campaigns", () => ({
	campaigns: {
		subscribe: vi.fn(),
		create: vi.fn(),
		delete: vi.fn(),
		fetchAll: vi.fn(),
		clearError: vi.fn(),
		reset: vi.fn(),
		handleMetricsEvent: vi.fn(),
	},
}));

vi.mock("$lib/stores/demo", () => ({
	demo: {
		subscribe: vi.fn((fn) => {
			fn({ initialized: true, showResetConfirmation: false, resetting: false, loading: false, error: null, prebakedSessions: [], loadedSession: null });
			return () => {};
		}),
	},
	isDemoModeEnabled: () => false,
	setDemoMode: vi.fn(),
}));

import { campaigns } from "$lib/stores/campaigns";

const testCampaigns: CampaignResponse[] = [
	{
		id: "1",
		uniqueName: "Campaign 1",
		title: "Campaign 1",
		year: "2024",
		region: "Region 1",
		regionId: "1",
		createdAt: new Date(),
		updatedAt: null,
	},
	{
		id: "2",
		uniqueName: "Campaign 2",
		title: "Campaign 2",
		year: "2024",
		region: "Region 2",
		regionId: "2",
		createdAt: new Date(),
		updatedAt: null,
	},
];

beforeAll(() => {
	try {
		const warmupCols = [{ key: "id", label: "ID", sortable: true }];
		const r = render(Table, {
			props: {
				columns: warmupCols,
				rows: [{ id: 1 }],
				sortable: true,
				sortConfig: { key: "id", direction: "asc" },
				onSortChange: vi.fn(),
				emptyMessage: "none",
			},
		});
		r.unmount();
	} catch {}
	try {
		const r = render(Table, {
			props: {
				columns: [{ key: "id", label: "ID" }],
				rows: [],
				emptyMessage: "none",
				sortable: true,
				onSortChange: vi.fn(),
			},
		});
		r.unmount();
	} catch {}
});

describe("Campaigns List Page", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
			fn({ campaigns: [], loading: false, loaded: true, error: null, metrics: {} });
			return () => {};
		});
	});

	describe("Display", () => {
		it("shows campaigns table", async () => {
			vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
				fn({ campaigns: testCampaigns, loading: false, loaded: true, error: null, metrics: {} });
				return () => {};
			});

			render(Page);

			await waitFor(() => {
				expect(screen.getByText("Campaign 1")).toBeTruthy();
				expect(screen.getByText("Campaign 2")).toBeTruthy();
			});
		});

		it("shows empty state when no campaigns", async () => {
			vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
				fn({ campaigns: [], loading: false, loaded: true, error: null, metrics: {} });
				return () => {};
			});

			render(Page);

			await waitFor(() => {
				expect(screen.getByText(/no campaigns yet/i)).toBeTruthy();
			});
		});

		it("shows loading spinner while loading", () => {
			vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
				fn({ campaigns: [], loading: true, loaded: false, error: null, metrics: {} });
				return () => {};
			});

			render(Page);

			expect(screen.getByRole("status")).toBeTruthy();
		});
	});

	describe("Create", () => {
		it("opens create modal on button click", async () => {
			vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
				fn({ campaigns: [], loading: false, loaded: true, error: null, metrics: {} });
				return () => {};
			});

			render(Page);

			const createButton = screen.getByRole("button", { name: /create campaign/i });
			await fireEvent.click(createButton);

			await waitFor(() => {
				expect(screen.getByRole("dialog")).toBeTruthy();
			});
		});

		it("calls create with form data", async () => {
			vi.mocked(campaigns.create).mockResolvedValue({} as CampaignResponse);
			vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
				fn({ campaigns: [], loading: false, loaded: true, error: null, metrics: {} });
				return () => {};
			});

			render(Page);

			await fireEvent.click(screen.getByRole("button", { name: /create campaign/i }));
			await fireEvent.input(screen.getByLabelText(/name/i), { target: { value: "New Campaign" } });
			await fireEvent.input(screen.getByLabelText(/year/i), { target: { value: "2024" } });
			await fireEvent.input(screen.getByLabelText(/region/i), { target: { value: "DC" } });
			await fireEvent.click(screen.getByRole("button", { name: /^create$/i }));

			await waitFor(() => {
				expect(campaigns.create).toHaveBeenCalledWith({
					name: "New Campaign",
					year: 2024,
					region: "DC",
				});
			});
		});
	});

	describe("Delete", () => {
		it("calls delete on button click", async () => {
			vi.mocked(campaigns.delete).mockResolvedValue(undefined);

			vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
				fn({ campaigns: testCampaigns.slice(0, 1), loading: false, loaded: true, error: null, metrics: {} });
				return () => {};
			});

			render(Page);

			const deleteButton = await screen.findByText(/delete/i);
			await fireEvent.click(deleteButton);

			await waitFor(() => {
				expect(screen.getByText(/are you sure/i)).toBeTruthy();
			});

			const confirmButton = screen.getByRole("button", { name: /^delete$/i });
			await fireEvent.click(confirmButton);

			await waitFor(() => {
				expect(campaigns.delete).toHaveBeenCalledWith("1");
			});
		});

		it("does not delete if user cancels", async () => {
			vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
				fn({ campaigns: testCampaigns.slice(0, 1), loading: false, loaded: true, error: null, metrics: {} });
				return () => {};
			});

			render(Page);

			const deleteButton = await screen.findByText(/delete/i);
			await fireEvent.click(deleteButton);

			await waitFor(() => {
				expect(screen.getByText(/are you sure/i)).toBeTruthy();
			});

			const cancelButton = screen.getByRole("button", { name: /cancel/i });
			await fireEvent.click(cancelButton);

			expect(campaigns.delete).not.toHaveBeenCalled();
		});
	});
});
