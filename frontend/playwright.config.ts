import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
	testDir: "./tests/e2e",
	fullyParallel: true,
	forbidOnly: !!process.env.CI,
	retries: process.env.CI ? 2 : 0,
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
			reuseExistingServer: !process.env.CI,
			timeout: 120000,
			env: {
				FEATURE_DEMO_MODE: "1",
				FEATURE_ENABLE_SIMULATION: "1",
			},
		},
		{
			command: "bun run dev",
			url: "http://localhost:5173",
			reuseExistingServer: !process.env.CI,
			timeout: 120000,
			env: {
				PUBLIC_DEMO_MODE: "true",
				DEMO_RESET: "true",
				PUBLIC_API_URL: "http://localhost:8080",
			},
		},
	],
});
