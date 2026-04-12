import { setupServer } from "msw/node";
import { http, HttpHandler, HttpResponse, RequestHandler } from "msw";
import { beforeAll, afterEach, afterAll } from "vitest";

const BASE_URL = "http://localhost:8000";

function apiUrl(path: string): string {
	return new URL(path, BASE_URL).href;
}

const handlers: HttpHandler[] = [
	http.get(apiUrl("api/valid-campaign-id/matching/result/valid-job-id"), () => {
		return HttpResponse.json({}, { status: 200, statusText: "OK" });
	}),
	http.get(apiUrl("api/invalid-campaign-id/matching/result/valid-job-id"), () => {
		return new HttpResponse(null, {
			status: 404,
			statusText: "Campaign not found",
		});
	}),
	http.get(apiUrl("api/valid-campaign-id/matching/result/invalid-job-id"), () => {
		return new HttpResponse(null, {
			status: 404,
			statusText: "Job not found",
		});
	}),
];

const server = setupServer(...handlers);
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

export function addRequestHandler(handler: RequestHandler) {
	server.use(handler);
}
