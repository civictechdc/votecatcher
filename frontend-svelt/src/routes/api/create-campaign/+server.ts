import type { RequestHandler } from '@sveltejs/kit';

export const POST: RequestHandler = async ({ request }) => {
	const body = await request.json();
	if (!body?.name || !body?.year) {
		return new Response(JSON.stringify({ error: 'Missing name or year' }), { status: 400 });
	}
	// Return a mock id
	return new Response(JSON.stringify({ id: 'campaign_abc123' }), {
		status: 200,
		headers: { 'Content-Type': 'application/json' }
	});
};
