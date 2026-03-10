import { expect, test } from '@playwright/test';

test.describe('Campaign Management', () => {
	test.beforeEach(async ({ page }) => {
		await page.goto('/workspace');
	});

	test('should display campaigns page', async ({ page }) => {
		await page.click('text=Campaigns');
		await expect(page).toHaveURL(/.*workspace\/campaigns/);
		await expect(page.locator('h1')).toContainText('Campaigns');
	});

	test('should have create campaign button', async ({ page }) => {
		await page.goto('/workspace/campaigns');

		await expect(page.locator('button:has-text("Create Campaign")')).toBeVisible();
	});

	test('should navigate between pages', async ({ page }) => {
		await page.goto('/workspace');

		await page.click('text=Campaigns');
		await expect(page).toHaveURL(/.*campaigns/);

		await page.click('text=Jobs');
		await expect(page).toHaveURL(/.*jobs/);

		await page.click('text=Results');
		await expect(page).toHaveURL(/.*results/);
	});
});
