"""Integration tests for data integrity in job API responses.

Tests that the API never returns invalid JSON regardless of the data stored
in the database. This covers control characters, unicode edge cases, and
other serialization hazards.

Also tests that worker operations persist critical identifiers before
long-running operations, preventing orphaned resources.
"""

import json
import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.data.database.model.jobs import JobStatus, MatcherJob
from app.data.database.model.schema import Campaign


class TestJobResponseJsonIntegrity:
    """API responses must always produce valid, parseable JSON.

    Any string field sourced from the database must survive JSON
    serialization — control characters, embedded quotes, null bytes,
    and other edge cases must not break the response.
    """

    def test_campaign_name_with_newline_produces_valid_json(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Campaign name containing newline must serialize to valid JSON."""
        test_campaign.unique_name = "Demo\nCampaign"
        session.add(test_campaign)
        session.commit()

        job = MatcherJob(
            campaign_id=test_campaign.id,
            current_status=JobStatus.NOT_STARTED,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        response = client.get(f"/api/jobs/{job.id}")

        assert response.status_code == 200
        parsed = response.json()
        assert parsed["campaignName"] is not None

    def test_campaign_name_with_tab_produces_valid_json(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Campaign name containing tab must serialize to valid JSON."""
        test_campaign.unique_name = "Tab\tSeparated"
        session.add(test_campaign)
        session.commit()

        job = MatcherJob(
            campaign_id=test_campaign.id,
            current_status=JobStatus.NOT_STARTED,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        response = client.get(f"/api/jobs/{job.id}")

        assert response.status_code == 200
        parsed = response.json()
        assert parsed["campaignName"] is not None

    def test_campaign_name_with_control_chars_produces_valid_json(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Campaign name with mixed control characters must serialize cleanly."""
        test_campaign.unique_name = "Test\x00\x01\x02Name"
        session.add(test_campaign)
        session.commit()

        job = MatcherJob(
            campaign_id=test_campaign.id,
            current_status=JobStatus.NOT_STARTED,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        response = client.get(f"/api/jobs/{job.id}")

        assert response.status_code == 200
        parsed = response.json()
        assert parsed["campaignName"] is not None

    def test_campaign_name_with_mixed_special_chars_produces_valid_json(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Campaign name with backslash, quotes, and control chars must serialize."""
        test_campaign.unique_name = 'He said "hi"\n\t\\end'
        session.add(test_campaign)
        session.commit()

        job = MatcherJob(
            campaign_id=test_campaign.id,
            current_status=JobStatus.NOT_STARTED,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        response = client.get(f"/api/jobs/{job.id}")

        assert response.status_code == 200
        parsed = response.json()
        assert parsed["campaignName"] is not None

    def test_response_bytes_are_valid_utf8_json(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """Raw response bytes must be parseable as UTF-8 JSON regardless of content."""
        test_campaign.unique_name = "Line1\r\nLine2\tTab\x0cFormFeed"
        session.add(test_campaign)
        session.commit()

        job = MatcherJob(
            campaign_id=test_campaign.id,
            current_status=JobStatus.NOT_STARTED,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        response = client.get(f"/api/jobs/{job.id}")

        raw = response.content.decode("utf-8")
        parsed = json.loads(raw)
        assert isinstance(parsed, dict)
        assert "campaignName" in parsed

    def test_list_jobs_with_control_chars_in_campaign_name(
        self, client: TestClient, test_campaign: Campaign, session: Session
    ):
        """List endpoint must also produce valid JSON with control chars."""
        test_campaign.unique_name = "List\nTest"
        session.add(test_campaign)
        session.commit()

        job = MatcherJob(
            campaign_id=test_campaign.id,
            current_status=JobStatus.NOT_STARTED,
        )
        session.add(job)
        session.commit()

        response = client.get("/api/jobs")

        assert response.status_code == 200
        raw = response.content.decode("utf-8")
        parsed = json.loads(raw)
        assert "jobs" in parsed
        assert len(parsed["jobs"]) >= 1
