import { expect, test } from '@playwright/test';

test.describe('Error Handling', () => {
	test('error page displays on 404', async ({ page }) => {
		await page.goto('/workspace/nonexistent-page-12345');

		await expect(page.locator('h1').first()).toBeVisible({ timeout: 5000 });
	});

	test('error page has navigation options', async ({ page }) => {
		await page.goto('/workspace/nonexistent-page-12345');
		await page.waitForLoadState('domcontentloaded');

		const hasButton = await page.locator('button').count() > 0;
		const hasLink = await page.locator('a').count() > 0;

		expect(hasButton || hasLink).toBeTruthy();
	});

	test('campaigns page handles loading state', async ({ page }) => {
		await page.goto('/workspace/campaigns');

		await expect(page.locator('h1')).toContainText('Campaigns');
	});

	test('workspace redirects to campaigns', async ({ page }) => {
		await page.goto('/workspace');

		await page.waitForURL(/.*campaigns/, { timeout: 5000 }).catch(() => {});

		await expect(page).toHaveURL(/.*campaigns/);
	});

	test('demo page shows heading', async ({ page }) => {
		await page.goto('/workspace/demo');

		await expect(page.locator('h1')).toContainText('Demo Mode');
	});

	test('settings page loads', async ({ page }) => {
		await page.goto('/workspace/settings');

		await expect(page.locator('h1').first()).toBeVisible();
	});
});
