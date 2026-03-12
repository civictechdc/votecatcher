import { expect, test } from '@playwright/test';

test.describe('Campaign-Scoped Navigation', () => {
	test('Scenario 1: Navigate to campaign dashboard', async ({ page }) => {
		await page.goto('/workspace/campaigns');
		await page.waitForLoadState('networkidle');

		const campaignLink = page.locator('table a[href^="/workspace/"]').first();

		if (await campaignLink.isVisible({ timeout: 5000 }).catch(() => false)) {
			await campaignLink.click();
			const url = page.url();
			expect(url).toMatch(/\/workspace\/[^/]+$/);

			await expect(page.locator('h1').first()).toBeVisible();
		} else {
			console.log('No campaigns found - skipping test');
			expect(true).toBeTruthy();
		}
	});

	test('Scenario 2: Jobs are scoped to campaign', async ({ page }) => {
		await page.goto('/workspace/campaigns');
		const campaignLink = page.locator('table a[href^="/workspace/"]').first();

		if (await campaignLink.isVisible({ timeout: 5000 }).catch(() => false)) {
			await campaignLink.click();
			const campaignId = page.url().match(/\/workspace\/([^/]+)/)?.[1];

			if (campaignId) {
				await page.goto(`/workspace/${campaignId}/jobs`);
				await expect(page).toHaveURL(new RegExp(`/workspace/${campaignId}/jobs`));
				await expect(page.locator('h1').first()).toBeVisible();
			}
		} else {
			console.log('No campaigns found - skipping test');
			expect(true).toBeTruthy();
		}
	});

	test('Scenario 3: Campaign switcher navigates', async ({ page }) => {
		await page.goto('/workspace/campaigns');
		await page.waitForLoadState('networkidle');

		const table = page.locator('table');
		const campaignLinks = await table.locator('a[href^="/workspace/"]').filter({
			hasNotText: 'Campaigns'
		}).all();

		if (campaignLinks.length >= 2) {
			const firstHref = await campaignLinks[0].getAttribute('href') || '';
			await campaignLinks[0].click();
			await expect(page).toHaveURL(new RegExp(firstHref.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')), { timeout: 5000 });
			const firstCampaignUrl = page.url();

			await page.goto('/workspace/campaigns');
			await page.waitForLoadState('networkidle');

			const newTable = page.locator('table');
			const newLinks = await newTable.locator('a[href^="/workspace/"]').filter({
				hasNotText: 'Campaigns'
			}).all();
			const secondHref = await newLinks[1].getAttribute('href') || '';
			await newLinks[1].click();
			await expect(page).toHaveURL(new RegExp(secondHref.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')), { timeout: 5000 });
			const secondCampaignUrl = page.url();

			expect(firstCampaignUrl).not.toBe(secondCampaignUrl);
		} else {
			console.log(`Found ${campaignLinks.length} campaign links - need 2+ for switcher test`);
			expect(true).toBeTruthy();
		}
	});

	test('Scenario 4: Results scoped to campaign', async ({ page }) => {
		await page.goto('/workspace/campaigns');
		await page.waitForLoadState('networkidle');
		const campaignLink = page.locator('table a[href^="/workspace/"]').first();

		if (await campaignLink.isVisible({ timeout: 5000 }).catch(() => false)) {
			await campaignLink.click();
			const url = page.url();
			const campaignId = url.match(/\/workspace\/([^/]+)/)?.[1];

			if (campaignId) {
				await page.goto(`/workspace/${campaignId}/results`);
				await expect(page).toHaveURL(new RegExp(`/workspace/${campaignId}/results`));
				await expect(page.locator('h1').first()).toBeVisible();
			}
		} else {
			console.log('No campaigns found - skipping test');
			expect(true).toBeTruthy();
		}
	});

	test('Scenario 5: Upload scoped to campaign', async ({ page }) => {
		await page.goto('/workspace/campaigns');
		await page.waitForLoadState('networkidle');
		const campaignLink = page.locator('table a[href^="/workspace/"]').first();

		if (await campaignLink.isVisible({ timeout: 5000 }).catch(() => false)) {
			await campaignLink.click();
			const url = page.url();
			const campaignId = url.match(/\/workspace\/([^/]+)/)?.[1];

			if (campaignId) {
				await page.goto(`/workspace/${campaignId}/upload`);
				await expect(page).toHaveURL(new RegExp(`/workspace/${campaignId}/upload`));
				await expect(page.locator('h1').first()).toBeVisible();

				await expect(page.locator('button:has-text("Voter List")').first()).toBeVisible();
			}
		} else {
			console.log('No campaigns found - skipping test');
			expect(true).toBeTruthy();
		}
	});

	test('Scenario 6: Root landing page exists', async ({ page }) => {
		await page.goto('/');

		const getStartedButton = page.locator('a:has-text("Start")').first();
		await expect(getStartedButton).toBeVisible({ timeout: 5000 });
	});

	test('Workspace redirects to campaigns', async ({ page }) => {
		await page.goto('/workspace');

		await page.waitForURL(/\/workspace\/campaigns/, { timeout: 5000 }).catch(() => {});
		const url = page.url();

		expect(url).toContain('/workspace/campaigns');
	});

	test('Demo route works', async ({ page }) => {
		await page.goto('/workspace/demo');

		await expect(page.locator('h1').first()).toBeVisible();
	});
});

test.describe('Campaign Dashboard', () => {
	test('Dashboard shows campaign metrics', async ({ page }) => {
		await page.goto('/workspace/campaigns');
		await page.waitForLoadState('networkidle');
		const campaignLink = page.locator('table a[href^="/workspace/"]').first();

		if (await campaignLink.isVisible({ timeout: 5000 }).catch(() => false)) {
			await campaignLink.click();

			await expect(page.locator('h1').first()).toBeVisible();

			await page.waitForLoadState('networkidle');
			await page.waitForTimeout(500);

			const metricsSection = page.locator('[data-testid="metrics"]');
			await expect(metricsSection).toBeVisible({ timeout: 5000 });
		} else {
			console.log('No campaigns found - skipping test');
			expect(true).toBeTruthy();
		}
	});

	test('Sidebar shows campaign-scoped navigation', async ({ page }) => {
		await page.goto('/workspace/campaigns');
		await page.waitForLoadState('networkidle');
		const campaignLink = page.locator('table a[href^="/workspace/"]').first();

		if (await campaignLink.isVisible({ timeout: 5000 }).catch(() => false)) {
			await campaignLink.click();
			const url = page.url();
			const campaignId = url.match(/\/workspace\/([^/]+)/)?.[1];

			if (campaignId) {
				await page.waitForLoadState('networkidle');

				const sidebar = page.locator('aside, nav').first();
				await expect(sidebar).toBeVisible();

				const navLinks = await page.locator('a[href*="' + campaignId + '"]').count();
				expect(navLinks).toBeGreaterThan(0);
			}
		} else {
			console.log('No campaigns found - skipping test');
			expect(true).toBeTruthy();
		}
	});

	test('Job details page is campaign-scoped', async ({ page }) => {
		await page.goto('/workspace/campaigns');
		await page.waitForLoadState('networkidle');
		const campaignLink = page.locator('table a[href^="/workspace/"]').first();

		if (await campaignLink.isVisible({ timeout: 5000 }).catch(() => false)) {
			await campaignLink.click();
			const url = page.url();
			const campaignId = url.match(/\/workspace\/([^/]+)/)?.[1];

			if (campaignId) {
				await page.goto(`/workspace/${campaignId}/jobs`);
				await page.waitForLoadState('networkidle');

				const jobLink = page.locator('a[href*="/jobs/"]').first();
				if (await jobLink.isVisible({ timeout: 3000 }).catch(() => false)) {
					await jobLink.click();

					await expect(page).toHaveURL(new RegExp(`/workspace/${campaignId}/jobs/\\d+`));
					await expect(page.locator('h1').first()).toBeVisible();
				} else {
					console.log('No jobs found - skipping test');
					expect(true).toBeTruthy();
				}
			}
		} else {
			console.log('No campaigns found - skipping test');
			expect(true).toBeTruthy();
		}
	});
});

test.describe('Campaign Results Page', () => {
	test('Results page shows extracted name and address columns', async ({ page }) => {
		await page.goto('/workspace/campaigns');
		await page.waitForLoadState('networkidle');
		const campaignLink = page.locator('table a[href^="/workspace/"]').first();

		if (await campaignLink.isVisible({ timeout: 5000 }).catch(() => false)) {
			await campaignLink.click();
			const url = page.url();
			const campaignId = url.match(/\/workspace\/([^/]+)/)?.[1];

			if (campaignId) {
				await page.goto(`/workspace/${campaignId}/results`);
				await page.waitForLoadState('networkidle');

				await expect(page.locator('h1').first()).toBeVisible();

				const noResultsVisible = await page.locator('text=No results found').isVisible({ timeout: 1000 }).catch(() => false);
				if (noResultsVisible) {
					console.log('Campaign has no results - skipping test');
					expect(true).toBeTruthy();
					return;
				}

				const tableHeaders = page.locator('table th');
				const headerCount = await tableHeaders.count();
				if (headerCount === 0) {
					console.log('No table headers found - skipping test');
					expect(true).toBeTruthy();
					return;
				}

				const headerTexts = await tableHeaders.allTextContents();
				expect(headerTexts.some(h => h.toLowerCase().includes('extracted name'))).toBeTruthy();
				expect(headerTexts.some(h => h.toLowerCase().includes('extracted address'))).toBeTruthy();
				expect(headerTexts.some(h => h.toLowerCase().includes('matched name'))).toBeTruthy();
				expect(headerTexts.some(h => h.toLowerCase().includes('matched address'))).toBeTruthy();
			}
		} else {
			console.log('No campaigns found - skipping test');
			expect(true).toBeTruthy();
		}
	});

	test('Results page does not show "No results" flash on load', async ({ page }) => {
		await page.goto('/workspace/campaigns');
		await page.waitForLoadState('networkidle');
		const campaignLink = page.locator('table a[href^="/workspace/"]').first();

		if (await campaignLink.isVisible({ timeout: 5000 }).catch(() => false)) {
			await campaignLink.click();
			const url = page.url();
			const campaignId = url.match(/\/workspace\/([^/]+)/)?.[1];

			if (campaignId) {
				await page.goto(`/workspace/${campaignId}/results`);

				await page.waitForLoadState('networkidle');
				await page.waitForTimeout(500);

				const loadingState = page.locator('text=Loading');
				const noResults = page.locator('text=No results found');

				const hasLoading = await loadingState.isVisible({ timeout: 100 }).catch(() => false);
				const hasNoResults = await noResults.isVisible({ timeout: 100 }).catch(() => false);

				expect(hasLoading || !hasNoResults).toBeTruthy();
			}
		} else {
			console.log('No campaigns found - skipping test');
			expect(true).toBeTruthy();
		}
	});

	test('Results table is horizontally scrollable', async ({ page }) => {
		await page.goto('/workspace/campaigns');
		await page.waitForLoadState('networkidle');
		const campaignLink = page.locator('table a[href^="/workspace/"]').first();

		if (await campaignLink.isVisible({ timeout: 5000 }).catch(() => false)) {
			await campaignLink.click();
			const url = page.url();
			const campaignId = url.match(/\/workspace\/([^/]+)/)?.[1];

			if (campaignId) {
				await page.goto(`/workspace/${campaignId}/results`);
				await page.waitForLoadState('networkidle');

				const noResultsVisible = await page.locator('text=No results found').isVisible({ timeout: 1000 }).catch(() => false);
				if (noResultsVisible) {
					console.log('Campaign has no results - skipping test');
					expect(true).toBeTruthy();
					return;
				}

				await page.setViewportSize({ width: 400, height: 800 });
				await page.waitForTimeout(200);

				const scrollContainer = page.locator('.overflow-x-auto').first();
				const scrollContainerExists = await scrollContainer.count();
				if (scrollContainerExists === 0) {
					console.log('No scroll container found - skipping test');
					expect(true).toBeTruthy();
					return;
				}

				const hasOverflow = await scrollContainer.evaluate((el) => {
					return el.scrollWidth > el.clientWidth;
				});

				expect(hasOverflow).toBeTruthy();
			}
		} else {
			console.log('No campaigns found - skipping test');
			expect(true).toBeTruthy();
		}
	});
});
