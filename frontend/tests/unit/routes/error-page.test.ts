import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/svelte";
import RootError from "../../../src/routes/+error.svelte";
import WorkspaceError from "../../../src/routes/(app)/workspace/+error.svelte";

/**
 * Error-boundary prop contract (Kit 3; spec: error-pages).
 *
 * Kit 3 hands `+error.svelte` a single `error` prop — an `HttpError` from
 * `error(status, body)` (has `status` + `body.message`) or a runtime `Error`
 * (only `message`). These tests pin the derivation for both shapes plus the
 * minimal-prop fallback, so the rendered heading is never status-less.
 */

describe("root +error.svelte — Kit 3 error prop derivation", () => {
	it("surfaces status and body.message for HttpError-shaped props (404)", () => {
		render(RootError, {
			props: { error: { status: 404, body: { message: "Campaign not found." }, message: "" } },
		});

		expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("404");
		expect(screen.getByRole("heading", { level: 2 }).textContent).toBe("Page Not Found");
		expect(screen.getByText("Campaign not found.")).toBeTruthy();
	});

	it("falls back to 500 but keeps the message for generic Error props", () => {
		render(RootError, { props: { error: new Error("boom") } });

		expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("500");
		expect(screen.getByRole("heading", { level: 2 }).textContent).toBe("Server Error");
		expect(screen.getByText("boom")).toBeTruthy();
	});

	it("renders 500 + generic copy for minimal props", () => {
		render(RootError, { props: { error: { message: "" } } });

		expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("500");
		expect(screen.getByText("An unexpected error occurred. Please try again.")).toBeTruthy();
	});
});

describe("workspace +error.svelte — Kit 3 error prop derivation", () => {
	it("surfaces the thrown 404 status and message (unknown campaign boundary)", () => {
		render(WorkspaceError, {
			props: {
				error: { status: 404, body: { message: 'Campaign "nope" not found.' }, message: "" },
			},
		});

		expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("404");
		expect(screen.getByText('Campaign "nope" not found.')).toBeTruthy();
		// retry affordances required by the spec
		expect(screen.getByRole("button", { name: /try again/i })).toBeTruthy();
		expect(screen.getByRole("button", { name: /go back/i })).toBeTruthy();
	});

	it("falls back to 500 + workspace copy for minimal props", () => {
		render(WorkspaceError, { props: { error: { message: "" } } });

		expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("500");
		expect(screen.getByText("Something went wrong in your workspace.")).toBeTruthy();
	});
});
