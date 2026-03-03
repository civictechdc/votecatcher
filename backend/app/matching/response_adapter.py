from typing import Any

import pandas as pd
import structlog
from pandas import DataFrame
from pydantic import BaseModel, Field, field_validator

logger = structlog.get_logger(__name__)


class OcrMatchValueItem(BaseModel):
	value: str = Field(description="String representation of the field value")
	column_idx: int = Field(description="The index of the value's associated column")
	data_type: str = Field(
		description="Description of the value type the column will contain"
	)


class OcrMatchColumnSpec(BaseModel):
	name: str = Field(description="Display name of the column")
	position_idx: int = Field(description="Display order of the column")
	data_type: str = Field(
		description="Description of the value type the column will contain"
	)


class OcrMatchRow(BaseModel):
	row_idx: int = Field(description="Position of row in results list")
	values: list[OcrMatchValueItem] = Field(
		description="List of values for a record listed in column order"
	)


class OcrMatchResults(BaseModel):
	column_data: list[OcrMatchColumnSpec] = Field(
		description="Ordered list of columns for matching result"
	)
	result_data: list[OcrMatchRow] = Field(description="")

	@field_validator("column_data")
	@classmethod
	def sort_columns_by_position(
		cls, v: list[OcrMatchColumnSpec]
	) -> list[OcrMatchColumnSpec]:
		"""Ensure column_data is sorted by position_idx."""
		return sorted(v, key=lambda col: col.position_idx)


def create_ocr_match_result_response(match_results: DataFrame) -> OcrMatchResults:
	column_spec: list[OcrMatchColumnSpec] = [
		OcrMatchColumnSpec(
			name=col, position_idx=idx, data_type=str(match_results[col].dtype)
		)
		for idx, col in enumerate[str](match_results.columns)
	]

	results_data: list[OcrMatchRow] = []
	for i, (idx, row) in enumerate(match_results.iterrows()):
		entry: OcrMatchRow = OcrMatchRow(
			row_idx=i,
			values=[
				# Set the info for each field
				OcrMatchValueItem(
					# Handle NaN and infinity values for numeric fields
					value=(
						str(value)
						if not (
							isinstance(value, float)
							and (
								value != value
								or value == float("inf")
								or value == float("-inf")
							)
						)
						else "0.0"
					),
					column_idx=col_idx,
					data_type=str(type(value)),
				)
				for col_idx, value in enumerate(row.values)
			],
		)
		results_data.append(entry)

	return OcrMatchResults(column_data=column_spec, result_data=results_data)
