import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { get } from 'svelte/store';
import { uploads, resetUploadsStore } from './uploads';

describe('Uploads Store', () => {
	let mockFetch: ReturnType<typeof vi.fn>;

	beforeEach(() => {
		vi.clearAllMocks();
		resetUploadsStore();
		mockFetch = vi.fn();
		vi.stubGlobal('fetch', mockFetch);
	});

	afterEach(() => {
		vi.unstubAllGlobals();
	});

	describe('initial state', () => {
		it('starts with empty state', () => {
			const state = get(uploads);
			expect(state.voterListUploading).toBe(false);
			expect(state.voterListProgress).toBe(0);
			expect(state.voterListError).toBeNull();
			expect(state.petitionUploading).toBe(false);
			expect(state.petitionProgress).toBe(0);
			expect(state.petitionError).toBeNull();
			expect(state.lastUploadResult).toBeNull();
		});
	});

	describe('uploadVoterList', () => {
		it('sets uploading state and progress on start', async () => {
			mockFetch.mockImplementation(() => {
				return new Promise((resolve) => {
					setTimeout(() => resolve({
						ok: true,
						json: () => Promise.resolve({ success: true })
					}), 100);
				});
			});

			const promise = uploads.uploadVoterList(new File(['data'], 'voters.csv'));

			let state = get(uploads);
			expect(state.voterListUploading).toBe(true);

			await promise;

			state = get(uploads);
			expect(state.voterListUploading).toBe(false);
			expect(state.voterListProgress).toBe(100);
		});

		it('handles upload errors', async () => {
			mockFetch.mockResolvedValue({
				ok: false,
				statusText: 'Bad Request',
				json: () => Promise.resolve({ detail: 'Invalid CSV format' })
			});

			await uploads.uploadVoterList(new File(['bad'], 'bad.csv'));

			const state = get(uploads);
			expect(state.voterListError).toBe('Invalid CSV format');
			expect(state.voterListUploading).toBe(false);
		});

		it('clears previous error on new upload', async () => {
			mockFetch
				.mockResolvedValueOnce({
					ok: false,
					statusText: 'Bad Request',
					json: () => Promise.resolve({ detail: 'First error' })
				})
				.mockResolvedValueOnce({
					ok: true,
					json: () => Promise.resolve({ success: true })
				});

			await uploads.uploadVoterList(new File(['bad'], 'bad.csv'));
			expect(get(uploads).voterListError).toBe('First error');

			await uploads.uploadVoterList(new File(['good'], 'good.csv'));
			expect(get(uploads).voterListError).toBeNull();
		});
	});

	describe('uploadPetition', () => {
		it('uploads petition with progress tracking', async () => {
			mockFetch.mockResolvedValue({
				ok: true,
				json: () => Promise.resolve({ scan_id: 'scan-1', crop_count: 10 })
			});

			const result = await uploads.uploadPetition(
				new File(['pdf'], 'petition.pdf'),
				'campaign-1'
			);

			expect(result?.scan_id).toBe('scan-1');
			expect(result?.crop_count).toBe(10);

			const state = get(uploads);
			expect(state.petitionUploading).toBe(false);
			expect(state.petitionProgress).toBe(100);
		});

		it('handles petition upload errors', async () => {
			mockFetch.mockResolvedValue({
				ok: false,
				statusText: 'Bad Request',
				json: () => Promise.resolve({ detail: 'Invalid PDF' })
			});

			await expect(
				uploads.uploadPetition(new File(['bad'], 'bad.pdf'), 'campaign-1')
			).rejects.toThrow('Invalid PDF');

			const state = get(uploads);
			expect(state.petitionError).toBe('Invalid PDF');
		});

		it('stores last upload result', async () => {
			mockFetch.mockResolvedValue({
				ok: true,
				json: () => Promise.resolve({ scan_id: 'scan-2', crop_count: 25 })
			});

			await uploads.uploadPetition(new File(['pdf'], 'petition.pdf'), 'campaign-1');

			const state = get(uploads);
			expect(state.lastUploadResult).toEqual({
				scan_id: 'scan-2',
				crop_count: 25
			});
		});
	});

	describe('clearErrors', () => {
		it('clears all errors', async () => {
			mockFetch
				.mockResolvedValueOnce({
					ok: false,
					json: () => Promise.resolve({ detail: 'Voter error' })
				})
				.mockResolvedValueOnce({
					ok: false,
					json: () => Promise.resolve({ detail: 'Petition error' })
				});

			await uploads.uploadVoterList(new File(['bad'], 'bad.csv'));
			await uploads.uploadPetition(new File(['bad'], 'bad.pdf'), 'camp-1').catch(() => {});

			expect(get(uploads).voterListError).toBe('Voter error');
			expect(get(uploads).petitionError).toBe('Petition error');

			uploads.clearErrors();

			expect(get(uploads).voterListError).toBeNull();
			expect(get(uploads).petitionError).toBeNull();
		});
	});

	describe('reset', () => {
		it('resets store to initial state', async () => {
			mockFetch.mockResolvedValue({
				ok: true,
				json: () => Promise.resolve({ scan_id: 'scan-1', crop_count: 10 })
			});

			await uploads.uploadPetition(new File(['pdf'], 'petition.pdf'), 'campaign-1');

			expect(get(uploads).lastUploadResult).not.toBeNull();

			uploads.reset();

			const state = get(uploads);
			expect(state.voterListUploading).toBe(false);
			expect(state.voterListProgress).toBe(0);
			expect(state.voterListError).toBeNull();
			expect(state.petitionUploading).toBe(false);
			expect(state.petitionProgress).toBe(0);
			expect(state.petitionError).toBeNull();
			expect(state.lastUploadResult).toBeNull();
		});
	});
});
