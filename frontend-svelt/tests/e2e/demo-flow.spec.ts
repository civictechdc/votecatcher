import { expect, test } from '@playwright/test';

test.describe('Demo Flow', () => {
	test('complete demo workflow', async ({ page }) => {
		// Navigate to demo page
		await page.goto('/workspace/demo');

		// Load pre-baked session
		await page.click('button:has-text("Load DC Petition Demo")');

		// Wait for success
		await expect(page.locator('text=Loaded demo session')).toBeVisible({ timeout: 10000 });

		// Verify campaign was created
		await page.goto('/workspace/campaigns');
		await expect(page.locator('text=DC Demo 2024')).toBeVisible();

		// Verify results exist
		await page.goto('/workspace/results');
		await expect(page.locator('table')).toBeVisible();

		// Reset demo
		await page.goto('/workspace/demo');
		await page.click('button:has-text("Reset Demo")');
		await page.click('button:has-text("Confirm")');

		// Verify reset
		await page.goto('/workspace/campaigns');
		await expect(page.locator('text=DC Demo 2024')).not.toBeVisible();
	});
});
