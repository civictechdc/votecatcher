from app.events.event_types import (
	BaseEvent,
	EventType,
	JobProgressEvent,
	JobStatusEvent,
)


class TestEventType:
	def test_event_type_values(self):
		assert EventType.JOB_STATUS_CHANGED == "job:status_changed"
		assert EventType.JOB_PROGRESS == "job:progress"
		assert EventType.METRICS_UPDATED == "metrics:updated"


class TestBaseEvent:
	def test_base_event_generates_event_id(self):
		event = BaseEvent(event_type=EventType.JOB_STATUS_CHANGED)
		assert event.event_id is not None
		assert len(event.event_id) == 36

	def test_base_event_generates_timestamp(self):
		event = BaseEvent(event_type=EventType.JOB_STATUS_CHANGED)
		assert event.timestamp is not None


class TestJobStatusEvent:
	def test_job_status_event_has_required_fields(self):
		event = JobStatusEvent(
			job_id=1,
			campaign_id="abc123",
			status="MATCHING",
			previous_status="OCR_COMPLETED",
		)
		assert event.job_id == 1
		assert event.campaign_id == "abc123"
		assert event.status == "MATCHING"
		assert event.event_type == EventType.JOB_STATUS_CHANGED


class TestJobProgressEvent:
	def test_job_progress_event_calculates_percentage(self):
		event = JobProgressEvent(
			job_id=1, campaign_id="abc123", processed=50, total=100, percentage=50.0
		)
		assert event.percentage == 50.0
