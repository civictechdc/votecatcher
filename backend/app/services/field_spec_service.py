from __future__ import annotations

from pathlib import Path
from uuid import UUID

import json5
import structlog

from app.domain.field_spec import (
    FieldSpecNotFoundError,
    RegionFieldSpecConfig,
    render_template,
)
from app.persistence.contracts import FieldSpecRepository

logger = structlog.get_logger(__name__)

REGIONS_DIR = Path(__file__).resolve().parent.parent / "regions"


class SpecLoadingError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(
            f"Spec loading failed with {len(errors)} error(s): {'; '.join(errors)}"
        )


class FieldSpecService:
    """Application service: field spec use cases."""

    def __init__(self, repo: FieldSpecRepository) -> None:
        self._repo: FieldSpecRepository = repo

    def get_spec(self, region_id: UUID) -> RegionFieldSpecConfig:
        spec = self._repo.find_by_region(region_id)
        if spec is None:
            raise FieldSpecNotFoundError(region_id)
        return spec

    def get_spec_by_key(self, region_key: str) -> RegionFieldSpecConfig:
        spec = self._repo.find_by_region_key(region_key)
        if spec is None:
            raise FieldSpecNotFoundError(UUID(int=0))
        return spec

    def map_voter_to_ballot(
        self, spec: RegionFieldSpecConfig, voter_data: dict[str, str]
    ) -> dict[str, str]:
        result: dict[str, str] = {}
        for mapping in spec.field_mappings:
            result[mapping.ballot_field_id] = render_template(
                mapping.template, voter_data
            )
        return result

    def validate_spec(self, spec: RegionFieldSpecConfig) -> list[str]:
        errors = spec.validate_integrity()
        if not spec.ballot_fields:
            errors.append("Must have at least one ballot field")
        if not spec.voter_reg_fields:
            errors.append("Must have at least one voter reg field")
        return errors

    def load_all_specs(
        self,
        specs_dir: Path | None = None,
        *,
        fail_fast: bool = False,
    ) -> tuple[int, list[str]]:
        dir_path = specs_dir or REGIONS_DIR
        if not dir_path.exists():
            logger.info(
                "Regions directory not found, skipping spec loading", path=str(dir_path)
            )
            return 0, []

        spec_files = sorted(dir_path.glob("*.json5"))
        if not spec_files:
            logger.info("No .json5 spec files found", path=str(dir_path))
            return 0, []

        count = 0
        errors: list[str] = []
        for spec_file in spec_files:
            region_key = spec_file.stem.upper()
            try:
                raw = spec_file.read_text()
                data = json5.loads(raw)
                spec = RegionFieldSpecConfig.model_validate(data)
            except Exception as e:
                msg = f"{spec_file.name}: parse error — {e}"
                errors.append(msg)
                logger.error("Spec parse error", file=spec_file.name, error=str(e))
                continue

            integrity_errors = spec.validate_integrity()
            if integrity_errors:
                msg = f"{spec_file.name}: integrity errors — {'; '.join(integrity_errors)}"
                errors.append(msg)
                logger.error(
                    "Spec integrity errors",
                    file=spec_file.name,
                    errors=integrity_errors,
                )
                continue

            self._repo.upsert(
                region_key,
                spec,
                region_name=spec.region_name,
                country_code=spec.country_code,
            )
            count += 1
            logger.info(
                "Loaded spec", region_key=region_key, region_name=spec.region_name
            )

        if fail_fast and errors:
            raise SpecLoadingError(errors)

        return count, errors
