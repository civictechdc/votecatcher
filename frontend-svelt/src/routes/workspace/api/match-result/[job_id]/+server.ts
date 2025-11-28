import type { RequestHandler } from '@sveltejs/kit';
import { isDemoMode } from '$lib/stores/demo';
import { json } from '@sveltejs/kit';
import { api, type ApiResult } from '$lib/api/client';
import { error } from '@sveltejs/kit';
import type { OcrMatchResults } from '$lib/api/response-types';

export const GET: RequestHandler = async ({ params }) => {
	const jobId = params?.job_id;

	const result: ApiResult<OcrMatchResults> = await api.demoGetMatchingResults();
	console.log(`Match result client: ${JSON.stringify(result)}`);
	if (!result.ok) {
		return error(500, `Error: ${result.error}`);
	}

	const response = result.data;

	console.log(`Matching results: ${JSON.stringify(response)}`);

	return json({ response }, { status: 200 });
};
