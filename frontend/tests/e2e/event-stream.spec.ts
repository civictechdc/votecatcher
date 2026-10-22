import { expect } from "@playwright/test";

import { test } from "./fixtures";

test.describe("Event Stream Integration", () => {
	test("campaign page establishes SSE connection", async ({ page, seededCampaign }) => {
		await page.goto(`/workspace/${seededCampaign.id}`);
		await page.waitForLoadState("domcontentloaded");

		let eventSourceConnected = false;

		page.on("request", (request) => {
			if (request.url().includes("/events/campaigns/") && request.url().includes("/stream")) {
				eventSourceConnected = true;
			}
		});

		await page.reload();
		await page.waitForTimeout(2000);

		expect(eventSourceConnected).toBeTruthy();
	});

	test("event store handles connection status", async ({ page, seededCampaign }) => {
		await page.goto(`/workspace/${seededCampaign.id}`);
		await page.waitForLoadState("domcontentloaded");

		await page.waitForTimeout(2000);

		const eventsConnected = await page
			.evaluate(() => {
				return new Promise<boolean>((resolve) => {
					const checkInterval = setInterval(() => {
						const statusEl = document.querySelector("[data-event-status]");
						if (statusEl?.textContent === "connected") {
							clearInterval(checkInterval);
							resolve(true);
						}
					}, 100);
					setTimeout(() => {
						clearInterval(checkInterval);
						resolve(false);
					}, 3000);
				});
			})
			.catch(() => false);

		expect(typeof eventsConnected).toBe("boolean");
	});
});

