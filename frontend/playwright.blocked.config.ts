import { defineConfig } from "@playwright/test";

import baseConfig from "./playwright.config";

/**
 * Blocked-target config (task 3.6): boots the Vite dev server on :5174 with
 * a TRUSTED_ORIGINS allowlist that deliberately excludes the app origin, so
 * server loads with relative fetches (auth + getting-started) hit the
 * trusted-origin rejection path: actionable error(502), no request sent.
 *
 * The frontend .env still sets ORIGIN=http://localhost:5173 — that becomes
 * the rejected base, exactly the scenario under test. No backend needed.
 *
 * Run with: `bun run test:e2e:blocked`
 */
const BLOCKED_PORT = 5174;

export default defineConfig({
	...baseConfig,
	testMatch: "tests/e2e/blocked-target.spec.ts",
	testIgnore: [], // undo the base config's prod-smoke ignore for this wrapper
	use: { ...baseConfig.use, baseURL: `http://localhost:${BLOCKED_PORT}` },
	webServer: [
		{
			command: `bun run dev --port ${BLOCKED_PORT}`,
			url: `http://localhost:${BLOCKED_PORT}`,
			reuseExistingServer: false,
			timeout: 120000,
			env: {
				// dev server, but with a production-shaped allowlist that does
				// NOT include the app origin (ORIGIN=http://localhost:5173)
				TRUSTED_ORIGINS: "https://canonical.example.com",
			},
		},
	],
});
