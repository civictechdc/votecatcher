"""Integration tests for VoterListService."""

import pytest
from sqlmodel import Session, select

from app.data.database.model.registered_voter import RegisteredVoter
from app.data.database.model.schema import Region
from app.data.database.model.voter_list_upload import UploadStatus, VoterListUpload
from app.domain.field_spec import (
    BallotField,
    CropConfig,
    FieldMapping,
    RegionFieldSpecConfig,
    VoterRegField,
)
from app.services.voter_list_service import VoterListService


@pytest.fixture
def voter_list_service(session: Session):
    return VoterListService(session)


@pytest.fixture
def test_spec() -> RegionFieldSpecConfig:
    return RegionFieldSpecConfig(
        region_name="Test Region",
        country_code="US",
        ballot_fields=[
            BallotField(
                id="name",
                label="Full Name",
                field_type="text",
                required_for_matching=True,
                match_weight=1.0,
            ),
            BallotField(
                id="address",
                label="Address",
                field_type="address",
                required_for_matching=True,
                match_weight=1.0,
            ),
        ],
        voter_reg_fields=[
            VoterRegField(
                id="first_name",
                csv_column_name="First_Name",
                data_type="text",
                category="name",
            ),
            VoterRegField(
                id="last_name",
                csv_column_name="Last_Name",
                data_type="text",
                category="name",
            ),
            VoterRegField(
                id="street",
                csv_column_name="Street",
                data_type="text",
                category="address",
            ),
            VoterRegField(
                id="city",
                csv_column_name="City",
                data_type="text",
                category="address",
            ),
            VoterRegField(
                id="state",
                csv_column_name="State",
                data_type="text",
                category="address",
            ),
            VoterRegField(
                id="zip",
                csv_column_name="Zip",
                data_type="text",
                category="address",
            ),
        ],
        field_mappings=[
            FieldMapping(ballot_field_id="name", template="{first_name} {last_name}"),
            FieldMapping(
                ballot_field_id="address",
                template="{street} {city} {state} {zip}",
            ),
        ],
        hash_fields=["last_name", "first_name", "street"],
        crop_config=CropConfig(top_crop=0.385, bottom_crop=0.725, base_threshold=85),
    )


class TestVoterListServiceIntegration:
    """Integration tests for VoterListService with database."""

    def test_merge_creates_new_voters(
        self,
        session: Session,
        voter_list_service: VoterListService,
        test_region: Region,
        test_spec: RegionFieldSpecConfig,
    ):
        upload = VoterListUpload(
            region_id=test_region.id,
            original_filename="test.csv",
            file_size=1000,
            row_count=2,
            status=UploadStatus.ACTIVE,
        )
        session.add(upload)
        session.commit()

        rows = [
            {
                "first_name": "John",
                "last_name": "Doe",
                "street": "123 Main St",
                "city": "City",
                "state": "ST",
                "zip": "12345",
            },
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "street": "456 Oak Ave",
                "city": "City",
                "state": "ST",
                "zip": "67890",
            },
        ]

        new_count, updated_count = voter_list_service.merge(
            test_region.id, rows, upload, spec=test_spec
        )

        assert new_count == 2
        assert updated_count == 0

        voters = session.exec(
            select(RegisteredVoter).where(RegisteredVoter.region_id == test_region.id)
        ).all()
        assert len(voters) == 2

    def test_merge_updates_existing(
        self,
        session: Session,
        voter_list_service: VoterListService,
        test_region: Region,
        test_spec: RegionFieldSpecConfig,
    ):
        upload1 = VoterListUpload(
            region_id=test_region.id,
            original_filename="test1.csv",
            file_size=1000,
            row_count=1,
            status=UploadStatus.ACTIVE,
        )
        session.add(upload1)
        session.commit()

        rows = [
            {
                "first_name": "John",
                "last_name": "Doe",
                "street": "123 Main St",
                "city": "City",
                "state": "ST",
                "zip": "12345",
            },
        ]

        voter_list_service.merge(test_region.id, rows, upload1, spec=test_spec)

        upload2 = VoterListUpload(
            region_id=test_region.id,
            original_filename="test2.csv",
            file_size=1000,
            row_count=1,
            status=UploadStatus.ACTIVE,
        )
        session.add(upload2)
        session.commit()

        new_count, updated_count = voter_list_service.merge(
            test_region.id, rows, upload2, spec=test_spec
        )

        assert new_count == 0
        assert updated_count == 1

        voters = session.exec(
            select(RegisteredVoter).where(RegisteredVoter.region_id == test_region.id)
        ).all()
        assert len(voters) == 1
        assert voters[0].last_upload_id == upload2.id

    def test_supersede_previous_uploads(
        self,
        session: Session,
        voter_list_service: VoterListService,
        test_region: Region,
    ):
        upload1 = VoterListUpload(
            region_id=test_region.id,
            original_filename="old.csv",
            file_size=1000,
            row_count=1,
            status=UploadStatus.ACTIVE,
        )
        session.add(upload1)
        session.commit()

        upload2 = VoterListUpload(
            region_id=test_region.id,
            original_filename="new.csv",
            file_size=1000,
            row_count=1,
            status=UploadStatus.ACTIVE,
        )
        session.add(upload2)
        session.commit()

        voter_list_service.supersede_previous_uploads(test_region.id, upload2)

        session.refresh(upload1)
        assert upload1.status == UploadStatus.SUPERSEDED
        assert upload1.superseded_by == upload2.id

    def test_get_active_upload_returns_most_recent(
        self,
        session: Session,
        voter_list_service: VoterListService,
        test_region: Region,
    ):
        upload1 = VoterListUpload(
            region_id=test_region.id,
            original_filename="first.csv",
            file_size=1000,
            row_count=1,
            status=UploadStatus.ACTIVE,
        )
        session.add(upload1)
        session.commit()

        upload2 = VoterListUpload(
            region_id=test_region.id,
            original_filename="second.csv",
            file_size=2000,
            row_count=2,
            status=UploadStatus.ACTIVE,
        )
        session.add(upload2)
        session.commit()

        active = voter_list_service.get_active_upload(test_region.id)

        assert active is not None
        assert active.original_filename == "second.csv"

    def test_delete_voters_for_region(
        self,
        session: Session,
        voter_list_service: VoterListService,
        test_region: Region,
        test_spec: RegionFieldSpecConfig,
    ):
        upload = VoterListUpload(
            region_id=test_region.id,
            original_filename="test.csv",
            file_size=1000,
            row_count=2,
            status=UploadStatus.ACTIVE,
        )
        session.add(upload)
        session.commit()

        rows = [
            {
                "first_name": "John",
                "last_name": "Doe",
                "street": "123 Main St",
                "city": "City",
                "state": "ST",
                "zip": "12345",
            },
        ]
        voter_list_service.merge(test_region.id, rows, upload, spec=test_spec)

        deleted_count = voter_list_service.delete_voters_for_region(test_region.id)

        assert deleted_count == 1

        voters = session.exec(
            select(RegisteredVoter).where(RegisteredVoter.region_id == test_region.id)
        ).all()
        assert len(voters) == 0
