import type { RequestHandler } from '@sveltejs/kit';

export const POST: RequestHandler = async ({ request }) => {
	const body = await request.json().catch(() => ({}));
	const { email, code } = body ?? {};
	if (!email || !code)
		return new Response(JSON.stringify({ error: 'Missing parameters' }), { status: 400 });
	// Mock validation: accept 123456
	if (code === '123456') {
		return new Response(JSON.stringify({ ok: true, user: { id: 'user_dev_1', email } }), {
			status: 200,
			headers: { 'Content-Type': 'application/json' }
		});
	}
	return new Response(JSON.stringify({ error: 'Invalid code' }), { status: 400 });
};
