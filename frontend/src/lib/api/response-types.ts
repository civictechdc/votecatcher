//OCR Matching
export enum MatchJobStatus {
	NOT_STARTED = 'not started',
	PENDING = 'pending',
	OCR_PENDING = 'ocr_pending',
	OCR_IN_PROGRESS = 'ocr extract',
	MATCHING = 'matching',
	COMPLETED = 'completed',
	OCR_COMPLETED = 'ocr_completed',
	OCR_FAILED = 'ocr_failed',
	MATCHING_FAILED = 'matching failed',
	OCR_TIMED_OUT = 'ocr timed out',
	OCR_CANCELLED = 'ocr cancelled',
	CANCELLED = 'cancelled',
	TIMED_OUT = 'timed out',
	MISC_ERROR = 'error',
}

export interface MatchingProgressResponse {
	campaign_id: string;
	started_at: Date;
	task_id: string;
	ocr_provider: string;
	last_updated_at?: Date;
	ended_at?: Date;
	failure_reason?: string;
	job_status: MatchJobStatus;
}

//OCR Results
export interface MatchRowEntryResponse {
	value: string;
	column_idx: number;
	data_type: string;
}

export interface MatchColumnsResponse {
	name: string;
	position_idx: number;
	data_type: string;
}

export interface MatchRowsResponse {
	row_idx: number;
	values: MatchRowEntryResponse[];
}

export interface MatchMetaDataResponse {
	campaign_id: string;
	started_at: Date;
	completed_at?: Date;
	region: string;
	ocr_provider: string;
}

export interface MatchResultResponse {
	column_data: MatchColumnsResponse[];
	result_data: MatchRowsResponse[];
	page_idx: number;
	max_row_count: number;
	total_pages: number;
	metadata: MatchMetaDataResponse;
}

export interface MatchResponse {
	results: MatchResultResponse;
	stats: Record<string, unknown>;
}
