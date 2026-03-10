import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import Page from './+page.svelte';

const mockUploadPetition = vi.fn();
const mockClearErrors = vi.fn();
const mockFetchAll = vi.fn();

let uploadsState: {
	voterListUploading: boolean;
	voterListProgress: number;
	voterListError: string | null;
	petitionUploading: boolean;
	petitionProgress: number;
	petitionError: string | null;
	lastUploadResult: { scan_id: string; crop_count: number } | null;
} = {
	voterListUploading: false,
	voterListProgress: 0,
	voterListError: null,
	petitionUploading: false,
	petitionProgress: 0,
	petitionError: null,
	lastUploadResult: null
};

let campaignsState = {
	campaigns: [
		{ id: 1, name: 'DC 2024', year: 2024, regionId: 1, createdAt: '2024-01-01' },
		{ id: 2, name: 'MD 2024', year: 2024, regionId: 2, createdAt: '2024-01-01' }
	],
	loading: false,
	error: null
};

vi.mock('$lib/stores/uploads', () => ({
	uploads: {
		subscribe: (callback: (value: any) => void) => {
			callback(uploadsState);
			return () => {};
		},
		uploadPetition: mockUploadPetition,
		clearErrors: mockClearErrors
	}
}));

vi.mock('$lib/stores/campaigns', () => ({
	campaigns: {
		subscribe: (callback: (value: any) => void) => {
			callback(campaignsState);
			return () => {};
		},
		fetchAll: mockFetchAll
	}
}));

describe('Petition Upload Page', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		uploadsState = {
			voterListUploading: false,
			voterListProgress: 0,
			voterListError: null,
			petitionUploading: false,
			petitionProgress: 0,
			petitionError: null,
			lastUploadResult: null
		};
		campaignsState = {
			campaigns: [
				{ id: 1, name: 'DC 2024', year: 2024, regionId: 1, createdAt: '2024-01-01' },
				{ id: 2, name: 'MD 2024', year: 2024, regionId: 2, createdAt: '2024-01-01' }
			],
			loading: false,
			error: null
		};
	});

	it('displays campaign selector', () => {
		render(Page);
		expect(screen.getByLabelText(/campaign/i)).toBeInTheDocument();
	});

	it('displays upload form', () => {
		render(Page);
		expect(screen.getByText(/upload petition/i)).toBeInTheDocument();
		expect(screen.getByLabelText(/file/i)).toBeInTheDocument();
	});

	it('shows drag and drop zone', () => {
		render(Page);
		expect(screen.getByText(/drag and drop/i)).toBeInTheDocument();
	});

	it('loads campaigns on mount', () => {
		render(Page);
		expect(mockFetchAll).toHaveBeenCalled();
	});

	it('calls uploadPetition with selected campaign ID', async () => {
		mockUploadPetition.mockResolvedValue({
			scan_id: 'scan-1',
			crop_count: 10
		});

		render(Page);

		const file = new File(['pdf content'], 'petition.pdf', { type: 'application/pdf' });
		const input = screen.getByLabelText(/file/i) as HTMLInputElement;

		await fireEvent.change(input, { target: { files: [file] } });

		await waitFor(() => {
			expect(mockUploadPetition).toHaveBeenCalledWith(file, '1');
		});
	});

	it('shows progress during upload', () => {
		uploadsState.petitionUploading = true;
		uploadsState.petitionProgress = 50;

		render(Page);

		expect(screen.getByText('50%')).toBeInTheDocument();
	});

	it('shows crop count after successful upload', () => {
		uploadsState.petitionProgress = 100;
		uploadsState.lastUploadResult = { scan_id: 'scan-1', crop_count: 10 };

		render(Page);

		expect(screen.getByText(/10.*signature/i)).toBeInTheDocument();
	});

	it('shows error state', () => {
		uploadsState.petitionError = 'Invalid PDF format';

		render(Page);

		expect(screen.getByText(/invalid pdf format/i)).toBeInTheDocument();
	});

	it('has retry button on error', async () => {
		uploadsState.petitionError = 'Upload failed';

		render(Page);

		const retryButton = screen.getByRole('button', { name: /try again/i });
		expect(retryButton).toBeInTheDocument();

		await fireEvent.click(retryButton);
		expect(mockClearErrors).toHaveBeenCalled();
	});

	it('disables upload when no campaign selected', () => {
		campaignsState.campaigns = [];

		render(Page);

		const fileInput = screen.getByLabelText(/file/i);
		expect(fileInput).toBeDisabled();
	});
});
