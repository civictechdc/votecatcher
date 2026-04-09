export type JobStatusEnum =
	| "NOT_STARTED"
	| "OCR_PENDING"
	| "OCR_STARTED"
	| "OCR_COMPLETED"
	| "OCR_FAILED"
	| "OCR_TIMEOUT"
	| "MATCHING_PENDING"
	| "MATCHING"
	| "MATCHING_COMPLETED"
	| "MATCHING_ERROR"
	| "CANCELLED";

export interface JobResponse {
	jobId: number;
	status: JobStatusEnum;
	campaignId: string;
	campaignName?: string | null;
	providerName?: string | null;
	providerModel?: string | null;
	forceReprocess?: boolean;
	cachedOcrCount?: number | null;
	newOcrCount?: number | null;
	ocrDurationSeconds?: number | null;
	matchingDurationSeconds?: number | null;
	createdAt?: string | Date | null;
	updatedAt?: string | Date | null;
	startedAt?: string | Date | null;
	endedAt?: string | Date | null;
	errorMessage?: string | null;
	isOrphaned?: boolean;
	progress?: number;
}

export interface JobListResponse {
	jobs: JobResponse[];
	total: number;
}

export interface CreateJobRequest {
	campaignId: string;
	scanIds?: number[];
	providerName?: string | null;
	providerModel?: string | null;
	forceReprocess?: boolean;
}
