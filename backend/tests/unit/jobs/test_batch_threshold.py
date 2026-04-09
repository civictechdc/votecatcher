"""Tests for OCR batching threshold and always-batch feature flag.

Issue #13: Lower batch threshold to 5 and add always-batch feature flag.
"""

from app.jobs.worker import BATCH_THRESHOLD


class TestBatchThresholdAndFeatureFlag:
    """Test suite for OCR batch threshold and feature flag behavior."""

    def test_batch_threshold_is_5(self):
        """Verify BATCH_THRESHOLD is set to 5."""
        assert BATCH_THRESHOLD == 5, "BATCH_THRESHOLD should be 5"

    def test_always_batch_ocr_flag_exists(self):
        """Verify always_batch_ocr flag exists in settings."""
        from app.settings import Settings

        settings = Settings(FEATURE_ALWAYS_BATCH_OCR=True)
        assert hasattr(settings, "always_batch_ocr"), (
            "Settings should have always_batch_ocr attribute"
        )
        assert settings.always_batch_ocr is True, "Default value should be True"

    def test_config_router_includes_always_batch_flag(self):
        """Verify FeatureFlagsResponse includes always_batch_ocr field."""
        from app.routers.config_router import FeatureFlagsResponse

        field_names = FeatureFlagsResponse.model_fields.keys()
        assert "always_batch_ocr" in field_names, (
            "FeatureFlagsResponse should include always_batch_ocr"
        )

    def test_config_endpoint_returns_always_batch_flag(self):
        """Verify /config/features endpoint returns always_batch_ocr value."""
        from app.routers.config_router import get_features
        from app.settings import get_settings

        settings = get_settings()
        response = get_features(settings)

        assert hasattr(response, "always_batch_ocr")
        assert response.always_batch_ocr == settings.always_batch_ocr

    def test_settings_endpoint_returns_always_batch_flag(self):
        """Verify /config/settings endpoint returns always_batch_ocr in features."""
        from app.routers.config_router import get_settings_endpoint
        from app.settings import get_settings

        settings = get_settings()
        response = get_settings_endpoint(settings)

        assert hasattr(response.features, "always_batch_ocr")
        assert response.features.always_batch_ocr == settings.always_batch_ocr
