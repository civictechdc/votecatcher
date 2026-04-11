import { describe, it, expect, vi, beforeEach } from "vitest";
import { get } from "svelte/store";
import { jobs, resetJobsStore } from "./jobs";
import type { JobResponse } from "$lib/api/generated";

const mockListJobs = vi.fn();
const mockCreateJob = vi.fn();
const mockGetJob = vi.fn();
const mockCancelJob = vi.fn();

vi.mock("$lib/api/generated", () => {
	return {
		JobsApi: class {
			listJobsJobsGet = mockListJobs;
			createJobJobsPost = mockCreateJob;
			getJobJobsJobIdGet = mockGetJob;
			cancelJobJobsJobIdCancelPost = mockCancelJob;
		},
	};
});

describe("Jobs Store", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockListJobs.mockReset();
		mockCreateJob.mockReset();
		mockGetJob.mockReset();
		mockCancelJob.mockReset();
		resetJobsStore();
	});

	describe("fetchAll", () => {
		it("starts with empty state", () => {
			const state = get(jobs);
			expect(state.jobs).toEqual([]);
			expect(state.loading).toBe(false);
			expect(state.error).toBeNull();
		});

		it("fetches jobs list", async () => {
			const mockJobs: JobResponse[] = [
				{
					jobId: 1,
					status: "MATCHING_COMPLETED",
					campaignId: "1",
				},
			];

			mockListJobs.mockResolvedValue({ jobs: mockJobs });

			await jobs.fetchAll();

			const state = get(jobs);
			expect(state.jobs).toEqual(mockJobs);
			expect(state.loading).toBe(false);
		});
	});

	describe("create", () => {
		it("creates a new job", async () => {
			const mockJob: JobResponse = {
				jobId: 1,
				status: "NOT_STARTED",
				campaignId: "1",
			};

			mockCreateJob.mockResolvedValue(mockJob);

			const result = await jobs.create({
				campaignId: "1",
				scanIds: [1],
			});

			expect(result).toEqual(mockJob);
		});

		it("handles creation errors", async () => {
			mockCreateJob.mockRejectedValue(new Error("Invalid campaign"));

			await expect(
				jobs.create({
					campaignId: "999",
					scanIds: [],
				}),
			).rejects.toThrow("Invalid campaign");
		});
	});

	describe("fetch", () => {
		it("fetches job status", async () => {
			const mockJob: JobResponse = {
				jobId: 1,
				status: "OCR_STARTED",
				campaignId: "1",
			};

			mockGetJob.mockResolvedValue(mockJob);

			await jobs.fetch(1);

			const state = get(jobs);
			expect(state.currentJob).toEqual(mockJob);
		});
	});

	describe("cancel", () => {
		it("cancels a running job", async () => {
			const mockJob: JobResponse = {
				jobId: 1,
				status: "OCR_PENDING",
				campaignId: "1",
			};

			mockCancelJob.mockResolvedValue(mockJob);

			await jobs.cancel(1);

			expect(mockCancelJob).toHaveBeenCalledWith({ jobId: 1 });
		});
	});

	describe("SSE Integration", () => {
		it("connects to job status stream", () => {
			const mockEventSource = {
				close: vi.fn(),
				onopen: null as (() => void) | null,
				onmessage: null as ((event: MessageEvent) => void) | null,
				onerror: null as (() => void) | null,
			};

			const EventSourceMock = vi.fn(function (this: typeof mockEventSource) {
				Object.assign(this, mockEventSource);
				return this;
			});

			vi.stubGlobal("EventSource", EventSourceMock);

			jobs.connectToJob("job-1");

			expect(EventSourceMock).toHaveBeenCalledWith(expect.stringContaining("/api/jobs/job-1/status"));

			vi.unstubAllGlobals();
		});

		it("disconnects cleanly", () => {
			const mockEventSource = {
				close: vi.fn(),
			};

			const EventSourceMock = vi.fn(function (this: typeof mockEventSource) {
				Object.assign(this, mockEventSource);
				return this;
			});

			vi.stubGlobal("EventSource", EventSourceMock);

			jobs.connectToJob("job-1");
			jobs.disconnect();

			expect(mockEventSource.close).toHaveBeenCalled();

			vi.unstubAllGlobals();
		});
	});
});
