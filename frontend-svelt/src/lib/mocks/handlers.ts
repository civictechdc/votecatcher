import { rest } from 'msw';
import { featureFlags } from '$lib/config/featureFlags';

/**
 * Handlers used by the client-side MSW worker.
 * Driven by feature flags (VITE_FEATURES or localStorage vc:flags via DevFlags).
 *
 * Flags used:
 * - mockApi : enable the worker
 * - mock:session:loggedIn / mock:session:loggedOut
 * - mock:createCampaign:missingFields
 * - mock:createCampaign:success
 * - mock:createCampaign:delay
 *
 * Add more flags/handlers to simulate additional backend behaviors.
 */

function jsonSafe(req: any) {
	try {
		return req.json ? req.json() : {};
	} catch {
		return {};
	}
}

export const handlers = [
	// session endpoint used by server-side load and client code
	rest.get('/api/session', async (req, res, ctx) => {
		// Dev override: allow local toggles
		if (featureFlags.isEnabled('mock:session:loggedOut')) {
			return res(ctx.status(401), ctx.json({ error: 'Not authenticated' }));
		}
		if (featureFlags.isEnabled('mock:session:loggedIn')) {
			return res(
				ctx.status(200),
				ctx.json({
					user: { id: 'user_mock_1', email: 'dev@example.test' }
				})
			);
		}
		// Default: pass-through to real network (MSW config onUnhandledRequest: 'bypass')
		return res(ctx.status(401), ctx.json({ error: 'Not authenticated' }));
	}),

	// store API key endpoint (onboarding provider step)
	rest.post('/api/store-api-key', async (req, res, ctx) => {
		const body = await jsonSafe(req);
		const provider = body?.provider ?? body?.name ?? null;
		const apiKey = body?.apiKey ?? body?.api_key ?? null;

		if (!provider || !apiKey) {
			return res(ctx.status(400), ctx.json({ error: 'Missing provider or apiKey' }));
		}

		// Simulate small latency if requested
		if (featureFlags.isEnabled('mock:createCampaign:delay')) {
			await new Promise((r) => setTimeout(r, 600));
		}

		return res(ctx.status(200), ctx.json({ ok: true }));
	}),

	// create campaign
	rest.post('/api/create-campaign', async (req, res, ctx) => {
		const body = await jsonSafe(req);

		// explicit mocked failures/overrides
		if (featureFlags.isEnabled('mock:createCampaign:missingFields')) {
			return res(ctx.status(400), ctx.json({ error: 'Missing name or year (mocked)' }));
		}

		if (featureFlags.isEnabled('mock:createCampaign:delay')) {
			await new Promise((r) => setTimeout(r, 1200));
		}

		if (featureFlags.isEnabled('mock:createCampaign:success')) {
			return res(ctx.status(200), ctx.json({ id: 'mock_campaign_success_123' }));
		}

		// Normal validation to mirror your server real behavior
		if (!body?.name || !('year' in body) || body?.year === null || body?.year === undefined) {
			return res(ctx.status(400), ctx.json({ error: 'Missing name or year' }));
		}

		// Return an id similar to your server route
		return res(ctx.status(200), ctx.json({ id: 'campaign_abc123' }));
	}),

	// upload metadata
	rest.post('/api/upload-file', async (req, res, ctx) => {
		const body = await jsonSafe(req);
		if (!body?.fileName || !('size' in body)) {
			return res(ctx.status(400), ctx.json({ error: 'Missing file metadata' }));
		}
		return res(ctx.status(200), ctx.json({ uploadId: 'upload_mock_1' }));
	}),

	// trigger file processing
	rest.post('/api/process-voter-file', async (req, res, ctx) => {
		const body = await jsonSafe(req);
		if (!body?.filePath) {
			return res(ctx.status(400), ctx.json({ error: 'Missing filePath' }));
		}
		// simulate processing delay
		if (featureFlags.isEnabled('mock:createCampaign:delay')) {
			await new Promise((r) => setTimeout(r, 900));
		}
		return res(ctx.status(200), ctx.json({ jobId: 'process_job_mock_1' }));
	})
];
