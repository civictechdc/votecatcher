import { browser } from "$app/environment";
import { API_BASE_URL } from "$lib/api/base-url";

export interface UserSession {
	accessToken: string;
	refreshToken: string;
	isAuthenticated: boolean;
	email: string;
	id: string;
}

const defaultUnauthenticatedSession: UserSession = {
	accessToken: "",
	refreshToken: "",
	isAuthenticated: false,
	email: "",
	id: "",
};

export let authStore: UserSession = $state(defaultUnauthenticatedSession);

export async function logout() {
	authStore = defaultUnauthenticatedSession;
}

export async function authenticatedFetch(
	url: string | URL,
	options: RequestInit & { headers?: Record<string, string> } = {},
) {
	const currentToken = authStore.accessToken;

	const headers: Record<string, string> = {
		...(options.headers as Record<string, string> | undefined),
	};

	if (currentToken) {
		headers["Authorization"] = `Bearer ${currentToken}`;
	}

	let response = await fetch(url, { ...options, headers });

	if (response.status === 401 && browser) {
		const refreshResponse = await fetch(`${API_BASE_URL}/api/refresh-token`, {
			method: "POST",
			credentials: "include",
		});

		if (refreshResponse.ok) {
			const refreshData = await refreshResponse.json();
			authStore.accessToken = refreshData.access_token;
			headers["Authorization"] = `Bearer ${refreshData.access_token}`;
			response = await fetch(url, { ...options, headers });
			return response;
		}

		await logout();
		throw new Error("Session expired, please log in again.");
	}

	return response;
}
