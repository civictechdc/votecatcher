import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/svelte';
import Page from './+page.svelte';
import { jobs } from '$lib/stores/jobs';
import { goto } from '$app/navigation';

vi.mock('$lib/stores/jobs');
vi.mock('$app/navigation', () => ({
	goto: vi.fn()
}));

vi.mock('$app/stores', () => ({
	page: {
		subscribe: vi.fn((fn) => {
			fn({ params: { id: 'job-1' } });
			return () => {};
		})
	}
}));

describe('Job Status Page', () => {
	beforeEach(() => {
		vi.clearAllMocks();

		vi.mocked(jobs.subscribe).mockImplementation((fn: any) => {
			fn({
				currentJob: {
					id: 1,
					campaignId: 1,
					status: 'OCR_STARTED',
					progress: 50,
					createdAt: new Date('2024-01-01T00:00:00Z')
				},
				loading: false,
				error: null,
				sse: { connected: true, reconnectAttempts: 0, error: null }
			});
			return () => {};
		});
	});

	it('displays job status', () => {
		render(Page);

		expect(screen.getByText(/ocr started/i)).toBeInTheDocument();
		expect(screen.getByText(/50%/)).toBeInTheDocument();
	});

	it('shows progress bar', () => {
		render(Page);

		const progressBar = screen.getByRole('progressbar');
		expect(progressBar).toHaveAttribute('aria-valuenow', '50');
	});

	it('displays cancel button for active job', () => {
		render(Page);

		expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
	});

	it('hides cancel button for completed job', async () => {
		vi.mocked(jobs.subscribe).mockImplementation((fn: any) => {
			fn({
				currentJob: {
					id: 1,
					campaignId: 1,
					status: 'MATCHING_COMPLETED',
					progress: 100,
					createdAt: new Date('2024-01-01T00:00:00Z')
				},
				loading: false,
				error: null,
				sse: { connected: false, reconnectAttempts: 0, error: null }
			});
			return () => {};
		});

		render(Page);

		expect(screen.queryByRole('button', { name: /cancel/i })).not.toBeInTheDocument();
	});

	it('shows SSE connection status', () => {
		render(Page);

		expect(screen.getByText(/connected/i)).toBeInTheDocument();
	});

	it('displays error state', () => {
		vi.mocked(jobs.subscribe).mockImplementation((fn: any) => {
			fn({
				currentJob: null,
				loading: false,
				error: 'Job not found',
				sse: { connected: false, reconnectAttempts: 0, error: null }
			});
			return () => {};
		});

		render(Page);

		expect(screen.getByText(/job not found/i)).toBeInTheDocument();
	});

	it('calls cancel when button clicked', async () => {
		vi.mocked(jobs.cancel).mockResolvedValue({
			id: 1,
			campaignId: 1,
			status: 'CANCELLED',
			createdAt: new Date()
		} as any);

		render(Page);

		const cancelButton = screen.getByRole('button', { name: /cancel/i });
		cancelButton.click();

		await waitFor(() => {
			expect(jobs.cancel).toHaveBeenCalledWith(1);
		});
	});
});
