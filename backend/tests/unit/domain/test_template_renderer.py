from app.domain.field_spec import render_template


class TestRenderTemplate:
    def test_concatenates_fields(self):
        result = render_template(
            "{first_name} {last_name}",
            {"first_name": "John", "last_name": "Smith"},
        )
        assert result == "John Smith"

    def test_drops_empty_placeholder(self):
        result = render_template(
            "{first_name} {middle_name} {last_name}",
            {"first_name": "Jane", "middle_name": "", "last_name": "Doe"},
        )
        assert result == "Jane Doe"

    def test_address_without_apartment(self):
        result = render_template(
            "{street_number} {street_name}, Apt {apartment}",
            {"street_number": "730", "street_name": "Lawrence St NE", "apartment": ""},
        )
        assert result == "730 Lawrence St NE"

    def test_address_with_apartment(self):
        result = render_template(
            "{street_number} {street_name}, Apt {apartment}",
            {
                "street_number": "1300",
                "street_name": "4th St SE",
                "apartment": "UNIT 715",
            },
        )
        assert result == "1300 4th St SE, Apt UNIT 715"

    def test_empty_template_returns_empty(self):
        result = render_template("", {"first_name": "John"})
        assert result == ""

    def test_all_fields_empty_returns_empty(self):
        result = render_template(
            "{first_name} {last_name}",
            {"first_name": "", "last_name": ""},
        )
        assert result == ""

    def test_single_field(self):
        result = render_template("{ward}", {"ward": "3"})
        assert result == "3"

    def test_missing_field_treated_as_empty(self):
        result = render_template(
            "{first_name} {middle_name} {last_name}",
            {"first_name": "John", "last_name": "Smith"},
        )
        assert result == "John Smith"

    def test_collapses_multiple_spaces(self):
        result = render_template(
            "{a} {b} {c}",
            {"a": "hello", "b": "", "c": "world"},
        )
        assert result == "hello world"

    def test_handles_special_characters(self):
        result = render_template(
            "{name}",
            {"name": "O'Brien-Smith Jr."},
        )
        assert result == "O'Brien-Smith Jr."

    def test_na_values_treated_as_empty(self):
        result = render_template(
            "{street_number} {street_name}",
            {"street_number": "N/A", "street_name": "4th St NW"},
        )
        assert result == "4th St NW"

    def test_na_case_insensitive(self):
        result = render_template(
            "{a} {b}",
            {"a": "n/a", "b": "test"},
        )
        assert result == "test"

    def test_na_uppercase(self):
        result = render_template(
            "{a} {b}",
            {"a": "NA", "b": "test"},
        )
        assert result == "test"

    def test_na_lowercase(self):
        result = render_template(
            "{a} {b}",
            {"a": "na", "b": "test"},
        )
        assert result == "test"
