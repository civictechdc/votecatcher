import { describe, it, expect, vi } from "vitest";
import { render, fireEvent } from "@testing-library/svelte";
import Sidebar from "./Sidebar.svelte";

vi.mock("$app/stores", () => ({
	page: {
		subscribe: vi.fn((fn) => {
			fn({ url: { pathname: "/workspace/campaigns" } });
			return { unsubscribe: vi.fn() };
		}),
	},
}));

vi.mock("$lib/stores/campaigns", () => ({
	campaigns: {
		subscribe: vi.fn((fn) => {
			fn({ campaigns: [], loading: false, loaded: true, error: null, metrics: {} });
			return () => {};
		}),
		fetchAll: vi.fn(),
	},
}));

vi.mock("$lib/utils/mode", () => ({
	getLogoDestination: () => "/workspace/campaigns",
}));

describe("Sidebar Component", () => {
	describe("Rendering", () => {
		it("renders all navigation items", () => {
			const { getByText } = render(Sidebar);
			expect(getByText("Campaigns")).toBeTruthy();
			expect(getByText("Settings")).toBeTruthy();
		});

		it("renders logo/branding", () => {
			const { getByText } = render(Sidebar);
			expect(getByText("Votecatcher")).toBeTruthy();
		});
	});

	describe("Active State", () => {
		it("highlights active nav item based on current path", () => {
			const { getByText } = render(Sidebar);
			const campaignsLink = getByText("Campaigns").closest("a");
			expect(campaignsLink?.classList.contains("bg-blue-50")).toBe(true);
		});
	});

	describe("Mobile Behavior", () => {
		it("shows hamburger menu button on mobile", () => {
			const { container } = render(Sidebar);
			const menuButton = container.querySelector('button[aria-label="Toggle menu"]');
			expect(menuButton).toBeTruthy();
		});

		it("toggles sidebar visibility on mobile", async () => {
			const { container } = render(Sidebar);
			const menuButton = container.querySelector('button[aria-label="Toggle menu"]');

			await fireEvent.click(menuButton!);

			const sidebar = container.querySelector("aside");
			expect(sidebar?.classList.contains("translate-x-0")).toBe(true);
		});
	});

	describe("Accessibility", () => {
		it("has proper nav landmark", () => {
			const { container } = render(Sidebar);
			const nav = container.querySelector("nav");
			expect(nav?.getAttribute("aria-label")).toBe("Workspace navigation");
		});
	});
});
