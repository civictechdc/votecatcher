import type { RequestHandler } from "@sveltejs/kit";
import { api, type ApiResult } from "#lib/api/client.ts";
import { MATCH_RESULT_TIMEOUT_MS } from "#lib/api/fetch-deadline.ts";
import { error } from "@sveltejs/kit";
import type {
	MatchColumnsResponse,
	MatchResponse,
	MatchResultResponse,
	MatchRowsResponse,
	MatchRowEntryResponse,
} from "#lib/api/response-types.ts";
import {
	type MatchRow,
	type MatchColumn,
	type MatchResults,
	MatchValueFormatKeys,
} from "#lib/workspace-types.ts";

export const GET: RequestHandler = async ({ params }) => {
	const jobId: string = params?.job_id as string;

	// Bounded deadline: abort the upstream request if it hangs. A timed-out
	// request surfaces as 504, an upstream 4xx is forwarded with its message,
	// and other failures (no response, upstream 5xx) map to a 5xx with a
	// generic message so upstream internals never reach the client.
	const deadline = new AbortController();
	const timeoutId = setTimeout(
		() => deadline.abort(new DOMException("Upstream request timed out.", "TimeoutError")),
		MATCH_RESULT_TIMEOUT_MS,
	);
	let response: ApiResult<MatchResponse>;
	try {
		response = await api.demoGetMatchingResults(jobId, { signal: deadline.signal });
	} finally {
		clearTimeout(timeoutId);
	}

	if (!response.ok) {
		// The proxy-owned deadline is authoritative: if it fired, the request
		// hit the deadline — even when the client reports a generic no-response
		// status 0 (which also covers plain network failures and body-phase
		// aborts, none of which are distinguishable on their own).
		const timedOut = deadline.signal.aborted && deadline.signal.reason?.name === "TimeoutError";
		const status = timedOut
			? 504
			: response.status >= 400 && response.status <= 599
				? response.status
				: 500;
		if (status >= 500) {
			// Server-side failures: keep upstream internals out of the response
			// body and log them here instead.
			console.error(`Match results upstream failure (status ${status}): ${response.error}`);
			return error(status, "Upstream match results unavailable.");
		}
		return error(status, `Error: ${response.error}`);
	}

	const results: MatchResultResponse = response.data.results;
	const matchResults = transformToMatchResults(results);

	console.log(
		`Found ${matchResults.matchRecords.length} match results with ${matchResults.matchColumns.length} columns`,
	);

	return Response.json({ matchResults }, { status: 200 });
};

function transformToMatchResults(response: MatchResultResponse): MatchResults {
	const columnData = response.column_data;
	const rowData = response.result_data;

	console.log(`Start transformation...`);

	const matchHeaders: MatchColumn[] = [];
	const matchRows: MatchRow[] = [];

	columnData
		.sort((a, b) => a.position_idx - b.position_idx)
		.forEach((column) => {
			matchHeaders[column.position_idx] = {
				name: column.name,
				isSortable: false,
			};
		});
	rowData.forEach((row) => {
		const flatRow = flattenRow(columnData, row);
		matchRows.push(flatRow);
	});

	console.log(`Finished transformation.`);
	const results: MatchResults = {
		matchColumns: matchHeaders,
		matchRecords: matchRows,
		timestamp: new Date().toISOString(),
	};

	return results;
}

function processValueItem(
	columnType: string,
	item: MatchRowEntryResponse,
): string | number | boolean | null {
	switch (columnType.toLowerCase()) {
		case "int":
		case "float": {
			const num = parseFloat(item.value);
			return isNaN(num) ? null : num;
		}
		case "bool": {
			const lowerVal = item.value.toLowerCase();
			if (lowerVal === "true" || lowerVal === "1") return true;
			if (lowerVal === "false" || lowerVal === "0") return false;
			return null;
		}
		case "str":
		case "string":
			return item.value;
		default:
			return item.value;
	}
}

function flattenRow(cols: Array<MatchColumnsResponse>, row: MatchRowsResponse): MatchRow {
	const flatObject: MatchRow = {
		row_idx: row.row_idx,
	};

	row.values.forEach((item, idx) => {
		const column = cols[idx];
		if (!column) return;
		const keyName = column.name;

		const typedValue = processValueItem(column.data_type, item);
		switch (keyName) {
			case "Match Score":
				flatObject[MatchValueFormatKeys.MATCH_SCORE] = typedValue;
				break;
			default:
				flatObject[`${keyName}`] = typedValue;
				break;
		}
	});

	return flatObject;
}