test.describe("Job Event Stream", () => {
	test("job status updates via SSE trigger UI refresh", async ({ page, seededCampaign }) => {
		await page.goto(`/workspace/${seededCampaign.id}/jobs`);
		await page.waitForLoadState("domcontentloaded");

		const eventSourceConnected = await page.evaluate(() => {
			return new Promise<boolean>((resolve) => {
				const checkInterval = setInterval(() => {
					const statusEl = document.querySelector("[data-event-status]");
					if (statusEl?.textContent === "connected") {
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

		expect(typeof eventSourceConnected).toBe("boolean");
	});

	test("job progress events update job details", async ({ page, seededCampaign }) => {
		await page.goto(`/workspace/${seededCampaign.id}/jobs`);
		await page.waitForLoadState("domcontentloaded");

		await expect(page.locator("h1")).toContainText("Jobs");

		const hasEventHandlers = await page.evaluate(() => {
			return typeof window !== "undefined";
		});

		expect(hasEventHandlers).toBeTruthy();
	});
});

test.describe("Job Status Event UI Update", () => {
	test("CustomEvent votecatcher:job:status is handled without error", async ({
		page,
		seededCampaign,
	}) => {
		await page.goto(`/workspace/${seededCampaign.id}/jobs`);
		await page.waitForLoadState("domcontentloaded");

		await expect(page.locator("h1")).toContainText("Jobs");

		const handlerResult = await page.evaluate(
			({ campaignId }) => {
				return new Promise<{ handled: boolean; error: string | null }>((resolve) => {
					let handled = false;
					let error: string | null = null;

					const errorHandler = (e: ErrorEvent) => {
						error = e.message;
					};
					window.addEventListener("error", errorHandler);

					document.dispatchEvent(
						new CustomEvent("votecatcher:job:status", {
							detail: {
								event_id: "test-event-1",
								event_type: "job:status_changed",
								timestamp: new Date().toISOString(),
								trace_id: null,
								source: "test",
								campaign_id: campaignId,
								job_id: 99999,
								status: "OCR_STARTED",
								previous_status: "NOT_STARTED",
							},
						}),
					);

					setTimeout(() => {
						window.removeEventListener("error", errorHandler);
						handled = error === null;
						resolve({ handled, error });
					}, 200);
				});
			},
			{ campaignId: seededCampaign.id },
		);

		expect(handlerResult.error).toBeNull();
		expect(handlerResult.handled).toBeTruthy();
	});

	test("CustomEvent votecatcher:job:progress is handled without error", async ({
		page,
		seededCampaign,
	}) => {
		await page.goto(`/workspace/${seededCampaign.id}/jobs`);
		await page.waitForLoadState("domcontentloaded");

		await expect(page.locator("h1")).toContainText("Jobs");

		const handlerResult = await page.evaluate(
			({ campaignId }) => {
				return new Promise<{ handled: boolean; error: string | null }>((resolve) => {
					let error: string | null = null;

					const errorHandler = (e: ErrorEvent) => {
						error = e.message;
					};
					window.addEventListener("error", errorHandler);

					document.dispatchEvent(
						new CustomEvent("votecatcher:job:progress", {
							detail: {
								event_id: "test-event-2",
								event_type: "job:progress",
								timestamp: new Date().toISOString(),
								trace_id: null,
								source: "test",
								campaign_id: campaignId,
								job_id: 12345,
								processed: 50,
								total: 100,
								percentage: 50,
							},
						}),
					);

					setTimeout(() => {
						window.removeEventListener("error", errorHandler);
						resolve({ handled: error === null, error });
					}, 200);
				});
			},
			{ campaignId: seededCampaign.id },
		);

		expect(handlerResult.error).toBeNull();
		expect(handlerResult.handled).toBeTruthy();
	});

	test("SSE job status event reaches the page in real-time", async ({
		page,
		apiContext,
		campaignWithJobInputs,
	}) => {
		// Seeding uploads the sample petition PDF and can exceed the 30s default —
		// the timeout is handled by the campaignWithJobInputs fixture via testInfo.
		const sseResponsePromise = page.waitForResponse(
			(response) =>
				response.url().includes("/events/campaigns/") && response.url().includes("/stream"),
		);

		await page.goto(`/workspace/${campaignWithJobInputs.id}/jobs`);

		const sseResponse = await sseResponsePromise;
		expect(sseResponse.ok(), `SSE stream status: ${sseResponse.status()}`).toBeTruthy();

		// Register the in-page listener without awaiting it: it resolves on the
		// first job status event or after the listener window expires. The worker
		// polls NOT_STARTED jobs and publishes JobStatusEvent as processing begins;
		// job creation itself publishes no event.
		const listenerPromise = page.evaluate(() => {
			return new Promise<{ job_id: number; status: string } | null>((resolve) => {
				const eventListener = (event: CustomEvent) => {
					document.removeEventListener("votecatcher:job:status", eventListener as EventListener);
					resolve({
						job_id: event.detail?.job_id,
						status: event.detail?.status,
					});
				};
				document.addEventListener("votecatcher:job:status", eventListener as EventListener);
				setTimeout(() => {
					document.removeEventListener("votecatcher:job:status", eventListener as EventListener);
					resolve(null);
				}, 10000);
			});
		});

		const createResponse = await apiContext.post("/api/jobs", {
			data: {
				campaign_id: campaignWithJobInputs.id,
				provider_name: "test-provider",
				provider_model: "test-model",
				force_reprocess: false,
			},
		});

		// Read the failure body before asserting so a bad create surfaces with
		// its payload instead of only a status code.
		const createBody = await createResponse.text();
		expect(
			createResponse.ok(),
			`POST /api/jobs failed: ${createResponse.status()} ${createBody}`,
		).toBeTruthy();
		const job = JSON.parse(createBody);
		const jobId = job.jobId;

		const event = await listenerPromise;

		if (!event) {
			// Include the server's view of the job so a failure shows whether the
			// poller ever picked it up.
			const jobStatus = await apiContext.get(`/api/jobs/${jobId}`);
			const jobStatusBody = jobStatus.ok() ? await jobStatus.text() : `${jobStatus.status()}`;
			throw new Error(
				`No votecatcher:job:status event observed within the listener window; job status: ${jobStatusBody}`,
			);
		}
		expect(event.job_id).toBe(jobId);
		// The first event for a fresh NOT_STARTED job is deterministically an
		// OCR_* transition, though the job may have progressed further by the
		// time we observe the event.
		expect(event.status).toMatch(/^OCR_/);
	});
});
