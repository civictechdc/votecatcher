import type { RequestHandler } from "./$types";
import { API_BASE_URL } from "$lib/api/base-url";

export const GET: RequestHandler = async ({ params }) => {
	try {
		const job_id = params.job_id;
		const eventResponse = await fetch(
			`${API_BASE_URL}/workspace/ocr/batch/${encodeURIComponent(job_id)}/status`,
		);

		if (!eventResponse.ok || !eventResponse.body) {
			console.log(`Error with response is ${JSON.stringify(eventResponse)}`);
			throw new Error(`Upstream error: ${eventResponse.statusText}`);
		}

		// Step 3: Return the FastAPI response stream directly to the browser
		return new Response(eventResponse.body, {
			headers: {
				"Content-Type": "text/event-stream",
				"Cache-Control": "no-cache",
				Connection: "keep-alive",
			},
		});
	} catch (error) {
		console.error("Error proxying SSE stream:", error);
		return new Response("Proxy error: Cannot connect to upstream SSE source.", { status: 500 });
	}
};
