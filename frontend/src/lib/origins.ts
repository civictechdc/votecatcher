/**
 * Pure origin-contract helpers — no environment or framework imports.
 *
 * Shared by `src/env.ts` (schema validation for `ORIGIN`/`TRUSTED_ORIGINS`)
 * and `src/lib/server/trusted-origins.ts` (server-side fetch validation).
 * Keep this module free of `$app/*` imports so it stays safe to evaluate
 * from `src/env.ts` in any context (build, server, tests) and easy to unit
 * test in isolation.
 */

/**
 * Allowlist used in development when `TRUSTED_ORIGINS` is unset.
 * Mirrors the backend development CORS policy (localhost origins).
 */
export const DEFAULT_DEV_TRUSTED_ORIGINS: readonly string[] = [
	"http://localhost",
	"http://localhost:5173",
];

const TRUSTED_ORIGINS_FORMAT =
	'comma-separated http(s) origins, e.g. "https://app.example.com,https://staging.example.com"';

/** Validate and normalize a single http(s) origin. */
export function normalizeOrigin(raw: string, variable: string): string {
	const trimmed = raw.trim();
	if (trimmed === "*") {
		throw new Error(
			`${variable} must not contain "*": a wildcard allowlist disables origin validation. Set explicit origins — ${TRUSTED_ORIGINS_FORMAT}`,
		);
	}
	let url: URL;
	try {
		url = new URL(trimmed);
	} catch {
		throw new Error(
			`${variable} contains an invalid origin "${trimmed}": expected an http(s) origin like "https://app.example.com"`,
		);
	}
	if (url.protocol !== "http:" && url.protocol !== "https:") {
		throw new Error(`${variable} origin "${trimmed}" must use http(s), got "${url.protocol}"`);
	}
	if (url.username || url.password || url.pathname !== "/" || url.search || url.hash) {
		throw new Error(
			`${variable} entries must be bare origins (no credentials, path, query, or fragment): got "${trimmed}"`,
		);
	}
	return url.origin;
}

/** Parse a comma-separated allowlist into normalized, de-duplicated origins. */
export function parseTrustedOrigins(raw: string): string[] {
	const seen = new Set<string>();
	for (const entry of raw.split(",")) {
		if (entry.trim() === "") continue;
		seen.add(normalizeOrigin(entry, "TRUSTED_ORIGINS"));
	}
	return [...seen];
}

/**
 * `TRUSTED_ORIGINS` contract (spec: trusted-origins):
 *
 * - wildcard entries are rejected in every environment (they would disable
 *   origin validation entirely)
 * - development (`dev`) + unset → localhost development origins
 * - `building` + unset → `undefined` (producing a build must not require it)
 * - production (not dev, not building) + missing/empty → throw an actionable
 *   error naming the variable (fail-closed at startup)
 */
export function validateTrustedOrigins(
	value: string | undefined,
	options: { dev: boolean; building: boolean },
): string[] | undefined {
	if (value === undefined || value.trim() === "") {
		if (options.building) return undefined;
		if (options.dev) return [...DEFAULT_DEV_TRUSTED_ORIGINS];
		throw new Error(
			`TRUSTED_ORIGINS is required in production but is not set. Provide ${TRUSTED_ORIGINS_FORMAT}.`,
		);
	}
	const origins = parseTrustedOrigins(value);
	if (origins.length === 0) {
		throw new Error(
			`TRUSTED_ORIGINS is set but parses to an empty allowlist. Provide ${TRUSTED_ORIGINS_FORMAT}.`,
		);
	}
	return origins;
}
