"""Load configuration from OS environment variables."""

import os


class EnvironmentSource:
    """Read configuration from os.environ."""

    def get(self, key: str, default: str | None = None) -> str | None:
        return os.environ.get(key, default)
