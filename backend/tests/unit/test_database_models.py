"""Tests for database API models."""

import pytest
from pydantic import ValidationError


class TestDatabaseStatus:
    """Tests for DatabaseStatus model."""

    def test_create_status(self):
        from app.api_models.database import DatabaseStatus

        status = DatabaseStatus(
            configured=True,
            type="sqlite",
            connected=True,
            message="Database ready",
        )
        assert status.configured is True
        assert status.type == "sqlite"

    def test_validates_type(self):
        from app.api_models.database import DatabaseStatus

        with pytest.raises(ValidationError):
            DatabaseStatus(
                configured=True,
                type="invalid",
                connected=True,
                message="",
            )

    def test_valid_types(self):
        from app.api_models.database import DatabaseStatus

        for valid_type in ("sqlite", "postgres", "supabase"):
            status = DatabaseStatus(
                configured=True,
                type=valid_type,
                connected=False,
                message="",
            )
            assert status.type == valid_type


class TestSupabaseCredentials:
    """Tests for SupabaseCredentials model."""

    def test_valid_credentials(self):
        from app.api_models.database import SupabaseCredentials

        creds = SupabaseCredentials(
            project_url="https://xyz.supabase.co",
            service_key="sb_secret_" + "x" * 100,  # pragma: allowlist secret
            db_password="my_password",  # pragma: allowlist secret
        )
        assert creds.project_url == "https://xyz.supabase.co"

    def test_valid_credentials_regional_url(self):
        from app.api_models.database import SupabaseCredentials

        creds = SupabaseCredentials(
            project_url="https://xyz.supabase.in",
            service_key="sb_secret_" + "x" * 100,  # pragma: allowlist secret
            db_password="my_password",  # pragma: allowlist secret
        )
        assert creds.project_url == "https://xyz.supabase.in"

    def test_valid_credentials_custom_domain(self):
        from app.api_models.database import SupabaseCredentials

        creds = SupabaseCredentials(
            project_url="https://db.mycompany.com",
            service_key="sb_secret_" + "x" * 100,  # pragma: allowlist secret
            db_password="my_password",  # pragma: allowlist secret
        )
        assert creds.project_url == "https://db.mycompany.com"

    def test_validates_url_format(self):
        from app.api_models.database import SupabaseCredentials

        with pytest.raises(ValidationError):
            SupabaseCredentials(
                project_url="invalid-url",
                service_key="sb_secret_" + "x" * 100,  # pragma: allowlist secret
                db_password="password",  # pragma: allowlist secret
            )

    def test_service_key_is_secret(self):
        from pydantic import SecretStr

        from app.api_models.database import SupabaseCredentials

        creds = SupabaseCredentials(
            project_url="https://xyz.supabase.co",
            service_key="sb_secret_" + "x" * 100,  # pragma: allowlist secret
            db_password="password",  # pragma: allowlist secret
        )
        assert isinstance(creds.service_key, SecretStr)

    def test_db_password_is_secret(self):
        from pydantic import SecretStr

        from app.api_models.database import SupabaseCredentials

        creds = SupabaseCredentials(
            project_url="https://xyz.supabase.co",
            service_key="sb_secret_" + "x" * 100,  # pragma: allowlist secret
            db_password="password",  # pragma: allowlist secret
        )
        assert isinstance(creds.db_password, SecretStr)

    def test_service_key_min_length(self):
        from app.api_models.database import SupabaseCredentials

        with pytest.raises(ValidationError):
            SupabaseCredentials(
                project_url="https://xyz.supabase.co",
                service_key="short",  # pragma: allowlist secret
                db_password="password",  # pragma: allowlist secret
            )


class TestConnectionTestResult:
    """Tests for ConnectionTestResult model."""

    def test_success_result(self):
        from app.api_models.database import ConnectionTestResult

        result = ConnectionTestResult(
            success=True,
            message="Connection successful",
            project_ref="xyzproject",
        )
        assert result.success is True
        assert result.project_ref == "xyzproject"

    def test_failure_result(self):
        from app.api_models.database import ConnectionTestResult

        result = ConnectionTestResult(
            success=False,
            message="Connection refused",
        )
        assert result.success is False
        assert result.project_ref is None


class TestProvisionResult:
    """Tests for ProvisionResult model."""

    def test_success_with_tables(self):
        from app.api_models.database import ProvisionResult

        result = ProvisionResult(
            success=True,
            message="Provisioned",
            tables_created=["campaign", "voter"],
        )
        assert result.tables_created == ["campaign", "voter"]

    def test_failure_no_tables(self):
        from app.api_models.database import ProvisionResult

        result = ProvisionResult(
            success=False,
            message="Failed",
        )
        assert result.tables_created is None
