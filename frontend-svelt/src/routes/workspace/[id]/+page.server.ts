import type { PageServerLoad } from '../$types';
import { redirect, fail, error } from '@sveltejs/kit';
import { api } from '$lib/api/client';

async function loadMatchingFields(id: string) {
	const response = await api.fetchMatchFields(id);
	if (response.ok) {
		const { id, field_names }: { id: string; field_names: string[] } = response.data;
		return field_names;
	}
	return [];
}

export const load: PageServerLoad = async ({ params, fetch }) => {
	const responseData = {};

	responseData.matchingFields = await loadMatchingFields(params.id);

	if (params.id) {
		const json = await api.getWorkspace(params.id);
		if (!json.ok) throw error(json.status, json.statusText);
		if (params.id === 'demo') {
			responseData.isDemoMode = params.id === 'demo';
		}
		return responseData;
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
