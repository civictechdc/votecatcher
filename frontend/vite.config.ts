import adapterAuto from "@sveltejs/adapter-auto";
import adapterNode from "@sveltejs/adapter-node";
import { defineConfig } from "vitest/config";
import tailwindcss from "@tailwindcss/vite";
import { sveltekit } from "@sveltejs/kit/vite";
import oxlintPlugin from "vite-plugin-oxlint";
import { visualizer } from "rollup-plugin-visualizer";

const adapter = process.env["ADAPTER"] === "node" ? adapterNode() : adapterAuto();

export default defineConfig({
	plugins: [
		sveltekit({ adapter }),
		tailwindcss(),
		oxlintPlugin(),
		visualizer({
			filename: "bundle-stats.html",
			open: false,
			gzipSize: true,
			template: "treemap",
		}),
	],
});
