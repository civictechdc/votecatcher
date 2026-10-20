import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/svelte";
import DevFlags from "../../../src/lib/components/DevFlags.svelte";

vi.mock("$app/environment", () => ({
	browser: true,
	dev: true,
	prerendering: false,
	SSR: false,
}));

// Mock substrate for the config helper. `known` models the configured set
// the panel lists (env-seeded keys plus previously persisted keys);
// `local` models the persisted vc:flags set.
// beforeEach reseeds both so every test is order-independent.
const state = vi.hoisted(() => {
	const known = new Set<string>(["mockApi", "mock:createCampaign:success"]);
	const local = new Set<string>(["mock:createCampaign:success"]);
	return {
		known,
		local,
		reset() {
			known.clear();
			known.add("mockApi");
			known.add("mock:createCampaign:success");
			local.clear();
			local.add("mock:createCampaign:success");
		},
		empty() {
			known.clear();
			local.clear();
		},
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
		list: () => Array.from(new Set([...Array.from(state.known), ...Array.from(state.local)])),
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
		state.reset();
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

	it("toggling a persisted flag off persists the flip to vc:flags and re-renders disabled", async () => {
		render(DevFlags);

		await fireEvent.click(screen.getByRole("button", { name: /flags/i }));

		const box = rowOf("mock:createCampaign:success");
		expect(box.checked).toBe(true);

		await fireEvent.click(box);

		// The flag stays in the configured list (still known) but renders disabled.
		expect((localStorage.getItem("vc:flags") || "").split(",")).not.toContain(
			"mock:createCampaign:success",
		);
		expect(rowOf("mock:createCampaign:success").checked).toBe(false);
	});

	it("add-flag input bootstraps a flag when the list is empty", async () => {
		state.empty();
		localStorage.clear();

		render(DevFlags);

		await fireEvent.click(screen.getByRole("button", { name: /flags/i }));

		// Empty configured set: no flag rows, only the add-flag affordance.
		expect(document.querySelectorAll("label").length).toBe(0);

		const input = screen.getByLabelText("New flag name");
		await fireEvent.input(input, { target: { value: "myNewFlag" } });
		await fireEvent.click(screen.getByRole("button", { name: /add/i }));

		expect(rowOf("myNewFlag").checked).toBe(true);
		expect((localStorage.getItem("vc:flags") || "").split(",")).toContain("myNewFlag");
	});
});
