export interface VoterListUploadResponse {
	message: string;
	filePath: string;
	rowCount: number;
	importedCount: number | null;
}

export interface PetitionUploadResponse {
	message: string;
	scanId: number;
	cropCount: number;
}
