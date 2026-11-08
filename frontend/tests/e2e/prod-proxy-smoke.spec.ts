import { expect, test } from "@playwright/test";
import type { Page, Response } from "@playwright/test";

/**
 * Header-derived-origin prod smoke: runs ONLY under
 * playwright.proxy-smoke.config.ts (`bun run test:e2e:prod:proxy`), where
 * the adapter-node build sits behind scripts/reverse-proxy.mjs and Kit
 * derives request origins from x-forwarded-proto/x-forwarded-host
 * (PROTOCOL_HEADER/HOST_HEADER are set; Host is rewritten to the upstream,
 * so a coincidental Host match cannot make these tests pass).
 *
 * Covers the trusted-origins spec scenario "Allowlist does not widen CSRF":
 * enhanced form submissions succeed through the proxy (derived origin
 * matches the browser origin — CSRF accepts), while a cross-site POST is
 * still rejected. Auth flows (sign-up/sign-out/sign-in) prove Better Auth's
 * own ORIGIN reader and cookie handling work through the proxy.
 */
const LOGIN_PATH = "/demo/better-auth/login";
const AUTHED_PATH = "/demo/better-auth";
const PUBLIC_ORIGIN = "http://localhost:5173";

const EMAIL_DOMAIN = "@example.test";

function uniqueEmail(): string {
	return `e2e-proxy-${Date.now()}-${Math.floor(Math.random() * 10_000)}${EMAIL_DOMAIN}`;
}

async function gotoLogin(page: Page): Promise<void> {
	await page.goto(LOGIN_PATH);
	await page.waitForLoadState("domcontentloaded");
	await expect(page.locator('input[name="email"]')).toBeVisible();
	// settle for hydration so the click goes through use:enhance (fetch),
	// not a native form post
	await page.waitForTimeout(500);
}

/** Wait for the POST that submits a named form action. */
function waitForActionPost(page: Page, action: string): Promise<Response> {
	return page.waitForResponse(
		(response) => response.url().includes(`?/${action}`) && response.request().method() === "POST",
		{ timeout: 15_000 },
	);
}

async function registerViaForm(
	page: Page,
	email: string,
	password: string,
	name: string,
): Promise<Response> {
	await gotoLogin(page);
	await page.fill('input[name="email"]', email);
	await page.fill('input[name="password"]', password);
	await page.fill('input[name="name"]', name);
	const responsePromise = waitForActionPost(page, "signUpEmail");
	await page.getByRole("button", { name: "Register" }).click();
	return responsePromise;
}

async function signInViaForm(page: Page, email: string, password: string): Promise<Response> {
	await gotoLogin(page);
	await page.fill('input[name="email"]', email);
	await page.fill('input[name="password"]', password);
	const responsePromise = waitForActionPost(page, "signInEmail");
	await page.getByRole("button", { name: "Login", exact: true }).click();
	return responsePromise;
}

async function signOutViaForm(page: Page): Promise<Response> {
	await page.goto(AUTHED_PATH);
	await page.waitForLoadState("domcontentloaded");
	await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();
	await page.waitForTimeout(500);
	const responsePromise = waitForActionPost(page, "signOut");
	await page.getByRole("button", { name: "Sign out" }).click();
	return responsePromise;
}

test.describe("Prod smoke behind a reverse proxy (header-derived origin)", () => {
	test("landing page is served through the proxy", async ({ page }) => {
		const response = await page.goto("/");
		await page.waitForLoadState("domcontentloaded");

		expect(response?.status()).toBeLessThan(400);
		await expect(page.locator("main")).toHaveCount(1);
	});

	test("auth round-trip works when Kit derives the origin from forwarded headers", async ({
		page,
	}) => {
		const email = uniqueEmail();
		const name = `E2E Proxy ${Date.now()}`;

		// sign-up: enhanced POST passes CSRF via the derived origin
		const signUp = await registerViaForm(page, email, "sup3r-secret-pw", name);
		expect(signUp.status()).toBe(200); // Kit 3 success-path pin (auth-forms.spec.ts)
		await expect(page).toHaveURL(new RegExp(AUTHED_PATH.replace(/\//g, "\\/")));
		await expect(page.locator("h1")).toContainText(`Hi, ${name}!`);

		// sign-out: second enhanced POST + Better Auth session teardown
		const signOut = await signOutViaForm(page);
		expect(signOut.status()).toBe(200);
		await expect(page).toHaveURL(/\/demo\/better-auth\/login/);

		// sign-in: Better Auth verifies credentials + re-issues the session
		const signIn = await signInViaForm(page, email, "sup3r-secret-pw");
		expect(signIn.status()).toBe(200);
		await expect(page.locator("h1")).toContainText(`Hi, ${name}!`);
	});

	test("cross-site POST form submission is still CSRF-rejected", async ({ request }) => {
		const response = await request.post(`${PUBLIC_ORIGIN}${LOGIN_PATH}?/signInEmail`, {
			headers: {
				origin: "https://attacker.example",
				"content-type": "application/x-www-form-urlencoded",
			},
			data: "email=csrf-probe@example.test&password=nope",
		});

		// Kit 3 CSRF protection is always-on: the derived origin
		// (http://localhost:5173 from x-forwarded-host/proto) does not match
		// the forged origin header, so the POST never reaches the action
		expect(response.status()).toBe(403);
	});
});
