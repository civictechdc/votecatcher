import { writable } from 'svelte/store';
import { getApiClient } from './api-client';
import { PUBLIC_DEMO_MODE } from '$env/static/public';

export interface PrebakedSession {
	id: string;
	name: string;
	description: string;
}

export interface LoadedSessionInfo {
	success: boolean;
	session_id: string;
	message: string;
	campaign_id: string;
	voters_count: number;
	match_results_count: number;
}

interface DemoState {
	initialized: boolean;
	showResetConfirmation: boolean;
	resetting: boolean;
	loading: boolean;
	error: string | null;
	prebakedSessions: PrebakedSession[];
	loadedSession: LoadedSessionInfo | null;
}

let _demoModeEnabled = PUBLIC_DEMO_MODE === 'true';

export function setDemoMode(enabled: boolean): void {
	_demoModeEnabled = enabled;
}

export function isDemoModeEnabled(): boolean {
	return _demoModeEnabled;
}

function createDemoStore() {
	const { subscribe, set, update } = writable<DemoState>({
		initialized: false,
		showResetConfirmation: false,
		resetting: false,
		loading: false,
		error: null,
		prebakedSessions: [],
		loadedSession: null,
	});

	async function fetchWithAuth(url: string, options?: RequestInit) {
		const client = getApiClient();
		const baseUrl = client.basePath;
		const response = await fetch(`${baseUrl}${url}`, {
			...options,
			headers: {
				'Content-Type': 'application/json',
				...options?.headers,
			},
		});
		if (!response.ok) {
			const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
			throw new Error(error.detail || `HTTP ${response.status}`);
		}
		return response;
	}

	return {
		subscribe,

		confirmReset() {
			update((s) => ({ ...s, showResetConfirmation: true }));
		},

		cancelReset() {
			update((s) => ({ ...s, showResetConfirmation: false }));
		},

		async resetData(): Promise<void> {
			update((s) => ({ ...s, resetting: true, error: null }));

			try {
				await fetchWithAuth('/demo/reset', { method: 'POST' });
				update((s) => ({
					...s,
					resetting: false,
					showResetConfirmation: false,
				}));
			} catch (error) {
				const message = error instanceof Error ? error.message : 'Unknown error';
				update((s) => ({ ...s, error: message, resetting: false }));
			}
		},

		async loadPrebaked(sessionId: string): Promise<LoadedSessionInfo> {
			update((s) => ({ ...s, loading: true, error: null, loadedSession: null }));

			try {
				const response = await fetchWithAuth(`/demo/sessions/${sessionId}/load`, {
					method: 'POST',
				});
				const session: LoadedSessionInfo = await response.json();
				update((s) => ({ ...s, loading: false, loadedSession: session }));
				return session;
			} catch (error) {
				const message = error instanceof Error ? error.message : 'Unknown error';
				update((s) => ({ ...s, error: message, loading: false }));
				throw error;
			}
		},

		async fetchPrebakedSessions(): Promise<void> {
			update((s) => ({ ...s, loading: true, error: null }));

			try {
				const response = await fetchWithAuth('/demo/sessions');
				const data = await response.json();
				update((s) => ({
					...s,
					initialized: true,
					prebakedSessions: data.sessions || [],
					loading: false,
				}));
			} catch (error) {
				const message = error instanceof Error ? error.message : 'Unknown error';
				update((s) => ({
					...s,
					initialized: true,
					error: message,
					loading: false,
					prebakedSessions: [],
				}));
			}
		},

		clearError() {
			update((s) => ({ ...s, error: null }));
		},

		resetStore() {
			set({
				initialized: false,
				showResetConfirmation: false,
				resetting: false,
				loading: false,
				error: null,
				prebakedSessions: [],
				loadedSession: null,
			});
		},
	};
}

export const demo = createDemoStore();

export function resetDemoStore() {
	demo.resetStore();
}
