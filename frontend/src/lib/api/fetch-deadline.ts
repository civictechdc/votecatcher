// Shared deadlines and outage classification for server-side fetches
// (workspace guards in +layout.server.ts / +page.server.ts and the
// /workspace/api/* proxies). One definition per deadline so callers stay
// in sync on the outage contract.

/**
 * Deadline for the SSR guards' existence checks (campaign layout guard and
 * job page guard). Guards must not hang SSR waiting on a stuck backend;
 * on deadline they fall through to the page's client-side fallback.
 */
export const GUARD_FETCH_TIMEOUT_MS = 5000;

/**
 * Deadline for the match-result proxy's upstream results request.
 */
export const MATCH_RESULT_TIMEOUT_MS = 10000;

/**
 * Deadline for the match-status (SSE) proxy's initial fetch. It only bounds
 * the time until upstream response headers arrive — it is cleared before the
 * streamed Response is returned, so the SSE body is never aborted mid-flight.
 */
export const MATCH_STATUS_CONNECT_TIMEOUT_MS = 5000;

/**
 * Error name of a rejection, tolerating non-Error objects (jsdom's
 * DOMException is notably not `instanceof Error`, unlike browsers/Node).
 */
function errorName(err: unknown): string | undefined {
	if (err instanceof Error) return err.name;
	if (typeof err === "object" && err !== null && "name" in err) {
		return String((err as { name: unknown }).name);
	}
	return undefined;
}

/**
 * True when a fetch rejection is an abort/deadline (TimeoutError, AbortError)
 * — the deadline was hit, which is not a transient fault worth retrying.
 */
export function isAbortError(err: unknown): boolean {
	const name = errorName(err);
	return name === "TimeoutError" || name === "AbortError";
}

/**
 * True when a fetch rejection belongs to the "backend unreachable" outage
 * class: deadline hit (TimeoutError/AbortError) or a plain network failure
 * (TypeError, as thrown by fetch on connection errors).
 */
export function isOutageError(err: unknown): boolean {
	return errorName(err) === "TypeError" || isAbortError(err);
}
