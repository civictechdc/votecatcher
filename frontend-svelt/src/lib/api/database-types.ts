export type DatabaseType = 'sqlite' | 'postgres' | 'supabase';

export interface DatabaseStatus {
	configured: boolean;
	type: DatabaseType;
	connected: boolean;
	message: string;
}

export interface SupabaseCredentials {
	project_url: string;
	service_key: string;
	db_password: string;
}

export interface ConnectionTestResult {
	success: boolean;
	message: string;
	project_ref?: string;
}

export interface ProvisionResult {
	success: boolean;
	message: string;
	tables_created?: string[];
}
