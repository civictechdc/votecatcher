"""Tests for metrics service query optimization.

RED phase: Tests assert that _count_total_signatures uses exactly 1 SQL query
and _count_processed_results uses exactly 1 SQL query.
"""

from datetime import UTC, datetime

from sqlmodel import Session

from app.data.database.model.jobs import JobStatus, MatcherJob
from app.data.database.model.match_result import ConfidenceLevel, MatchResult
from app.data.database.model.ocr_result import OcrResult
from app.data.database.model.petition_crop import PetitionCrop
from app.data.database.model.petition_scan import PetitionScan
from app.data.database.model.schema import Campaign, Region


def _seed_campaign_with_data(session: Session, n_ocr: int = 10):
    region = Region(
        region_key="DC", region_name="Washington, DC", country_code="US"
    )
    session.add(region)
    session.flush()

    campaign = Campaign(
        unique_name=f"metrics-opt-{n_ocr}",
        title="Metrics Opt Test",
        year="2024",
        region_id=region.id,
    )
    session.add(campaign)
    session.flush()

    scan = PetitionScan(
        campaign_id=campaign.id,
        original_filename="test.pdf",
        stored_path="/tmp/test.pdf",
        file_hash="abc123",
        page_count=1,
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

    for i in range(n_ocr):
        crop = PetitionCrop(
            scan_id=scan.id,
            crop_index=i,
            stored_path=f"/tmp/crop_{i}.png",
            crop_coordinates={},
            page_number=1,
        )
        session.add(crop)
        session.flush()

        ocr = OcrResult(
            crop_id=crop.id,
            ocr_job_id=1,
            extracted_text={"name": f"Name {i}"},
        )
        session.add(ocr)
        session.flush()

        level = [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW][
            i % 3
        ]
        session.add(
            MatchResult(
                ocr_result_id=ocr.id,
                matcher_job_id=job.id,
                rank=1,
                similarity_score=0.9,
                confidence_level=level,
            )
        )
    session.commit()

    return region, campaign, job


class TestMetricsQueryOptimization:
    """Feature: Metrics queries use JOINs instead of sequential round-trips.

    _count_total_signatures must execute exactly 1 SQL statement.
    _count_processed_results must execute exactly 1 SQL statement.
    """

    def test_count_total_signatures_single_query(self, session):
        """Scenario: _count_total_signatures fires exactly 1 SQL query."""
        from unittest.mock import patch

        from app.services.metrics import MetricsService

        region, campaign, job = _seed_campaign_with_data(session, 10)

        service = MetricsService(session)
        original_exec = session.exec
        call_count = 0

        def counting_exec(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return original_exec(*args, **kwargs)

        with patch.object(type(session), "exec", side_effect=counting_exec):
            count = service._count_total_signatures(campaign.id)

        assert count == 10
        assert call_count == 1, (
            f"_count_total_signatures must use exactly 1 query, got {call_count}"
        )

    def test_count_processed_results_single_query(self, session):
        """Scenario: _count_processed_results fires exactly 1 SQL query."""
        from unittest.mock import patch

        from app.services.metrics import MetricsService

        region, campaign, job = _seed_campaign_with_data(session, 10)

        service = MetricsService(session)
        original_exec = session.exec
        call_count = 0

        def counting_exec(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return original_exec(*args, **kwargs)

        with patch.object(type(session), "exec", side_effect=counting_exec):
            processed, confidence_counts = service._count_processed_results(
                campaign.id
            )

        assert processed == 10
        assert call_count == 1, (
            f"_count_processed_results must use exactly 1 query, got {call_count}"
        )

    def test_total_signatures_matches_current_behavior(self, session):
        """Scenario: Optimized query returns same result as current implementation."""
        from app.services.metrics import MetricsService

        region, campaign, job = _seed_campaign_with_data(session, 15)

        service = MetricsService(session)
        count = service._count_total_signatures(campaign.id)

        assert count == 15
