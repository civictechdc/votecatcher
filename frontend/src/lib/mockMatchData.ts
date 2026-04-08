// Mock data to test MatchConfidenceIndicator component
// This simulates the data that would come from the backend API

import type { MatchResultResponse } from "./api/response-types";

export const mockMatchResponse: MatchResultResponse = {
	column_data: [
		{ name: "OCR Name", position_idx: 0, data_type: "object" },
		{ name: "OCR Address", position_idx: 1, data_type: "object" },
		{ name: "Matched Name", position_idx: 2, data_type: "object" },
		{ name: "Matched Address", position_idx: 3, data_type: "object" },
		{ name: "Date", position_idx: 4, data_type: "object" },
		{ name: "Ward", position_idx: 5, data_type: "int64" },
		{ name: "Match Score", position_idx: 6, data_type: "float64" },
		{ name: "Valid", position_idx: 7, data_type: "bool" },
		{ name: "Page Number", position_idx: 8, data_type: "int64" },
		{ name: "Row Number", position_idx: 9, data_type: "int64" },
		{ name: "Filename", position_idx: 10, data_type: "object" },
	],
	result_data: [
		{
			row_idx: 0,
			values: [
				{ value: "John Smith", column_idx: 0, data_type: "str" },
				{ value: "123 Main St", column_idx: 1, data_type: "str" },
				{ value: "John Smith", column_idx: 2, data_type: "str" },
				{ value: "123 Main St", column_idx: 3, data_type: "str" },
				{ value: "2024-01-15", column_idx: 4, data_type: "str" },
				{ value: "1", column_idx: 5, data_type: "int" },
				{ value: "95.5", column_idx: 6, data_type: "str" },
				{ value: "true", column_idx: 7, data_type: "str" },
				{ value: "1", column_idx: 8, data_type: "int" },
				{ value: "1", column_idx: 9, data_type: "int" },
				{ value: "file1.pdf", column_idx: 10, data_type: "str" },
			],
		},
		{
			row_idx: 1,
			values: [
				{ value: "Jane Doe", column_idx: 0, data_type: "str" },
				{ value: "456 Oak Ave", column_idx: 1, data_type: "str" },
				{ value: "Jane Doe", column_idx: 2, data_type: "str" },
				{ value: "456 Oak Ave", column_idx: 3, data_type: "str" },
				{ value: "2024-01-16", column_idx: 4, data_type: "str" },
				{ value: "2", column_idx: 5, data_type: "int" },
				{ value: "87.3", column_idx: 6, data_type: "str" },
				{ value: "true", column_idx: 7, data_type: "str" },
				{ value: "1", column_idx: 8, data_type: "int" },
				{ value: "2", column_idx: 9, data_type: "int" },
				{ value: "file1.pdf", column_idx: 10, data_type: "str" },
			],
		},
		{
			row_idx: 2,
			values: [
				{ value: "Bob Johnson", column_idx: 0, data_type: "str" },
				{ value: "789 Pine Rd", column_idx: 1, data_type: "str" },
				{ value: "Robert Johnson", column_idx: 2, data_type: "str" },
				{ value: "789 Pine Road", column_idx: 3, data_type: "str" },
				{ value: "2024-01-17", column_idx: 4, data_type: "str" },
				{ value: "3", column_idx: 5, data_type: "int" },
				{ value: "92.1", column_idx: 6, data_type: "str" },
				{ value: "true", column_idx: 7, data_type: "str" },
				{ value: "2", column_idx: 8, data_type: "int" },
				{ value: "1", column_idx: 9, data_type: "int" },
				{ value: "file2.pdf", column_idx: 10, data_type: "str" },
			],
		},
		{
			row_idx: 3,
			values: [
				{ value: "Alice Williams", column_idx: 0, data_type: "str" },
				{ value: "321 Elm St", column_idx: 1, data_type: "str" },
				{ value: "Alice Williams", column_idx: 2, data_type: "str" },
				{ value: "321 Elm Street", column_idx: 3, data_type: "str" },
				{ value: "2024-01-18", column_idx: 4, data_type: "str" },
				{ value: "4", column_idx: 5, data_type: "int" },
				{ value: "0.0", column_idx: 6, data_type: "str" },
				{ value: "false", column_idx: 7, data_type: "str" },
				{ value: "2", column_idx: 8, data_type: "int" },
				{ value: "2", column_idx: 9, data_type: "int" },
				{ value: "file2.pdf", column_idx: 10, data_type: "str" },
			],
		},
	],
	page_idx: 0,
	max_row_count: 4,
	total_pages: 1,
	metadata: {
		campaign_id: "test-campaign",
		started_at: new Date(),
		completed_at: new Date(),
		region: "DC",
		ocr_provider: "test-provider",
	},
};

export const expectedConfidenceLevels = [
	"High", // 95.5 >= 95
	"Low", // 87.3 < 90
	"Medium", // 92.1 >= 90 but < 95
	"Low", // 0.0 < 90
];
