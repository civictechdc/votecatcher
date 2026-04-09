"""BDD tests for API serialization contract.

All API-facing models must serialize snake_case fields to camelCase JSON
and accept both formats on deserialization.
"""

import pytest

from app.api_models import ApiModel


class TestApiModelSerializationContract:
    """ApiModel must convert snake_case to camelCase in JSON output."""

    def test_single_word_field_is_unchanged(self):
        class Subject(ApiModel):
            name: str

        assert Subject(name="x").model_dump(by_alias=True) == {"name": "x"}

    def test_two_word_field_becomes_camel_case(self):
        class Subject(ApiModel):
            campaign_id: str

        dumped = Subject(campaign_id="abc").model_dump(by_alias=True)
        assert dumped == {"campaignId": "abc"}

    def test_three_word_field_becomes_camel_case(self):
        class Subject(ApiModel):
            provider_model_name: str

        dumped = Subject(provider_model_name="gpt-4").model_dump(by_alias=True)
        assert dumped == {"providerModelName": "gpt-4"}


class TestApiModelDeserializationContract:
    """ApiModel must accept both camelCase and snake_case on input."""

    def test_accepts_camel_case_input(self):
        class Subject(ApiModel):
            campaign_id: str

        result = Subject.model_validate({"campaignId": "abc"})
        assert result.campaign_id == "abc"

    def test_accepts_snake_case_input(self):
        class Subject(ApiModel):
            campaign_id: str

        result = Subject.model_validate({"campaign_id": "abc"})
        assert result.campaign_id == "abc"


class TestSchemasUseApiModel:
    """All models in schemas.py with multi-word fields must use ApiModel."""

    @pytest.fixture(autouse=True)
    def _import_schemas(self):
        from app import schemas

        self.module = schemas

    def test_workspace_response_serializes_to_camel_case(self):
        from uuid import uuid4

        ws = self.module.WorkspaceResponse(
            id=str(uuid4()),
            campaign_id=str(uuid4()),
            campaign_name="Test Campaign",
        )
        dumped = ws.model_dump(by_alias=True)
        assert "campaignId" in dumped
        assert "campaignName" in dumped

    def test_session_token_response_serializes_to_camel_case(self):
        token = self.module.SessionTokenResponse(
            access_token="at",
            token_type="bearer",
            refresh_token="rt",
            expires_in=3600,
            expires_at=None,
        )
        dumped = token.model_dump(by_alias=True)
        assert "accessToken" in dumped
        assert "tokenType" in dumped
        assert "refreshToken" in dumped
        assert "expiresIn" in dumped

    def test_match_fields_response_serializes_to_camel_case(self):
        mf = self.module.MatchFieldsResponse(id="1", field_names=["a", "b"])
        dumped = mf.model_dump(by_alias=True)
        assert "fieldNames" in dumped

    def test_ocr_provider_payload_serializes_to_camel_case(self):
        payload = self.module.OcrProviderPayload(
            provider_name="openai",
            provider_model="gpt-4",
            api_key="sk-test",  # pragma: allowlist secret
        )
        dumped = payload.model_dump(by_alias=True)
        assert "providerName" in dumped
        assert "providerModel" in dumped
        assert "apiKey" in dumped

    def test_voter_records_upload_response_uses_api_model(self):
        resp = self.module.VoterRecordsUploadResponse(
            file_name="voters.csv", message="ok"
        )
        dumped = resp.model_dump(by_alias=True)
        assert "fileName" in dumped

    def test_petition_file_upload_response_uses_api_model(self):
        resp = self.module.PetitionFileUploadResponse(
            file_name="petitions.pdf", message="ok"
        )
        dumped = resp.model_dump(by_alias=True)
        assert "fileName" in dumped


class TestCreateCampaignRequestUsesApiModel:
    """CreateCampaignRequest must use ApiModel for consistency."""

    def test_accepts_snake_case_input(self):
        from app.routers.campaign_router import CreateCampaignRequest

        req = CreateCampaignRequest.model_validate(
            {
                "name": "Test",
                "year": 2025,
                "region": "DC",
            }
        )
        assert req.name == "Test"

    def test_inherits_from_api_model(self):
        from app.routers.campaign_router import CreateCampaignRequest

        assert issubclass(CreateCampaignRequest, ApiModel)
