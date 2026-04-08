from typing import Any

# In-memory 'database' for testing/debug purposes. Do not use to store
# large volumes of data

_memory_db: dict[str, Any] | None = None


def get_memory_db() -> dict[str, Any]:
    global _memory_db
    if _memory_db is None:
        _memory_db = {}
    return _memory_db
