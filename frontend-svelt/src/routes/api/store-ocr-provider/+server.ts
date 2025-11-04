import type { RequestHandler } from '@sveltejs/kit';

export const POST: RequestHandler = async ({ request }) => {
	const body = await request.json().catch(() => ({}));
	// Expect provider and apiKey (was mistakenly validating name/year)
	const provider = body?.provider ?? body?.name ?? null;
	const apiKey = body?.apiKey ?? body?.api_key ?? null;

	if (!provider || !apiKey) {
		return new Response(JSON.stringify({ error: 'Missing provider or apiKey' }), { status: 400 });
	}

	// In real app: store provider and key securely, return status
	return new Response(JSON.stringify({ ok: true }), {
		status: 200,
		headers: { 'Content-Type': 'application/json' }
	});
};
