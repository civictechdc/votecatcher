"""OCR service for batch OCR job management.

Handles batch job creation, status polling, and result storage.
Follows the Router → Service pattern from SPEC.md §3.2.
"""

import base64
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

from app.data.database.model.jobs import JobStatus, OcrJob
from app.data.database.model.ocr_result import OcrResult, OcrResultCreate
from app.data.database.model.petition_crop import PetitionCrop
from app.matching.match_repository import MatchingStatus
from app.ocr.data.data_models import EncodedPetitionPage
from app.ocr.ocr_manager import OcrClient, OcrJobStatus, OcrRequest

if TYPE_CHECKING:
	from sqlmodel import Session

logger = structlog.get_logger(__name__)


class OCRService:
	"""Service for managing OCR batch jobs and result storage."""

	def __init__(self, session: "Session", storage_base: Path) -> None:
		"""
		Initialize OCR service.

		Args:
		    session: Database session
		    storage_base: Base path for file storage
		"""
		self.session = session
		self.storage_base = storage_base

	async def encode_crops(
		self, crops: list[PetitionCrop], campaign_id: str
	) -> list[EncodedPetitionPage]:
		"""
		Encode petition crops to base64 images.

		Args:
		    crops: List of petition crops to encode
		    campaign_id: Campaign identifier

		Returns:
		    List of EncodedPetitionPage objects
		"""
		encoded_pages: list[EncodedPetitionPage] = []

		for crop in crops:
			crop_path = Path(crop.stored_path)

			if not crop_path.exists():
				logger.warning(
					f"Crop file not found: {crop_path}",
					crop_id=crop.id,
					campaign_id=campaign_id,
				)
				continue

			try:
				img_bytes = crop_path.read_bytes()
				encoded = base64.b64encode(img_bytes).decode("utf-8")

				encoded_page = EncodedPetitionPage(
					petition_file_name=crop_path.name,
					page_num=crop.page_number,
					encoded_page=encoded,
					image_path=str(crop_path),
					petition_file_page_total=1,
					scan_id=str(crop.scan_id),
				)
				encoded_pages.append(encoded_page)

				logger.debug(
					"Encoded crop to base64",
					crop_id=crop.id,
					page_num=crop.page_number,
				)
			except Exception as e:
				logger.error(
					"Failed to encode crop",
					crop_id=crop.id,
					error=str(e),
				)
				continue

		logger.info(
			f"Encoded {len(encoded_pages)}/{len(crops)} crops "
			f"for campaign {campaign_id}"
		)
		return encoded_pages

	async def create_ocr_job(
		self,
		matcher_job_id: int,
		crops: list[PetitionCrop],
		ocr_client: OcrClient,
		campaign_id: str,
		task_id: str,
	) -> OcrJob:
		"""
		Create an OCR batch job and persist to database.

		Args:
		    matcher_job_id: Parent matcher job ID
		    crops: List of petition crops to process
		    ocr_client: OCR provider client
		    campaign_id: Campaign identifier
		    task_id: Task identifier for tracking

		Returns:
		    Created OcrJob instance

		Raises:
		    ValueError: If no crops provided or encoding fails
		"""
		if not crops:
			raise ValueError("No crops provided for OCR processing")

		encoded_pages = await self.encode_crops(crops, campaign_id)

		if not encoded_pages:
			raise ValueError("Failed to encode any crops")

		request = OcrRequest(
			campaign_id=campaign_id,
			provider_id=ocr_client.provider_id,
			task_id=task_id,
			encoded_pages=encoded_pages,
		)

		logger.info(
			"Creating OCR batch job",
			matcher_job_id=matcher_job_id,
			campaign_id=campaign_id,
			crop_count=len(crops),
			provider=ocr_client.provider_id,
		)

		job_status: OcrJobStatus = await ocr_client.create_batch_job(request)

		ocr_job = OcrJob(
			matcher_job_id=matcher_job_id,
			provider_job_id=job_status.ocr_job_id,
			status=self._map_status_to_job_status(job_status.task_status),
			started_on=job_status.created_at,
		)

		if job_status.failure_message:
			ocr_job.error_data = {"message": job_status.failure_message}

		self.session.add(ocr_job)
		self.session.commit()
		self.session.refresh(ocr_job)

		logger.info(
			"Created OCR job",
			ocr_job_id=ocr_job.id,
			provider_job_id=ocr_job.provider_job_id,
			status=ocr_job.status,
		)

		return ocr_job

	async def poll_job_status(self, ocr_job_id: int, ocr_client: OcrClient) -> OcrJob:
		"""
		Poll OCR job status from provider and update database.

		Args:
		    ocr_job_id: Database ID of OCR job
		    ocr_client: OCR provider client

		Returns:
		    Updated OcrJob instance

		Raises:
		    ValueError: If job not found or has no provider job ID
		"""
		ocr_job = self.session.get(OcrJob, ocr_job_id)

		if not ocr_job:
			raise ValueError(f"OCR job not found: {ocr_job_id}")

		if not ocr_job.provider_job_id:
			raise ValueError(f"OCR job has no provider job ID: {ocr_job_id}")

		logger.debug(
			"Polling OCR job status",
			ocr_job_id=ocr_job.id,
			provider_job_id=ocr_job.provider_job_id,
		)

		job_status = await ocr_client.fetch_job_status(ocr_job.provider_job_id)

		ocr_job.status = self._map_status_to_job_status(job_status.task_status)
		ocr_job.updated_on = job_status.updated_at or datetime.now(UTC)

		if job_status.ended_at:
			ocr_job.ended_on = job_status.ended_at

		if job_status.failure_message:
			ocr_job.error_data = {"message": job_status.failure_message}

		self.session.commit()
		self.session.refresh(ocr_job)

		logger.debug(
			"Updated OCR job status",
			ocr_job_id=ocr_job.id,
			status=ocr_job.status,
		)

		return ocr_job

	async def retrieve_and_store_results(
		self,
		ocr_job_id: int,
		ocr_client: OcrClient,
		crops: list[PetitionCrop],
	) -> list[OcrResult]:
		"""
		Retrieve OCR results from provider and store in database.

		Args:
		    ocr_job_id: Database ID of OCR job
		    ocr_client: OCR provider client
		    crops: List of petition crops (for mapping results)

		Returns:
		    List of created OcrResult instances

		Raises:
		    ValueError: If job not found or has no provider job ID
		"""
		ocr_job = self.session.get(OcrJob, ocr_job_id)

		if not ocr_job:
			raise ValueError(f"OCR job not found: {ocr_job_id}")

		if not ocr_job.provider_job_id:
			raise ValueError(f"OCR job has no provider job ID: {ocr_job_id}")

		logger.info(
			"Retrieving OCR results",
			ocr_job_id=ocr_job.id,
			provider_job_id=ocr_job.provider_job_id,
		)

		results: list[OcrResult] = []
		crop_map = {crop.stored_path: crop for crop in crops}

		try:
			async for result_data in ocr_client.get_ocr_results(
				ocr_job.provider_job_id
			):
				crop = crop_map.get(result_data.document_path)

				if not crop:
					logger.warning(
						"Crop not found for result",
						document_path=result_data.document_path,
					)
					continue

				extracted_text = {}
				for part in result_data.result_parts:
					extracted_text[part["field_name"]] = part["value"]

				ocr_result_create = OcrResultCreate(
					crop_id=crop.id,
					ocr_job_id=ocr_job.id,
					extracted_text=extracted_text,
					raw_response={"result_parts": result_data.result_parts},
				)

				ocr_result = OcrResult(**ocr_result_create.model_dump())
				self.session.add(ocr_result)
				results.append(ocr_result)

				logger.debug(
					"Stored OCR result",
					crop_id=crop.id,
					fields=list(extracted_text.keys()),
				)

		except Exception as e:
			logger.error(
				"Error retrieving OCR results",
				ocr_job_id=ocr_job.id,
				error=str(e),
			)
			raise

		self.session.commit()

		for result in results:
			self.session.refresh(result)

		logger.info(
			f"Stored {len(results)} OCR results",
			ocr_job_id=ocr_job.id,
		)

		return results

	def _map_status_to_job_status(self, status: MatchingStatus) -> JobStatus:
		"""Map MatchingStatus to JobStatus enum."""
		mapping = {
			MatchingStatus.NOT_STARTED: JobStatus.NOT_STARTED,
			MatchingStatus.PENDING: JobStatus.OCR_PENDING,
			MatchingStatus.OCR_PENDING: JobStatus.OCR_PENDING,
			MatchingStatus.OCR_IN_PROGRESS: JobStatus.OCR_STARTED,
			MatchingStatus.OCR_COMPLETED: JobStatus.OCR_COMPLETED,
			MatchingStatus.OCR_FAILED: JobStatus.OCR_FAILED,
			MatchingStatus.OCR_TIMED_OUT: JobStatus.OCR_TIMEOUT,
			MatchingStatus.OCR_CANCELLED: JobStatus.OCR_FAILED,
			MatchingStatus.MATCHING: JobStatus.MATCHING,
			MatchingStatus.COMPLETED: JobStatus.MATCHING_COMPLETED,
			MatchingStatus.MATCHING_FAILED: JobStatus.MATCHING_ERROR,
			MatchingStatus.CANCELLED: JobStatus.MATCHING_ERROR,
			MatchingStatus.TIMED_OUT: JobStatus.OCR_TIMEOUT,
			MatchingStatus.MISC_ERROR: JobStatus.MATCHING_ERROR,
		}
		return mapping.get(status, JobStatus.NOT_STARTED)
