import type { RequestHandler } from '@sveltejs/kit';

/**
 * Mock session endpoint.
 * - In development this returns a fake user when VITE_FEATURES contains 'mockAuth'
 * - Replace with real session validation (FastAPI) later.
 */
export const GET: RequestHandler = async () => {
	// Simple dev mock: return a user if a cookie or header indicates it,
	// or always return a mocked user to enable local flows. Adjust as needed.
	// For now return a mock user to allow dev flows to proceed.
	const user = { id: 'user_dev_1', email: 'dev@example.com' };
	return new Response(JSON.stringify({ user }), {
		status: 200,
		headers: { 'Content-Type': 'application/json' },
	});
};
