import { expect, test } from '@playwright/test';

test.describe('Dashboard', () => {
	test('should redirect workspace to campaigns', async ({ page }) => {
		await page.goto('/workspace');

		await page.waitForURL(/.*campaigns/, { timeout: 5000 }).catch(() => {});

		await expect(page).toHaveURL(/.*campaigns/);
	});

	test('should display campaigns page', async ({ page }) => {
		await page.goto('/workspace/campaigns');

		await expect(page.locator('h1')).toContainText('Campaigns');
	});

	test('should navigate via sidebar', async ({ page }) => {
		await page.goto('/workspace/campaigns');
		await page.waitForLoadState('domcontentloaded');

		await page.click('text=Settings');
		await expect(page).toHaveURL(/.*settings/);

		await page.click('text=Campaigns');
		await expect(page).toHaveURL(/.*campaigns/);
	});
});

test.describe('Campaign Dashboard Flow', () => {
	test('should navigate to campaign dashboard', async ({ page }) => {
		await page.goto('/workspace/campaigns');
		await page.waitForLoadState('domcontentloaded');

		const campaignLink = page.locator('table a[href^="/workspace/"]').first();
		if (await campaignLink.isVisible({ timeout: 5000 }).catch(() => false)) {
			await campaignLink.click();

			await expect(page.locator('h1').first()).toBeVisible();
		} else {
			test.skip();
		}
	});
});
