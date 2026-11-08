import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { sveltekitCookies } from "better-auth/svelte-kit";
import { BETTER_AUTH_SECRET, ORIGIN } from "$app/env/private";
import { getRequestEvent } from "$app/server";
import { db } from "#lib/server/db/index.ts";

export const auth = betterAuth({
	baseURL: ORIGIN,
	secret: BETTER_AUTH_SECRET,
	database: drizzleAdapter(db, { provider: "pg" }),
	emailAndPassword: { enabled: true },
	plugins: [sveltekitCookies(getRequestEvent)], // make sure this is the last plugin in the array
});
