"""Tests for configuration contracts."""


class TestProvidesDatabaseConfig:
    """Tests for ProvidesDatabaseConfig protocol."""

    def test_protocol_has_url_property(self):
        """Protocol must define url property."""
        from app.settings.contracts import ProvidesDatabaseConfig

        assert hasattr(ProvidesDatabaseConfig, "__protocol_attrs__")
        attrs = ProvidesDatabaseConfig.__protocol_attrs__
        assert "url" in attrs
        assert "type" in attrs


class TestProvidesSupabaseConfig:
    """Tests for ProvidesSupabaseConfig protocol."""

    def test_protocol_has_required_properties(self):
        """Protocol must define all Supabase properties."""
        from app.settings.contracts import ProvidesSupabaseConfig

        attrs = ProvidesSupabaseConfig.__protocol_attrs__
        assert "url" in attrs
        assert "service_key" in attrs
        assert "is_connected" in attrs
        assert "database_url" in attrs
