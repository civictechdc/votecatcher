# Regional Field Specifications

This directory contains JSON5 field specification files for each supported voter region.

## Files

| File | Region | Description |
|------|--------|-------------|
| `dc.json5` | District of Columbia | DC Board of Elections voter roll format |
| `demo.json5` | Demo Region | Simplified DC subset for dev/demo/simulation modes and fallback |

## Adding a New Region

1. Copy `dc.json5` as a template: `cp dc.json5 <region_key>.json5`
2. Update the fields to match the new region's voter roll CSV format
3. Validate locally:

```bash
uv run python -c "
from app.domain.field_spec import RegionFieldSpecConfig
import json5
spec = RegionFieldSpecConfig.model_validate(json5.loads(open('app/regions/<region_key>.json5').read()))
errors = spec.validate_integrity()
print('OK' if not errors else errors)
"
```

4. Run approval tests — the new spec gets its own snapshot
5. See `docs/development/field-spec-schema.md` for the full schema reference

## Naming Convention

- Filename: lowercase region key (e.g., `dc.json5`, `md.json5`)
- The stem is uppercased at startup to form `region_key` in the database (`dc.json5` → `"DC"`)
