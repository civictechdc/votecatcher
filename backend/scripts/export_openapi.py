#!/usr/bin/env python
"""Export the FastAPI OpenAPI schema to backend/openapi.yaml.

`backend/openapi.yaml` is a deterministic derivation of the app's route
table: no server boot, no lifespan execution, no database access. Running
the script twice yields byte-identical output (sorted keys, stable
serialization, atomic replace).
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

# Hermetic shim, modeled on tests/conftest.py (which sets an in-memory
# SQLite URI and empty Supabase vars but pins no ENVIRONMENT): the export
# must not vary with developer-local settings or databases. This script
# adds the ENVIRONMENT pin that conftest lacks, because production mode
# fail-closes on missing CORS_ORIGINS at import time — CORS config is
# middleware-only and never appears in the schema, so this pin cannot
# change the output.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["ENVIRONMENT"] = "development"
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_SERVICE_KEY"] = ""
os.environ["SUPABASE_DB_PASSWORD"] = ""

import yaml

OUTPUT_PATH = Path(__file__).parent.parent / "openapi.yaml"


def build_schema() -> dict[str, Any]:
    from app.api import app

    # Round-trip through JSON so every mapping key is a string (PyYAML
    # cannot sort mixed-type keys) and shared object references are
    # unshared, so no anchors/aliases are emitted.
    return json.loads(json.dumps(app.openapi()))


def export_openapi(output_path: Path = OUTPUT_PATH) -> None:
    schema = build_schema()
    text = yaml.safe_dump(
        schema,
        sort_keys=True,
        default_flow_style=False,
        allow_unicode=True,
    )
    fd, tmp_name = tempfile.mkstemp(
        dir=output_path.parent, prefix=".openapi.", suffix=".yaml.tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.chmod(tmp_name, 0o644)
        os.replace(tmp_name, output_path)
    except BaseException:
        # Remove on ANY failure (including UnicodeEncodeError, whose parent
        # ValueError the previous OSError-only catch missed); re-raise.
        Path(tmp_name).unlink(missing_ok=True)
        raise
    print(f"Exported OpenAPI schema: {output_path}")


if __name__ == "__main__":
    export_openapi()
