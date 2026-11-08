import { defineEnvVars } from "@sveltejs/kit/env";
import { building, dev } from "$app/env";
import { normalizeOrigin, validateTrustedOrigins } from "./lib/origins.ts";

/**
 * Full Kit 3 environment contract (design D3/D4).
 *
 * All variables are dynamic (no `static: true`): values are read at runtime so
 * one build serves every environment. `$app/env/*` reads are populated from
 * these declarations; `envPrefix`-era `import.meta.env` reads are gone.
 *
 * Validation semantics (per variable `schema`):
 * - omitted schema → variable must be set (may be an empty string)
 * - `undefined` returned → variable is optional in that context
 * - thrown error → app fails to start (or build) with the message
 *
 * `building` relaxes startup-only requirements while `vite build` runs (CI
 * builds carry no runtime env); `dev` supplies development defaults.
 */

/** Validate an http(s) API base URL; returns it normalized (no trailing slash). */
function validateApiUrl(value: string): string {
	let url: URL;
	try {
		url = new URL(value.trim());
	} catch {
		throw new Error(
			`PUBLIC_API_URL "${value.trim()}" is not a valid URL — expected an http(s) URL like "http://localhost:8080" (no /api suffix)`,
		);
	}
	if (url.protocol !== "http:" && url.protocol !== "https:") {
		throw new Error(`PUBLIC_API_URL must use http(s), got "${url.protocol}"`);
	}
	return url.toString().replace(/\/$/, "");
}

/** Parse a comma-separated flag list (e.g. "mockApi,2fa") into a clean array. */
function parseFlagList(value: string | undefined): string[] {
	if (!value) return [];
	const flags = new Set(
		value
			.split(",")
			.map((flag: string) => flag.trim())
			.filter(Boolean),
	);
	return [...flags];
}

export const variables = defineEnvVars({
	// --- private ---
	DATABASE_URL: {
		description: "PostgreSQL connection string used by the Drizzle client",
	},
	BETTER_AUTH_SECRET: {
		description: "Secret used to sign Better Auth session tokens",
	},
	ORIGIN: {
		description:
			"Canonical deployment origin (no trailing slash). Consumed by the trusted-origin helper and Better Auth baseURL; SvelteKit itself derives request origins from headers (PROTOCOL_HEADER/HOST_HEADER).",
		schema: (value) =>
			value === undefined || value.trim() === "" ? undefined : normalizeOrigin(value, "ORIGIN"),
	},
	TRUSTED_ORIGINS: {
		description:
			'Comma-separated trusted-origin allowlist, e.g. "https://app.example.com,https://staging.example.com". Wildcards are rejected; defaults to localhost origins in development; required in production.',
		schema: (value) => validateTrustedOrigins(value, { dev, building }),
	},
	OCR_PROVIDER_NAME: {
		description: "OCR provider used for signature verification (e.g. openai)",
		schema: (v) => v,
	},
	OCR_PROVIDER_MODEL: {
		description: "OCR model identifier passed to the provider",
		schema: (v) => v,
	},
	OCR_PROVIDER_API_KEY: {
		description: "API key for the configured OCR provider",
		schema: (v) => v,
	},
	DEMO_MODE: {
		description: 'Set to "true" to run the frontend server against canned demo data',
		schema: (v) => v === "true",
	},

	// --- public ---
	PUBLIC_API_URL: {
		public: true,
		description: "Backend API base URL without the /api suffix (e.g. http://localhost:8080)",
		schema: (value) => {
			if (value === undefined || value.trim() === "") {
				// dynamic variable: the placeholder is never used at runtime,
				// it only keeps the schema's output type a plain string
				if (building) return "";
				throw new Error(
					'PUBLIC_API_URL is required but is not set. Provide an http(s) URL like "http://localhost:8080" (no /api suffix).',
				);
			}
			return validateApiUrl(value);
		},
	},
	PUBLIC_DEMO_MODE: {
		public: true,
		description: 'Set to "true" to enable the demo workspace',
		schema: (v) => v === "true",
	},
	PUBLIC_FEATURES: {
		public: true,
		description:
			'Comma-separated feature flags seeded at startup (e.g. "mockApi,2fa"), merged with the dev vc:flags localStorage set',
		schema: (v) => parseFlagList(v),
	},
});
