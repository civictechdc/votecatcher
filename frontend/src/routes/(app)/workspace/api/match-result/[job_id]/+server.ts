import type { RequestHandler } from "@sveltejs/kit";
import { json } from "@sveltejs/kit";
import { api, type ApiResult } from "$lib/api/client";
import { error } from "@sveltejs/kit";
import type {
	MatchColumnsResponse,
	MatchResponse,
	MatchResultResponse,
	MatchRowsResponse,
	MatchRowEntryResponse,
} from "$lib/api/response-types";
import {
	type MatchRow,
	type MatchColumn,
	type MatchResults,
	MatchValueFormatKeys,
} from "$lib/workspace-types";

export const GET: RequestHandler = async ({ params }) => {
	const jobId: string = params?.job_id as string;

	const response: ApiResult<MatchResponse> = await api.demoGetMatchingResults(jobId);
	if (!response.ok) {
		return error(500, `Error: ${response.error}`);
	}

	const results: MatchResultResponse = response.data.results;
	const matchResults = transformToMatchResults(results);

	console.log(
		`Found ${matchResults.matchRecords.length} match results with ${matchResults.matchColumns.length} columns`,
	);

	return json({ matchResults }, { status: 200 });
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
