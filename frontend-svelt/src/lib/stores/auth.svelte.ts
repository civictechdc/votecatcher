import { browser } from '$app/environment';

import { PUBLIC_API_URL } from '$env/static/public';
const _BASE_URL = PUBLIC_API_URL ?? '';

export interface UserSession {
	accessToken: string;
	refreshToken: string;
	isAuthenticated: boolean;
	email: string;
	id: string;
}

const defaultUnauthenticatedSession: UserSession = {
	accessToken: '',
	refreshToken: '',
	isAuthenticated: false,
	email: '',
	id: '',
};

export let authStore: UserSession = $state(defaultUnauthenticatedSession);

export async function logout() {
	authStore = defaultUnauthenticatedSession;
}

/**
 * A custom fetch wrapper that handles token injection and automatic refreshing.
 */
export async function authenticatedFetch(
	url: string | URL,
	options: RequestInit & { headers?: Record<string, string> } = {}
) {
	const currentToken = authStore.accessToken;

	const headers: Record<string, string> = {
		...(options.headers as Record<string, string> | undefined),
	};

	// 1. Inject the current access token
	if (currentToken) {
		headers['Authorization'] = `Bearer ${currentToken}`;
	}

	// 2. Make the original request
	let response = await fetch(url, { ...options, headers });

	// 3. Handle 401 Unauthorized (expired access token)
	if (response.status === 401 && browser) {
		console.log('Access token expired. Attempting to refresh...');

		// Ensure the refresh call includes credentials to send the HttpOnly cookie
		const refreshResponse = await fetch('http://localhost:8000/api/refresh-token', {
			method: 'POST',
			credentials: 'include',
		});

		if (refreshResponse.ok) {
			const refreshData = await refreshResponse.json();
			const newAccessToken = refreshData.access_token;

			// Update the Svelte store reactivity
			authStore.accessToken = newAccessToken;

			// 4. Retry the original failed request with the new token
			headers['Authorization'] = `Bearer ${newAccessToken}`;
			response = await fetch(url, { ...options, headers });

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
