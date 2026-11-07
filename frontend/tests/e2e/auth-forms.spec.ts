import { expect } from "@playwright/test";
import type { Page, Response } from "@playwright/test";

import { test } from "@playwright/test";

const LOGIN_PATH = "/demo/better-auth/login";
const AUTHED_PATH = "/demo/better-auth";

const EMAIL_DOMAIN = "@example.test";

/**
 * Characterization suite for the better-auth demo form actions
 * (`src/routes/(app)/demo/better-auth/**`).
 *
 * These tests PIN current SvelteKit 2 behavior as a tripwire for the
 * SvelteKit 3 upgrade. Notably, `use:enhance` form posts that hit a
 * `fail()` action are answered with HTTP 200 on Kit 2 (Kit 3 will surface
 * the real status code) — the status assertions below are deliberate and
 * must be flipped together with the migration (task 3.6).
 */

function uniqueEmail(): string {
	return `e2e-auth-${Date.now()}-${Math.floor(Math.random() * 10_000)}${EMAIL_DOMAIN}`;
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

test.describe("Better Auth Demo Forms (characterization)", () => {
	test("unauthenticated /demo/better-auth redirects to login", async ({ page }) => {
		await page.goto(AUTHED_PATH);
		await page.waitForURL(/\/demo\/better-auth\/login/, { timeout: 10_000 });
		await expect(page).toHaveURL(/\/demo\/better-auth\/login/);
		await expect(page.getByRole("button", { name: "Login", exact: true })).toBeVisible();
	});

	test("sign-up success registers user and lands on authed page", async ({ page }) => {
		const email = uniqueEmail();
		const name = `E2E Auth ${Date.now()}`;

		const response = await registerViaForm(page, email, "sup3r-secret-pw", name);

		await expect(page).toHaveURL(new RegExp(AUTHED_PATH.replace(/\//g, "\\/")));
		await expect(page.locator("h1")).toContainText(`Hi, ${name}!`);

		// status PIN (Kit 2): enhanced action POSTs answer HTTP 200 even when
		// the action redirects — the redirect is conveyed in the response body
		// and applied client-side. Kit 3 changes this; flip with task 3.6.
		expect(response.status()).toBe(200);
	});

	test("sign-out success returns to login page", async ({ page }) => {
		const email = uniqueEmail();
		const name = `E2E Auth ${Date.now()}`;
		await registerViaForm(page, email, "sup3r-secret-pw", name);
		await expect(page.locator("h1")).toContainText(`Hi, ${name}!`);

		const response = await signOutViaForm(page);

		await expect(page).toHaveURL(/\/demo\/better-auth\/login/);
		await expect(page.locator("h1")).toContainText("Login");

		// status PIN (Kit 2): enhanced signOut POST answers HTTP 200; the
		// redirect to /demo/better-auth/login is body-carried and applied
		// client-side. Kit 3 changes this; flip with task 3.6.
		expect(response.status()).toBe(200);
	});

	test("sign-in success with registered credentials", async ({ page }) => {
		const email = uniqueEmail();
		const name = `E2E Auth ${Date.now()}`;
		await registerViaForm(page, email, "sup3r-secret-pw", name);
		await expect(page.locator("h1")).toContainText(`Hi, ${name}!`);
		await signOutViaForm(page);
		await expect(page).toHaveURL(/\/demo\/better-auth\/login/);

		const response = await signInViaForm(page, email, "sup3r-secret-pw");

		await expect(page.locator("h1")).toContainText(`Hi, ${name}!`);

		// status PIN (Kit 2): successful signInEmail enhanced POST answers
		// HTTP 200; redirect is body-carried. Flip with task 3.6.
		expect(response.status()).toBe(200);
	});

	test("sign-in failure with wrong password shows error message", async ({ page }) => {
		const email = uniqueEmail();
		const name = `E2E Auth ${Date.now()}`;
		await registerViaForm(page, email, "sup3r-secret-pw", name);
		await signOutViaForm(page);

		const response = await signInViaForm(page, email, "wrong-password-1");

		await expect(page).toHaveURL(/\/demo\/better-auth\/login/);
		const message = await page.locator("p.text-red-500").textContent();
		expect(message?.trim().length ?? 0).toBeGreaterThan(0);

		// status PIN (Kit 2): fail(400) action answered as HTTP 200 to the
		// enhanced post — Kit 3 will return the real status; flip with task 3.6
		expect(response.status()).toBe(200);
	});

	test("sign-up failure with duplicate email shows error message", async ({ page }) => {
		const email = uniqueEmail();
		const name = `E2E Auth ${Date.now()}`;
		await registerViaForm(page, email, "sup3r-secret-pw", name);
		await expect(page.locator("h1")).toContainText(`Hi, ${name}!`);
		await signOutViaForm(page);

		const response = await registerViaForm(page, email, "another-secret-pw", name);

		await expect(page).toHaveURL(/\/demo\/better-auth\/login/);
		const message = await page.locator("p.text-red-500").textContent();
		expect(message?.trim().length ?? 0).toBeGreaterThan(0);

		// status PIN (Kit 2): fail(400) action answered as HTTP 200 to the
		// enhanced post — Kit 3 will return the real status; flip with task 3.6
		expect(response.status()).toBe(200);
	});
});
