export interface SessionResponse {
	id: number;
	name: string;
	campaign_id: string | null;
	session_type: string;
	snapshot_data: unknown;
	created_at: string | Date;
	updated_at: string | Date;
}
