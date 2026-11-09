import type { PageServerLoad } from "./$types";
import type { JobResponse } from "#lib/api/generated/index.ts";
import { error } from "@sveltejs/kit";
import { API_BASE_URL } from "#lib/api/base-url.ts";
import { GUARD_FETCH_TIMEOUT_MS, isOutageError } from "#lib/api/fetch-deadline.ts";

/**
 * Job-existence guard for `/workspace/[id]/jobs/[job_id]`. Without it the
 * page answers 200 and shows an inline error card for deep links to jobs
 * that don't exist (spec: error-pages).
 *
 * The backend is the source of truth: the campaign-scoped endpoint
 * `GET {API_BASE_URL}/campaigns/{campaign_id}/jobs/{job_id}` answers 404 for
 * an unknown job, an unknown campaign, or a campaign/job mismatch, and 422
 * for a non-uuid campaign id or non-numeric job id — both map to 404 here.
 * A 200 body is returned as `{ job }` so the page can seed its store without
 * a redundant client-side fetch; the body read has its own catch, so a 200
 * whose payload stalls or is unparseable falls through to client-side
 * handling instead of a 500 boundary. The existence check is bounded by a
 * deadline (`AbortSignal.timeout`): a fetch timeout or network failure falls
 * through with `{ job: null }` — as does any other non-404/422 response
 * (e.g. a backend 5xx) — and unexpected rejections still propagate. The
 * page's own client-side store fetch stays in place as the slow-load
 * fallback.
 */
export const load: PageServerLoad = async ({ fetch, params }) => {
	let res: Response;
	// Only the fetch is inside the try: arbitrary code failures can never be
	// misclassified as a backend outage (which would fail open).
	try {
		res = await fetch(
			`${API_BASE_URL}/campaigns/${encodeURIComponent(params.id)}/jobs/${encodeURIComponent(params.job_id)}`,
			{ signal: AbortSignal.timeout(GUARD_FETCH_TIMEOUT_MS) },
		);
	} catch (err) {
		// Backend outage class (timeout, abort, network failure): do not fail
		// SSR — let the page's client-side fallback handle it.
		if (isOutageError(err)) return { job: null };
		throw err;
	}
	if (res.status === 404 || res.status === 422) {
		// Kit 3 signature: message as the second argument.
		throw error(404, `Job "${params.job_id}" not found.`);
	}
	if (res.ok) {
		try {
			return { job: (await res.json()) as JobResponse };
		} catch {
			// Body stalled past the deadline or isn't parseable JSON: fall
			// through to the client-side fetch rather than a 500 boundary.
			return { job: null };
		}
	}
	return { job: null };
};
