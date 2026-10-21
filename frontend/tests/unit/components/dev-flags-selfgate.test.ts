import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/svelte";
import DevFlags from "../../../src/lib/components/DevFlags.svelte";

// Pinned self-gate (defense in depth): even if a page mounts DevFlags without its own gate, the component renders nothing outside dev.
// This per-file factory overrides the repo-wide dev:true mock (tests/setup.ts) — the file factory wins.
// A separate file is required because mode.ts snapshots `dev` into IS_DEV at import time, so the flip must land before any import, in a fresh module graph.
vi.mock("$app/environment", () => ({
	browser: true,
	dev: false,
	prerendering: false,
	SSR: false,
}));

vi.mock("$lib/config/featureFlags", () => ({
	featureFlags: {
		isEnabled: vi.fn(() => true),
		toggleLocal: vi.fn(),
		list: vi.fn(() => ["mockApi"]),
	},
}));

describe("DevFlags self-gate", () => {
	it("renders nothing when the environment is not dev", () => {
		render(DevFlags);

		expect(screen.queryByRole("button", { name: /flags/i })).toBeNull();
		expect(screen.queryByText("Dev Flags")).toBeNull();
		expect(document.querySelectorAll("label").length).toBe(0);
	});
});
