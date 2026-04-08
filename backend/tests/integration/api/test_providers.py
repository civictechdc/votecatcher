"""Integration tests for provider settings endpoints."""


class TestListProviders:
    def test_list_providers_returns_all_supported(self, client, session):
        response = client.get("/api/settings/providers")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        provider_names = [p["provider"] for p in data]
        assert "openai" in provider_names
        assert "gemini" in provider_names
        assert "mistral" in provider_names

    def test_list_providers_shows_unconfigured_state(self, client, session):
        response = client.get("/api/settings/providers")
        data = response.json()
        for provider in data:
            assert provider["is_configured"] is False
            assert provider["last_validated"] is None


class TestConfigureProvider:
    def test_configure_provider_success(self, client, session):
        response = client.post(
            "/api/settings/providers/openai",
            json={"api_key": "sk-test-key", "model": "gpt-4o"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "openai"
        assert data["model"] == "gpt-4o"
        assert data["is_configured"] is True

    def test_configure_unsupported_provider_fails(self, client):
        response = client.post(
            "/api/settings/providers/unknown",
            json={"api_key": "test-key", "model": "test-model"},
        )
        assert response.status_code == 400

    def test_configure_provider_updates_existing(self, client, session):
        client.post(
            "/api/settings/providers/openai",
            json={"api_key": "sk-first", "model": "gpt-4o"},
        )
        response = client.post(
            "/api/settings/providers/openai",
            json={"api_key": "sk-second", "model": "gpt-4o-mini"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "gpt-4o-mini"

    def test_list_providers_shows_configured(self, client, session):
        client.post(
            "/api/settings/providers/gemini",
            json={"api_key": "gemini-key", "model": "gemini-1.5-pro"},
        )
        response = client.get("/api/settings/providers")
        data = response.json()
        gemini = next(p for p in data if p["provider"] == "gemini")
        assert gemini["is_configured"] is True
        assert gemini["model"] == "gemini-1.5-pro"


class TestDeleteProvider:
    def test_delete_provider_success(self, client, session):
        client.post(
            "/api/settings/providers/openai",
            json={"api_key": "sk-test", "model": "gpt-4o"},
        )
        response = client.delete("/api/settings/providers/openai")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        response = client.get("/api/settings/providers")
        data = response.json()
        openai = next(p for p in data if p["provider"] == "openai")
        assert openai["is_configured"] is False

    def test_delete_nonexistent_provider(self, client):
        response = client.delete("/api/settings/providers/openai")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False


class TestTestProvider:
    def test_test_provider_invalid_key(self, client):
        response = client.post(
            "/api/settings/providers/openai/test",
            json={"api_key": "invalid-key", "model": "gpt-4o"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["error"] is not None

    def test_test_unsupported_provider(self, client):
        response = client.post(
            "/api/settings/providers/unknown/test",
            json={"api_key": "test-key", "model": "test-model"},
        )
        assert response.status_code == 400
