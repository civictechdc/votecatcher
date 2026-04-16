# Results System Performance

Reference guide for the match results query pipeline at production scale (10k+ petition signatures).

## Scale Model

| Entity | Per 10k petitions | Per 50k petitions |
|---|---|---|
| `petition_crops` | 10,000 | 50,000 |
| `ocr_results` (5 per crop) | 50,000 | 250,000 |
| `match_results` (5 per OCR) | 250,000 | 1,250,000 |
| `registered_voters` | 100,000+ | 500,000+ |

## Query Architecture

### Pagination

Results pages use SQL-level pagination, not in-memory filtering:

```python
# Count — single SQL statement
total = session.exec(
    select(func.count())
    .select_from(MatchResult)
    .where(MatchResult.matcher_job_id == job_id)
).one()

# Page — subquery for page's OCR IDs, then fetch only those rows
page_ocr_ids = session.exec(
    select(func.distinct(MatchResult.ocr_result_id))
    .where(MatchResult.matcher_job_id == job_id)
    .order_by(MatchResult.ocr_result_id)
    .offset(offset)
    .limit(page_size)
).all()

page_results = session.exec(
    select(MatchResult)
    .where(
        MatchResult.matcher_job_id == job_id,
        MatchResult.ocr_result_id.in_(page_ocr_ids),
    )
).all()
```

Memory per request: O(page_size × 5), never O(total_results).

### Metrics Aggregation

Confidence breakdowns use SQL `GROUP BY`, not Python-side counting:

```python
counts = session.exec(
    select(MatchResult.confidence_level, func.count())
    .where(MatchResult.matcher_job_id == job_id, MatchResult.rank == 1)
    .group_by(MatchResult.confidence_level)
).all()
```

### CSV Export

Exports stream rows in chunks via SQLAlchemy `yield_per()`, never loading all results into memory at once.

## Required Indexes

| Table | Column | Why |
|---|---|---|
| `match_results` | `matcher_job_id` | Primary filter for all result queries |
| `match_results` | `ocr_result_id` | JOIN target for OCR text resolution |
| `ocr_results` | `crop_id` | JOIN target for crop thumbnail resolution |

These are not auto-created by SQLModel FK declarations. Must be set explicitly with `index=True`.

## Crop Image Serving

### Endpoint

`GET /api/crops/{crop_id}/image` — serves PNG from `PetitionCrop.stored_path`.

### Cache Headers

```
Cache-Control: public, max-age=86400, immutable
```

Crop images never change once created. Browser/proxy caches indefinitely.

### Storage Backends

| Backend | Implementation | Use Case |
|---|---|---|
| `LocalFileAdapter` | `FileResponse` from filesystem | Development / SQLite |
| `SupabaseStorageAdapter` | CDN URL with `?width=` transforms | Production / Postgres |

Supabase Storage provides built-in image transforms — no need to generate separate thumbnail files. Use `?width=60&height=40` for table thumbnails, full size for lightbox.

### Concurrency

Image endpoint uses `asyncio.Semaphore(50)` to prevent file handle exhaustion under load.

## Frontend

### Thumbnail Loading

```svelte
<img src={result.thumbnailUrl} loading="lazy" width="60" height="40" />
```

- `loading="lazy"` — browser defers off-screen images, only decodes visible thumbnails (~10-15)
- `Cache-Control: immutable` — subsequent page visits load from disk cache, zero backend hit
- Store replaces results on each page fetch — no accumulation across pages

### Accordion Expand

One row expanded at a time via `{#if}` block. Svelte destroys old expanded row DOM when collapsed. No DOM leak.

### Client-Side Sort

Phase 1: sort current page data client-side (50 rows — trivial). Phase 2: server-side sort via `sort_by`/`sort_order` query params for cross-page consistency.

## Connection Pooling (Supabase)

```python
create_engine(url, pool_recycle=300, pool_pre_ping=True)
```

- `pool_recycle=300` — recycle connections after 5 minutes (Supabase idle limits)
- `pool_pre_ping=True` — verify connection liveness before use

## Benchmark

Run pagination benchmarks:

```bash
cd backend
uv run pytest tests/benchmarks/ -v --benchmark-only
```

Expected: page request < 100ms with 10k results on SQLite.

## Related

- [Architecture](../architecture/README.md) — C4 diagrams, ADRs
- [Testing Guide](./testing.md) — approval tests, patterns
- [Matching Algorithm](./matching-algorithm.md) — scoring formula
