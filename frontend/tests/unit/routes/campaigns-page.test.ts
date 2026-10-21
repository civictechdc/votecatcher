import { describe, it, expect, vi, beforeEach, beforeAll, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent, cleanup } from "@testing-library/svelte";
import Page from "../../../src/routes/(app)/workspace/campaigns/+page.svelte";
import type { CampaignResponse } from "$lib/api/generated";
import Table from "$lib/components/ui/Table.svelte";
import fc from "fast-check";

// Property-test render budget: each run renders the page (~30ms plus transform
// warm-up). 25 runs keeps the property suite fast; raise only if CI allows.
const DEFAULT_YEAR_PROPERTY_RUNS = 25;
const YEAR_PAYLOAD_PROPERTY_RUNS = 25;
const YEAR_MIN = 1990;
const YEAR_MAX = 2100;

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
			fn({
				initialized: true,
				showResetConfirmation: false,
				resetting: false,
				loading: false,
				error: null,
				prebakedSessions: [],
				loadedSession: null,
			});
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
		// Pin the system time deterministically for every Create test. setSystemTime
		// mocks `Date` without faking vitest timers, so async UI waits stay real.
		beforeEach(() => {
			vi.setSystemTime(new Date(2030, 5, 15, 12));
		});

		afterEach(() => {
			vi.useRealTimers();
		});

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

		it("defaults year input to the current year when opened", async () => {
			vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
				fn({ campaigns: [], loading: false, loaded: true, error: null, metrics: {} });
				return () => {};
			});

			render(Page);

			await fireEvent.click(screen.getByRole("button", { name: /create campaign/i }));

			await waitFor(() => {
				expect(screen.getByRole("dialog")).toBeTruthy();
			});
			expect(screen.getByLabelText(/year/i)).toHaveProperty(
				"value",
				String(new Date().getFullYear()),
			);
		});

		it("resets year to the new current year after creation across New Year", async () => {
			vi.mocked(campaigns.create).mockResolvedValue({} as CampaignResponse);
			vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
				fn({ campaigns: [], loading: false, loaded: true, error: null, metrics: {} });
				return () => {};
			});

			vi.setSystemTime(new Date(2030, 11, 31, 12)); // local Dec 31, 2030

			render(Page);

			await fireEvent.click(screen.getByRole("button", { name: /create campaign/i }));
			expect(screen.getByLabelText(/year/i)).toHaveProperty("value", "2030");

			await fireEvent.input(screen.getByLabelText(/name/i), { target: { value: "New Campaign" } });
			await fireEvent.input(screen.getByLabelText(/year/i), { target: { value: "2001" } });

			// local Jan 1, 2031 — the year turns over before submission
			vi.setSystemTime(new Date(2031, 0, 1, 12));

			await fireEvent.click(screen.getByRole("button", { name: /^create$/i }));

			await waitFor(() => {
				expect(campaigns.create).toHaveBeenCalledWith({
					name: "New Campaign",
					year: 2001,
					region: "DC",
				});
			});

			await waitFor(() => {
				expect(screen.queryByRole("dialog")).toBeNull();
			});

			await fireEvent.click(screen.getByRole("button", { name: /create campaign/i }));

			await waitFor(() => {
				expect(screen.getByRole("dialog")).toBeTruthy();
			});
			expect(screen.getByLabelText(/year/i)).toHaveProperty("value", "2031");
		});

		it("resets year input to the current year after a creation", async () => {
			vi.mocked(campaigns.create).mockResolvedValue({} as CampaignResponse);
			vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
				fn({ campaigns: [], loading: false, loaded: true, error: null, metrics: {} });
				return () => {};
			});

			render(Page);

			await fireEvent.click(screen.getByRole("button", { name: /create campaign/i }));
			await fireEvent.input(screen.getByLabelText(/name/i), { target: { value: "New Campaign" } });
			await fireEvent.input(screen.getByLabelText(/year/i), { target: { value: "2001" } });
			await fireEvent.click(screen.getByRole("button", { name: /^create$/i }));

			await waitFor(() => {
				expect(campaigns.create).toHaveBeenCalled();
			});

			await fireEvent.click(screen.getByRole("button", { name: /create campaign/i }));

			await waitFor(() => {
				expect(screen.getByRole("dialog")).toBeTruthy();
			});
			expect(screen.getByLabelText(/year/i)).toHaveProperty(
				"value",
				String(new Date().getFullYear()),
			);
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
			await fireEvent.input(screen.getByLabelText(/region/i), { target: { value: "DC" } });
			await fireEvent.click(screen.getByRole("button", { name: /^create$/i }));

			await waitFor(() => {
				expect(campaigns.create).toHaveBeenCalledWith({
					name: "New Campaign",
					year: new Date().getFullYear(),
					region: "DC",
				});
			});
		});

		it("property: default year always equals the pinned system year", async () => {
			await fc.assert(
				fc.asyncProperty(
					fc.integer({ min: 2000, max: 2100 }),
					// Map year → a local mid-July date so the local year is unambiguous
					// regardless of the environment's time zone or UTC offset.
					async (theYear) => {
						vi.setSystemTime(new Date(theYear, 6, 15, 12));
						vi.mocked(campaigns.create).mockClear();
						vi.mocked(campaigns.subscribe).mockClear();
						vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
							fn({ campaigns: [], loading: false, loaded: true, error: null, metrics: {} });
							return () => {};
						});

						const { unmount } = render(Page);

						await fireEvent.click(screen.getByRole("button", { name: /create campaign/i }));
						await waitFor(() => {
							expect(screen.getByRole("dialog")).toBeTruthy();
						});
						expect(screen.getByLabelText(/year/i)).toHaveProperty("value", String(theYear));

						unmount();
						cleanup();
					},
				),
				{ numRuns: DEFAULT_YEAR_PROPERTY_RUNS },
			);
		});

		it("property: an entered year survives to the create payload", async () => {
			await fc.assert(
				fc.asyncProperty(fc.integer({ min: YEAR_MIN, max: YEAR_MAX }), async (enteredYear) => {
					vi.setSystemTime(new Date(2030, 5, 15, 12));
					vi.mocked(campaigns.create).mockClear();
					vi.mocked(campaigns.subscribe).mockClear();
					vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
						fn({ campaigns: [], loading: false, loaded: true, error: null, metrics: {} });
						return () => {};
					});

					const { unmount } = render(Page);

					await fireEvent.click(screen.getByRole("button", { name: /create campaign/i }));
					await fireEvent.input(screen.getByLabelText(/name/i), {
						target: { value: "Property Campaign" },
					});
					await fireEvent.input(screen.getByLabelText(/year/i), {
						target: { value: String(enteredYear) },
					});
					await fireEvent.click(screen.getByRole("button", { name: /^create$/i }));

					await waitFor(() => {
						expect(campaigns.create).toHaveBeenCalledWith({
							name: "Property Campaign",
							year: enteredYear,
							region: "DC",
						});
					});

					unmount();
					cleanup();
				}),
				{ numRuns: YEAR_PAYLOAD_PROPERTY_RUNS },
			);
		});
	});

	describe("Delete", () => {
		it("calls delete on button click", async () => {
			vi.mocked(campaigns.delete).mockResolvedValue(undefined);

			vi.mocked(campaigns.subscribe).mockImplementation((fn) => {
				fn({
					campaigns: testCampaigns.slice(0, 1),
					loading: false,
					loaded: true,
					error: null,
					metrics: {},
				});
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
				fn({
					campaigns: testCampaigns.slice(0, 1),
					loading: false,
					loaded: true,
					error: null,
					metrics: {},
				});
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
