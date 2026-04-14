"""Integration tests for regions API endpoints (G9).

Tests:
- GET /regions — list available regions
- POST /campaigns with region_key — creates campaign with specified region
"""

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.data.database.model.schema import Region


class TestListRegions:
    def test_list_regions_returns_empty_when_no_specs(self, client: TestClient):
        response = client.get("/api/regions")
        assert response.status_code == 200
        data = response.json()
        assert "regions" in data
        assert isinstance(data["regions"], list)

    def test_list_regions_returns_dc_when_spec_loaded(
        self, client: TestClient, session: Session
    ):
        from app.data.database.model.region_field_spec import RegionFieldSpecModel

        dc_region = session.exec(
            select(Region).where(Region.region_key == "DC")
        ).first()
        if dc_region is None:
            dc_region = Region(
                region_key="DC",
                region_name="District of Columbia",
                country_code="US",
            )
            session.add(dc_region)
            session.commit()
            session.refresh(dc_region)

        existing_spec = session.exec(
            select(RegionFieldSpecModel).where(RegionFieldSpecModel.region_key == "DC")
        ).first()
        if existing_spec is None:
            spec = RegionFieldSpecModel(
                region_id=dc_region.id,
                region_key="DC",
                name="DC Default",
                ballot_fields=[],
                voter_reg_fields=[],
                field_mappings=[],
                hash_fields=[],
                crop_config={
                    "top_crop": 0.0,
                    "bottom_crop": 0.0,
                    "base_threshold": 0.5,
                },
            )
            session.add(spec)
            session.commit()

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
        dc_region = session.exec(
            select(Region).where(Region.region_key == "DC")
        ).first()
        if dc_region is None:
            dc_region = Region(
                region_key="DC",
                region_name="District of Columbia",
                country_code="US",
            )
            session.add(dc_region)
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
