import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { svelteTesting } from '@testing-library/svelte/vite';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';

export default defineConfig({
	plugins: [svelte(), svelteTesting(), tailwindcss()],
	resolve: {
		alias: {
			$lib: path.resolve('./src/lib'),
		},
	},
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}', 'tests/**/*.{test,spec}.{js,ts}'],
		environment: 'jsdom',
		exclude: ['**/node_modules/**', '**/e2e/**'],
	},
});
