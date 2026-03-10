import { http, HttpResponse } from 'msw';
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

async function jsonSafe(request: Request) {
	try {
		return await request.json();
	} catch {
		return {};
	}
}

export const handlers = [
	// session endpoint used by server-side load and client code
	http.get('/api/session', async () => {
		// Dev override: allow local toggles
		if (featureFlags.isEnabled('mock:session:loggedOut')) {
			return new HttpResponse(JSON.stringify({ error: 'Not authenticated' }), {
				status: 401,
				headers: { 'Content-Type': 'application/json' }
			});
		}
		if (featureFlags.isEnabled('mock:session:loggedIn')) {
			return new HttpResponse(
				JSON.stringify({
					user: { id: 'user_mock_1', email: 'dev@example.test' }
				}),
				{
					status: 200,
					headers: { 'Content-Type': 'application/json' }
				}
			);
		}
		// Default: pass-through to real network (MSW config onUnhandledRequest: 'bypass')
		return new HttpResponse(JSON.stringify({ error: 'Not authenticated' }), {
			status: 401,
			headers: { 'Content-Type': 'application/json' }
		});
	}),

	// store API key endpoint (onboarding provider step)
	http.post('/api/store-api-key', async ({ request }) => {
		const body = await jsonSafe(request);
		const provider = (body as any)?.provider ?? (body as any)?.name ?? null;
		const apiKey = (body as any)?.apiKey ?? (body as any)?.api_key ?? null;

		if (!provider || !apiKey) {
			return new HttpResponse(JSON.stringify({ error: 'Missing provider or apiKey' }), {
				status: 400,
				headers: { 'Content-Type': 'application/json' }
			});
		}

		// Simulate small latency if requested
		if (featureFlags.isEnabled('mock:createCampaign:delay')) {
			await new Promise((r) => setTimeout(r, 600));
		}

		return new HttpResponse(JSON.stringify({ ok: true }), {
			status: 200,
			headers: { 'Content-Type': 'application/json' }
		});
	}),

	// create campaign
	http.post('/api/create-campaign', async ({ request }) => {
		const body = await jsonSafe(request);

		// explicit mocked failures/overrides
		if (featureFlags.isEnabled('mock:createCampaign:missingFields')) {
			return new HttpResponse(JSON.stringify({ error: 'Missing name or year (mocked)' }), {
				status: 400,
				headers: { 'Content-Type': 'application/json' }
			});
		}

		if (featureFlags.isEnabled('mock:createCampaign:delay')) {
			await new Promise((r) => setTimeout(r, 1200));
		}

		if (featureFlags.isEnabled('mock:createCampaign:success')) {
			return new HttpResponse(JSON.stringify({ id: 'mock_campaign_success_123' }), {
				status: 200,
				headers: { 'Content-Type': 'application/json' }
			});
		}

		// Normal validation to mirror your server real behavior
		if (!(body as any)?.name || !('year' in (body as any)) || (body as any)?.year === null || (body as any)?.year === undefined) {
			return new HttpResponse(JSON.stringify({ error: 'Missing name or year' }), {
				status: 400,
				headers: { 'Content-Type': 'application/json' }
			});
		}

		// Return an id similar to your server route
		return new HttpResponse(JSON.stringify({ id: 'campaign_abc123' }), {
			status: 200,
			headers: { 'Content-Type': 'application/json' }
		});
	}),

	// upload metadata
	http.post('/api/upload-file', async ({ request }) => {
		const body = await jsonSafe(request);
		if (!(body as any)?.fileName || !('size' in (body as any))) {
			return new HttpResponse(JSON.stringify({ error: 'Missing file metadata' }), {
				status: 400,
				headers: { 'Content-Type': 'application/json' }
			});
		}
		return new HttpResponse(JSON.stringify({ uploadId: 'upload_mock_1' }), {
			status: 200,
			headers: { 'Content-Type': 'application/json' }
		});
	}),

	// trigger file processing
	http.post('/api/process-voter-file', async ({ request }) => {
		const body = await jsonSafe(request);
		if (!(body as any)?.filePath) {
			return new HttpResponse(JSON.stringify({ error: 'Missing filePath' }), {
				status: 400,
				headers: { 'Content-Type': 'application/json' }
			});
		}
		// simulate processing delay
		if (featureFlags.isEnabled('mock:createCampaign:delay')) {
			await new Promise((r) => setTimeout(r, 900));
		}
		return new HttpResponse(JSON.stringify({ jobId: 'process_job_mock_1' }), {
			status: 200,
			headers: { 'Content-Type': 'application/json' }
		});
	})
];
