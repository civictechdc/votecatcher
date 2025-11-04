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

export interface OcrMatch {
	voterId: string;
	registeredName: string;
	registeredAddress: string;
	ocrPredictedName: string;
	predictionScore: number; // 0..1
	nameDistance?: number;
	predictedAddress?: string;
	addressDistance?: number;
	ward?: string;
	petitionPageNumber: number;
	petitionRowNumber: number;
	matchRank: number;
}

export interface MatchResults {
	matchColumns: MatchColumn[];
	matchRecords: OcrMatch[];
	timestamp: string;
}

export class MatchColumn {
	public readonly name: string;
	public readonly sort?: (first: OcrMatch, second: OcrMatch) => number;
	public readonly isSortable: boolean;

	constructor(name: string, sort?: (first: OcrMatch, second: OcrMatch) => number) {
		this.name = name;
		this.sort = sort;
		this.isSortable = typeof sort !== 'undefined';
	}
}

export interface ConfidenceThresholds {
	high: number; // e.g. 0.8
	medium: number; // e.g. 0.5
}
