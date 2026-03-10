import { describe, it, expect, vi, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import { jobs, resetJobsStore } from './jobs';
import type { Job } from '$lib/api/generated';

const mockCreateJob = vi.fn();
const mockGetJob = vi.fn();
const mockCancelJob = vi.fn();

vi.mock('$lib/api/generated', () => {
	return {
		JobsApi: class {
			createJob = mockCreateJob;
			getJob = mockGetJob;
			cancelJob = mockCancelJob;
		}
	};
});

describe('Jobs Store', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockCreateJob.mockReset();
		mockGetJob.mockReset();
		mockCancelJob.mockReset();
		resetJobsStore();
	});

	describe('create', () => {
		it('creates a new job', async () => {
			const mockJob: Job = {
				id: 1,
				campaignId: 1,
				status: 'NOT_STARTED',
				createdAt: new Date('2024-01-01T00:00:00Z')
			};

			mockCreateJob.mockResolvedValue(mockJob);

			const result = await jobs.create({
				campaignId: 1,
				petitionScanIds: [1]
			});

			expect(result).toEqual(mockJob);
			expect(mockCreateJob).toHaveBeenCalledWith({
				createJob: { campaignId: 1, petitionScanIds: [1] }
			});
		});

		it('handles creation errors', async () => {
			mockCreateJob.mockRejectedValue(new Error('Invalid campaign'));

			await expect(
				jobs.create({
					campaignId: 999,
					petitionScanIds: []
				})
			).rejects.toThrow('Invalid campaign');
		});
	});

	describe('fetch', () => {
		it('fetches job status', async () => {
			const mockJob: Job = {
				id: 1,
				campaignId: 1,
				status: 'OCR_STARTED',
				createdAt: new Date('2024-01-01T00:00:00Z')
			};

			mockGetJob.mockResolvedValue(mockJob);

			await jobs.fetch(1);

			const state = get(jobs);
			expect(state.currentJob).toEqual(mockJob);
			expect(mockGetJob).toHaveBeenCalledWith({ jobId: 1 });
		});
	});

	describe('cancel', () => {
		it('cancels a running job', async () => {
			const mockJob: Job = {
				id: 1,
				campaignId: 1,
				status: 'OCR_PENDING',
				createdAt: new Date('2024-01-01T00:00:00Z')
			};

			mockCancelJob.mockResolvedValue(mockJob);

			await jobs.cancel(1);

			expect(mockCancelJob).toHaveBeenCalledWith({ jobId: 1 });
		});
	});
});
