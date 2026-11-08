import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
	testDir: "./tests/e2e",
	// the adapter-node smoke specs run only under playwright.prod.config.ts
	// (`bun run test:e2e:prod`) / playwright.proxy-smoke.config.ts
	// (`bun run test:e2e:prod:proxy`); the blocked-target spec runs only under
	// playwright.blocked.config.ts (`bun run test:e2e:blocked`) — keep all
	// out of dev-server runs
	testIgnore: [
		"tests/e2e/prod-smoke.spec.ts",
		"tests/e2e/prod-proxy-smoke.spec.ts",
		"tests/e2e/blocked-target.spec.ts",
	],
	fullyParallel: true,
	forbidOnly: !!process.env["CI"],
	retries: process.env["CI"] ? 2 : 0,
	// The vite dev server compiles modules on demand; parallel workers racing
	// the same cold compile graph intermittently break hydration.
	workers: 1,
	reporter: "html",
	use: {
		baseURL: "http://localhost:5173",
		trace: "on-first-retry",
		screenshot: "only-on-failure",
	},
	projects: [
		{
			name: "chromium",
			use: { ...devices["Desktop Chrome"] },
		},
	],
	webServer: [
		{
			command: "cd ../backend && uv run python main.py --env local",
			url: "http://localhost:8080/docs",
			reuseExistingServer: !process.env["CI"],
			timeout: 120000,
			env: {
				FEATURE_DEMO_MODE: "1",
				FEATURE_ENABLE_SIMULATION: "1",
			},
		},
		{
			command: "bun run dev",
			url: "http://localhost:5173",
			reuseExistingServer: !process.env["CI"],
			timeout: 120000,
			env: {
				PUBLIC_DEMO_MODE: "true",
				PUBLIC_API_URL: "http://localhost:8080",
				// Note: no DEMO_RESET here — traced 2026-11-07: nothing reads
				// it. The backend demo-reset gate is FEATURE_DEMO_RESET (see
				// backend/app/settings/settings.py).
			},
		},
	],
});
