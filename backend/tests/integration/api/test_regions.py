"""Integration tests for regions API endpoints (G9).

Tests:
- GET /regions — list available regions
- POST /campaigns with region_key — creates campaign with specified region
"""

from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.data.database.model.schema import Region
from app.settings.providers.features._base import FeatureFlag, FlagMeta, FlagPhase
from app.settings.providers.features.fieldspec import FieldSpecFlags


def _make_settings_with_api_enabled():
    flags = FieldSpecFlags(
        api=FeatureFlag(
            enabled=True,
            meta=FlagMeta(
                lifecycle="transitional",
                issue=12,
                description="G9 test",
                phase=FlagPhase.ACTIVATED,
            ),
        )
    )
    return type(
        "MockSettings",
        (),
        {"features": type("MockFeatures", (), {"fieldspec": flags})()},
    )()


class TestListRegions:
    def test_list_regions_returns_empty_when_no_specs(self, client: TestClient):
        with patch(
            "app.routers.region_router.get_settings",
            return_value=_make_settings_with_api_enabled(),
        ):
            response = client.get("/api/regions")
        assert response.status_code == 200
        data = response.json()
        assert "regions" in data
        assert isinstance(data["regions"], list)

    def test_list_regions_returns_dc_when_spec_loaded(
        self, client: TestClient, session: Session
    ):
        from app.data.database.model.region_field_spec import RegionFieldSpecModel

        region = Region(
            region_key="DC",
            region_name="District of Columbia",
            country_code="US",
        )
        session.add(region)
        session.commit()
        session.refresh(region)

        spec = RegionFieldSpecModel(
            region_id=region.id,
            region_key="DC",
            name="DC Default",
            ballot_fields=[],
            voter_reg_fields=[],
            field_mappings=[],
            hash_fields=[],
            crop_config={"top_crop": 0.0, "bottom_crop": 0.0, "base_threshold": 0.5},
        )
        session.add(spec)
        session.commit()

        with patch(
            "app.routers.region_router.get_settings",
            return_value=_make_settings_with_api_enabled(),
        ):
            response = client.get("/api/regions")

        assert response.status_code == 200
        data = response.json()
        assert len(data["regions"]) >= 1
        dc = next((r for r in data["regions"] if r["key"] == "DC"), None)
        assert dc is not None
        assert dc["name"] == "District of Columbia"
        assert dc["id"] is not None


class TestCreateCampaignWithRegion:
    def test_create_campaign_with_region_key(
        self, client: TestClient, session: Session
    ):
        region = Region(
            region_key="DC",
            region_name="District of Columbia",
            country_code="US",
        )
        session.add(region)
        session.commit()

        response = client.post(
            "/api/campaigns",
            json={
                "name": "Test Campaign",
                "year": 2024,
                "region": "DC",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["region"] == "DC"
        assert data["regionId"] is not None

    def test_create_campaign_with_nonexistent_region_raises(self, client: TestClient):
        response = client.post(
            "/api/campaigns",
            json={
                "name": "Test Campaign",
                "year": 2024,
                "region": "XX",
            },
        )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    def test_create_campaign_defaults_to_dc(self, client: TestClient, session: Session):
        response = client.post(
            "/api/campaigns",
            json={
                "name": "Default Campaign",
                "year": 2024,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["region"] == "DC"
