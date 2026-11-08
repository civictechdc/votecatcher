import type { User, Session } from "better-auth";

declare global {
	namespace App {
		interface Locals {
			user?: User;
			session?: Session;
		}

		/**
		 * Error shape surfaced to `+error.svelte` boundaries. Kit passes an
		 * `HttpError` (from `error(status, body)`, carrying `status` and
		 * `body.message`) or a plain runtime `Error` (carrying only `message`).
		 * Boundaries derive the displayed status/message from whichever
		 * fields are present; unexpected errors fall back to 500 + generic copy.
		 */
		interface Error {
			message: string;
			status?: number;
			body?: { message?: string };
		}
	}
}

export {};
