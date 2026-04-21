export interface MatchPrediction {
	rank: number;
	voterName: string;
	voterAddress: string;
	similarityScore: number;
	confidence: "HIGH" | "MEDIUM" | "LOW";
}

export interface ResultResponse {
	ocrResultId: number;
	extractedText: string;
	cropId: number;
	predictions: MatchPrediction[];
}

export interface ResultsListResponse {
	results: ResultResponse[];
	total: number;
	pageSize: number;
	nextCursor: number | null;
}
