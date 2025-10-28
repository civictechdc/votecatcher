// Explanation: Small fetch wrapper to call the backend FastAPI session endpoint.
// Reasoning: keep Supabase logic in backend; front-end only asks backend whether a session exists.
export async function getSession(apiUrl?: string) {
	const base = apiUrl ?? import.meta.env.VITE_API_URL ?? '';
	const url = base ? `${base.replace(/\/$/, '')}/auth/session` : '/auth/session';
	// Note: if you prefer a dev proxy, set VITE_API_URL to your backend (http://localhost:8000)
	const res = await fetch(url, {
		credentials: 'include', // if backend uses cookies for session
		headers: { Accept: 'application/json' }
	});

	if (!res.ok) {
		// return null for unauthenticated or failed calls
		return null;
	}
	return await res.json();
}
