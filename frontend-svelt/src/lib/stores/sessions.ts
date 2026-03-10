import { writable } from 'svelte/store';
import { getApiClient } from './api-client';

export interface Session {
	id: number;
	name: string;
	campaign_id: string | null;
	session_type: 'REAL' | 'DEMO';
	snapshot_data: Record<string, unknown>;
	created_at: string;
	updated_at: string;
}

interface SessionsState {
	sessions: Session[];
	currentSession: Session | null;
	loading: boolean;
	saving: boolean;
	error: string | null;
}

function createSessionsStore() {
	const { subscribe, set, update } = writable<SessionsState>({
		sessions: [],
		currentSession: null,
		loading: false,
		saving: false,
		error: null
	});

	async function fetchWithAuth(url: string, options?: RequestInit) {
		const client = getApiClient();
		const baseUrl = client.basePath;
		const response = await fetch(`${baseUrl}${url}`, {
			...options,
			headers: {
				'Content-Type': 'application/json',
				...options?.headers
			}
		});
		if (!response.ok) {
			const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
			throw new Error(error.detail || `HTTP ${response.status}`);
		}
		return response;
	}

	return {
		subscribe,

		async fetchAll() {
			update((s) => ({ ...s, loading: true, error: null }));

			try {
				const response = await fetchWithAuth('/sessions');
				const data = await response.json();
				update((s) => ({ ...s, sessions: data.sessions, loading: false }));
			} catch (error) {
				const message = error instanceof Error ? error.message : 'Unknown error';
				update((s) => ({ ...s, error: message, loading: false, sessions: [] }));
			}
		},

		async save(name: string, snapshotData: Record<string, unknown>, campaignId?: string): Promise<Session> {
			update((s) => ({ ...s, saving: true, error: null }));

			try {
				const response = await fetchWithAuth('/sessions', {
					method: 'POST',
					body: JSON.stringify({
						name,
						campaign_id: campaignId || null,
						snapshot_data: snapshotData,
						session_type: 'REAL'
					})
				});
				const newSession = await response.json();
				update((s) => ({
					...s,
					sessions: [...s.sessions, newSession],
					currentSession: newSession,
					saving: false
				}));
				return newSession;
			} catch (error) {
				const message = error instanceof Error ? error.message : 'Unknown error';
				update((s) => ({ ...s, error: message, saving: false }));
				throw error;
			}
		},

		async load(sessionId: number): Promise<Session> {
			update((s) => ({ ...s, loading: true, error: null }));

			try {
				const response = await fetchWithAuth(`/sessions/${sessionId}`);
				const session = await response.json();
				update((s) => ({ ...s, currentSession: session, loading: false }));
				return session;
			} catch (error) {
				const message = error instanceof Error ? error.message : 'Unknown error';
				update((s) => ({ ...s, error: message, loading: false }));
				throw error;
			}
		},

		async delete(sessionId: number): Promise<void> {
			update((s) => ({ ...s, loading: true, error: null }));

			try {
				await fetchWithAuth(`/sessions/${sessionId}`, { method: 'DELETE' });
				update((s) => ({
					...s,
					sessions: s.sessions.filter((s) => s.id !== sessionId),
					currentSession: s.currentSession?.id === sessionId ? null : s.currentSession,
					loading: false
				}));
			} catch (error) {
				const message = error instanceof Error ? error.message : 'Unknown error';
				update((s) => ({ ...s, error: message, loading: false }));
				throw error;
			}
		},

		async export(sessionId: number): Promise<void> {
			try {
				const client = getApiClient();
				const baseUrl = client.basePath;
				const response = await fetch(`${baseUrl}/sessions/${sessionId}/export`);

				if (!response.ok) {
					throw new Error('Export failed');
				}

				const blob = await response.blob();
				const contentDisposition = response.headers.get('Content-Disposition');
				const filenameMatch = contentDisposition?.match(/filename="(.+)"/);
				const filename = filenameMatch?.[1] || `session_${sessionId}.zip`;

				const url = URL.createObjectURL(blob);
				const a = document.createElement('a');
				a.href = url;
				a.download = filename;
				document.body.appendChild(a);
				a.click();
				document.body.removeChild(a);
				URL.revokeObjectURL(url);
			} catch (error) {
				const message = error instanceof Error ? error.message : 'Export failed';
				update((s) => ({ ...s, error: message }));
				throw error;
			}
		},

		clearCurrentSession() {
			update((s) => ({ ...s, currentSession: null }));
		},

		clearError() {
			update((s) => ({ ...s, error: null }));
		},

		reset() {
			set({ sessions: [], currentSession: null, loading: false, saving: false, error: null });
		}
	};
}

export const sessions = createSessionsStore();

export function resetSessionsStore() {
	sessions.reset();
}
