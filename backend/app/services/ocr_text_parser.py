"""OCR text parser for formatting extracted_text into display strings."""

from __future__ import annotations


class OcrTextParser:
    """Formats OCR extracted_text (dict/str/None) into consistent strings.

    Pure functions — no I/O. Handles the three formats extracted_text
    can appear as: dict, str, or None.
    """

    @staticmethod
    def format_text(extracted_text: dict | str | None) -> str:
        if extracted_text is None:
            return ""
        if isinstance(extracted_text, str):
            return extracted_text
        text_parts = []
        for key in sorted(extracted_text.keys()):
            val = extracted_text.get(key)
            if val:
                text_parts.append(str(val))
        return " ".join(text_parts)

    @staticmethod
    def extract_name_and_address(
        extracted_text: dict | str | None,
    ) -> tuple[str, str]:
        if extracted_text is None:
            return "", ""
        if isinstance(extracted_text, str):
            return extracted_text, ""
        return (
            extracted_text.get("name") or "",
            extracted_text.get("address") or "",
        )
