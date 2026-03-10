import { writable } from 'svelte/store';
import { getApiClient } from './api-client';

export interface PrebakedSession {
	id: string;
	name: string;
	description: string;
}

interface DemoState {
	showResetConfirmation: boolean;
	resetting: boolean;
	loading: boolean;
	error: string | null;
	prebakedSessions: PrebakedSession[];
}

let _demoModeEnabled = false;

export function setDemoMode(enabled: boolean): void {
	_demoModeEnabled = enabled;
}

export function isDemoModeEnabled(): boolean {
	return _demoModeEnabled;
}

function createDemoStore() {
	const { subscribe, set, update } = writable<DemoState>({
		showResetConfirmation: false,
		resetting: false,
		loading: false,
		error: null,
		prebakedSessions: []
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
					showResetConfirmation: false
				}));
			} catch (error) {
				const message = error instanceof Error ? error.message : 'Unknown error';
				update((s) => ({ ...s, error: message, resetting: false }));
			}
		},

		async loadPrebaked(sessionId: string): Promise<Record<string, unknown>> {
			update((s) => ({ ...s, loading: true, error: null }));

			try {
				const response = await fetchWithAuth(`/demo/sessions/${sessionId}/load`, {
					method: 'POST'
				});
				const session = await response.json();
				update((s) => ({ ...s, loading: false }));
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
					prebakedSessions: data.sessions || [],
					loading: false
				}));
			} catch (error) {
				const message = error instanceof Error ? error.message : 'Unknown error';
				update((s) => ({ ...s, error: message, loading: false, prebakedSessions: [] }));
			}
		},

		clearError() {
			update((s) => ({ ...s, error: null }));
		},

		resetStore() {
			set({
				showResetConfirmation: false,
				resetting: false,
				loading: false,
				error: null,
				prebakedSessions: []
			});
		}
	};
}

export const demo = createDemoStore();

export function resetDemoStore() {
	demo.resetStore();
}
