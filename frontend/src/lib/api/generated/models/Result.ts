export interface MatchPrediction {
	rank: number;
	voter_name: string;
	voter_address: string;
	similarity_score: number;
	confidence: "HIGH" | "MEDIUM" | "LOW";
}

export interface ResultResponse {
	ocr_result_id: number;
	extracted_text: string;
	crop_id: number;
	predictions: MatchPrediction[];
}

export interface ResultListResponse {
	results: ResultResponse[];
	total: number;
	page: number;
	page_size: number;
}
