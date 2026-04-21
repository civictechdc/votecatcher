from fastapi.testclient import TestClient

from app.data.database.model.schema import Campaign


class TestSQLInjection:
    """Tests for SQL injection protection."""

    def test_campaign_id_rejects_non_uuid(self, client: TestClient):
        """Should reject non-UUID campaign ID."""
        response = client.get("/api/campaigns/not-a-uuid")

        assert response.status_code == 422

    def test_campaign_id_rejects_sql_injection(self, client: TestClient):
        """Should reject SQL injection attempt in campaign ID."""
        response = client.get("/api/campaigns/1' OR '1'='1")

        assert response.status_code == 422

    def test_campaign_delete_rejects_sql_injection(self, client: TestClient):
        """Should reject SQL injection attempt in delete."""
        response = client.delete("/api/campaigns/DROP TABLE")

        assert response.status_code == 422

    def test_campaign_results_safe_with_special_chars(
        self, client: TestClient, test_campaign: Campaign
    ):
        """Should reject invalid confidence values (typed enum rejects injection strings)."""
        response = client.get(
            f"/api/campaigns/{test_campaign.id}/results?confidence=HIGH' OR '1'='1"
        )

        assert response.status_code == 422

    def test_list_campaigns_with_negative_offset(self, client: TestClient):
        """Should handle negative offset gracefully."""
        response = client.get("/api/campaigns?offset=-1")

        assert response.status_code == 200

    def test_list_campaigns_with_huge_limit(self, client: TestClient):
        """Should handle huge limit gracefully."""
        response = client.get("/api/campaigns?limit=999999999")

        assert response.status_code == 200
