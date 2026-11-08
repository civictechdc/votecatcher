import type { LayoutServerLoad } from "./$types";
import { error } from "@sveltejs/kit";
import { API_BASE_URL } from "#lib/api/base-url.ts";

/**
 * Campaign-existence guard for every `/workspace/[id]` route (dashboard and
 * all children: upload, jobs, results, job detail).
 *
 * Spec: error-pages — unknown campaign ids must answer 404 with the error
 * boundary, not render the dashboard skeleton with a 200. The backend is the
 * source of truth: `GET {PUBLIC_API_URL}/campaigns/{id}` answers 404 for an
 * unknown id and 422 for a non-uuid id (which can never name a campaign) —
 * both map to 404 here. Any other failure propagates and surfaces through
 * the error boundary unchanged.
 */
export const load: LayoutServerLoad = async ({ fetch, params }) => {
	const res = await fetch(`${API_BASE_URL}/campaigns/${encodeURIComponent(params.id)}`);
	if (res.status === 404 || res.status === 422) {
		// Kit 3 signature: message as the second argument.
		throw error(404, `Campaign "${params.id}" not found.`);
	}
	return {};
};
