import { writable } from 'svelte/store';
import { getApiClient } from './api-client';
import { PUBLIC_API_URL } from '$env/static/public';

export interface UploadResult {
	scan_id: string;
	crop_count: number;
}

export interface UploadsState {
	voterListUploading: boolean;
	voterListSuccess: boolean;
	voterListError: string | null;
	petitionUploading: boolean;
	petitionError: string | null;
	lastUploadResult: UploadResult | null;
}

function createUploadsStore() {
	const { subscribe, set, update } = writable<UploadsState>({
		voterListUploading: false,
		voterListSuccess: false,
		voterListError: null,
		petitionUploading: false,
		petitionError: null,
		lastUploadResult: null
	});

	return {
		subscribe,

		async uploadVoterList(file: File): Promise<void> {
			update(s => ({
				...s,
				voterListUploading: true,
				voterListSuccess: false,
				voterListError: null
			}));

			try {
				const formData = new FormData();
				formData.append('file', file);

				const response = await fetch(`${PUBLIC_API_URL || 'http://localhost:8000'}/api/upload/voter-list`, {
					method: 'POST',
					body: formData
				});

				if (!response.ok) {
					const errorData = await response.json().catch(() => ({}));
					throw new Error(errorData.detail || `Upload failed: ${response.statusText}`);
				}

				update(s => ({
					...s,
					voterListUploading: false,
					voterListSuccess: true
				}));
			} catch (error) {
				const message = error instanceof Error ? error.message : 'Unknown error';
				update(s => ({
					...s,
					voterListUploading: false,
					voterListError: message
				}));
			}
		},

		async uploadPetition(file: File, campaignId: string): Promise<UploadResult | null> {
			update(s => ({
				...s,
				petitionUploading: true,
				petitionError: null
			}));

			try {
				const formData = new FormData();
				formData.append('file', file);
				formData.append('campaign_id', campaignId);

				const response = await fetch(`${PUBLIC_API_URL || 'http://localhost:8000'}/api/upload/petition`, {
					method: 'POST',
					body: formData
				});

				if (!response.ok) {
					const errorData = await response.json().catch(() => ({}));
					throw new Error(errorData.detail || `Upload failed: ${response.statusText}`);
				}

				const result = await response.json() as UploadResult;

				update(s => ({
					...s,
					petitionUploading: false,
					lastUploadResult: result
				}));

				return result;
			} catch (error) {
				const message = error instanceof Error ? error.message : 'Unknown error';
				update(s => ({
					...s,
					petitionUploading: false,
					petitionError: message
				}));
				throw error;
			}
		},

		clearErrors() {
			update(s => ({
				...s,
				voterListError: null,
				petitionError: null
			}));
		},

		clearSuccess() {
			update(s => ({
				...s,
				voterListSuccess: false,
				lastUploadResult: null
			}));
		},

		reset() {
			set({
				voterListUploading: false,
				voterListSuccess: false,
				voterListError: null,
				petitionUploading: false,
				petitionError: null,
				lastUploadResult: null
			});
		}
	};
}

export const uploads = createUploadsStore();

export function resetUploadsStore() {
	uploads.reset();
}
