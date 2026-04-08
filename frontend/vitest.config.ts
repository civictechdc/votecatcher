import { defineConfig } from "vitest/config";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { svelteTesting } from "@testing-library/svelte/vite";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

export default defineConfig({
	plugins: [svelte(), svelteTesting(), tailwindcss()],
	resolve: {
		alias: {
			$lib: path.resolve("./src/lib"),
			$app: path.resolve("./tests/__mocks__/$app"),
			"$env/static/public": path.resolve("./tests/__mocks__/$env/static/public.ts"),
		},
	},
	test: {
		include: ["src/**/*.{test,spec}.{js,ts}", "tests/**/*.{test,spec}.{js,ts}"],
		environment: "jsdom",
		exclude: ["**/node_modules/**", "**/e2e/**"],
		setupFiles: ["./tests/setup.ts"],
		coverage: {
			provider: "v8",
			reporter: ["text", "json", "html"],
			thresholds: {
				lines: 0,
				functions: 0,
				branches: 0,
				statements: 0,
			},
		},
	},
});
