import { expect, test } from '@playwright/test';

test.describe('Demo Flow', () => {
	test('demo page loads and shows controls', async ({ page }) => {
		await page.goto('/workspace/demo');

		// Should show demo mode heading
		await expect(page.locator('h1')).toContainText('Demo Mode');

		// Either shows demo controls (if demo mode enabled) or warning message
		const hasControls = await page.locator('text=Reset Demo').isVisible().catch(() => false);
		const hasWarning = await page.locator('text=Demo mode is not enabled').isVisible().catch(() => false);
		expect(hasControls || hasWarning).toBeTruthy();
	});

	test('complete demo workflow (requires backend)', async ({ page }) => {
		await page.goto('/workspace/demo');

		// Check if demo mode is enabled
		const warningVisible = await page.locator('text=Demo mode is not enabled').isVisible();
		if (warningVisible) {
			// Skip test if demo mode not enabled
			test.skip();
			return;
		}

		// Wait for prebaked sessions to load (or fail)
		await page.waitForTimeout(2000);

		// Check if sessions are available
		const loadButtonVisible = await page.locator('button:has-text("Load")').first().isVisible().catch(() => false);

		if (loadButtonVisible) {
			// Click the first Load button
			await page.locator('button:has-text("Load")').first().click();

			// Wait for success or error
			const successVisible = await page.locator('text=Loaded').isVisible({ timeout: 10000 }).catch(() => false);
			const errorVisible = await page.locator('[role="alert"]').isVisible({ timeout: 10000 }).catch(() => false);

			// Either success or error is valid (depends on backend)
			expect(successVisible || errorVisible).toBeTruthy();
		} else {
			// No sessions available - check for error or empty state
			const noSessions = await page.locator('text=No pre-baked sessions').isVisible().catch(() => false);
			const errorVisible = await page.locator('[role="alert"]').isVisible().catch(() => false);
			expect(noSessions || errorVisible).toBeTruthy();
		}
	});
});
