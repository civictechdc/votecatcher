//OCR Matching
export enum MatchJobStatus {
	PENDING = 'pending',
	IN_PROGRESS = 'in_progress',
	COMPLETED = 'completed',
	FAILED = 'failed',
	EXPIRED = 'expired',
	CANCELLED = 'cancelled'
}

export interface MatchingProgressResponse {
	campaign_id: string;
	started_at: Date;
	ocr_job_id: string;
	ocr_provider: string;
	last_updated_at?: Date;
	ended_at?: Date;
	failure_reason?: string;
	job_status: MatchJobStatus;
}

//OCR Results
export interface OcrMatchValueItem {
	value: string;
	column_idx: number;
	data_type: string;
}

export interface OcrMatchColumnSpec {
	name: string;
	position_idx: number;
	data_type: string;
}

export interface OcrMatchRow {
	row_idx: number;
	values: Array<OcrMatchValueItem>;
}

export interface OcrMatchResults {
	column_data: Array<OcrMatchColumnSpec>;
	result_data: Array<OcrMatchRow>;
}
