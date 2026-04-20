<!-- Project-Specific Rules -->
<!-- Add rules specific to your project here. Examples: -->
<!-- - Don't modify the /v1/ API endpoints without approval -->
<!-- - Always update CHANGELOG.md when adding features -->
<!-- - Database migrations must be backward-compatible -->

## Branching & PR Discipline

Non-trivial changes (features, refactors, multi-file fixes, epics) MUST use a **feature branch + PR**. Do not push directly to `main`.

**Trivial exceptions** (direct to `main` OK): CI config fixes, typo corrections, version bumps, documentation-only changes that don't affect behavior.

Rationale: Direct pushes to `main` bypass CI as a gate, skip code review, and make rollback harder. Branch protection is enabled — enforce it in practice too.

## Debugging OCR → Matching Pipeline

The matching pipeline has live data from job #3 (campaign `c870000c-2382-4dcc-823c-8a678f5c6b9b`) preserved in SQLite. Use this to debug matching without re-running OCR.

### Current Data State

- **50 OcrResult rows** (from batch `batch_69de93cfefc8190b4f3b32fcf9ec36d`)
- **250 MatchResult rows** (5 matches per OCR result, top-N)
- **100K RegisteredVoter rows**
- **10 PetitionCrop rows** (from petition `fake_signed_petitions_1-10.pdf`)
- **Known bug**: All address scores are 0.0 because voter data uses flat `street` field, not structured `street_number`/`street_name`/`street_type`

### Quick Sanity Checks

```bash
cd backend

# Count data
uv run python3 -c "
from sqlmodel import Session, select, func
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.match_result import MatchResult
from app.data.database.model.registered_voter import RegisteredVoter
from app.persistence.session import get_engine
engine = get_engine().raw_engine
with Session(engine) as s:
    print(f'OCR results: {s.exec(select(func.count()).select_from(OcrResult)).one()}')
    print(f'Match results: {s.exec(select(func.count()).select_from(MatchResult)).one()}')
    print(f'Voters: {s.exec(select(func.count()).select_from(RegisteredVoter)).one()}')
"

# Check address score distribution (currently all 0.0)
uv run python3 -c "
from sqlmodel import Session, select
from app.data.database.model.match_result import MatchResult
from app.persistence.session import get_engine
engine = get_engine().raw_engine
with Session(engine) as s:
    for mr in s.exec(select(MatchResult).where(MatchResult.rank == 1).limit(3)).all():
        print(f'voter={mr.voter_id} score={mr.similarity_score:.3f} fields={mr.field_scores}')
"
```

### Trace a Single Match (End-to-End)

```bash
cd backend
uv run python3 -c "
from sqlmodel import Session, select
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.jobs import OcrJob
from app.data.database.model.match_result import MatchResult
from app.data.database.model.registered_voter import RegisteredVoter
from app.domain.field_spec import render_template
from app.matching.voter_data_adapter import flatten_voter_data
from app.dependencies import get_field_spec_service
from app.persistence.session import get_engine

engine = get_engine().raw_engine
with Session(engine) as s:
    # 1. Pick an OCR result
    ocr_job = s.exec(select(OcrJob).where(OcrJob.matcher_job_id == 3)).first()
    ocr = s.exec(select(OcrResult).where(OcrResult.ocr_job_id == ocr_job.id).limit(1)).first()
    print(f'OCR extracted: {ocr.extracted_text}')

    # 2. Get top match
    mr = s.exec(select(MatchResult).where(
        MatchResult.ocr_result_id == ocr.id, MatchResult.rank == 1
    )).first()
    print(f'Top match: score={mr.similarity_score} confidence={mr.confidence_level}')
    print(f'Field scores: {mr.field_scores}')

    # 3. Check the matched voter
    voter = s.get(RegisteredVoter, mr.voter_id)
    print(f'Voter name_data: {voter.name_data}')
    print(f'Voter address_data: {voter.address_data}')

    # 4. Trace what the template renders
    spec = next(get_field_spec_service()).get_spec_by_key('DC')
    flat = flatten_voter_data(voter, spec.voter_reg_fields)
    mapping = spec.get_mapping_for('address')
    rendered = render_template(mapping.template, flat)
    print(f'Address template: {mapping.template}')
    print(f'Rendered: \"{rendered}\"')
    print(f'OCR address: \"{ocr.extracted_text.get(\"address\", \"\")}\"')
    print(f'Match? {rendered == ocr.extracted_text.get(\"address\", \"\")}')
"
```

### Re-Run Matching (Without OCR)

```bash
cd backend
# Fast: first N results only
timeout 30 uv run python3 -c "
from sqlmodel import Session, select
from app.data.database.model.schema import Campaign
from app.data.database.model.jobs import OcrJob, MatcherJob, JobStatus
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.match_result import MatchResult
from app.dependencies import get_field_spec_service
from app.matching.matching_service import MatchingService
from app.persistence.session import get_engine
import json

engine = get_engine().raw_engine
with Session(engine) as s:
    ocr_job = s.exec(select(OcrJob).where(OcrJob.matcher_job_id == 3)).first()
    ocr_results = s.exec(select(OcrResult).where(OcrResult.ocr_job_id == ocr_job.id).limit(5)).all()
    campaign = s.get(Campaign, 'c870000c-2382-4dcc-823c-8a678f5c6b9b')
    spec = next(get_field_spec_service()).get_spec_by_key('DC')
    ms = MatchingService(session=s)
    for idx, ocr in enumerate(ocr_results, 1):
        matches = ms.match_ocr_result_with_spec(spec=spec, ocr_text=ocr.extracted_text, region_id=campaign.region_id, top_n=5)
        top = matches[0] if matches else None
        print(f'{idx}. OCR={ocr.extracted_text}  top_score={top[\"similarity_score\"]:.3f}  fields={top[\"field_scores\"]}')
"
```

### Known Gotchas

1. **Campaign model**: Fields are `unique_name`/`title` (not `name`). Region key is on `campaign.region_id`.
2. **Voter model**: Data is nested in JSON columns (`name_data`, `address_data`, `other_field_data`), not flat fields.
3. **FK crash**: Standalone scripts that commit `MatcherJob` status changes hit `NoReferencedTableError` for `users` table. Use `engine.raw_engine` and intermediate commits to avoid.
4. **Address scoring**: Currently broken — voter CSV imports don't parse into structured columns (`street_number`, `street_name`, etc.). Template renders `""`. Fix needed.
5. **Performance**: ~0.2 results/sec against 100K voters. Full run of 50 results takes ~4 min.

### OpenAI Batch API Inspection

```bash
cd backend
# List recent batches
uv run python3 -c "
from sqlmodel import Session, select
from app.data.database.model.llm_provider_config import LlmProviderConfig
from app.persistence.session import get_engine
from openai import AsyncOpenAI
import asyncio

async def check():
    engine = get_engine().raw_engine
    with Session(engine) as s:
        config = s.exec(select(LlmProviderConfig).where(LlmProviderConfig.provider == 'openai')).first()
    client = AsyncOpenAI(api_key=config.api_key, base_url='https://oai.helicone.ai/v1')
    batches = await client.batches.list(limit=5)
    async for b in batches:
        print(f'{b.id} status={b.status} completed={b.request_counts.completed}/{b.request_counts.total} meta={b.metadata}')

asyncio.run(check())
"
```
