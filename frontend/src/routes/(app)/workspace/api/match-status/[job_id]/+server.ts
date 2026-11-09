import type { RequestHandler } from "./$types";
import { API_BASE_URL } from "#lib/api/base-url.ts";
import { MATCH_STATUS_CONNECT_TIMEOUT_MS } from "#lib/api/fetch-deadline.ts";

// Upstream statuses that cannot carry a body: forwarding them verbatim would
// throw when constructing the proxy Response, so normalize them to 502.
const BODYLESS_UPSTREAM_STATUSES = new Set([204, 205, 304]);

export const GET: RequestHandler = async ({ params, request }) => {
	const job_id = params.job_id;

	// One upstream controller, two abort sources: the connect deadline (it
	// only bounds the time until upstream headers arrive and is cleared
	// before the streamed Response is returned, so the SSE body is never
	// aborted mid-flight) and the browser disconnecting during the connect
	// phase — that one aborts the upstream request too, so a vanished client
	// does not leave a request hanging upstream.
	const deadline = new AbortController();
	const timeoutId = setTimeout(
		() => deadline.abort(new DOMException("Upstream SSE connection timed out.", "TimeoutError")),
		MATCH_STATUS_CONNECT_TIMEOUT_MS,
	);
	const onClientAbort = () => deadline.abort(request.signal.reason);
	if (request.signal.aborted) {
		onClientAbort();
	} else {
		request.signal.addEventListener("abort", onClientAbort, { once: true });
	}
	const stopForwardingClientAborts = () => {
		clearTimeout(timeoutId);
		request.signal.removeEventListener("abort", onClientAbort);
	};

	let eventResponse: Response;
	try {
		eventResponse = await fetch(
			`${API_BASE_URL}/workspace/ocr/batch/${encodeURIComponent(job_id)}/status`,
			{ signal: deadline.signal },
		);
	} catch (err) {
		stopForwardingClientAborts();
		console.error("Error proxying SSE stream:", err);
		if (deadline.signal.reason?.name === "TimeoutError") {
			return new Response("Proxy error: Upstream SSE connection timed out.", { status: 504 });
		}
		return new Response("Proxy error: Cannot connect to upstream SSE source.", { status: 500 });
	}
	stopForwardingClientAborts();

	if (!eventResponse.ok) {
		console.log(`Upstream SSE error: ${eventResponse.status} ${eventResponse.statusText}`);
		if (BODYLESS_UPSTREAM_STATUSES.has(eventResponse.status)) {
			return new Response("Upstream error: empty body.", { status: 502 });
		}
		return new Response(`Upstream error: ${eventResponse.statusText}`, {
			status: eventResponse.status,
		});
	}
	if (!eventResponse.body) {
		console.log(`Upstream SSE error: ${eventResponse.status} with empty body.`);
		return new Response("Upstream error: empty body.", { status: 502 });
	}

	// Step 3: Return the FastAPI response stream directly to the browser
	return new Response(eventResponse.body, {
		headers: {
			"Content-Type": "text/event-stream",
			"Cache-Control": "no-cache",
			Connection: "keep-alive",
		},
	});
};
