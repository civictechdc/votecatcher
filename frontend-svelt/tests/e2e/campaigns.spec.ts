import { expect, test } from '@playwright/test';

test.describe('Campaign Management', () => {
	test('should display campaigns page', async ({ page }) => {
		await page.goto('/workspace/campaigns');
		await expect(page.locator('h1')).toContainText('Campaigns');
	});

	test('should have create campaign button', async ({ page }) => {
		await page.goto('/workspace/campaigns');

		await expect(page.locator('button:has-text("Create Campaign")')).toBeVisible();
	});

	test('workspace redirects to campaigns', async ({ page }) => {
		await page.goto('/workspace');

		await page.waitForURL(/.*campaigns/, { timeout: 5000 });

		await expect(page).toHaveURL(/.*campaigns/);
	});

	test('should navigate to campaign dashboard from list', async ({ page }) => {
		await page.goto('/workspace/campaigns');
		await page.waitForLoadState('networkidle');

		const campaignLink = page.locator('table a[href^="/workspace/"]').first();
		if (await campaignLink.isVisible({ timeout: 5000 }).catch(() => false)) {
			await campaignLink.click();

			await expect(page.locator('h1').first()).toBeVisible();
		} else {
			test.skip();
		}
	});
});
