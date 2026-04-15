import { describe, it, expect, vi } from "vitest";
import { render, fireEvent } from "@testing-library/svelte";
import CropLightbox from "./CropLightbox.svelte";

describe("CropLightbox", () => {
	describe("Rendering", () => {
		it("renders when open is true with image", () => {
			const { container } = render(CropLightbox, {
				props: { open: true, imageUrl: "/api/crops/1/image", onClose: () => {} },
			});
			const img = container.querySelector("img") as HTMLImageElement;
			expect(img).toBeTruthy();
			expect(img.getAttribute("src")).toBe("/api/crops/1/image");
		});

		it("does not render when open is false", () => {
			const { container } = render(CropLightbox, {
				props: { open: false, imageUrl: "/api/crops/1/image", onClose: () => {} },
			});
			expect(container.querySelector("img")).toBeNull();
		});

		it("renders image with descriptive alt text", () => {
			const { container } = render(CropLightbox, {
				props: { open: true, imageUrl: "/api/crops/42/image", onClose: () => {} },
			});
			const img = container.querySelector("img") as HTMLImageElement;
			expect(img.getAttribute("alt")).toBe("Enlarged petition signature crop");
		});
	});

	describe("Close behavior", () => {
		it("calls onClose when Escape key is pressed", async () => {
			const onClose = vi.fn();
			render(CropLightbox, {
				props: { open: true, imageUrl: "/api/crops/1/image", onClose },
			});
			await fireEvent.keyDown(document, { key: "Escape" });
			expect(onClose).toHaveBeenCalledTimes(1);
		});

		it("calls onClose when backdrop is clicked", async () => {
			const onClose = vi.fn();
			const { container } = render(CropLightbox, {
				props: { open: true, imageUrl: "/api/crops/1/image", onClose },
			});
			const backdrop = container.querySelector(".fixed.inset-0.z-50");
			expect(backdrop).toBeTruthy();
			if (backdrop) await fireEvent.click(backdrop);
			expect(onClose).toHaveBeenCalledTimes(1);
		});

		it("calls onClose when close button is clicked", async () => {
			const onClose = vi.fn();
			const { getByLabelText } = render(CropLightbox, {
				props: { open: true, imageUrl: "/api/crops/1/image", onClose },
			});
			const closeBtn = getByLabelText("Close lightbox");
			await fireEvent.click(closeBtn);
			expect(onClose).toHaveBeenCalledTimes(1);
		});
	});

	describe("Accessibility", () => {
		it("has dialog role", () => {
			const { getByRole } = render(CropLightbox, {
				props: { open: true, imageUrl: "/api/crops/1/image", onClose: () => {} },
			});
			expect(getByRole("dialog")).toBeTruthy();
		});

		it("has aria-modal attribute", () => {
			const { getByRole } = render(CropLightbox, {
				props: { open: true, imageUrl: "/api/crops/1/image", onClose: () => {} },
			});
			expect(getByRole("dialog").getAttribute("aria-modal")).toBe("true");
		});
	});
});
