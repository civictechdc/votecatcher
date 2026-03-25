"""Unit tests for VoterListUpload model."""

import uuid
from datetime import datetime

from app.data.database.model.voter_list_upload import UploadStatus, VoterListUpload


class TestVoterListUploadModel:
	"""Tests for VoterListUpload model."""

	def test_voter_list_upload_creation(self):
		"""Test basic VoterListUpload instantiation."""
		region_id = uuid.uuid4()
		upload = VoterListUpload(
			region_id=region_id,
			original_filename="voters.csv",
			file_size=12345,
			row_count=1000,
			status=UploadStatus.ACTIVE,
		)
		assert upload.region_id == region_id
		assert upload.original_filename == "voters.csv"
		assert upload.file_size == 12345
		assert upload.row_count == 1000
		assert upload.status == UploadStatus.ACTIVE
		assert upload.superseded_at is None
		assert upload.superseded_by is None

	def test_voter_list_upload_status_enum(self):
		"""Test UploadStatus enum values."""
		assert UploadStatus.ACTIVE == "active"
		assert UploadStatus.SUPERSEDED == "superseded"

	def test_voter_list_upload_defaults(self):
		"""Test default values for VoterListUpload."""
		region_id = uuid.uuid4()
		upload = VoterListUpload(
			region_id=region_id,
			original_filename="voters.csv",
			file_size=12345,
			row_count=1000,
		)
		assert upload.status == UploadStatus.ACTIVE
		assert isinstance(upload.uploaded_at, datetime)
		assert isinstance(upload.id, uuid.UUID)

	def test_voter_list_upload_superseded(self):
		"""Test VoterListUpload with superseded fields."""
		region_id = uuid.uuid4()
		new_upload_id = uuid.uuid4()
		upload = VoterListUpload(
			region_id=region_id,
			original_filename="voters.csv",
			file_size=12345,
			row_count=1000,
			status=UploadStatus.SUPERSEDED,
			superseded_at=datetime.now(),
			superseded_by=new_upload_id,
		)
		assert upload.status == UploadStatus.SUPERSEDED
		assert upload.superseded_at is not None
		assert upload.superseded_by == new_upload_id
