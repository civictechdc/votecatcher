"""Rate limiting configuration and setup.

In-memory per-IP rate limiting via slowapi.
"""

from dataclasses import dataclass

_DEFAULT_LIMIT = "60/minute"
_UPLOAD_LIMIT = "10/minute"
_JOB_CREATE_LIMIT = "10/minute"


@dataclass
class RateLimitConfig:
    enabled: bool = True
    default_limit: str = _DEFAULT_LIMIT
    upload_limit: str = _UPLOAD_LIMIT
    job_create_limit: str = _JOB_CREATE_LIMIT


def create_rate_limiter(config: RateLimitConfig):
    if not config.enabled:
        return None

    from slowapi import Limiter
    from slowapi.util import get_remote_address

    return Limiter(key_func=get_remote_address)
