import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility Audit', () => {
	test('landing page should have no WCAG 2.2 AA violations', async ({ page }) => {
		await page.goto('/');
		await page.waitForLoadState('domcontentloaded');

		const accessibilityScanResults = await new AxeBuilder({ page })
			.withTags(['wcag2a', 'wcag2aa', 'wcag22aa'])
			.analyze();

		expect(accessibilityScanResults.violations).toEqual([]);
	});

	test('campaigns page should have no WCAG 2.2 AA violations', async ({ page }) => {
		await page.goto('/workspace/campaigns');
		await page.waitForLoadState('domcontentloaded');

		const accessibilityScanResults = await new AxeBuilder({ page })
			.withTags(['wcag2a', 'wcag2aa', 'wcag22aa'])
			.analyze();

		expect(accessibilityScanResults.violations).toEqual([]);
	});

	test('demo page should have no WCAG 2.2 AA violations', async ({ page }) => {
		await page.goto('/workspace/demo');
		await page.waitForLoadState('domcontentloaded');

		const accessibilityScanResults = await new AxeBuilder({ page })
			.withTags(['wcag2a', 'wcag2aa', 'wcag22aa'])
			.analyze();

		expect(accessibilityScanResults.violations).toEqual([]);
	});

	test('settings page should have no WCAG 2.2 AA violations', async ({ page }) => {
		await page.goto('/workspace/settings');
		await page.waitForLoadState('domcontentloaded');

		const accessibilityScanResults = await new AxeBuilder({ page })
			.withTags(['wcag2a', 'wcag2aa', 'wcag22aa'])
			.analyze();

		expect(accessibilityScanResults.violations).toEqual([]);
	});

	test('campaign dashboard should have no WCAG 2.2 AA violations', async ({ page }) => {
		await page.goto('/workspace/campaigns');
		await page.waitForLoadState('domcontentloaded');

		const campaignLink = page.locator('table a[href^="/workspace/"]').first();
		if (await campaignLink.isVisible({ timeout: 5000 }).catch(() => false)) {
			await campaignLink.click();
			await page.waitForLoadState('domcontentloaded');

			const accessibilityScanResults = await new AxeBuilder({ page })
				.withTags(['wcag2a', 'wcag2aa', 'wcag22aa'])
				.analyze();

			expect(accessibilityScanResults.violations).toEqual([]);
		} else {
			test.skip();
		}
	});
});

test.describe('Color Contrast', () => {
	test('all text should meet minimum contrast ratio', async ({ page }) => {
		await page.goto('/workspace/campaigns');
		await page.waitForLoadState('domcontentloaded');

		const contrastResults = await new AxeBuilder({ page })
			.withRules(['color-contrast'])
			.analyze();

		const violations = contrastResults.violations.filter((v) => v.id === 'color-contrast');
		expect(violations).toEqual([]);
	});
});

test.describe('Keyboard Navigation', () => {
	test('sidebar navigation should be keyboard accessible', async ({ page }) => {
		await page.goto('/workspace/campaigns');
		await page.waitForLoadState('domcontentloaded');

		await page.keyboard.press('Tab');

		const focusedElement = await page.evaluateHandle(() => document.activeElement);
		const tagName = await focusedElement.evaluate((el) => el?.tagName.toLowerCase() ?? '');

		expect(['a', 'button', 'input', 'select', 'textarea']).toContain(tagName);
	});

	test('can navigate to all sidebar links with Tab', async ({ page }) => {
		await page.goto('/workspace/campaigns');
		await page.waitForLoadState('domcontentloaded');

		const tabPresses = 10;
		for (let i = 0; i < tabPresses; i++) {
			await page.keyboard.press('Tab');
			await page.waitForTimeout(50);
		}

		const focusedElement = await page.evaluateHandle(() => document.activeElement);
		const isFocusable = await focusedElement.evaluate((el) => {
			const tag = el?.tagName.toLowerCase() ?? '';
			return ['a', 'button', 'input', 'select', 'textarea'].includes(tag);
		});

		expect(isFocusable).toBeTruthy();
	});

	test('landing page CTA is keyboard accessible', async ({ page }) => {
		await page.goto('/');
		await page.waitForLoadState('domcontentloaded');

		const ctaButton = page.locator('a:has-text("Start")').first();
		await expect(ctaButton).toBeVisible();

		await ctaButton.focus();
		await expect(ctaButton).toBeFocused();

		await page.keyboard.press('Enter');
		await page.waitForURL(url => url.pathname !== '/', { timeout: 5000 });

		expect(page.url()).not.toBe('http://localhost:5173/');
	});
});
