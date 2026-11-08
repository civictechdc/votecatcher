import { defineConfig } from "@playwright/test";

import baseConfig from "./playwright.config";

/**
 * Header-derived-origin prod smoke (task 4.2): boots the adapter-node build
 * BEHIND a simulated reverse proxy, matching the adapter-node 6 deployment
 * contract.
 *
 * Differences from playwright.prod.config.ts (direct prod smoke):
 * - The app listens on :5174 and runs with PROTOCOL_HEADER/HOST_HEADER set,
 *   so SvelteKit derives each request's origin from the x-forwarded-proto /
 *   x-forwarded-host headers. ORIGIN is no longer consumed by Kit in
 *   adapter-node 6 — only Better Auth (baseURL) and the trusted-origin
 *   helper read it; both keep working here.
 * - scripts/reverse-proxy.mjs listens on :5173 (the origin the browser and
 *   the backend's local CORS allowlist use), rewrites Host to the upstream
 *   and injects the forwarded headers — so form submissions passing CSRF
 *   prove Kit really derived the origin from the headers, not from a
 *   matching Host.
 * - testMatch restricts this config to the proxy smoke spec (auth flows +
 *   CSRF under derived origin); the route-walk coverage stays in
 *   prod-smoke.spec.ts.
 *
 * Run with: `bun run test:e2e:prod:proxy` (Postgres must already be up).
 */
const PUBLIC_PORT = 5173;
const APP_PORT = 5174;

export default defineConfig({
	...baseConfig,
	testMatch: "tests/e2e/prod-proxy-smoke.spec.ts",
	testIgnore: [], // undo the base config's dev-only ignore of this spec
	webServer: [
		baseConfig.webServer[0]!, // backend on :8080 (unchanged)
		{
			command: "ADAPTER=node bun run build && node build",
			url: `http://localhost:${APP_PORT}`,
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
				// runtime env (dynamic vars, read at runtime; one build serves
				// all environments)
				PUBLIC_API_URL: "http://localhost:8080",
				ORIGIN: `http://localhost:${PUBLIC_PORT}`,
				// required in production (src/env.ts fails closed at startup
				// without it); must include the public ORIGIN above
				TRUSTED_ORIGINS: `http://localhost:${PUBLIC_PORT}`,
				// reverse-proxy contract: Kit derives request origins from
				// these headers — ORIGIN is NOT consumed by Kit (adapter-node 6)
				PROTOCOL_HEADER: "x-forwarded-proto",
				HOST_HEADER: "x-forwarded-host",
				PORT: String(APP_PORT),
			},
		},
		{
			command: "node scripts/reverse-proxy.mjs",
			url: `http://localhost:${PUBLIC_PORT}`,
			reuseExistingServer: false,
			timeout: 30_000,
			env: {
				PROXY_PORT: String(PUBLIC_PORT),
				UPSTREAM_PORT: String(APP_PORT),
				PUBLIC_ORIGIN: `http://localhost:${PUBLIC_PORT}`,
			},
		},
	],
});
