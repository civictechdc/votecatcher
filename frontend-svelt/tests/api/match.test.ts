import { describe, it, expect, vi } from "vitest";

vi.stubEnv("VITE_API_URL", "https://testserver.com/");

import "./web-server";
import { matchApi } from "$lib/api/matching-requests";
import type { ApiResult } from "$lib/api/client";
import type { MatchResultResponse } from "$lib/api/response-types";

describe("matchApi.getMatchResults", () => {
	describe("when called with", () => {
		it.each([
			{ campaign_id: "valid-campaign-id", job_id: "valid-job-id", ok: true, status: 200 },
			{ campaign_id: "invalid-campaign-id", job_id: "valid-job-id", ok: false, status: 404 },
			{ campaign_id: "valid-campaign-id", job_id: "invalid-job-id", ok: false, status: 404 },
			{ campaign_id: null, job_id: "valid-job-id", ok: false, status: 500, error: "fetch failed" },
		])(
			"$campaign_id and $job_id, returns { ok: $ok, status: $status } for campaign_id=$campaign_id, job_id=$job_id",
			async ({ campaign_id, job_id, ok, status, error }) => {
				const response: ApiResult<MatchResultResponse> = await matchApi.getMatchResults({
					campaign_id: campaign_id as string,
					job_id,
				});

				expect(response.ok).toBe(ok);
				expect(response.status).toBe(status);
				if (error && !response.ok) {
					expect(response.error).toBe(error);
				}
			},
		);
	});
});
