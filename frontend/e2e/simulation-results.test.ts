import { expect, test } from "@playwright/test";

test.describe("Simulation Results E2E", () => {
	test("workspace demo page loads with expected elements", async ({ page }) => {
		await page.goto("/workspace/demo");

		await expect(page.locator("h3")).toContainText("Workspace");
		await expect(page.locator("text=Upload")).toBeVisible();
		await expect(page.locator('button:has-text("Run Matching")')).toBeVisible();
		await expect(page.locator("text=No matches yet")).toBeVisible();
	});

	test("simulation toggle checkbox exists", async ({ page }) => {
		await page.goto("/workspace/demo");
		const checkbox = page.locator('label:has-text("Use Simulated Data") input');
		await expect(checkbox).toBeVisible();
	});
});
