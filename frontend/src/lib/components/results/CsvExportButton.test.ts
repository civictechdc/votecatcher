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
		vi.mocked(results.exportCSV).mockResolvedValue();

		// Mock URL.createObjectURL and anchor click
		const mockAnchor = { click: vi.fn(), href: '' };
		vi.spyOn(document, 'createElement').mockReturnValue(mockAnchor as unknown as HTMLElement);
		vi.stubGlobal('URL', {
			createObjectURL: vi.fn().mockReturnValue('blob:test-url'),
		});

		render(CsvExportButton, { jobId: 1 });

		const button = screen.getByRole('button', { name: /export.*csv/i });
		await fireEvent.click(button);

		await waitFor(() => {
			expect(results.exportCSV).toHaveBeenCalledWith(1);
		});

		vi.unstubAllGlobals();
	});

	it('shows loading state during export', async () => {
		let resolveExport: (() => void) | undefined;
		vi.mocked(results.exportCSV).mockImplementation(
			() =>
				new Promise<void>((resolve) => {
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
		resolveExport?.();

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
