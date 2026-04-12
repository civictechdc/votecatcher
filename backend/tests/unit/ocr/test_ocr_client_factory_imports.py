"""Tests for ocr_client_factory using updated settings module."""

import ast


class TestOcrClientFactoryImports:
    """Verify ocr_client_factory uses the current settings API."""

    def test_imports_get_settings_not_load_settings(self):
        """ocr_client_factory must import get_settings, not load_settings."""
        source = open("app/ocr/ocr_client_factory.py").read()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "settings" in node.module:
                    alias_names = [a.name for a in node.names]
                    assert "load_settings" not in alias_names, (
                        "ocr_client_factory must not import load_settings (deleted)"
                    )

    def test_does_not_import_deleted_config_classes(self):
        """ocr_client_factory must not import OpenAiConfig/MistralAiConfig/GeminiAiConfig."""
        source = open("app/ocr/ocr_client_factory.py").read()
        tree = ast.parse(source)

        deleted_classes = {"OpenAiConfig", "MistralAiConfig", "GeminiAiConfig"}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "settings" in node.module:
                    alias_names = [a.name for a in node.names]
                    for name in alias_names:
                        assert name not in deleted_classes, (
                            f"ocr_client_factory must not import deleted class {name}"
                        )

    def test_uses_ocr_config_from_settings(self):
        """ocr_client_factory should use get_settings().ocr for OCR config."""
        source = open("app/ocr/ocr_client_factory.py").read()
        assert "get_settings" in source, "ocr_client_factory must use get_settings"
        assert (
            ".ocr" in source or "ocr_config" in source or "provider_name" in source
        ), "ocr_client_factory should use OCR config from get_settings()"
