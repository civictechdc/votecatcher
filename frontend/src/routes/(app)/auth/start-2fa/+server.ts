import type { RequestHandler } from "@sveltejs/kit";

export const POST: RequestHandler = async ({ request }) => {
	const body = await request.json().catch(() => ({}));
	if (!body?.email)
		return new Response(JSON.stringify({ error: "Missing email" }), { status: 400 });
	// Mock: return success and pretend we sent a code "123456"
	return new Response(
		JSON.stringify({ ok: true, codeSent: true, hint: "Use code 123456 in tests" }),
		{ status: 200, headers: { "Content-Type": "application/json" } },
	);
};
