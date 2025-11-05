// Frontend fetch wrapper for auth-related REST endpoints.
// Replace base with your FastAPI /auth base URL by setting VITE_API_URL.
type ApiResult<T = unknown> = { ok: true; data: T } | { ok: false; error: string };

const BASE = (import.meta as any).env?.VITE_API_URL?.replace(/\/$/, '') ?? '';

async function post<T = unknown>(path: string, body: unknown): Promise<ApiResult<T>> {
	const url = BASE ? `${BASE}${path}` : path;
	try {
		const res = await fetch(url, {
			method: 'POST',
			credentials: 'include',
			headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
			body: JSON.stringify(body)
		});
		const json = await res.json().catch(() => ({}));
		if (!res.ok) return { ok: false, error: json?.error || res.statusText || 'request failed' };
		return { ok: true, data: json as T };
	} catch (err) {
		return { ok: false, error: err instanceof Error ? err.message : String(err) };
	}
}

async function get<T = unknown>(path: string): Promise<ApiResult<T>> {
	const url = BASE ? `${BASE}${path}` : path;
	try {
		const res = await fetch(url, {
			credentials: 'include',
			headers: { Accept: 'application/json' }
		});
		const json = await res.json().catch(() => ({}));
		if (!res.ok) return { ok: false, error: json?.error || res.statusText || 'request failed' };
		return { ok: true, data: json as T };
	} catch (err) {
		return { ok: false, error: err instanceof Error ? err.message : String(err) };
	}
}

export const authApi = {
	refreshSession: (refreshToken: string) => post('/api/refresh-session', { refreshToken }),
	getSession: () => get<{ user?: { id: string; email?: string } }>('/api/session'),
	signUp: (email: string, password: string) => post('/api/auth/sign-up', { email, password }),
	signIn: (email: string, password: string) => post('/api/auth/sign-in', { email, password }),
	signOut: () => post('/api/auth/sign-out', {}),
	// 2FA / Passkey endpoints (optional)
	start2fa: (email: string) => post('/api/auth/start-2fa', { email }),
	verify2fa: (email: string, code: string) => post('/api/auth/verify-2fa', { email, code })
};

// Convenience named export used by pages that import getSession directly
export const getSession = authApi.getSession;

import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export const authStore = writable({
	accessToken: null,
	isAuthenticated: false,
	userEmail: null
});

export async function logout() {
	// ... (logout logic remains the same) ...
}

/**
 * A custom fetch wrapper that handles token injection and automatic refreshing.
 */
export async function authenticatedFetch(url: string | URL, options = {}) {
	let currentToken = null;
	authStore.subscribe((value) => {
		currentToken = value.accessToken;
	})();

	// 1. Inject the current access token
	if (currentToken) {
		options.headers = {
			...options.headers,
			Authorization: `Bearer ${currentToken}`
		};
	}

	// 2. Make the original request
	let response = await fetch(url, options);

	// 3. Handle 401 Unauthorized (expired access token)
	if (response.status === 401 && browser) {
		console.log('Access token expired. Attempting to refresh...');

		// Ensure the refresh call includes credentials to send the HttpOnly cookie
		const refreshResponse = await fetch(`${BASE}api/refresh-token`, {
			method: 'POST',
			credentials: 'include'
		});

		if (refreshResponse.ok) {
			const refreshData = await refreshResponse.json();
			const newAccessToken = refreshData.access_token;

			// Update the Svelte store reactivity
			authStore.update((store) => ({
				...store,
				accessToken: newAccessToken,
				isAuthenticated: true
			}));

			// 4. Retry the original failed request with the new token
			options.headers['Authorization'] = `Bearer ${newAccessToken}`;
			response = await fetch(url, options);

			return response; // Return the successfully retried response
		} else {
			// Refresh failed (maybe refresh token expired too). Force logout.
			console.error('Refresh token failed. Logging out.');
			await logout();
			throw new Error('Session expired, please log in again.');
		}
	}

	return response;
}
