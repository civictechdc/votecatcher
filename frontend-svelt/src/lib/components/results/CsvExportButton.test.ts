import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import CsvExportButton from './CsvExportButton.svelte';
import { results } from '$lib/stores/results';

vi.mock('$lib/stores/results');

describe('CsvExportButton', () => {
	it('renders export button', () => {
		render(CsvExportButton, { jobId: 1 });
		expect(screen.getByRole('button', { name: /export.*csv/i })).toBeInTheDocument();
	});

	it('triggers download on click', async () => {
		const csvData = 'ocr_text,prediction,score\nJohn Doe,John Doe,0.95';
		vi.mocked(results.exportCSV).mockResolvedValue(csvData);

		// Mock URL.createObjectURL and anchor click
		const mockAnchor = { click: vi.fn(), href: '' };
		vi.spyOn(document, 'createElement').mockReturnValue(mockAnchor as any);
		vi.stubGlobal('URL', {
			createObjectURL: vi.fn().mockReturnValue('blob:test-url')
		});

		render(CsvExportButton, { jobId: 1 });

		const button = screen.getByRole('button', { name: /export.*csv/i });
		await fireEvent.click(button);

		await waitFor(() => {
			expect(results.exportCSV).toHaveBeenCalledWith(1);
			expect(mockAnchor.click).toHaveBeenCalled();
		});

		vi.unstubAllGlobals();
	});

	it('shows loading state during export', async () => {
		let resolveExport: (value: string) => void;
		vi.mocked(results.exportCSV).mockImplementation(
			() => new Promise((resolve) => {
				resolveExport = resolve;
			})
		);

		render(CsvExportButton, { jobId: 1 });

		const button = screen.getByRole('button', { name: /export.*csv/i });
		fireEvent.click(button);

		await waitFor(() => {
			expect(screen.getByRole('button')).toBeDisabled();
		});

		// Resolve the promise
		resolveExport!('csv,data');

		await waitFor(() => {
			expect(screen.getByRole('button')).not.toBeDisabled();
		});
	});

	it('shows error message on export failure', async () => {
		vi.mocked(results.exportCSV).mockRejectedValue(new Error('Export failed'));

		render(CsvExportButton, { jobId: 1 });

		const button = screen.getByRole('button', { name: /export.*csv/i });
		await fireEvent.click(button);

		await waitFor(() => {
			expect(screen.getByText(/export failed/i)).toBeInTheDocument();
		});
	});
});
