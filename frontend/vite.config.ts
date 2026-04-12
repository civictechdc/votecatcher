import { defineConfig } from "vitest/config";
import tailwindcss from "@tailwindcss/vite";
import { sveltekit } from "@sveltejs/kit/vite";
import oxlintPlugin from "vite-plugin-oxlint";
import { visualizer } from "rollup-plugin-visualizer";
import path from "path";

export default defineConfig({
	plugins: [
		sveltekit(),
		tailwindcss(),
		oxlintPlugin(),
		visualizer({
			filename: "bundle-stats.html",
			open: false,
			gzipSize: true,
			template: "treemap",
		}),
	] as any,
	resolve: {
		alias: {
			$lib: path.resolve("./src/lib"),
		},
	},
});
