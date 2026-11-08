import { error } from "@sveltejs/kit";
import { ORIGIN, TRUSTED_ORIGINS } from "$app/env/private";

/**
 * Server-side trusted-origin helper (spec: trusted-origins).
 *
 * Every server-side fetch with a relative target resolves through here
 * first: the base is the canonical `ORIGIN` when set (else the request's
 * own derived origin), and that base must be in the validated
 * `TRUSTED_ORIGINS` allowlist before the request is sent. Untrusted bases
 * fail fast with an actionable error naming the rejected target — no silent
 * fallback, no wildcard exemptions. This allowlist never relaxes the app's
 * CSRF protection (it is only consulted for outgoing server fetches).
 */

/** The validated allowlist (schema-parsed by `src/env.ts`; dev-defaulted). */
export function trustedOrigins(): readonly string[] {
	return TRUSTED_ORIGINS ?? [];
}

/**
 * Resolve the trusted base origin for a server-side fetch. Prefers the
 * canonical `ORIGIN` env var; falls back to the request's derived origin.
 * Throws `error(502, …)` when the resolved base is not trusted.
 */
export function resolveTrustedBase(eventOrigin: string): string {
	const base = ORIGIN ?? eventOrigin;
	const allowlist = trustedOrigins();
	if (!allowlist.includes(base)) {
		throw error(
			502,
			`Rejected untrusted server fetch base "${base}": it is not in the TRUSTED_ORIGINS allowlist [${allowlist.join(", ") || "(empty)"}]. Add this deployment's origin to TRUSTED_ORIGINS (comma-separated, e.g. "https://app.example.com,https://staging.example.com") and restart the server.`,
		);
	}
	return base;
}

/**
 * Resolve a site-root-relative fetch target (e.g. "/api/session") against the
 * trusted base. Returns the absolute URL to pass to `fetch`, or throws
 * `error(502, …)` — in which case no request must be sent.
 */
export function trustedFetchUrl(path: string, eventOrigin: string): string {
	if (!path.startsWith("/")) {
		throw error(
			502,
			`trustedFetchUrl expects a site-root-relative path starting with "/", got "${path}"`,
		);
	}
	return new URL(path, resolveTrustedBase(eventOrigin)).toString();
}
