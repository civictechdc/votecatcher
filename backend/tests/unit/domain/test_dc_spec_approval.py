from pathlib import Path

import json5
from approvaltests import verify

from app.domain.field_spec import RegionFieldSpecConfig

SPEC_PATH = Path(__file__).resolve().parents[3] / "app" / "regions" / "dc.json5"


class TestDcDefaultSpecApproval:
    def test_dc_seed_spec(self):
        assert SPEC_PATH.exists(), f"Spec file not found at {SPEC_PATH}"
        raw = SPEC_PATH.read_text()
        data = json5.loads(raw)
        spec = RegionFieldSpecConfig.model_validate(data)
        verify(spec.model_dump_json(indent=2))

    def test_dc_spec_passes_integrity_validation(self):
        assert SPEC_PATH.exists(), f"Spec file not found at {SPEC_PATH}"
        raw = SPEC_PATH.read_text()
        data = json5.loads(raw)
        spec = RegionFieldSpecConfig.model_validate(data)
        errors = spec.validate_integrity()
        assert errors == [], f"DC spec integrity errors: {errors}"
