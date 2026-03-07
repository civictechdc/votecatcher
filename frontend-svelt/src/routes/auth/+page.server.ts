import type { Actions, PageServerLoad } from './$types';
import { redirect, fail } from '@sveltejs/kit';

/**
 * Server-side load: redirect to app if session exists.
 * Uses relative fetch to /auth/session (mocked locally).
 */
export const load: PageServerLoad = async ({ fetch }) => {
	const res = await fetch('/auth/session');
	if (res.ok) {
		const json = await res.json().catch(() => ({}));
		if (json?.user) {
			// already authenticated -> go to getting-started
			throw redirect(303, '/getting-started');
		}
	}
	return {};
};

/**
 * Optional server actions for progressive enhancement (forms).
 * They proxy to server-side mock endpoints. Keep them minimal.
 */
export const actions: Actions = {
	signUp: async ({ request, fetch }) => {
		const form = await request.formData();
		const email = String(form.get('email') ?? '');
		const password = String(form.get('password') ?? '');
		if (!email || !password) return fail(400, { error: 'Missing email or password' });

		const res = await fetch('/api/auth/sign-up', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ email, password }),
		});
		const payload = await res.json().catch(() => ({}));
		if (!res.ok) return fail(res.status, { error: payload?.error || 'sign up failed' });
		return { success: true };
	},

	signIn: async ({ request, fetch }) => {
		const form = await request.formData();
		const email = String(form.get('email') ?? '');
		const password = String(form.get('password') ?? '');
		if (!email || !password) return fail(400, { error: 'Missing email or password' });

		const res = await fetch('/api/auth/sign-in', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ email, password }),
		});
		const payload = await res.json().catch(() => ({}));
		if (!res.ok) return fail(res.status, { error: payload?.error || 'sign in failed' });
		// if success, redirect to getting-started
		throw redirect(303, '/getting-started');
	},
};
