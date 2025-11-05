import type { PageServerLoad } from '../$types';
import { redirect, fail, error } from '@sveltejs/kit';
import { api } from '$lib/api/client';

export const load: PageServerLoad = async ({ params, fetch }) => {
	if (params.id) {
		const json = await api.getWorkspace(params.id);
		if (!json.ok) throw error(json.status, json.statusText);
		if (json.body?.id === 'demo') {
			return {
				isDemoMode: json.body.id === 'demo'
			};
		}
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
