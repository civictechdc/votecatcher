"""BDD contract tests for the pure-Python .env parser.

These tests define the behavioral contract for parse_env_file and
load_env_into_os — what the .env format parser must handle.
"""

import os
from pathlib import Path

from app.settings.env_parser import load_env_into_os, parse_env_file


class TestParseEnvFile:
    """parse_env_file reads .env files and returns key-value pairs."""

    def test_simple_key_value(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("DATABASE_URL=sqlite:///./dev.db\n")
        assert parse_env_file(env) == {"DATABASE_URL": "sqlite:///./dev.db"}

    def test_multiple_entries(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("KEY_A=value_a\nKEY_B=value_b\n")
        result = parse_env_file(env)
        assert result == {"KEY_A": "value_a", "KEY_B": "value_b"}

    def test_ignores_comments(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("# This is a comment\nKEY=value\n")
        assert parse_env_file(env) == {"KEY": "value"}

    def test_ignores_blank_lines(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("\n\nKEY=value\n\n")
        assert parse_env_file(env) == {"KEY": "value"}

    def test_strips_double_quoted_values(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text('KEY="quoted value"\n')
        assert parse_env_file(env) == {"KEY": "quoted value"}

    def test_strips_single_quoted_values(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("KEY='quoted value'\n")
        assert parse_env_file(env) == {"KEY": "quoted value"}

    def test_handles_export_prefix(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("export KEY=value\n")
        assert parse_env_file(env) == {"KEY": "value"}

    def test_returns_empty_for_missing_file(self, tmp_path: Path):
        assert parse_env_file(tmp_path / ".env.nonexistent") == {}

    def test_skips_malformed_lines(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("NO_EQUALS_SIGN\nKEY=value\n")
        assert parse_env_file(env) == {"KEY": "value"}

    def test_empty_value(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("EMPTY=\n")
        assert parse_env_file(env) == {"EMPTY": ""}

    def test_value_with_equals_sign(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("URL=postgres://user@host:5432/db\n")
        assert parse_env_file(env) == {"URL": "postgres://user@host:5432/db"}

    def test_inline_comment_not_stripped(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("KEY=value # comment\n")
        result = parse_env_file(env)
        assert result["KEY"] == "value # comment"


class TestLoadEnvIntoOs:
    """load_env_into_os populates os.environ from an .env file."""

    def test_sets_env_vars(self, tmp_path: Path, monkeypatch):
        env = tmp_path / ".env"
        env.write_text("TEST_PARSER_KEY=parser_value\n")
        monkeypatch.delenv("TEST_PARSER_KEY", raising=False)

        load_env_into_os(env, override=True)
        assert os.environ["TEST_PARSER_KEY"] == "parser_value"

        monkeypatch.delenv("TEST_PARSER_KEY")

    def test_override_true_replaces_existing(self, tmp_path: Path, monkeypatch):
        env = tmp_path / ".env"
        env.write_text("TEST_PARSER_OVERRIDE=new_value\n")
        monkeypatch.setenv("TEST_PARSER_OVERRIDE", "old_value")

        load_env_into_os(env, override=True)
        assert os.environ["TEST_PARSER_OVERRIDE"] == "new_value"

        monkeypatch.delenv("TEST_PARSER_OVERRIDE")

    def test_override_false_preserves_existing(self, tmp_path: Path, monkeypatch):
        env = tmp_path / ".env"
        env.write_text("TEST_PARSER_PRESERVE=file_value\n")
        monkeypatch.setenv("TEST_PARSER_PRESERVE", "existing_value")

        load_env_into_os(env, override=False)
        assert os.environ["TEST_PARSER_PRESERVE"] == "existing_value"

        monkeypatch.delenv("TEST_PARSER_PRESERVE")

    def test_noop_for_missing_file(self, tmp_path: Path):
        load_env_into_os(tmp_path / ".env.nonexistent", override=True)
