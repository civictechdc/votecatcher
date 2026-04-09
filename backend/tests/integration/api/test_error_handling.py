"""Tests for error handling and CORS headers on error responses."""

from fastapi.testclient import TestClient


class TestErrorHandlingCORS:
    """Tests for CORS headers on error responses."""

    def test_404_error_includes_cors_headers(self, client: TestClient):
        """Should include CORS headers on 404 errors."""
        response = client.get(
            "/api/campaigns/00000000-0000-0000-0000-000000000000",
            headers={"Origin": "http://localhost"},
        )

        assert response.status_code == 404
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] in [
            "http://localhost",
            "http://localhost:5173",
            "*",
        ]

    def test_422_validation_error_includes_cors_headers(self, client: TestClient):
        """Should include CORS headers on validation errors."""
        response = client.post(
            "/api/campaigns", json={}, headers={"Origin": "http://localhost"}
        )

        assert response.status_code == 422
        assert "access-control-allow-origin" in response.headers

    def test_error_response_format(self, client: TestClient):
        """Should return user-friendly error format."""
        from uuid import uuid4

        fake_id = uuid4()
        response = client.get(f"/api/campaigns/{fake_id}/metrics")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
