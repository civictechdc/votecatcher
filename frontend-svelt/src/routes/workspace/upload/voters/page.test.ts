import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import Page from './+page.svelte';

vi.mock('$lib/stores/uploads', () => ({
	uploads: {
		subscribe: (callback: (value: any) => void) => {
			callback({
				voterListUploading: false,
				voterListProgress: 0,
				voterListError: null,
				petitionUploading: false,
				petitionProgress: 0,
				petitionError: null,
				lastUploadResult: null
			});
			return () => {};
		},
		uploadVoterList: vi.fn(),
		clearErrors: vi.fn()
	}
}));

describe('Voter List Upload Page', () => {
	it('renders upload heading', () => {
		render(Page);
		expect(screen.getByRole('heading', { name: /upload voter list/i })).toBeInTheDocument();
	});

	it('shows drag and drop zone', () => {
		render(Page);
		expect(screen.getByText(/drag and drop/i)).toBeInTheDocument();
	});

	it('has file input', () => {
		render(Page);
		const input = screen.getByLabelText(/file/i);
		expect(input).toBeInTheDocument();
	});
});
