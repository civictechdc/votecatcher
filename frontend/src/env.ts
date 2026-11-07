import { defineEnvVars } from "@sveltejs/kit/env";

/**
 * Minimal Kit 3 env bridge (declarations only).
 *
 * Kit 3 populates `$env/dynamic/private` exclusively from the variables declared
 * here, so this file must list every variable the current `$env/dynamic/private`
 * readers consume at runtime. `ORIGIN` is declared again so Better Auth's
 * `baseURL` (and its `__Secure-` cookie-name selection) keeps its pre-migration
 * source. Optional variables use `schema: (v) => v` — the documented pattern for
 * "a function can describe an optional variable" — which restores the in-code
 * fallbacks (`?? "false"`, `|| ""`) that schema-less declarations would make
 * boot-required.
 *
 * Task 3.1 still owns: real validators, public variables, TRUSTED_ORIGINS.
 */
export const variables = defineEnvVars({
	DATABASE_URL: {
		description: "PostgreSQL connection string used by the Drizzle client",
	},
	BETTER_AUTH_SECRET: {
		description: "Secret used to sign Better Auth session tokens",
	},
	ORIGIN: {
		description: "Canonical deployment origin consumed by Better Auth baseURL",
		schema: (v) => v,
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
		description: 'Set to "true" to run the frontend against canned demo data',
		schema: (v) => v,
	},
});
