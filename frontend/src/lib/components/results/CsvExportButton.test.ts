import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/svelte";
import CsvExportButton from "./CsvExportButton.svelte";

const mockExportCSV = vi.fn();

vi.mock("$lib/stores/results", () => ({
	results: {
		exportCSV: (...args: unknown[]) => mockExportCSV(...args),
		fetchResults: vi.fn(),
		clearError: vi.fn(),
		reset: vi.fn(),
		subscribe: vi.fn(() => () => {}),
	},
}));

describe("CsvExportButton", () => {
	afterEach(() => {
		vi.restoreAllMocks();
		vi.unstubAllGlobals();
		mockExportCSV.mockReset();
	});

	it("renders export button", () => {
		render(CsvExportButton, { jobId: 1 });
		const btn = screen.getByRole("button", { name: /export.*csv/i });
		expect(btn).toBeTruthy();
	});

	it("triggers download on click", async () => {
		mockExportCSV.mockResolvedValue(undefined);

		const mockAnchor = document.createElement("a");
		vi.spyOn(mockAnchor, "click");
		vi.spyOn(document, "createElement").mockImplementation((tagName: string) => {
			if (tagName.toLowerCase() === "a") return mockAnchor;
			return document.createElementNS("http://www.w3.org/1999/xhtml", tagName) as HTMLElement;
		});
		vi.stubGlobal("URL", {
			createObjectURL: vi.fn().mockReturnValue("blob:test-url"),
			revokeObjectURL: vi.fn(),
		});

		render(CsvExportButton, { jobId: 1 });

		const button = screen.getByRole("button", { name: /export.*csv/i });
		await fireEvent.click(button);

		await waitFor(() => {
			expect(mockExportCSV).toHaveBeenCalledWith(1);
		});
	});

	it("shows loading state during export", async () => {
		let resolveExport: (() => void) | undefined;
		mockExportCSV.mockImplementation(
			() =>
				new Promise<void>((resolve) => {
					resolveExport = resolve;
				}),
		);

		render(CsvExportButton, { jobId: 1 });

		const button = screen.getByRole("button", { name: /export.*csv/i });
		fireEvent.click(button);

		await waitFor(() => {
			const btn = screen.getByRole("button") as HTMLButtonElement;
			expect(btn.disabled).toBe(true);
		});

		resolveExport?.();

		await waitFor(() => {
			const btn = screen.getByRole("button") as HTMLButtonElement;
			expect(btn.disabled).toBe(false);
		});
	});

	it("shows error message on export failure", async () => {
		mockExportCSV.mockRejectedValue(new Error("Export failed"));

		render(CsvExportButton, { jobId: 1 });

		const button = screen.getByRole("button", { name: /export.*csv/i });
		await fireEvent.click(button);

		await waitFor(() => {
			expect(screen.getByText(/export failed/i)).toBeTruthy();
		});
	});
});
