import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/svelte";
import { createRawSnippet } from "svelte";
import Layout from "../../../src/routes/(app)/+layout.svelte";

// Overrides the repo-wide $app/env mock (tests/setup.ts); the per-file factory wins.
vi.mock("$app/env", () => ({
	browser: true,
	dev: true,
	building: false,
	version: "test",
}));

vi.mock("#lib/api/client.ts", () => ({
	api: {
		database: {
			getStatus: vi.fn(() => new Promise<void>(() => {})),
		},
	},
}));

vi.mock("$app/navigation", () => ({
	goto: vi.fn(),
}));

const children = createRawSnippet(() => ({
	render: () => '<p data-testid="page-content">Page</p>',
	setup: () => {},
}));

describe("(app) layout dev flag mount", () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it("shows the collapsed flag affordance in developer mode", () => {
		render(Layout, { props: { children } });

		// The pill is mounted once at layout level, independent of backend status.
		expect(screen.getByRole("button", { name: /flags/i })).toBeTruthy();
		expect(screen.queryByText("Dev Flags")).toBeNull();
	});
});
