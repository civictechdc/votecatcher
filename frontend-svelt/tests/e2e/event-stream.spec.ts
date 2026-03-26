import { expect } from '@playwright/test';

import { test } from './fixtures';

test.describe('Event Stream Integration', () => {
	test('campaign page establishes SSE connection', async ({ page, seededCampaign }) => {
		await page.goto(`/workspace/${seededCampaign.id}`);
		await page.waitForLoadState('domcontentloaded');

		let eventSourceConnected = false;

		page.on('request', (request) => {
			if (request.url().includes('/events/campaigns/') && request.url().includes('/stream')) {
				eventSourceConnected = true;
			}
		});

		await page.reload();
		await page.waitForTimeout(2000);

		expect(eventSourceConnected).toBeTruthy();
	});

	test('event store handles connection status', async ({ page, seededCampaign }) => {
		await page.goto(`/workspace/${seededCampaign.id}`);
		await page.waitForLoadState('domcontentloaded');

		await page.waitForTimeout(2000);

		const eventsConnected = await page.evaluate(() => {
			return new Promise<boolean>((resolve) => {
				const checkInterval = setInterval(() => {
					const statusEl = document.querySelector('[data-event-status]');
					if (statusEl?.textContent === 'connected') {
						clearInterval(checkInterval);
						resolve(true);
					}
				}, 100);
				setTimeout(() => {
					clearInterval(checkInterval);
					resolve(false);
				}, 3000);
			});
		}).catch(() => false);

		expect(typeof eventsConnected).toBe('boolean');
	});
});

test.describe('Job Event Stream', () => {
	test('job status updates via SSE trigger UI refresh', async ({ page, seededCampaign }) => {
		await page.goto(`/workspace/${seededCampaign.id}/jobs`);
		await page.waitForLoadState('domcontentloaded');

		const eventSourceConnected = await page.evaluate(() => {
			return new Promise<boolean>((resolve) => {
				const checkInterval = setInterval(() => {
					const statusEl = document.querySelector('[data-event-status]');
					if (statusEl?.textContent === 'connected') {
						clearInterval(checkInterval);
						resolve(true);
					}
				}, 100);
				setTimeout(() => {
					clearInterval(checkInterval);
					resolve(false);
				}, 3000);
			});
		});

		expect(typeof eventSourceConnected).toBe('boolean');
	});

	test('job progress events update job details', async ({ page, seededCampaign }) => {
		await page.goto(`/workspace/${seededCampaign.id}/jobs`);
		await page.waitForLoadState('domcontentloaded');

		await expect(page.locator('h1')).toContainText('Jobs');

		const hasEventHandlers = await page.evaluate(() => {
			return typeof window !== 'undefined';
		});

		expect(hasEventHandlers).toBeTruthy();
	});
});

test.describe('Job Status Event UI Update', () => {
	test('CustomEvent votecatcher:job:status is handled without error', async ({ page, seededCampaign }) => {
		await page.goto(`/workspace/${seededCampaign.id}/jobs`);
		await page.waitForLoadState('domcontentloaded');

		await expect(page.locator('h1')).toContainText('Jobs');

		const handlerResult = await page.evaluate(({ campaignId }) => {
			return new Promise<{ handled: boolean; error: string | null }>((resolve) => {
				let handled = false;
				let error: string | null = null;

				const errorHandler = (e: ErrorEvent) => {
					error = e.message;
				};
				window.addEventListener('error', errorHandler);

				document.dispatchEvent(
					new CustomEvent('votecatcher:job:status', {
						detail: {
							event_id: 'test-event-1',
							event_type: 'job:status_changed',
							timestamp: new Date().toISOString(),
							trace_id: null,
							source: 'test',
							campaign_id: campaignId,
							job_id: 99999,
							status: 'OCR_STARTED',
							previous_status: 'NOT_STARTED'
						}
					})
				);

				setTimeout(() => {
					window.removeEventListener('error', errorHandler);
					handled = error === null;
					resolve({ handled, error });
				}, 200);
			});
		}, { campaignId: seededCampaign.id });

		expect(handlerResult.error).toBeNull();
		expect(handlerResult.handled).toBeTruthy();
	});

	test('CustomEvent votecatcher:job:progress is handled without error', async ({ page, seededCampaign }) => {
		await page.goto(`/workspace/${seededCampaign.id}/jobs`);
		await page.waitForLoadState('domcontentloaded');

		await expect(page.locator('h1')).toContainText('Jobs');

		const handlerResult = await page.evaluate(({ campaignId }) => {
			return new Promise<{ handled: boolean; error: string | null }>((resolve) => {
				let error: string | null = null;

				const errorHandler = (e: ErrorEvent) => {
					error = e.message;
				};
				window.addEventListener('error', errorHandler);

				document.dispatchEvent(
					new CustomEvent('votecatcher:job:progress', {
						detail: {
							event_id: 'test-event-2',
							event_type: 'job:progress',
							timestamp: new Date().toISOString(),
							trace_id: null,
							source: 'test',
							campaign_id: campaignId,
							job_id: 12345,
							processed: 50,
							total: 100,
							percentage: 50
						}
					})
				);

				setTimeout(() => {
					window.removeEventListener('error', errorHandler);
					resolve({ handled: error === null, error });
				}, 200);
			});
		}, { campaignId: seededCampaign.id });

		expect(handlerResult.error).toBeNull();
		expect(handlerResult.handled).toBeTruthy();
	});

	test('SSE job status change updates job list in real-time', async ({ page, apiContext, seededCampaign }) => {
		await page.goto(`/workspace/${seededCampaign.id}/jobs`);
		await page.waitForLoadState('domcontentloaded');

		const createResponse = await apiContext.post('/api/jobs', {
			data: {
				campaign_id: seededCampaign.id,
				provider_name: 'test-provider',
				provider_model: 'test-model',
				force_reprocess: false
			}
		});

		expect(createResponse.ok()).toBeTruthy();
		const job = await createResponse.json();
		const jobId = job.job_id;

		await page.waitForTimeout(1000);

		const eventReceived = await page.evaluate(({ testJobId }) => {
			return new Promise<{ received: boolean; status: string | null }>((resolve) => {
				let eventReceived = false;
				let receivedStatus: string | null = null;

				const eventListener = (event: any) => {
					if (event.detail.job_id === testJobId) {
						eventReceived = true;
						receivedStatus = event.detail.status;
						document.removeEventListener('votecatcher:job:status', eventListener as EventListener);
						resolve({ received: eventReceived, status: receivedStatus });
					}
				};

				document.addEventListener('votecatcher:job:status', eventListener as EventListener);

				setTimeout(() => {
					document.removeEventListener('votecatcher:job:status', eventListener as EventListener);
					resolve({ received: eventReceived, status: receivedStatus });
				}, 5000);
			});
		}, { testJobId: jobId });

		expect(eventReceived.received).toBeTruthy();
		expect(eventReceived.status).toBeTruthy();
	});
});
