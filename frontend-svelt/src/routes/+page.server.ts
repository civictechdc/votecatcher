import type { PageServerLoad } from './$types';
import { isDemoMode } from '$lib/stores/demo';
import { error } from '@sveltejs/kit';

export const load: PageServerLoad = async () => {
	if (!isDemoMode()) {
		//Load actual workspace data from DB e.g. workspaceData object
		error(404);
	}

	console.log('Is demo mode enabled:', isDemoMode());

	return {
		isDemoMode: isDemoMode(),
	};
};
