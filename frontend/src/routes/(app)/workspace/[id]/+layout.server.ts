import type { LayoutServerLoad } from "./$types";
import { error } from "@sveltejs/kit";
import { API_BASE_URL } from "#lib/api/base-url.ts";
import { GUARD_FETCH_TIMEOUT_MS, isOutageError } from "#lib/api/fetch-deadline.ts";

/**
 * Campaign-existence guard for every `/workspace/[id]` route (dashboard and
 * all children: upload, jobs, results, job detail).
 *
 * Spec: error-pages — unknown campaign ids must answer 404 with the error
 * boundary, not render the dashboard skeleton with a 200. The backend is the
 * source of truth: `GET {PUBLIC_API_URL}/campaigns/{id}` answers 404 for an
 * unknown id and 422 for a non-uuid id (which can never name a campaign) —
 * both map to 404 here. The existence check is bounded by a deadline
 * (`AbortSignal.timeout`): a fetch timeout or network failure falls through
 * to the page's client-side error handling, as does any other non-404/422
 * response (e.g. a backend 5xx). Unexpected rejections still propagate.
 * The response body is deliberately not read — the status code is all the
 * guard needs.
 */
export const load: LayoutServerLoad = async ({ fetch, params }) => {
	let res: Response;
	// Only the fetch is inside the try: arbitrary code failures can never be
	// misclassified as a backend outage (which would fail open).
	try {
		res = await fetch(`${API_BASE_URL}/campaigns/${encodeURIComponent(params.id)}`, {
			signal: AbortSignal.timeout(GUARD_FETCH_TIMEOUT_MS),
		});
	} catch (err) {
		// Backend outage class (timeout, abort, network failure): do not fail
		// SSR — let the page's client-side fallback handle it.
		if (isOutageError(err)) return {};
		throw err;
	}
	if (res.status === 404 || res.status === 422) {
		// Kit 3 signature: message as the second argument.
		throw error(404, `Campaign "${params.id}" not found.`);
	}
	return {};
};
