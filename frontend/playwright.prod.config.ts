import { defineConfig } from "@playwright/test";

import baseConfig from "./playwright.config";

/**
 * Production smoke config: boots the adapter-node build of the frontend
 * instead of the Vite dev server.
 *
 * Differences from the base (dev) config:
 * - The frontend webServer builds with `ADAPTER=node bun run build` and then
 *   starts the adapter-node server with `node build`. adapter-node does not
 *   auto-load `.env` in production, so every runtime variable is passed
 *   explicitly via `env`: the same VARIABLE SET as the CI build env
 *   (.github/workflows/ci.yml "Build" step) but with local dev values
 *   (CI uses a ci:ci database and placeholder secrets), plus the smoke-only
 *   extras PUBLIC_API_URL, ORIGIN and PORT.
 * - The server binds PORT 5173 — the same origin the dev server uses —
 *   because the backend's local CORS allowlist only accepts
 *   `http://localhost:5173` (backend/app/middleware/cors.py `_DEV_ORIGINS`)
 *   and product source must not change for this smoke. `reuseExistingServer`
 *   is therefore FALSE: if a dev server already occupies 5173 the run fails
 *   loudly instead of silently testing the dev server.
 * - `testMatch` restricts this config to the prod smoke spec; the dev config
 *   remains the entrypoint for the full e2e suite (`bunx playwright test`).
 *
 * Run with: `bun run test:e2e:prod` (Postgres must already be up).
 */
const PROD_PORT = 5173;

export default defineConfig({
	...baseConfig,
	testMatch: "tests/e2e/prod-smoke.spec.ts",
	testIgnore: [], // undo the base config's dev-only ignore of this spec
	webServer: [
		baseConfig.webServer[0]!, // backend on :8080 (unchanged)
		{
			command: "ADAPTER=node bun run build && node build",
			url: `http://localhost:${PROD_PORT}`,
			reuseExistingServer: false,
			timeout: 300_000,
			env: {
				// CI build matrix (.github/workflows/ci.yml "Build" step)
				DATABASE_URL: "postgresql://votecatcher:votecatcher_dev@localhost:5432/votecatcher", // pragma: allowlist secret
				BETTER_AUTH_SECRET: "dev-local-e2e-secret-not-for-prod", // pragma: allowlist secret
				DEMO_MODE: "false",
				OCR_PROVIDER_API_KEY: "ci-placeholder", // pragma: allowlist secret
				OCR_PROVIDER_NAME: "openai",
				OCR_PROVIDER_MODEL: "gpt-4o-mini",
				// smoke origin + API base (dynamic env vars, read at runtime)
				PUBLIC_API_URL: "http://localhost:8080",
				ORIGIN: `http://localhost:${PROD_PORT}`,
				// required in production (src/env.ts fails closed at startup
				// without it); must include the smoke ORIGIN above
				TRUSTED_ORIGINS: `http://localhost:${PROD_PORT}`,
				PORT: String(PROD_PORT),
			},
		},
	],
});
