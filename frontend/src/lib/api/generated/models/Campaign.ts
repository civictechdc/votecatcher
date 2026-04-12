export interface CampaignResponse {
	id: string;
	uniqueName: string;
	title: string;
	year: string;
	region: string | null;
	regionId: string | null;
	createdAt: string | Date | null;
	updatedAt: string | Date | null;
}

export interface CampaignListResponse {
	campaigns: CampaignResponse[];
	total: number;
}

export interface CreateCampaignRequest {
	name: string;
	year: number;
	region?: string;
}

export interface CampaignMetricsResponse {
	totalSignatures: number;
	processed: number;
	highConfidence: number;
	lastJob: LastJobInfo | null;
}

export interface LastJobInfo {
	jobId: number;
	status: string;
	startedAt: string | Date | null;
	endedAt: string | Date | null;
}

export interface PetitionScanResponse {
	id: number;
	originalFilename: string;
	pageCount: number | null;
	createdAt: string | Date | null;
}

export interface PetitionScanListResponse {
	scans: PetitionScanResponse[];
	total: number;
}

export interface SetupStatusResponse {
	voterList: VoterListStatus;
	petitions: PetitionsStatus;
	jobs: JobsStatus;
	state: "empty" | "voter_only" | "petitions_only" | "ready_to_process" | "has_jobs";
}

export interface VoterListStatus {
	exists: boolean;
	rowCount: number | null;
	uploadedAt: string | null;
	regionName: string | null;
}

export interface PetitionsStatus {
	exists: boolean;
	fileCount: number;
	signatureCount: number;
}

export interface JobsStatus {
	total: number;
	active: number;
}
