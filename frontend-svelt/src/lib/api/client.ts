// Lightweight API client wrapper used by onboarding UI.
// All direct Supabase calls in your previous app are replaced with REST endpoint calls.
// For now endpoints are mocked under src/routes/api/*.
import { VITE_API_URL } from '$env/static/private';

const BASE_URL = VITE_API_URL ?? '';

export type ApiResult<T = unknown> = { ok: true; data: T } | { ok: false; error: string };

// Middleware types
export type RequestMiddleware = (
	input: string,
	init: RequestInit
) => Promise<RequestInit> | RequestInit;
export type ResponseMiddleware = (res: Response) => Promise<Response> | Response;

// Middleware registries (can be extended at runtime)
const requestMiddlewares: RequestMiddleware[] = [];
const responseMiddlewares: ResponseMiddleware[] = [];

export function addRequestMiddleware(mw: RequestMiddleware) {
	return requestMiddlewares.push(mw);
}
export function addResponseMiddleware(mw: ResponseMiddleware) {
	return responseMiddlewares.push(mw);
}

// Helper to run middlewares in sequence
async function runRequestMiddlewares(path: string, init: RequestInit) {
	let out = { ...init };
	for (const m of requestMiddlewares) {
		out = await m(path, out);
	}
	return out;
}
async function runResponseMiddlewares(res: Response) {
	let out = res;
	for (const m of responseMiddlewares) {
		out = await m(out);
	}
	return out;
}

// Simple fetch with retry helper (internal)
async function fetchWithRetry(
	input: string,
	init: RequestInit,
	retries = 1,
	backoffMs = 250
): Promise<Response> {
	let attempt = 0;
	while (true) {
		try {
			const res = await fetch(input, init);
			// retry on 5xx
			if (res.ok || attempt >= retries || res.status < 500) return res;
			attempt++;
			await new Promise((r) => setTimeout(r, backoffMs * attempt));
		} catch (err) {
			if (attempt >= retries) throw err;
			attempt++;
			await new Promise((r) => setTimeout(r, backoffMs * attempt));
		}
	}
}

// Low-level fetch wrapper returning raw Response (applies middleware)
export async function fetchRaw(
	path: string,
	opts: RequestInit = {},
	optsOverride?: { retries?: number }
) {
	const resolved = path.startsWith('http')
		? path
		: `${BASE_URL}${path.startsWith('/') ? path : '/' + path}`;

	// normalize init
	let init: RequestInit = { credentials: 'include', ...opts };

	// Let request middlewares transform init (e.g. auth headers)
	init = await runRequestMiddlewares(resolved, init);

	// If body is plain object and not FormData / string / URLSearchParams, stringify it
	const isForm = typeof FormData !== 'undefined' && init.body instanceof FormData;
	if (
		!isForm &&
		init.body != null &&
		typeof init.body !== 'string' &&
		!(init.body instanceof URLSearchParams)
	) {
		init = {
			...init,
			body: JSON.stringify(init.body),
			headers: {
				'Content-Type': 'application/json',
				...(init.headers as Record<string, string> | undefined)
			}
		};
	} else if (isForm) {
		// ensure Content-Type not set so browser adds boundary
		if (init.headers) {
			const headers = { ...(init.headers as Record<string, string>) };
			delete headers['Content-Type'];
			init = { ...init, headers };
		}
	} else {
		init = { ...init, headers: init.headers ?? {} };
	}

	const res = await fetchWithRetry(resolved, init, optsOverride?.retries ?? 1);
	return runResponseMiddlewares(res);
}

// High-level request that returns ApiResult<T>
export async function request<T = unknown>(
	path: string,
	opts?: RequestInit
): Promise<ApiResult<T>> {
	try {
		const res = await fetchRaw(path, opts);
		// try parse json, fall back to text
		const contentType = res.headers.get('content-type') ?? '';
		let parsed: unknown = undefined;
		if (contentType.includes('application/json')) {
			parsed = await res.json().catch(() => ({}));
		} else {
			parsed = await res.text().catch(() => ({}));
		}
		if (!res.ok) {
			const err =
				(parsed && typeof parsed === 'object' && (parsed as any).error) ||
				res.statusText ||
				`HTTP ${res.status}`;
			return { ok: false, error: String(err) };
		}
		return { ok: true, data: parsed as T };
	} catch (err) {
		const msg = err instanceof Error ? err.message : String(err);
		return { ok: false, error: msg };
	}
}

// Convenience API surface
export const api = {
	getWorkspace: (id: string) => request(`${BASE_URL}workspace/${id}`, { method: 'GET' }),
	getSession: () =>
		request<{ user?: { id: string; email?: string } }>('/api/session', { method: 'GET' }),
	storeApiKey: (provider: string, apiKey: string) =>
		request('/api/store-ocr-provider', { method: 'POST', body: { provider, apiKey } }),
	createCampaign: (payload: { name: string; year: number; description?: string }) =>
		request('/api/create-campaign', { method: 'POST', body: payload }),
	uploadFileMeta: (payload: { fileName: string; size: number; campaignId: string | null }) =>
		request('/api/upload-file', { method: 'POST', body: payload }),

	// high-level (returns ApiResult)
	demoUploadVoters: (formData: FormData) =>
		request(`${BASE_URL}api/upload/voter-records`, { method: 'POST', body: formData }),

	// low-level raw fetch (useful in +server to forward response)
	demoUploadVotersRaw: (formData: FormData) =>
		fetchRaw(`${BASE_URL}api/upload/voter-records`, { method: 'POST', body: formData }),

	// high-level (returns ApiResult)
	demoUploadPetitions: (formData: FormData) =>
		request(`${BASE_URL}api/upload/petition-entries`, { method: 'POST', body: formData }),

	// low-level raw fetch (useful in +server to forward response)
	demoUploadPetitionsRaw: (formData: FormData) =>
		fetchRaw(`${BASE_URL}api/upload/petition-entries`, { method: 'POST', body: formData }),

	triggerProcessFile: (payload: { filePath: string; campaignId: string | null }) =>
		request('/api/process-voter-file', { method: 'POST', body: payload })
};
