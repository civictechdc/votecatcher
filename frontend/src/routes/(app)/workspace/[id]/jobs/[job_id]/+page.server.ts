import type { PageServerLoad } from "./$types";
import { error } from "@sveltejs/kit";
import { API_BASE_URL } from "#lib/api/base-url.ts";

/**
 * Job-existence guard for `/workspace/[id]/jobs/[job_id]`. Without it the
 * page answers 200 and shows an inline error card for deep links to jobs
 * that don't exist (spec: error-pages).
 *
 * The backend is the source of truth: `GET {API_BASE_URL}/jobs/{id}`
 * answers 404 for an unknown id and 422 for a non-numeric id (which can
 * never name a job) — both map to 404 here. Any other failure (e.g. a
 * backend 5xx) falls through to the page's client-side error handling.
 * The page's own client-side store fetch stays in place as the slow-load
 * fallback.
 */
export const load: PageServerLoad = async ({ fetch, params }) => {
	const res = await fetch(`${API_BASE_URL}/jobs/${encodeURIComponent(params.job_id)}`);
	if (res.status === 404 || res.status === 422) {
		// Kit 3 signature: message as the second argument.
		throw error(404, `Job "${params.job_id}" not found.`);
	}
	return {};
};
