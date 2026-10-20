import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/svelte";
import DevFlags from "../../../src/lib/components/DevFlags.svelte";

vi.mock("$app/environment", () => ({
	browser: true,
	dev: true,
	prerendering: false,
	SSR: false,
}));

const state = vi.hoisted(() => {
	let local = new Set<string>(["mock:createCampaign:success"]);
	return {
		local,
	};
});

vi.mock("$lib/config/featureFlags", () => ({
	featureFlags: {
		isEnabled: (f: string) => state.local.has(f),
		toggleLocal: (f: string) => {
			if (state.local.has(f)) state.local.delete(f);
			else state.local.add(f);
			localStorage.setItem("vc:flags", Array.from(state.local).join(","));
		},
		list: () => Array.from(new Set(["mockApi", ...Array.from(state.local)])),
	},
}));

function rowOf(label: string): HTMLInputElement {
	// Each flag row is: <label> <input type=checkbox /> {flag} </label>
	for (const lab of document.querySelectorAll("label")) {
		if (lab.textContent?.includes(label) === true) {
			const input = lab.querySelector("input");
			if (input) return input as HTMLInputElement;
		}
	}
	throw new Error(`flag row not found: ${label}`);
}

describe("DevFlags panel", () => {
	beforeEach(() => {
		localStorage.clear();
	});

	it("starts collapsed and expands into the panel from the Flags pill", async () => {
		render(DevFlags);

		expect(screen.queryByText("Dev Flags")).toBeNull();

		await fireEvent.click(screen.getByRole("button", { name: /flags/i }));

		expect(screen.getByText("Dev Flags")).toBeTruthy();
		expect(screen.getAllByText("mockApi").length).toBeGreaterThan(0);
		expect(screen.getByText("mock:createCampaign:success")).toBeTruthy();
	});

	it("toggling a flag persists it to vc:flags and the row re-renders enabled", async () => {
		render(DevFlags);

		await fireEvent.click(screen.getByRole("button", { name: /flags/i }));

		const box = rowOf("mockApi");
		expect(box.checked).toBe(false);

		await fireEvent.click(box);

		expect((localStorage.getItem("vc:flags") || "").split(",")).toContain("mockApi");
		expect(rowOf("mockApi").checked).toBe(true);
	});

	it("toggling a persisted flag off drops it from the panel's configured list", async () => {
		render(DevFlags);

		await fireEvent.click(screen.getByRole("button", { name: /flags/i }));

		const box = rowOf("mock:createCampaign:success");
		expect(box.checked).toBe(true);

		await fireEvent.click(box);

		// list() is the configured set (env ∪ persisted): a disabled flag leaves it.
		expect(
			[...document.querySelectorAll("label")].some((l) => l.textContent?.includes("success")),
		).toBe(false);
		expect((localStorage.getItem("vc:flags") || "").split(",")).not.toContain(
			"mock:createCampaign:success",
		);
	});
});
