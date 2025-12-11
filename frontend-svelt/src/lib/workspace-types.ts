export interface VoterList {
	fileName?: string;
}

export interface UploadFileMeta {
	id: string;
	name: string;
	size: number;
}

export interface UploadResult {
	success: boolean;
	message?: string;
	files?: UploadFileMeta[];
}

export enum MatchValueFormatKeys {
	MATCH_SCORE = 'match_score'
}

export type MatchValueTypes = string | number | boolean | null;
export interface MatchRow {
	row_idx: number;
	// A row value could be a set of the following configurations
	[key: string]: MatchValueTypes;
}

export interface MatchResults {
	matchColumns: MatchColumn[];
	matchRecords: MatchRow[];
	timestamp: string;
}

export class MatchColumn {
	public readonly name: string;
	public readonly sort?: (first: MatchRow, second: MatchRow) => number;
	public readonly isSortable: boolean;

	//TODO have sorting factories and selector?
	constructor(name: string, sort?: (first: MatchRow, second: MatchRow) => number) {
		this.name = name;
		this.sort = sort;
		this.isSortable = typeof sort !== 'undefined';
	}
}

export interface OcrProvider {
	provider_name: string;
	model_name: string;
	api_key: string;
}

export interface ConfidenceThresholds {
	high: number; // e.g. 0.8
	medium: number; // e.g. 0.5
}
