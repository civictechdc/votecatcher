import type { MatchResultResponse } from "$lib/api/response-types";
import type { MatchRow, MatchResults } from "$lib/workspace-types";
import { MatchColumn } from "$lib/workspace-types";
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

export function convertMatchResponseToMatchResults(
	matchResponse: MatchResultResponse,
): MatchResults {
	// Extract column names from column_data
	const matchColumns: MatchColumn[] = matchResponse.column_data.map((colSpec) => {
		// Create sorting functions for sortable columns
		let sortFn: ((first: MatchRow, second: MatchRow) => number) | undefined;

		if (colSpec.name.includes("Score") || colSpec.name.includes("Confidence")) {
			sortFn = function (first: MatchRow, second: MatchRow): number {
				const firstVal = parseFloat((first[colSpec.name] ?? 0) as string);
				const secondVal = parseFloat((second[colSpec.name] ?? 0) as string);
				return secondVal - firstVal; // Higher scores first
			};
		} else if (colSpec.name.includes("Name") || colSpec.name.includes("Address")) {
			sortFn = function (first: MatchRow, second: MatchRow): number {
				const firstVal = (first[colSpec.name] ?? "") as string;
				const secondVal = (second[colSpec.name] ?? "") as string;
				return firstVal.localeCompare(secondVal);
			};
		} else if (colSpec.name.includes("Page") || colSpec.name.includes("Row")) {
			sortFn = function (first: MatchRow, second: MatchRow): number {
				const firstVal = parseInt((first[colSpec.name] ?? 0) as string);
				const secondVal = parseInt((second[colSpec.name] ?? 0) as string);
				return firstVal - secondVal;
			};
		}

		return new MatchColumn(colSpec.name, sortFn);
	});

	// Convert result_data to matchRecords
	const matchRecords: MatchRow[] = matchResponse.result_data.map((rowData) => {
		const row: MatchRow = { row_idx: rowData.row_idx };

		// Map values to their column names
		rowData.values.forEach((valueItem, idx) => {
			const colName = matchResponse.column_data[idx]?.name || `Column ${idx}`;
			row[colName] = valueItem.value;
		});

		return row;
	});

	return {
		matchColumns,
		matchRecords,
		timestamp: new Date().toISOString(),
	};
}
