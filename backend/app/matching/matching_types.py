from typing import TypedDict

from app.matching.match_columns import MatchColumns


class DemoOcrColumns(TypedDict, total=False):
	MatchColumns.OCR_NAME
