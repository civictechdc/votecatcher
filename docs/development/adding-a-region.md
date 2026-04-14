# Adding a New Region

A step-by-step tutorial for adding support for a new voter region (e.g., Maryland).

## Prerequisites

- Local dev environment running (`uv run uvicorn app.main:app`)
- Familiarity with JSON5 syntax (comments, trailing commas allowed)

## Steps

### 1. Study the region's voter CSV

Download a sample voter registration CSV for the target region. Identify:

- **Column names** — these become `csv_column_name` in the spec
- **Field categories** — which columns are name fields, address fields, registration fields, or geography fields
- **Hash fields** — which fields uniquely identify a voter (typically last name, first name, street number, street name)

### 2. Create the spec file

Copy an existing spec as a starting point:

```bash
cp backend/app/regions/demo.json5 backend/app/regions/md.json5
```

Edit `md.json5` with the new region's details. See the [field spec schema reference](./field-spec-schema.md) for all field definitions.

Key fields to update:

| Field | Description | Example |
|-------|-------------|---------|
| `region_name` | Full region name | `"Maryland"` |
| `country_code` | ISO country code | `"US"` |
| `ballot_fields` | Fields on the petition/ballot | Usually same as DC (name, address, ward, date_signed) |
| `voter_reg_fields` | CSV column → field ID mapping | Match your region's CSV columns |
| `field_mappings` | Templates composing ballot fields from voter fields | e.g., `"{first_name} {middle_name} {last_name}"` |
| `hash_fields` | Fields used for voter deduplication | e.g., `["last_name", "first_name", "street_number"]` |
| `crop_config` | Petition image crop boundaries | Adjust for your region's petition layout |

### 3. Validate locally

```bash
cd backend
uv run python -c "
from app.domain.field_spec import RegionFieldSpecConfig
import json5
from pathlib import Path
raw = Path('app/regions/md.json5').read_text()
data = json5.loads(raw)
spec = RegionFieldSpecConfig.model_validate(data)
errors = spec.validate_integrity()
if errors:
    for e in errors:
        print(f'ERROR: {e}')
else:
    print('Spec is valid!')
"
```

Fix any validation errors before proceeding.

### 4. Run existing tests

All existing spec tests must still pass:

```bash
cd backend
uv run pytest tests/unit/domain/test_dc_spec_approval.py -v
uv run pytest tests/unit/domain/test_demo_spec_approval.py -v
uv run pytest tests/unit/domain/test_template_renderer.py -v
```

### 5. Commit the spec

```
feat(field-spec): add md.json5 Maryland region spec
```

### 6. Deploy

On deploy, app startup automatically loads all `.json5` files from `app/regions/` into the database. The new region appears in the campaign create dropdown — no code changes needed.

### 7. Verify

1. Start the app: `uv run uvicorn app.main:app`
2. Check logs for spec loading: `Loaded spec for region MD`
3. Open the campaign create modal — Maryland should appear in the region dropdown
4. Create a campaign with the Maryland region
5. Upload a Maryland voter CSV — verify column mapping works

## Tips

- **Use `demo.json5` as a minimal template** — it has only 7 voter reg fields, good for prototyping
- **Use `dc.json5` as a comprehensive reference** — it has 21 voter reg fields covering all categories
- **Test template rendering** — write a quick test that `render_template` produces correct ballot fields from your voter data shape
- **Categories matter** — `name` fields go into `name_data`, `address` into `address_data`, everything else into `other_field_data`. This determines how voters are stored and matched
- **Region key is auto-derived** — filename stem uppercased (`md.json5` → `"MD"`)
