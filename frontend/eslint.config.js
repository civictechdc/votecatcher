import { fileURLToPath } from "node:url";
import { includeIgnoreFile } from "@eslint/compat";
import js from "@eslint/js";
import svelte from "eslint-plugin-svelte";
import { defineConfig } from "eslint/config";
import globals from "globals";
import ts from "typescript-eslint";
import svelteConfig from "./svelte.config.js";
import storybook from "eslint-plugin-storybook";

const gitignorePath = fileURLToPath(new URL("./.gitignore", import.meta.url));

export default defineConfig(
	includeIgnoreFile(gitignorePath),
	js.configs.recommended,
	...ts.configs.recommended,
	...svelte.configs.recommended,
	...storybook.configs["flat/recommended"],
	{
		languageOptions: {
			globals: { ...globals.browser, ...globals.node },
		},
		rules: {
			"no-undef": "off",
		},
	},
	{
		rules: {
			"no-restricted-syntax": [
				"error",
				{
					message:
						"Do not dynamically access import.meta — use direct property access (e.g. import.meta.env.VITE_FOO). Vite's SSR module runner blocks dynamic access.",
					selector:
						"MemberExpression[computed=true][object.object.name=import][object.property.name=meta]",
				},
			],
		},
	},
	{
		files: ["**/*.svelte", "**/*.svelte.ts", "**/*.svelte.js"],
		languageOptions: {
			parserOptions: {
				projectService: true,
				extraFileExtensions: [".svelte"],
				parser: ts.parser,
				svelteConfig,
			},
		},
		rules: {
			"no-restricted-syntax": [
				"error",
				{
					message:
						"Use `dev` from `$app/environment` or `$env/static/public` instead of `import.meta.env` in Svelte files. See: https://svelte.dev/docs/kit/modules#$app-environment",
					selector: "MemberExpression[object.meta.property.name=env][object.object.name=import]",
				},
			],
		},
	},
);
