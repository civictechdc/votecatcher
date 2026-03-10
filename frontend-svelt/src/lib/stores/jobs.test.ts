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

	describe('SSE Integration', () => {
		it('connects to job status stream', () => {
			const mockEventSource = {
				close: vi.fn(),
				onopen: null,
				onmessage: null,
				onerror: null
			};

			vi.stubGlobal('EventSource', vi.fn(() => mockEventSource));

			jobs.connectToJob('job-1');

			expect(EventSource).toHaveBeenCalledWith(expect.stringContaining('/api/jobs/job-1/status'));

			vi.unstubAllGlobals();
		});

		it('updates job state on SSE message', async () => {
			const mockEventSource = {
				close: vi.fn(),
				onopen: null as (() => void) | null,
				onmessage: null as ((event: MessageEvent) => void) | null,
				onerror: null as (() => void) | null
			};

			vi.stubGlobal('EventSource', vi.fn(() => mockEventSource));

			jobs.connectToJob('job-1');

			// Simulate SSE message
			const messageEvent = new MessageEvent('message', {
				data: JSON.stringify({
					event: 'status_update',
					data: { status: 'OCR_STARTED', progress: 25 }
				})
			});

			if (mockEventSource.onmessage) {
				mockEventSource.onmessage(messageEvent);
			}

			const state = get(jobs);
			expect(state.currentJob?.status).toBe('OCR_STARTED');

			vi.unstubAllGlobals();
		});

		it('reconnects on connection error', async () => {
			const mockEventSource = {
				close: vi.fn(),
				onopen: null as (() => void) | null,
				onmessage: null as ((event: MessageEvent) => void) | null,
				onerror: null as (() => void) | null
			};

			vi.stubGlobal('EventSource', vi.fn(() => mockEventSource));
			vi.useFakeTimers();

			jobs.connectToJob('job-1');

			// First connection attempt
			expect(EventSource).toHaveBeenCalledTimes(1);

			// Simulate error
			if (mockEventSource.onerror) {
				mockEventSource.onerror();
			}

			// Fast-forward to reconnect
			await vi.advanceTimersByTimeAsync(2000);

			// Should have reconnected
			expect(EventSource).toHaveBeenCalledTimes(2);

			vi.useRealTimers();
			vi.unstubAllGlobals();
		});

		it('disconnects cleanly', () => {
			const mockEventSource = {
				close: vi.fn()
			};

			vi.stubGlobal('EventSource', vi.fn(() => mockEventSource));

			jobs.connectToJob('job-1');
			jobs.disconnect();

			expect(mockEventSource.close).toHaveBeenCalled();

			vi.unstubAllGlobals();
		});
	});
});
