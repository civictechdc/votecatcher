import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, waitFor } from "@testing-library/svelte";
import { createRawSnippet } from "svelte";
import Layout from "../../../src/routes/(app)/workspace/[id]/+layout.svelte";

const mocks = vi.hoisted(() => ({
	pageStore: null as null | { set: (v: unknown) => void },
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

vi.mock("$lib/stores/campaigns", () => ({
	campaigns: {
		subscribe: vi.fn((fn: (state: unknown) => void) => {
			fn({
				campaigns: [
					{ id: "1", uniqueName: "Campaign A", title: "A" },
					{ id: "2", uniqueName: "Campaign B", title: "B" },
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

vi.mock("$lib/stores/events", () => ({
	events: {
		subscribe: vi.fn((fn: (state: unknown) => void) => {
			fn({ status: "disconnected", lastEvent: null, reconnectAttempts: 0 });
			return () => {};
		}),
		connect: vi.fn(),
		disconnect: vi.fn(),
		reset: vi.fn(),
	},
}));

vi.mock("$lib/components/layout", () => ({
	CampaignSidebar: vi.fn(),
}));

import { events } from "$lib/stores/events";

const children = createRawSnippet(() => ({
	render: () => `<p data-testid="child">dashboard</p>`,
}));

function renderLayout() {
	return render(Layout, { props: { children } });
}

describe("Workspace Layout — event stream follows the active campaign", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		initialPage.params = { id: "1" };
		initialPage.url = new URL("http://localhost/workspace/1");
		mocks.pageStore?.set({ ...initialPage });
	});

	it("connects the event stream to the campaign on first render", async () => {
		renderLayout();

		await waitFor(() => {
			expect(events.connect).toHaveBeenCalledWith("1");
		});
		expect(events.connect).toHaveBeenCalledTimes(1);
	});

	it("reconnects when the campaign id changes (layout reuse)", async () => {
		renderLayout();

		await waitFor(() => {
			expect(events.connect).toHaveBeenCalledWith("1");
		});

		mocks.pageStore?.set({
			...initialPage,
			params: { id: "2" },
			url: new URL("http://localhost/workspace/2"),
		});

		await waitFor(() => {
			expect(events.connect).toHaveBeenLastCalledWith("2");
		});
	});

	it("does not connect for demo or empty campaign ids", async () => {
		mocks.pageStore?.set({
			...initialPage,
			params: {},
			url: new URL("http://localhost/workspace"),
		});
		renderLayout();

		await new Promise((resolve) => setTimeout(resolve, 20));

		expect(events.connect).not.toHaveBeenCalled();

		mocks.pageStore?.set({
			...initialPage,
			params: { id: "demo" },
			url: new URL("http://localhost/workspace/demo"),
		});

		await new Promise((resolve) => setTimeout(resolve, 20));

		expect(events.connect).not.toHaveBeenCalled();
	});
});
