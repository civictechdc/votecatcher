from fastapi.testclient import TestClient


class TestInputFuzzing:
    """Tests for input validation and fuzzing."""

    def test_create_campaign_rejects_empty_name(self, client: TestClient):
        """Should reject campaign creation with empty name."""
        response = client.post("/api/campaigns", json={"name": "", "year": 2024})

        assert response.status_code == 422

    def test_create_campaign_rejects_xss_name(self, client: TestClient):
        """Should reject XSS attempt in campaign name."""
        response = client.post(
            "/api/campaigns", json={"name": "<script>alert(1)</script>", "year": 2024}
        )

        assert response.status_code == 422

    def test_create_campaign_rejects_very_long_name(self, client: TestClient):
        """Should reject campaign with extremely long name."""
        long_name = "x" * 10001
        response = client.post("/api/campaigns", json={"name": long_name, "year": 2024})

        assert response.status_code == 422

    def test_create_campaign_rejects_sql_injection_name(self, client: TestClient):
        """Should reject SQL injection attempt in campaign name."""
        response = client.post(
            "/api/campaigns", json={"name": "'; DROP TABLE campaigns; --", "year": 2024}
        )

        assert response.status_code == 422

    def test_create_campaign_rejects_invalid_year(self, client: TestClient):
        """Should reject campaign creation with non-integer year."""
        response = client.post(
            "/api/campaigns", json={"name": "Test", "year": "twenty-twenty"}
        )

        assert response.status_code == 422

    def test_campaign_endpoint_rejects_put_method(self, client: TestClient):
        """Should reject PUT method on campaigns list endpoint."""
        response = client.put("/api/campaigns", json={"name": "Test", "year": 2024})

        assert response.status_code == 405

    def test_campaign_endpoint_rejects_patch_method(self, client: TestClient):
        """Should reject PATCH method on campaigns list endpoint."""
        response = client.patch("/api/campaigns", json={"name": "Test"})

        assert response.status_code == 405
