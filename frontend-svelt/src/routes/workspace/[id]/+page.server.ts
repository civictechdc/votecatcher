import type { PageServerLoad } from '../$types';
import { redirect, fail } from '@sveltejs/kit';

export const load: PageServerLoad = async ({ params, fetch }) => {
	// If demo mode, allow workspace page to load even without a real session.
	if (params.id === 'demo') {
		return {};
	}

	const res = await fetch('/workspace');
	if (res.ok) {
		const json = await res.json().catch(() => ({}));
		if (json?.user) {
			// already authenticated -> go to getting-started
			throw redirect(303, '/getting-started');
		}
	}
	return {};
};
