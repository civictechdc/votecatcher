import type { RequestHandler } from '@sveltejs/kit';

export const POST: RequestHandler = async ({ request }) => {
	const body = await request.json().catch(() => ({}));
	if (!body?.email || !body?.password) {
		return new Response(JSON.stringify({ error: 'Missing email or password' }), { status: 400 });
	}
	// Mock: in real backend send verification email and return pending status
	return new Response(JSON.stringify({ ok: true, message: 'verification_sent' }), {
		status: 200,
		headers: { 'Content-Type': 'application/json' }
	});
};
