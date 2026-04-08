"""Tests for Supabase service."""

from unittest.mock import MagicMock, patch

import pytest

from app.api_models.database import ConnectionTestResult, ProvisionResult
from app.services.supabase_service import update_env_file
from app.utils.masking import mask_connection_url, mask_url


class TestMaskUrl:
    """Tests for URL masking."""

    def test_masks_standard_supabase_co(self):
        assert mask_url("https://myproject.supabase.co") == "https://myp***.supabase.co"

    def test_masks_regional_supabase_in(self):
        assert mask_url("https://myproject.supabase.in") == "https://myp***.supabase.in"

    def test_masks_custom_domain(self):
        assert mask_url("https://db.mycompany.com") == "https://***.mycompany.com"

    def test_masks_short_subdomain(self):
        assert mask_url("https://ab.supabase.co") == "https://***.supabase.co"

    def test_returns_mask_for_non_url(self):
        assert mask_url("not-a-url") == "***"

    def test_masks_url_with_port(self):
        result = mask_url("https://myproject.supabase.co:5432")
        assert "myp***" in result


class TestMaskConnectionUrl:
    """Tests for PostgreSQL connection URL masking."""

    def test_masks_standard_postgresql(self):
        result = mask_connection_url("postgresql://user:secret@host:5432/db")
        assert result == "postgresql://user:****@host:5432/db"

    def test_masks_postgresql_with_driver(self):
        result = mask_connection_url("postgresql+psycopg://user:secret@host/db")
        assert result == "postgresql+psycopg://user:****@host/db"

    def test_preserves_url_without_password(self):
        url = "postgresql://host:5432/db"
        assert mask_connection_url(url) == url

    def test_masks_long_password(self):
        url = (
            "postgresql://admin:a_very_long_password_here"  # pragma: allowlist secret
            "@db.example.com:5432/mydb"
        )
        result = mask_connection_url(url)
        assert "a_very_long_password_here" not in result
        assert "****" in result
        assert "admin:" in result
        assert "@db.example.com" in result


class TestSupabaseService:
    """Tests for Supabase connection and provisioning."""

    @pytest.mark.asyncio
    async def test_test_connection_success(self):
        """test_connection should return success when auth session is valid."""
        from app.services.supabase_service import test_connection

        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_client.auth.get_session.return_value = mock_session

        with patch(
            "supabase.create_client",
            return_value=mock_client,
        ):
            result = await test_connection(
                project_url="https://testproj.supabase.co",
                service_key="valid_key",  # pragma: allowlist secret
            )
        assert result.success is True
        assert result.project_ref == "testproj"

    @pytest.mark.asyncio
    async def test_test_connection_auth_returns_none(self):
        """test_connection should return failure when auth session is None."""
        from app.services.supabase_service import test_connection

        mock_client = MagicMock()
        mock_client.auth.get_session.return_value = None

        with patch(
            "supabase.create_client",
            return_value=mock_client,
        ):
            result = await test_connection(
                project_url="https://testproj.supabase.co",
                service_key="valid_key",  # pragma: allowlist secret
            )
        assert isinstance(result, ConnectionTestResult)
        assert result.success is False
        assert result.project_ref == "testproj"
        assert "Auth" in result.message

    @pytest.mark.asyncio
    async def test_test_connection_auth_raises(self):
        """test_connection should return failure when auth raises."""
        from app.services.supabase_service import test_connection

        mock_client = MagicMock()
        mock_client.auth.get_session.side_effect = Exception("Invalid key")

        with patch(
            "supabase.create_client",
            return_value=mock_client,
        ):
            result = await test_connection(
                project_url="https://testproj.supabase.co",
                service_key="bad_key",  # pragma: allowlist secret
            )
        assert isinstance(result, ConnectionTestResult)
        assert result.success is False

    @pytest.mark.asyncio
    async def test_test_connection_failure(self):
        """test_connection should return failure when client creation fails."""
        from app.services.supabase_service import test_connection

        with patch(
            "supabase.create_client",
            side_effect=Exception("Invalid URL"),
        ):
            result = await test_connection(
                project_url="https://bad.supabase.co",
                service_key="bad_key",  # pragma: allowlist secret
            )
        assert isinstance(result, ConnectionTestResult)
        assert result.success is False
        assert "Connection failed" in result.message

    @pytest.mark.asyncio
    async def test_test_connection_regional_url(self):
        """test_connection should extract project ref from regional URLs."""
        from app.services.supabase_service import test_connection

        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_client.auth.get_session.return_value = mock_session

        with patch(
            "supabase.create_client",
            return_value=mock_client,
        ):
            result = await test_connection(
                project_url="https://myproject.supabase.in",
                service_key="valid_key",  # pragma: allowlist secret
            )
        assert result.success is True
        assert result.project_ref == "myproject"

    @pytest.mark.asyncio
    async def test_test_connection_custom_domain(self):
        """test_connection should extract project ref from custom domains."""
        from app.services.supabase_service import test_connection

        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_client.auth.get_session.return_value = mock_session

        with patch(
            "supabase.create_client",
            return_value=mock_client,
        ):
            result = await test_connection(
                project_url="https://myproject.custom.example.com",
                service_key="valid_key",  # pragma: allowlist secret
            )
        assert result.success is True
        assert result.project_ref == "myproject"

    @pytest.mark.asyncio
    async def test_test_connection_non_standard_tld(self):
        """test_connection should handle non-standard TLDs."""
        from app.services.supabase_service import test_connection

        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_client.auth.get_session.return_value = mock_session

        with patch(
            "supabase.create_client",
            return_value=mock_client,
        ):
            result = await test_connection(
                project_url="https://myproject.supabase.party",
                service_key="valid_key",  # pragma: allowlist secret
            )
        assert result.success is True
        assert result.project_ref == "myproject"

    @pytest.mark.asyncio
    async def test_test_connection_no_project_ref(self):
        """test_connection should handle URLs with no extractable project ref."""
        from app.services.supabase_service import test_connection

        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_client.auth.get_session.return_value = mock_session

        with patch(
            "supabase.create_client",
            return_value=mock_client,
        ):
            result = await test_connection(
                project_url="localhost:5432",
                service_key="valid_key",  # pragma: allowlist secret
            )
        assert result.success is True
        assert result.project_ref is None

    @pytest.mark.asyncio
    async def test_provision_fails_when_connection_fails(self):
        """provision_database should fail if connection test fails."""
        from app.services.supabase_service import provision_database

        with patch(
            "app.services.supabase_service.test_connection",
            return_value=ConnectionTestResult(
                success=False, message="Connection refused"
            ),
        ):
            result = await provision_database(
                project_url="https://bad.supabase.co",
                service_key="bad_key",  # pragma: allowlist secret
                db_password="bad_pass",  # pragma: allowlist secret
            )
        assert isinstance(result, ProvisionResult)
        assert result.success is False
        assert "Connection refused" in result.message


