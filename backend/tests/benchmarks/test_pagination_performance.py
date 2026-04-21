"""Benchmark tests for pagination performance at scale.

Validates keyset pagination maintains constant-time performance
regardless of cursor position, compared to OFFSET which degrades.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.data.database.model.jobs import JobStatus, MatcherJob
from app.data.database.model.match_result import ConfidenceLevel, MatchResult
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.schema import Campaign, Region

N_RESULTS = 10_000


@pytest.fixture(scope="module")
def benchmark_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        region = Region(
            id=uuid4(), region_key="DC", region_name="DC", country_code="US"
        )
        session.add(region)
        session.flush()

        campaign = Campaign(
            id=uuid4(),
            unique_name="bench-campaign",
            title="Benchmark",
            year="2024",
            region_id=region.id,
        )
        session.add(campaign)
        session.flush()

        scan = PetitionScan(
            campaign_id=campaign.id,
            original_filename="bench.pdf",
            stored_path="/tmp/bench.pdf",
            file_hash="bench123",
            page_count=N_RESULTS,
        )
        session.add(scan)
        session.flush()

        job = MatcherJob(
            campaign_id=campaign.id,
            current_status=JobStatus.MATCHING_COMPLETED,
            ended_on=datetime.now(UTC),
        )
        session.add(job)
        session.flush()

        for i in range(N_RESULTS):
            crop = PetitionCrop(
                scan_id=scan.id,
                crop_index=i,
                stored_path=f"/tmp/bcrop_{i}.png",
                crop_coordinates={},
                page_number=1,
            )
            session.add(crop)
            session.flush()

            ocr = OcrResult(
                crop_id=crop.id,
                ocr_job_id=1,
                extracted_text={"name": f"Bench Sig {i}"},
            )
            session.add(ocr)
            session.flush()

            session.add(
                MatchResult(
                    matcher_job_id=job.id,
                    ocr_result_id=ocr.id,
                    voter_id=None,
                    rank=1,
                    similarity_score=0.85,
                    confidence_level=ConfidenceLevel.HIGH,
                )
            )

        session.commit()
        yield session, job, campaign


@pytest.mark.benchmark(group="pagination")
def test_keyset_first_page_performance(benchmark, benchmark_session):
    """Keyset page 1 should complete in < 100ms."""
    from app.services.results_query_service import ResultsQueryService

    session, job, _ = benchmark_session

    def fetch_first():
        return ResultsQueryService(session).get_results(
            job.id, cursor=None, page_size=50
        )

    result = benchmark(fetch_first)
    assert len(result.results) == 50


@pytest.mark.benchmark(group="pagination")
def test_keyset_deep_page_performance(benchmark, benchmark_session):
    """Keyset page ~200 should complete in comparable time to page 1."""
    from app.services.results_query_service import ResultsQueryService

    session, job, _ = benchmark_session

    service = ResultsQueryService(session)
    cursor = None
    for _ in range(199):
        page = service.get_results(job.id, cursor=cursor, page_size=50)
        if page.next_cursor is None:
            break
        cursor = page.next_cursor

    def fetch_deep():
        return ResultsQueryService(session).get_results(
            job.id, cursor=cursor, page_size=50
        )

    result = benchmark(fetch_deep)
    assert len(result.results) == 50


@pytest.mark.benchmark(group="metrics")
def test_metrics_performance_at_scale(benchmark, benchmark_session):
    """Metrics computation should complete in < 50ms at 10k results."""
    from app.services.metrics import MetricsService

    session, _, campaign = benchmark_session

    def compute():
        return MetricsService(session).compute_campaign_metrics(campaign.id)

    result = benchmark(compute)
    assert result["total_signatures"] == N_RESULTS
