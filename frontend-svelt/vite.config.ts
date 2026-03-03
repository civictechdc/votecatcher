import { defineConfig } from "vitest/config";
import tailwindcss from "@tailwindcss/vite";
import { sveltekit } from "@sveltejs/kit/vite";
import oxlintPlugin from "vite-plugin-oxlint";
import path from "path";

export default defineConfig({
	plugins: [sveltekit(), tailwindcss(), oxlintPlugin()],
	resolve: {
		alias: {
			$lib: path.resolve("./src/lib"),
		},
	},
});
