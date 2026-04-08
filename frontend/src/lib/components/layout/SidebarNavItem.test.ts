import { describe, it, expect } from "vitest";
import { render } from "@testing-library/svelte";
import SidebarNavItem from "./SidebarNavItem.svelte";

describe("SidebarNavItem Component", () => {
	describe("Rendering", () => {
		it("renders with label", () => {
			const { getByText } = render(SidebarNavItem, {
				props: { href: "/workspace", label: "Dashboard" },
			});
			expect(getByText("Dashboard")).toBeTruthy();
		});

		it("renders as anchor link", () => {
			const { container } = render(SidebarNavItem, {
				props: { href: "/workspace/campaigns", label: "Campaigns" },
			});
			const link = container.querySelector("a");
			expect(link).toBeTruthy();
			expect(link?.getAttribute("href")).toBe("/workspace/campaigns");
		});
	});

	describe("Active State", () => {
		it("shows active state when href matches current path", () => {
			const { container } = render(SidebarNavItem, {
				props: {
					href: "/workspace",
					label: "Dashboard",
					isActive: true,
				},
			});
			const link = container.querySelector("a");
			expect(link?.classList.contains("bg-blue-50")).toBe(true);
			expect(link?.classList.contains("text-blue-700")).toBe(true);
		});

		it("shows inactive state by default", () => {
			const { container } = render(SidebarNavItem, {
				props: {
					href: "/workspace/campaigns",
					label: "Campaigns",
					isActive: false,
				},
			});
			const link = container.querySelector("a");
			expect(link?.classList.contains("text-slate-700")).toBe(true);
			expect(link?.classList.contains("bg-blue-50")).toBe(false);
		});
	});

	describe("Icon", () => {
		it("renders icon when provided", () => {
			const { container } = render(SidebarNavItem, {
				props: {
					href: "/workspace",
					label: "Dashboard",
					icon: "home",
				},
			});
			const icon = container.querySelector("svg");
			expect(icon).toBeTruthy();
		});
	});

	describe("Accessibility", () => {
		it("has aria-current when active", () => {
			const { container } = render(SidebarNavItem, {
				props: {
					href: "/workspace",
					label: "Dashboard",
					isActive: true,
				},
			});
			const link = container.querySelector("a");
			expect(link?.getAttribute("aria-current")).toBe("page");
		});

		it("is keyboard accessible", async () => {
			const { container } = render(SidebarNavItem, {
				props: { href: "/workspace", label: "Dashboard" },
			});
			const link = container.querySelector("a");
			expect(link?.getAttribute("tabindex")).not.toBe("-1");
		});
	});
});
