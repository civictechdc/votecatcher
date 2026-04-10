"""Pure-Python .env file parser.

Replaces `dotenv.load_dotenv` and `dotenv.dotenv_values` with a minimal
implementation that handles the .env format used by the Settings system:
  - KEY=VALUE lines
  - Quoted values (single or double quotes)
  - export KEY=VALUE lines
  - # comments and blank lines
"""

import os
import re
from pathlib import Path

_LINE_RE = re.compile(
    r"""^\s*(?:export\s+)?"""
    r"""([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"""
    r"""(.*)$"""
)


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse a .env file and return a dict of key-value pairs."""
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        m = _LINE_RE.match(line)
        if not m:
            continue

        key, raw_val = m.group(1), m.group(2).strip()
        if len(raw_val) >= 2 and raw_val[0] == raw_val[-1] and raw_val[0] in ("'", '"'):
            raw_val = raw_val[1:-1]

        values[key] = raw_val
    return values


def load_env_into_os(path: Path, *, override: bool = True) -> None:
    """Load env vars from *path* into ``os.environ``."""
    for key, value in parse_env_file(path).items():
        if override or key not in os.environ:
            os.environ[key] = value
