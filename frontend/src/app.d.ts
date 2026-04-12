import type { User, Session } from "better-auth";

// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		interface Locals {
			user?: User;
			session?: Session;
		}

		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}
}

declare module "$env/static/public" {
	export const PUBLIC_API_URL: string;
	export const PUBLIC_DEMO_MODE: string;
}

declare module "$env/static/private" {
	export const OCR_PROVIDER_API_KEY: string;
	export const OCR_PROVIDER_NAME: string;
	export const OCR_PROVIDER_MODEL: string;
	export const DEMO_MODE: string;
}

export {};
