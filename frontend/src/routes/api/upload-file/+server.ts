import type { RequestHandler } from "@sveltejs/kit";

export const POST: RequestHandler = async ({ request }) => {
	const body = await request.json();
	if (!body?.fileName) {
		return new Response(JSON.stringify({ error: "Missing filename" }), { status: 400 });
	}
	// Return a mocked storage path
	return new Response(JSON.stringify({ path: `mock-storage/${body.fileName}` }), {
		status: 200,
		headers: { "Content-Type": "application/json" },
	});
};
