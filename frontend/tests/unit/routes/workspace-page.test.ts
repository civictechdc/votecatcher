import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/svelte";
import Page from "../../../src/routes/(app)/workspace/[id]/+page.svelte";

const mocks = vi.hoisted(() => ({
	pageStore: null as null | { set: (v: unknown) => void },
	goto: vi.fn(),
	afterNavigate: vi.fn(),
	initialPage: {
		url: new URL("http://localhost/workspace/1"),
		params: { id: "1" } as Record<string, string>,
		route: {},
		status: 200,
		error: null,
		data: {},
		state: {},
	},
}));

const { initialPage } = mocks;

vi.mock("$app/stores", async () => {
	const { writable } = await import("svelte/store");
	const page = writable(mocks.initialPage);
	mocks.pageStore = page as unknown as { set: (v: unknown) => void };
	return { page };
});

vi.mock("$app/navigation", () => ({
	goto: mocks.goto,
	afterNavigate: mocks.afterNavigate,
	invalidate: vi.fn(),
	invalidateAll: vi.fn(),
	beforeNavigate: vi.fn(),
}));

vi.mock("$lib/stores/campaigns", () => ({
	campaigns: {
		subscribe: vi.fn((fn: (state: unknown) => void) => {
			fn({
				campaigns: [
					{
						id: "1",
						uniqueName: "Campaign A",
						title: "A",
						year: "2024",
						region: "DC",
						regionId: "1",
						createdAt: new Date(),
						updatedAt: null,
					},
				],
				loading: false,
				loaded: true,
				error: null,
				metrics: {},
			});
			return () => {};
		}),
		fetchAll: vi.fn(),
		handleMetricsEvent: vi.fn(),
	},
}));

vi.mock("$lib/stores/jobs", () => ({
	jobs: {
		subscribe: vi.fn((fn: (state: unknown) => void) => {
			fn({ jobs: [], loading: false, error: null });
			return () => {};
		}),
		fetchAll: vi.fn(),
		handleStatusEvent: vi.fn(),
		handleProgressEvent: vi.fn(),
	},
}));

vi.mock("$lib/api/base-url", () => ({
	API_BASE_URL: "",
}));

const setupStatusPayload = {
	voter_list: { exists: false, rowCount: null, uploadedAt: null, regionName: null },
	petitions: { exists: false, fileCount: 0, signatureCount: 0 },
	jobs: { total: 0, active: 0 },
	state: "empty",
};

const metricsPayload = {
	totalSignatures: 0,
	processed: 0,
	highConfidence: 0,
	mediumConfidence: 0,
	lowConfidence: 0,
	progressPercentage: 0,
	voterListCount: 0,
};

function jsonResponse(data: unknown): Response {
	return { ok: true, status: 200, json: async () => data } as unknown as Response;
}

describe("Workspace Page — live state", () => {
	let fetchSpy: ReturnType<typeof vi.fn>;

	beforeEach(() => {
		vi.clearAllMocks();
		initialPage.params = { id: "1" };
		initialPage.url = new URL("http://localhost/workspace/1");
		mocks.pageStore?.set({ ...initialPage });

		fetchSpy = vi.fn((input: RequestInfo | URL) => {
			const url = String(input);
			if (url.includes("/setup-status")) {
				return Promise.resolve(jsonResponse(setupStatusPayload));
			}
			if (url.includes("/metrics")) {
				return Promise.resolve(jsonResponse(metricsPayload));
			}
			return Promise.resolve(jsonResponse({}));
		});
		vi.stubGlobal("fetch", fetchSpy);
	});

	afterEach(() => {
		vi.unstubAllGlobals();
	});

	it("refetches both setup status and metrics when a setup:updated event arrives", async () => {
		render(Page);

		// initial fetches settle
		await waitFor(() => {
			expect(fetchSpy).toHaveBeenCalledWith("/api/campaigns/1/setup-status");
			expect(fetchSpy).toHaveBeenCalledWith("/api/campaigns/1/metrics");
		});

		const callsBefore = fetchSpy.mock.calls.length;
		fireEvent(document, new CustomEvent("votecatcher:setup:updated", { detail: {} }));

		await waitFor(() => {
			const urls = fetchSpy.mock.calls.slice(callsBefore).map((c) => String(c[0]));
			expect(urls).toContain("/api/campaigns/1/setup-status");
			expect(urls).toContain("/api/campaigns/1/metrics");
		});
	});

	it("navigates client-side to the upload page on Upload Files (no full reload)", async () => {
		render(Page);

		const uploadButton = await screen.findByRole("button", { name: /upload files/i });
		await fireEvent.click(uploadButton);

		await waitFor(() => {
			expect(mocks.goto).toHaveBeenCalledWith("/workspace/1/upload");
		});
	});

	it("navigates client-side to the jobs page on New Job", async () => {
		render(Page);

		const jobsButton = await screen.findByRole("button", { name: /new job/i });
		await fireEvent.click(jobsButton);

		await waitFor(() => {
			expect(mocks.goto).toHaveBeenCalledWith("/workspace/1/jobs");
		});
	});

	it("navigates client-side on quick actions: voter list, petitions, results", async () => {
		render(Page);

		await waitFor(() => {
			expect(screen.getAllByRole("button", { name: /upload voter list/i }).length).toBeGreaterThan(
				0,
			);
		});
		// both the stepper CTA and the Quick Action share the label; click them all
		for (const button of screen.getAllByRole("button", { name: /upload voter list/i })) {
			await fireEvent.click(button);
		}
		await waitFor(() => expect(mocks.goto).toHaveBeenCalledWith("/workspace/1/upload"));

		await fireEvent.click(screen.getByRole("button", { name: /upload petitions/i }));
		await waitFor(() => expect(mocks.goto).toHaveBeenCalledWith("/workspace/1/upload"));
	});

	it("shows View Results quick action only with match results", async () => {
		fetchSpy = vi.fn((input: RequestInfo | URL) => {
			const url = String(input);
			if (url.includes("/setup-status")) {
				return Promise.resolve(jsonResponse(setupStatusPayload));
			}
			if (url.includes("/metrics")) {
				return Promise.resolve(
					jsonResponse({ ...metricsPayload, processed: 4, totalSignatures: 4 }),
				);
			}
			return Promise.resolve(jsonResponse({}));
		});
		vi.stubGlobal("fetch", fetchSpy);

		render(Page);

		const resultsButton = await screen.findByRole("button", { name: /view results/i });
		await fireEvent.click(resultsButton);

		await waitFor(() => expect(mocks.goto).toHaveBeenCalledWith("/workspace/1/results"));
	});
});
