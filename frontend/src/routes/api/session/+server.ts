import type { RequestHandler } from "@sveltejs/kit";

/**
 * Mock session endpoint.
 * - This route is in src/routes so SvelteKit exposes GET /api/session.
 * - Return a stable mock user for development; replace with FastAPI-backed session check later.
 */
export const GET: RequestHandler = async () => {
	const user = { id: "user_123", email: "dev@example.com" };
	return new Response(JSON.stringify({ user }), {
		status: 200,
		headers: { "Content-Type": "application/json" },
	});
};
