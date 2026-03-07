// Centralized auth store for UI and tests.
// Methods are thin wrappers around authApi, and state updates are deterministic for tests.

import { writable } from 'svelte/store';
import { authApi } from '$lib/api/auth';

export type User = { id: string; email?: string } | null;

export const initialAuthState = {
	user: null as User,
	loading: false,
	error: null as string | null,
	twoFactorRequired: false,
};

function createAuthStore() {
	const { subscribe, update, set } = writable({ ...initialAuthState });

	return {
		subscribe,
		reset: () => set({ ...initialAuthState }),
		setLoading: (v: boolean) => update((s) => ({ ...s, loading: v })),
		setError: (msg: string | null) => update((s) => ({ ...s, error: msg })),

		// Query server for session (used on app startup)
		initSession: async () => {
			update((s) => ({ ...s, loading: true, error: null }));
			const res = await authApi.getSession();
			if (res.ok) {
				// @ts-expect-error
				update((s) => ({ ...s, user: (res.data as any).user ?? null, loading: false }));
			} else {
				update((s) => ({ ...s, user: null, loading: false }));
			}
		},

		signUp: async (email: string, password: string) => {
			update((s) => ({ ...s, loading: true, error: null }));
			const res = await authApi.signUp(email, password);
			if (!res.ok) {
				update((s) => ({ ...s, loading: false, error: res.error }));
				return { ok: false, error: res.error };
			}
			// Mock flow: many systems require email verification. Backend should reflect that.
			update((s) => ({ ...s, loading: false }));
			return { ok: true };
		},

		signIn: async (email: string, password: string) => {
			update((s) => ({ ...s, loading: true, error: null }));
			const res = await authApi.signIn(email, password);
			if (!res.ok) {
				update((s) => ({ ...s, loading: false, error: res.error }));
				return { ok: false, error: res.error };
			}
			// @ts-expect-error
			const user = (res.data as any).user ?? null;
			update((s) => ({
				...s,
				user,
				loading: false,
				error: null,
				twoFactorRequired: !!(res.data as any).twoFactorRequired,
			}));
			return { ok: true };
		},

		signOut: async () => {
			update((s) => ({ ...s, loading: true }));
			await authApi.signOut();
			set({ ...initialAuthState });
		},

		start2fa: async (email: string) => {
			update((s) => ({ ...s, loading: true }));
			const res = await authApi.start2fa(email);
			update((s) => ({ ...s, loading: false }));
			return res;
		},

		verify2fa: async (email: string, code: string) => {
			update((s) => ({ ...s, loading: true }));
			const res = await authApi.verify2fa(email, code);
			if (res.ok) {
				// @ts-expect-error
				update((s) => ({
					...s,
					user: (res.data as any).user ?? null,
					loading: false,
					twoFactorRequired: false,
				}));
			} else {
				update((s) => ({ ...s, loading: false, error: res.error }));
			}
			return res;
		},
	};
}

export const auth = createAuthStore();
