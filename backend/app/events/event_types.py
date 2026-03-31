from datetime import UTC, datetime
from enum import Enum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
	JOB_STATUS_CHANGED = "job:status_changed"
	JOB_PROGRESS = "job:progress"
	METRICS_UPDATED = "metrics:updated"


class BaseEvent(BaseModel):
	event_id: str = Field(default_factory=lambda: str(uuid4()))
	event_type: EventType
	timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
	trace_id: str | None = None
	source: str | None = None
	campaign_id: str | None = None
	job_id: int | None = None


class JobStatusEvent(BaseEvent):
	event_type: Literal[EventType.JOB_STATUS_CHANGED] = EventType.JOB_STATUS_CHANGED
	status: str
	previous_status: str | None = None


class JobProgressEvent(BaseEvent):
	event_type: Literal[EventType.JOB_PROGRESS] = EventType.JOB_PROGRESS
	processed: int
	total: int
	percentage: float


class MetricsUpdatedEvent(BaseEvent):
	event_type: Literal[EventType.METRICS_UPDATED] = EventType.METRICS_UPDATED
	total_signatures: int
	processed: int
	high_confidence: int
