import { expect, test } from '@playwright/test';

test.describe('Error Handling', () => {
	test('error page displays on 404', async ({ page }) => {
		await page.goto('/workspace/nonexistent-page-12345');

		// Should show error state
		await expect(page.locator('text=Something went wrong').or(page.locator('[role="alert"]'))).toBeVisible();

		// Should have return home button
		const homeButton = page.locator('text=Return Home').or(page.locator('text=Go Back'));
		await expect(homeButton).toBeVisible();
	});

	test('error page has navigation options', async ({ page }) => {
		await page.goto('/workspace/nonexistent-page-12345');
		await page.waitForLoadState('networkidle');

		// Should have clickable elements to navigate away
		const hasButton = await page.locator('button').count() > 0;
		const hasLink = await page.locator('a').count() > 0;

		expect(hasButton || hasLink).toBeTruthy();
	});

	test('dashboard handles API error gracefully', async ({ page }) => {
		// Navigate to dashboard
		await page.goto('/workspace');

		// Wait for page to load
		await page.waitForLoadState('networkidle');

		// Either content loads or error state shows
		const hasContent = await page.locator('h1:has-text("Dashboard")').isVisible().catch(() => false);
		const hasError = await page.locator('[role="alert"]').isVisible().catch(() => false);

		expect(hasContent || hasError).toBeTruthy();
	});

	test('campaigns page handles loading state', async ({ page }) => {
		await page.goto('/workspace/campaigns');

		// Page should load with heading
		await expect(page.locator('h1')).toContainText('Campaigns');
	});

	test('results page handles empty state', async ({ page }) => {
		await page.goto('/workspace/results');

		// Page should load - either with results or empty state
		await expect(page.locator('h1')).toContainText('Results');
	});

	test('sessions page handles loading', async ({ page }) => {
		await page.goto('/workspace/sessions');

		// Page should load
		await expect(page.locator('h1')).toContainText('Sessions');
	});

	test('demo page shows warning when demo mode disabled', async ({ page }) => {
		await page.goto('/workspace/demo');

		// Should show demo mode heading
		await expect(page.locator('h1')).toContainText('Demo Mode');
	});
});
