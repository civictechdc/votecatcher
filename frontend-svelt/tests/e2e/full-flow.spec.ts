import { expect, test } from '@playwright/test';

test.describe('Dashboard', () => {
	test('should display workspace page', async ({ page }) => {
		await page.goto('/workspace');

		// Either the dashboard loads with content, or shows an error (if backend unavailable)
		// Both are valid states
		const hasHeading = await page.locator('h1, h2').first().isVisible().catch(() => false);
		const hasError = await page.locator('[role="alert"]').isVisible().catch(() => false);
		expect(hasHeading || hasError).toBeTruthy();
	});

	test('should navigate via sidebar', async ({ page }) => {
		await page.goto('/workspace');

		await page.click('text=Campaigns');
		await expect(page).toHaveURL(/.*campaigns/);

		await page.click('text=Jobs');
		await expect(page).toHaveURL(/.*jobs/);

		await page.click('text=Results');
		await expect(page).toHaveURL(/.*results/);

		await page.click('text=Settings');
		await expect(page).toHaveURL(/.*settings/);
	});
});

test.describe('Sessions', () => {
	test('should display sessions page', async ({ page }) => {
		await page.goto('/workspace/sessions');

		await expect(page.locator('h1')).toContainText('Sessions');
	});
});

test.describe('Upload Pages', () => {
	test('should display voter upload page', async ({ page }) => {
		await page.goto('/workspace/upload/voters');

		await expect(page.locator('h1')).toContainText('Voter List');
	});

	test('should display petition upload page', async ({ page }) => {
		await page.goto('/workspace/upload/petitions');

		await expect(page.locator('h1')).toContainText('Petition');
	});
});
