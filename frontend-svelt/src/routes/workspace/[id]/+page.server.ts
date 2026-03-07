import type { PageServerLoad } from '../$types';
import { redirect, error } from '@sveltejs/kit';
import { api } from '$lib/api/client';

async function loadMatchingFields(id: string) {
	const response = await api.fetchMatchFields(id);
	if (response.ok) {
		const { field_names }: { id: string; field_names: string[] } = response.data;
		return field_names;
	}
	return [];
}

export const load: PageServerLoad = async ({ params, fetch }) => {
	const responseData = {};

	responseData.matchingFields = await loadMatchingFields(params.id);

	if (params.id) {
		const json = await api.getWorkspace(params.id);
		if (!json.ok) throw error(404, json.error);
		if (params.id === 'demo') {
			responseData.isDemoMode = params.id === 'demo';
		}
		return responseData;
	}

	const res = await fetch('/workspace');
	if (res.ok) {
		const json = await res.json().catch(() => ({}));
		if (json?.user) {
			throw redirect(303, '/getting-started');
		}
	}
	return {};
};
