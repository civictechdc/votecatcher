export interface VoterListUploadResponse {
	message: string;
	file_path: string;
	row_count: number;
	imported_count: number | null;
}

export interface PetitionUploadResponse {
	message: string;
	scan_id: number;
	crop_count: number;
}
