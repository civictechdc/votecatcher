// Lightweight API client wrapper used by onboarding UI.
// All direct Supabase calls in your previous app are replaced with REST endpoint calls.
// For now endpoints are mocked under src/routes/api/*.

export type ApiResult<T = unknown> = { ok: true; data: T } | { ok: false; error: string };

async function request<T>(path: string, opts?: RequestInit): Promise<ApiResult<T>> {
	try {
		const res = await fetch(path, {
			credentials: 'include',
			headers: { 'Content-Type': 'application/json' },
			...opts
		});
		const json = await res.json().catch(() => ({}));
		if (!res.ok) {
			return { ok: false, error: json?.error || res.statusText || 'API error' };
		}
		return { ok: true, data: json };
	} catch (err) {
		const msg = err instanceof Error ? err.message : String(err);
		return { ok: false, error: msg };
	}
}

export const api = {
	getSession: () =>
		request<{ user?: { id: string; email?: string } }>('/api/session', { method: 'GET' }),
	storeApiKey: (provider: string, apiKey: string) =>
		request('/api/store-ocr-provider', {
			method: 'POST',
			body: JSON.stringify({ provider, apiKey })
		}),
	createCampaign: (payload: { name: string; year: number; description?: string }) =>
		request('/api/create-campaign', { method: 'POST', body: JSON.stringify(payload) }),
	uploadFileMeta: (payload: { fileName: string; size: number; campaignId: string | null }) =>
		request('/api/upload-file', { method: 'POST', body: JSON.stringify(payload) }),
	triggerProcessFile: (payload: { filePath: string; campaignId: string | null }) =>
		request('/api/process-voter-file', { method: 'POST', body: JSON.stringify(payload) })
};
