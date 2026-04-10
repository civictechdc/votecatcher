export interface SessionResponse {
	id: number;
	name: string;
	campaignId: string | null;
	sessionType: string;
	snapshotData: Record<string, unknown>;
	createdAt: string | Date;
	updatedAt: string | Date;
}

export interface SessionListResponse {
	sessions: SessionResponse[];
	total: number;
}

export interface CreateSessionRequest {
	name: string;
	campaignId?: string | null;
	snapshotData?: Record<string, unknown>;
	sessionType?: string;
}
