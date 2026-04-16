import type { User, Session } from "better-auth";

declare module "virtual:env" {
	interface ImportMetaEnv {
		PUBLIC_API_URL: string;
		PUBLIC_DEMO_MODE: string;
		DEMO_MODE: string;
		ORIGIN: string;
		DATABASE_URL: string;
		BETTER_AUTH_SECRET: string;
		OCR_PROVIDER_NAME: string;
		OCR_PROVIDER_MODEL: string;
		OCR_PROVIDER_API_KEY: string;
	}
}

declare global {
	namespace App {
		interface Locals {
			user?: User;
			session?: Session;
		}
	}
}

export {};
