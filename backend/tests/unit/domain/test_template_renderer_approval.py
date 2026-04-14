from approvaltests import set_default_reporter, verify_all
from approvaltests.reporters.python_native_reporter import PythonNativeReporter

from app.domain.field_spec import render_template

set_default_reporter(PythonNativeReporter())


class TestTemplateRendererApproval:
    def test_dc_address_variants(self):
        template = "{street_number}{street_number_suffix} {street_name} {street_type} {street_dir_suffix}, Apt {apartment_number}"
        dc_addresses = {
            "standard NE": {
                "street_number": "730",
                "street_number_suffix": "",
                "street_name": "Lawrence",
                "street_type": "St",
                "street_dir_suffix": "NE",
                "apartment_number": "",
            },
            "with unit SE": {
                "street_number": "1300",
                "street_number_suffix": "",
                "street_name": "4th",
                "street_type": "St",
                "street_dir_suffix": "SE",
                "apartment_number": "UNIT 715",
            },
            "with apt hash": {
                "street_number": "235",
                "street_number_suffix": "",
                "street_name": "Carroll",
                "street_type": "St",
                "street_dir_suffix": "NW",
                "apartment_number": "#316",
            },
            "N/A street num": {
                "street_number": "N/A",
                "street_number_suffix": "",
                "street_name": "4th",
                "street_type": "St",
                "street_dir_suffix": "NW",
                "apartment_number": "#011",
            },
            "empty street num": {
                "street_number": "",
                "street_number_suffix": "",
                "street_name": "Emailes",
                "street_type": "St",
                "street_dir_suffix": "SW",
                "apartment_number": "",
            },
        }
        verify_all(
            "DC address template renders",
            dc_addresses.items(),
            lambda pair: (
                f"{pair[0]}: {pair[1]} => {render_template(template, pair[1])!r}"
            ),
        )

    def test_dc_name_variants(self):
        template = "{first_name} {middle_name} {last_name}"
        names = {
            "full name": {
                "first_name": "John",
                "middle_name": "M",
                "last_name": "Smith",
            },
            "no middle": {"first_name": "Jane", "middle_name": "", "last_name": "Doe"},
            "empty middle": {
                "first_name": "Bob",
                "middle_name": " ",
                "last_name": "Jones",
            },
        }
        verify_all(
            "DC name template renders",
            names.items(),
            lambda pair: (
                f"{pair[0]}: {pair[1]} => {render_template(template, pair[1])!r}"
            ),
        )
