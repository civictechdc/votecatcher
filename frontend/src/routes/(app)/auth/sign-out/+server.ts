import type { RequestHandler } from "@sveltejs/kit";

export const POST: RequestHandler = async () => {
	// In real backend, clear session/cookie. Here we just return success.
	return new Response(JSON.stringify({ ok: true }), {
		status: 200,
		headers: { "Content-Type": "application/json" },
	});
};
