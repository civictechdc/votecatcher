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
		from app.settings.env_settings import AppSettings

		settings = AppSettings()
		assert hasattr(settings, "always_batch_ocr"), (
			"Settings should have always_batch_ocr attribute"
		)
		assert settings.always_batch_ocr is True, "Default value should be True"

	def test_config_router_includes_always_batch_flag(self):
		"""Verify FeatureFlagsResponse includes alwaysBatchOcr field."""
		from app.routers.config_router import FeatureFlagsResponse

		field_names = FeatureFlagsResponse.model_fields.keys()
		assert "alwaysBatchOcr" in field_names, (
			"FeatureFlagsResponse should include alwaysBatchOcr"
		)

	def test_config_endpoint_returns_always_batch_flag(self):
		"""Verify /config/features endpoint returns alwaysBatchOcr value."""
		from app.routers.config_router import get_features
		from app.settings.env_settings import get_settings

		settings = get_settings()
		response = get_features(settings)

		assert hasattr(response, "alwaysBatchOcr")
		assert response.alwaysBatchOcr == settings.always_batch_ocr

	def test_settings_endpoint_returns_always_batch_flag(self):
		"""Verify /config/settings endpoint returns alwaysBatchOcr in features."""
		from app.routers.config_router import get_settings_endpoint
		from app.settings.env_settings import get_settings

		settings = get_settings()
		response = get_settings_endpoint(settings)

		assert hasattr(response.features, "alwaysBatchOcr")
		assert response.features.alwaysBatchOcr == settings.always_batch_ocr
