import { API_BASE_URL } from "./base-url";

type ApiResult<T = unknown> = { ok: true; data: T } | { ok: false; error: string };

async function post<T = unknown>(path: string, body: unknown): Promise<ApiResult<T>> {
	const url = `${API_BASE_URL}${path}`;
	try {
		const res = await fetch(url, {
			method: "POST",
			credentials: "include",
			headers: { "Content-Type": "application/json", Accept: "application/json" },
			body: JSON.stringify(body),
		});
		const json = await res.json().catch(() => ({}));
		if (!res.ok) return { ok: false, error: json?.error || res.statusText || "request failed" };
		return { ok: true, data: json as T };
	} catch (err) {
		return { ok: false, error: err instanceof Error ? err.message : String(err) };
	}
}

async function get<T = unknown>(path: string): Promise<ApiResult<T>> {
	const url = `${API_BASE_URL}${path}`;
	try {
		const res = await fetch(url, {
			credentials: "include",
			headers: { Accept: "application/json" },
		});
		const json = await res.json().catch(() => ({}));
		if (!res.ok) return { ok: false, error: json?.error || res.statusText || "request failed" };
		return { ok: true, data: json as T };
	} catch (err) {
		return { ok: false, error: err instanceof Error ? err.message : String(err) };
	}
}

export const authApi = {
	refreshSession: (refreshToken: string) => post("/api/refresh-session", { refreshToken }),
	getSession: () => get<{ user?: { id: string; email?: string } }>("/api/session"),
	signUp: (email: string, password: string) => post("/api/auth/sign-up", { email, password }),
	signIn: (email: string, password: string) => post("/api/auth/sign-in", { email, password }),
	signOut: () => post("/api/auth/sign-out", {}),
	// 2FA / Passkey endpoints (optional)
	start2fa: (email: string) => post("/api/auth/start-2fa", { email }),
	verify2fa: (email: string, code: string) => post("/api/auth/verify-2fa", { email, code }),
};

// Convenience named export used by pages that import getSession directly
export const getSession = authApi.getSession;

import { writable } from "svelte/store";

export const authStore = writable({
	accessToken: null,
	isAuthenticated: false,
	userEmail: null,
});

export async function logout() {}
