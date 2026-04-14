import type { RequestHandler } from "@sveltejs/kit";

export const POST: RequestHandler = async ({ request }) => {
	const body = await request.json().catch(() => ({}));
	const { email, password } = body ?? {};
	if (!email || !password) {
		return new Response(JSON.stringify({ error: "Missing credentials" }), { status: 400 });
	}

	// Simple mock: if password matches mock value, require two-factor; else sign in
	if (password === "2fa") {
		// pragma: allowlist secret
		return new Response(JSON.stringify({ ok: true, twoFactorRequired: true }), {
			status: 200,
			headers: { "Content-Type": "application/json" },
		});
	}

	// Otherwise return a mock user
	return new Response(JSON.stringify({ ok: true, user: { id: "user_dev_1", email } }), {
		status: 200,
		headers: { "Content-Type": "application/json" },
	});
};
