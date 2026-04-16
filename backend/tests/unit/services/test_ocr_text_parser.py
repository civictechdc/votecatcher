"""Unit tests for OcrTextParser.

BDD-style tests verifying extracted_text dict→string formatting
produces consistent output across all call sites.
"""


class TestFormatOcrText:
    """Feature: OCR text formatting.

    As the results system
    I want to format OCR extracted_text into a display string
    So that results show readable signature text.
    """

    def test_dict_with_name_and_address(self):
        """Scenario: Dict with name and address keys → sorted value string."""
        from app.services.ocr_text_parser import OcrTextParser

        result = OcrTextParser.format_text({"name": "John Doe", "address": "1 Main St"})
        assert "John Doe" in result
        assert "1 Main St" in result

    def test_dict_with_single_key(self):
        """Scenario: Dict with one key → single value string."""
        from app.services.ocr_text_parser import OcrTextParser

        result = OcrTextParser.format_text({"name": "Alice"})
        assert result == "Alice"

    def test_dict_with_empty_values(self):
        """Scenario: Dict with empty/None values → filters them out."""
        from app.services.ocr_text_parser import OcrTextParser

        result = OcrTextParser.format_text({"name": "", "address": None})
        assert result == ""

    def test_empty_dict_returns_empty_string(self):
        """Scenario: Empty dict → empty string."""
        from app.services.ocr_text_parser import OcrTextParser

        result = OcrTextParser.format_text({})
        assert result == ""

    def test_none_returns_empty_string(self):
        """Scenario: None input → empty string."""
        from app.services.ocr_text_parser import OcrTextParser

        result = OcrTextParser.format_text(None)
        assert result == ""

    def test_string_passthrough(self):
        """Scenario: String input → returned as-is."""
        from app.services.ocr_text_parser import OcrTextParser

        result = OcrTextParser.format_text("raw text")
        assert result == "raw text"

    def test_dict_sorted_key_order(self):
        """Scenario: Dict values concatenated in sorted key order."""
        from app.services.ocr_text_parser import OcrTextParser

        result = OcrTextParser.format_text({"b": "second", "a": "first"})
        assert result == "first second"

    def test_dict_values_joined_by_space(self):
        """Scenario: Non-empty dict values joined with single space."""
        from app.services.ocr_text_parser import OcrTextParser

        result = OcrTextParser.format_text({"x": "hello", "y": "world"})
        assert result == "hello world"


class TestExtractNameAndAddress:
    """Feature: Name/address extraction from OCR dict.

    As the campaign results system
    I want to split extracted_text dict into name and address
    So that campaign results show separate name and address fields.
    """

    def test_extracts_name_and_address(self):
        """Scenario: Dict with name and address keys."""
        from app.services.ocr_text_parser import OcrTextParser

        name, address = OcrTextParser.extract_name_and_address(
            {"name": "John Smith", "address": "123 Main St"}
        )
        assert name == "John Smith"
        assert address == "123 Main St"

    def test_missing_name_returns_empty(self):
        """Scenario: Dict without name key."""
        from app.services.ocr_text_parser import OcrTextParser

        name, address = OcrTextParser.extract_name_and_address(
            {"address": "123 Main St"}
        )
        assert name == ""
        assert address == "123 Main St"

    def test_missing_address_returns_empty(self):
        """Scenario: Dict without address key."""
        from app.services.ocr_text_parser import OcrTextParser

        name, address = OcrTextParser.extract_name_and_address({"name": "Alice"})
        assert name == "Alice"
        assert address == ""

    def test_none_returns_empty_pair(self):
        """Scenario: None input → both empty."""
        from app.services.ocr_text_parser import OcrTextParser

        name, address = OcrTextParser.extract_name_and_address(None)
        assert name == ""
        assert address == ""

    def test_string_returns_as_name(self):
        """Scenario: String input → name only, no address."""
        from app.services.ocr_text_parser import OcrTextParser

        name, address = OcrTextParser.extract_name_and_address("plain text")
        assert name == "plain text"
        assert address == ""

    def test_empty_dict_returns_empty_pair(self):
        """Scenario: Empty dict → both empty."""
        from app.services.ocr_text_parser import OcrTextParser

        name, address = OcrTextParser.extract_name_and_address({})
        assert name == ""
        assert address == ""
