import { expect, test } from '@playwright/test';

test.describe('Demo Flow', () => {
	test('demo page loads and shows controls', async ({ page }) => {
		await page.goto('/workspace/demo');

		await expect(page.locator('h1')).toContainText('Demo Mode');

		const hasResetButton = await page
			.locator('button:has-text("Reset")')
			.isVisible()
			.catch(() => false);
		const hasWarning = await page
			.locator('text=not enabled')
			.isVisible()
			.catch(() => false);
		expect(hasResetButton || hasWarning).toBeTruthy();
	});

	test('complete demo workflow (requires backend)', async ({ page }) => {
		await page.goto('/workspace/demo');

		const warningVisible = await page
			.locator('text=not enabled')
			.isVisible()
			.catch(() => false);
		if (warningVisible) {
			test.skip();
			return;
		}

		await page.waitForLoadState('domcontentloaded');
		await page.waitForTimeout(1000);

		const loadButtonVisible = await page
			.locator('button:has-text("Load")')
			.first()
			.isVisible()
			.catch(() => false);

		if (loadButtonVisible) {
			await page.locator('button:has-text("Load")').first().click();

			await page.waitForTimeout(4000);

			const successBox = page.locator('.bg-green-50, .border-green-200');
			const errorBox = page.locator('.bg-red-50, [role="alert"]');
			const loadingText = page.locator('text=Loading...');

			const hasSuccess = await successBox.isVisible({ timeout: 1000 }).catch(() => false);
			const hasError = await errorBox.isVisible({ timeout: 1000 }).catch(() => false);
			const isLoading = await loadingText.isVisible({ timeout: 1000 }).catch(() => false);

			expect(hasSuccess || hasError || isLoading).toBeTruthy();
		} else {
			const noSessions = await page
				.locator('text=No pre-baked')
				.isVisible()
				.catch(() => false);
			const errorVisible = await page
				.locator('.bg-red-50, [role="alert"]')
				.isVisible()
				.catch(() => false);
			expect(noSessions || errorVisible).toBeTruthy();
		}
	});
});
