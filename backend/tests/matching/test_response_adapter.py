"""Tests for response adapter column ordering."""

from app.matching.response_adapter import (
	OcrMatchColumnSpec,
	OcrMatchResults,
	OcrMatchRow,
	OcrMatchValueItem,
)


def test_column_data_sorted_by_position_idx():
	"""Column data should be sorted by position_idx."""
	columns = [
		OcrMatchColumnSpec(name="third", position_idx=2, data_type="string"),
		OcrMatchColumnSpec(name="first", position_idx=0, data_type="string"),
		OcrMatchColumnSpec(name="second", position_idx=1, data_type="string"),
	]
	rows = [
		OcrMatchRow(
			row_idx=0,
			values=[
				OcrMatchValueItem(value="A", column_idx=0, data_type="string"),
				OcrMatchValueItem(value="B", column_idx=1, data_type="string"),
				OcrMatchValueItem(value="C", column_idx=2, data_type="string"),
			],
		)
	]
	result = OcrMatchResults(column_data=columns, result_data=rows)

	assert result.column_data[0].position_idx == 0
	assert result.column_data[1].position_idx == 1
	assert result.column_data[2].position_idx == 2


def test_column_data_contains_all_required_fields():
	"""Column data should contain all required fields."""
	column = OcrMatchColumnSpec(name="test_col", position_idx=0, data_type="string")

	assert column.name == "test_col"
	assert column.position_idx == 0
	assert column.data_type == "string"


def test_response_serializes_to_valid_json():
	"""Response should serialize to valid JSON."""
	import json

	columns = [OcrMatchColumnSpec(name="name", position_idx=0, data_type="string")]
	rows = [
		OcrMatchRow(
			row_idx=0,
			values=[OcrMatchValueItem(value="John", column_idx=0, data_type="string")],
		)
	]
	result = OcrMatchResults(column_data=columns, result_data=rows)

	json_str = result.model_dump_json()
	parsed = json.loads(json_str)

	assert "column_data" in parsed
	assert "result_data" in parsed
