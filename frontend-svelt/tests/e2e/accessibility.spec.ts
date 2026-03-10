import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility Audit', () => {
	test.beforeEach(async ({ page }) => {
		await page.goto('/workspace');
	});

	test('dashboard page should have no WCAG 2.2 AA violations', async ({ page }) => {
		await page.waitForLoadState('networkidle');

		const accessibilityScanResults = await new AxeBuilder({ page })
			.withTags(['wcag2a', 'wcag2aa', 'wcag22aa'])
			.analyze();

		expect(accessibilityScanResults.violations).toEqual([]);
	});

	test('campaigns page should have no WCAG 2.2 AA violations', async ({ page }) => {
		await page.goto('/workspace/campaigns');
		await page.waitForLoadState('networkidle');

		const accessibilityScanResults = await new AxeBuilder({ page })
			.withTags(['wcag2a', 'wcag2aa', 'wcag22aa'])
			.analyze();

		expect(accessibilityScanResults.violations).toEqual([]);
	});

	test('jobs page should have no WCAG 2.2 AA violations', async ({ page }) => {
		await page.goto('/workspace/jobs');
		await page.waitForLoadState('networkidle');

		const accessibilityScanResults = await new AxeBuilder({ page })
			.withTags(['wcag2a', 'wcag2aa', 'wcag22aa'])
			.analyze();

		expect(accessibilityScanResults.violations).toEqual([]);
	});

	test('sessions page should have no WCAG 2.2 AA violations', async ({ page }) => {
		await page.goto('/workspace/sessions');
		await page.waitForLoadState('networkidle');

		const accessibilityScanResults = await new AxeBuilder({ page })
			.withTags(['wcag2a', 'wcag2aa', 'wcag22aa'])
			.analyze();

		if (accessibilityScanResults.violations.length > 0) {
			console.log('Violations:', JSON.stringify(accessibilityScanResults.violations, null, 2));
		}

		expect(accessibilityScanResults.violations).toEqual([]);
	});

	test('settings page should have no WCAG 2.2 AA violations', async ({ page }) => {
		await page.goto('/workspace/settings');
		await page.waitForLoadState('networkidle');

		const accessibilityScanResults = await new AxeBuilder({ page })
			.withTags(['wcag2a', 'wcag2aa', 'wcag22aa'])
			.analyze();

		expect(accessibilityScanResults.violations).toEqual([]);
	});
});

test.describe('Color Contrast', () => {
	test('all text should meet minimum contrast ratio', async ({ page }) => {
		await page.goto('/workspace');
		await page.waitForLoadState('networkidle');

		const contrastResults = await new AxeBuilder({ page })
			.withRules(['color-contrast'])
			.analyze();

		const violations = contrastResults.violations.filter((v) => v.id === 'color-contrast');
		expect(violations).toEqual([]);
	});
});

test.describe('Keyboard Navigation', () => {
	test('sidebar navigation should be keyboard accessible', async ({ page }) => {
		await page.goto('/workspace');
		await page.waitForLoadState('networkidle');

		await page.keyboard.press('Tab');

		const focusedElement = await page.evaluateHandle(() => document.activeElement);
		const tagName = await focusedElement.evaluate((el) => el?.tagName.toLowerCase() ?? '');

		expect(['a', 'button', 'input', 'select', 'textarea']).toContain(tagName);
	});
});