class TestEnvFileWriting:
    """Tests for environment file operations."""

    def test_update_env_file_adds_new_vars(self, tmp_path):
        """Should add new variables to env file."""
        env_file = tmp_path / ".env.local"
        env_file.write_text("EXISTING_VAR=value\n")

        update_env_file(
            env_file,
            {
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_SERVICE_KEY": "test_key",  # pragma: allowlist secret
            },
        )

        content = env_file.read_text()
        assert "SUPABASE_URL=https://test.supabase.co" in content
        assert "EXISTING_VAR=value" in content

    def test_update_env_file_updates_existing(self, tmp_path):
        """Should update existing variables."""
        env_file = tmp_path / ".env.local"
        env_file.write_text("SUPABASE_URL=https://old.supabase.co\n")

        update_env_file(
            env_file,
            {"SUPABASE_URL": "https://new.supabase.co"},
        )

        content = env_file.read_text()
        assert "SUPABASE_URL=https://new.supabase.co" in content
        assert "old.supabase.co" not in content

    def test_update_env_file_removes_empty(self, tmp_path):
        """Should remove variables with empty values when remove_empty=True."""
        env_file = tmp_path / ".env.local"
        env_file.write_text("SUPABASE_URL=https://test.supabase.co\nKEEP_ME=yes\n")

        update_env_file(
            env_file,
            {"SUPABASE_URL": ""},
            remove_empty=True,
        )

        content = env_file.read_text()
        assert "SUPABASE_URL" not in content
        assert "KEEP_ME=yes" in content

    def test_update_env_file_creates_new(self, tmp_path):
        """Should create new file if it doesn't exist."""
        env_file = tmp_path / ".env.local"

        update_env_file(
            env_file,
            {"SUPABASE_URL": "https://test.supabase.co"},
        )

        assert env_file.exists()
        content = env_file.read_text()
        assert "SUPABASE_URL=https://test.supabase.co" in content

    def test_update_env_file_preserves_comments(self, tmp_path):
        """Should preserve comments and blank lines."""
        env_file = tmp_path / ".env.local"
        env_file.write_text("# Comment\n\nEXISTING_VAR=value\n")

        update_env_file(
            env_file,
            {"NEW_VAR": "new_value"},
        )

        content = env_file.read_text()
        assert "# Comment" in content
        assert "EXISTING_VAR=value" in content
        assert "NEW_VAR=new_value" in content

    def test_update_env_file_raises_on_unreadable(self, tmp_path):
        """Should raise OSError when env file cannot be read."""
        import stat

        env_file = tmp_path / ".env.local"
        env_file.write_text("EXISTING_VAR=value\n")
        env_file.chmod(0o000)

        try:
            with pytest.raises(OSError, match="Failed to read"):
                update_env_file(env_file, {"NEW_VAR": "new_value"})
        finally:
            env_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
