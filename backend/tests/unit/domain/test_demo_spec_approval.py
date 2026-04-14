from pathlib import Path

import json5
from approvaltests import verify

from app.domain.field_spec import RegionFieldSpecConfig, render_template

SPEC_PATH = Path(__file__).resolve().parents[3] / "app" / "regions" / "demo.json5"


class TestDemoSpecApproval:
    def test_demo_seed_spec(self):
        assert SPEC_PATH.exists(), f"Spec file not found at {SPEC_PATH}"
        raw = SPEC_PATH.read_text()
        data = json5.loads(raw)
        spec = RegionFieldSpecConfig.model_validate(data)
        verify(spec.model_dump_json(indent=2))

    def test_demo_spec_passes_integrity_validation(self):
        assert SPEC_PATH.exists(), f"Spec file not found at {SPEC_PATH}"
        raw = SPEC_PATH.read_text()
        data = json5.loads(raw)
        spec = RegionFieldSpecConfig.model_validate(data)
        errors = spec.validate_integrity()
        assert errors == [], f"Demo spec integrity errors: {errors}"


class TestDemoTemplateSmoke:
    def test_demo_address_template_renders_fake_csv_row(self):
        template = "{street_number} {street_name} {street_type} {street_dir_suffix}"
        voter = {
            "street_number": "6071",
            "street_name": "Martin Island",
            "street_type": "",
            "street_dir_suffix": "",
        }
        result = render_template(template, voter)
        assert result == "6071 Martin Island"

    def test_demo_name_template_renders_with_empty_middle(self):
        template = "{first_name} {middle_name} {last_name}"
        voter = {"first_name": "Erica", "middle_name": "", "last_name": "Massey"}
        result = render_template(template, voter)
        assert result == "Erica Massey"

    def test_demo_name_template_renders_with_middle(self):
        template = "{first_name} {middle_name} {last_name}"
        voter = {"first_name": "Terry", "middle_name": "Lee", "last_name": "Osborne"}
        result = render_template(template, voter)
        assert result == "Terry Lee Osborne"
