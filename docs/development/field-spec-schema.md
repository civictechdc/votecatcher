# Field Spec Schema Reference

Reference document for the JSON5 regional field specification file format.

## Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `region_name` | string | yes | Human-readable region name (e.g., `"District of Columbia"`) |
| `country_code` | string | no | ISO 3166-1 alpha-2 country code. Default: `"US"` |
| `ballot_fields` | array | yes | Fields expected on the ballot/petition |
| `voter_reg_fields` | array | yes | Fields available from voter registration CSV |
| `field_mappings` | array | yes | Templates mapping voter fields → ballot fields |
| `hash_fields` | array | yes | Voter field IDs used for deduplication hash |
| `crop_config` | object | yes | OCR crop region configuration |

## `ballot_fields` Schema

Each entry describes a field that appears on the ballot or petition.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique identifier (e.g., `"name"`, `"address"`, `"ward"`) |
| `label` | string | yes | Display label (e.g., `"Full Name"`) |
| `field_type` | enum | yes | One of: `"text"`, `"address"`, `"integer"`, `"date"` |
| `required_for_matching` | boolean | yes | Whether this field is used for voter matching |
| `match_weight` | number | no | Weight for similarity scoring. Default: `1.0`. Must be >= 0 |

## `voter_reg_fields` Schema

Each entry maps a CSV column to an internal field ID.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Internal field ID (e.g., `"first_name"`, `"zip_code"`) |
| `csv_column_name` | string | yes | Exact column header in the voter roll CSV |
| `data_type` | enum | yes | One of: `"text"`, `"integer"`, `"date"` |
| `category` | enum | yes | One of: `"name"`, `"address"`, `"registration"`, `"geography"` |

### Category → JSON Blob Mapping

When voter data is stored in the database, fields are grouped by category into nested JSON blobs on `RegisteredVoter`:

| Category | Blob | Example Fields |
|----------|------|----------------|
| `name` | `name_data` | `first_name`, `last_name`, `middle_name` |
| `address` | `address_data` | `street_number`, `street_name`, `zip_code` |
| `registration` | `other_field_data` | `party`, `voter_status`, `registration_date` |
| `geography` | `other_field_data` | `ward`, `precinct`, `anc`, `smd` |

## `field_mappings` Schema

Each entry defines how voter fields compose into a ballot field value.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ballot_field_id` | string | yes | References a `ballot_fields[].id` |
| `template` | string | yes | Template with `{field_id}` placeholders. Empty string = not rendered |

### Template Syntax

- Placeholders: `{voter_reg_field_id}` — replaced with the voter's field value
- Empty/missing values: placeholder removed, extra spaces collapsed
- N/A sentinel: values `"N/A"` or `"NA"` (case-insensitive) treated as empty
- Trailing `"Apt"` label: removed when apartment number is empty
- Multiple commas/spaces: collapsed

Example: `"{street_number}{street_number_suffix} {street_name} {street_type} {street_dir_suffix}, Apt {apartment_number}"`

## `hash_fields` Schema

Array of `voter_reg_fields[].id` values used to compute a deduplication hash for each voter row.

```json5
hash_fields: ["last_name", "first_name", "street_number", "street_name", "zip_code"]
```

## `crop_config` Schema

OCR crop region for petition/ballot image processing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `top_crop` | number | yes | Top boundary (0.0–1.0, fraction of image height) |
| `bottom_crop` | number | yes | Bottom boundary (0.0–1.0, must be > top_crop) |
| `base_threshold` | integer | yes | Grayscale threshold for line detection (0–255) |

## Validation Rules

`RegionFieldSpecConfig.validate_integrity()` enforces these rules:

1. **No duplicate `ballot_fields[].id`** — each ID must be unique
2. **No duplicate `voter_reg_fields[].id`** — each ID must be unique
3. **No duplicate `voter_reg_fields[].csv_column_name`** — each CSV column mapped once
4. **`field_mappings[].ballot_field_id` must reference a valid ballot field**
5. **Template placeholders must reference valid voter reg field IDs**
6. **Every matchable ballot field must have a field mapping**
7. **Every hash field must reference a valid voter reg field ID**
8. **At least one matchable field must exist** (required_for_matching=true AND match_weight > 0)
9. **`crop_config.top_crop` must be less than `crop_config.bottom_crop`**

## Minimal Valid Spec

```json5
{
  region_name: "Example Region",
  country_code: "US",
  ballot_fields: [
    {
      id: "name",
      label: "Name",
      field_type: "text",
      required_for_matching: true,
      match_weight: 1.0,
    },
  ],
  voter_reg_fields: [
    {
      id: "full_name",
      csv_column_name: "FullName",
      data_type: "text",
      category: "name",
    },
  ],
  field_mappings: [
    { ballot_field_id: "name", template: "{full_name}" },
  ],
  hash_fields: ["full_name"],
  crop_config: {
    top_crop: 0.3,
    bottom_crop: 0.7,
    base_threshold: 85,
  },
}
```

## Region Key Convention

- **Filename:** lowercase (e.g., `dc.json5`, `md.json5`)
- **Database `region_key`:** uppercase, derived from filename stem (e.g., `"DC"`, `"MD"`)
- **Startup loading:** `spec_file.stem.upper()` → `region_key`
