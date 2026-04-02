#!/usr/bin/env python
"""Auto-generate database schema documentation from SQLModel metadata."""

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import SQLModel


def import_all_models() -> None:
	from app.data.database.model.jobs import (  # noqa: F401
		MatcherJob,
		OcrJob,
		OcrModel,
		OcrProvider,
	)
	from app.data.database.model.llm_provider_config import (
		LlmProviderConfig,  # noqa: F401
	)
	from app.data.database.model.match_result import MatchResult  # noqa: F401
	from app.data.database.model.ocr_result import OcrResult  # noqa: F401
	from app.data.database.model.petition_crop import PetitionCrop  # noqa: F401
	from app.data.database.model.petition_scan import PetitionScan  # noqa: F401
	from app.data.database.model.registered_voter import RegisteredVoter  # noqa: F401
	from app.data.database.model.schema import Campaign, Region  # noqa: F401
	from app.data.database.model.session import Session as SessionModel  # noqa: F401
	from app.data.database.model.user import User  # noqa: F401
	from app.data.database.model.voter_list_upload import VoterListUpload  # noqa: F401


def _get_column_type(col) -> str:
	type_repr = repr(col.type)
	if "VARCHAR" in type_repr or "TEXT" in type_repr:
		return "string"
	if "INTEGER" in type_repr or "BIGINT" in type_repr:
		return "integer"
	if "FLOAT" in type_repr or "REAL" in type_repr or "NUMERIC" in type_repr:
		return "float"
	if "BOOLEAN" in type_repr:
		return "boolean"
	if "TIMESTAMP" in type_repr or "DATETIME" in type_repr or "DATE" in type_repr:
		return "datetime"
	if "JSON" in type_repr:
		return "json"
	if "BLOB" in type_repr or "LARGE BINARY" in type_repr:
		return "blob"
	return type_repr.split("(")[0].lower() if "(" in type_repr else type_repr.lower()


def _get_pk_cols(table) -> list[str]:
	return [col.name for col in table.primary_key.columns]


def _get_fk_info(table) -> dict[str, tuple[str, str]]:
	fks = {}
	for fk in table.foreign_keys:
		col_name = fk.column.name
		target_table = fk.column.table.name
		target_col = fk.column.name
		fks[col_name] = (target_table, target_col)
	return fks


def generate_mermaid(metadata, output_path: Path) -> None:
	lines = ["erDiagram"]
	relationships = []

	for table in sorted(metadata.tables.values(), key=lambda t: t.name):
		pk_cols = _get_pk_cols(table)
		fk_info = _get_fk_info(table)

		lines.append(f"    {table.name} {{")
		for col in table.columns:
			col_type = _get_column_type(col)
			pk_marker = " PK" if col.name in pk_cols else ""
			fk_marker = " FK" if col.name in fk_info else ""
			lines.append(f"        {col_type} {col.name}{pk_marker}{fk_marker}")
		lines.append("    }")

		for col_name, (target_table, _target_col) in fk_info.items():
			relationships.append(
				f"    {table.name} ||--o{{ {target_table} : {col_name}"
			)

	lines.append("")
	lines.extend(relationships)
	output_path.write_text("\n".join(lines) + "\n")


def generate_readme(output_dir: Path) -> None:
	table_descriptions = {
		"campaigns": "Election campaigns",
		"regions": "Geographic regions for campaigns",
		"petition_scans": "Uploaded petition PDFs",
		"petition_crops": "Extracted signature images",
		"registered_voters": "Voter registration data",
		"match_results": "Signature match results",
		"ocr_results": "OCR processing results",
		"users": "User accounts",
		"sessions": "User sessions",
		"llm_provider_config": "LLM provider configurations",
		"ocr_jobs": "OCR job queue",
		"matcher_jobs": "Matching job queue",
		"ocr_providers": "OCR provider definitions",
		"ocr_models": "OCR model definitions",
		"voter_list_uploads": "Voter list upload records",
	}

	now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

	tables_section = "\n".join(
		f"| `{name}` | {table_descriptions.get(name, 'See model definition')} |"
		for name in sorted(table_descriptions.keys())
	)

	content = f"""# Database Schema

Auto-generated from SQLModel definitions.

**Last updated:** {now}

## Diagram

- [Mermaid ERD](./schema.md) - Renders in GitHub

## Tables

| Table | Purpose |
|-------|---------|
{tables_section}

## Regeneration

Run to regenerate after model changes:

```bash
cd backend && python scripts/generate_schema_docs.py
```
"""
	(output_dir / "README.md").write_text(content)


def generate_schema_docs(output_dir: Path | None = None) -> None:
	if output_dir is None:
		output_dir = Path(__file__).parent.parent.parent / "docs" / "database"

	output_dir.mkdir(parents=True, exist_ok=True)

	import_all_models()

	mermaid_path = output_dir / "schema.md"
	generate_mermaid(SQLModel.metadata, mermaid_path)
	print(f"Generated: {mermaid_path}")

	generate_readme(output_dir)
	print(f"Updated: {output_dir / 'README.md'}")


if __name__ == "__main__":
	generate_schema_docs()
