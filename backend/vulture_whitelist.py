"""Vulture whitelist — false positives.

These are required by framework protocols/callbacks but flagged as unused.
Run: vulture app/ vulture_whitelist.py --min-confidence 80
"""

# FastAPI lifespan callback — param required by signature
_.application  # noqa: F821 - app/api.py:21

# TYPE_CHECKING import — used for type annotations only
_.OCRService  # noqa: F821 - app/jobs/job_orchestrator.py:23

# Structlog processor protocol — param required by signature
_.method  # noqa: F821 - app/observability/event_validation.py:52

# Sentry before_send callback — param required by signature
_.hint  # noqa: F821 - app/observability/sentry.py:25

# Protocol method param — used by implementers
_.cropped_assets  # noqa: F821 - app/files/file_repository.py:78

# Structlog processor protocol — param required by signature
_.method_name  # noqa: F821 - app/logger_config/app_logger.py:41
_.method_name  # noqa: F821 - app/logger_config/app_logger.py:67

# Pydantic model_post_init — param required by signature
_.__context  # noqa: F821 - app/settings/providers/database_config.py:33

# Pydantic settings_customise_sources — param required by override signature
_.dotenv_settings  # noqa: F821 - app/settings/settings.py:68
