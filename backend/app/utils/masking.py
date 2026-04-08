"""URL masking utilities for safe logging."""

import re


def mask_url(url: str) -> str:
    """Mask project ref in Supabase URL for logging."""
    if "://" in url:
        parts = url.split("://")
        host = parts[1].split("/")[0].split(":")[0]
        sub = host.split(".")[0]
        rest = host[len(sub) + 1 :]
        if len(sub) > 3:
            return f"{parts[0]}://{sub[:3]}***.{rest}"
        return f"{parts[0]}://***.{rest}"
    return "***"


def mask_connection_url(url: str) -> str:
    """Mask password in PostgreSQL connection URL for logging."""
    return re.sub(
        r"(postgresql(\+\w+)?://[^:]+:)[^@]+(@.*)",
        r"\1****\3",
        url,
    )
