"""Unit tests for SSE connection manager."""

import asyncio

import pytest

from app.events.sse_manager import SSEConnectionManager


@pytest.fixture
def sse_manager():
	"""SSE connection manager instance."""
	return SSEConnectionManager()


class TestSSEConnectionManager:
	"""Test SSE connection manager."""

	def test_manager_initialization(self, sse_manager):
		"""Test manager initializes with empty connections."""
		assert sse_manager.active_connections == {}
		assert sse_manager.connection_count == 0

	@pytest.mark.asyncio
	async def test_connect_client(self, sse_manager):
		"""Test client connection."""
		mock_queue = asyncio.Queue()
		job_id = 1

		await sse_manager.connect(job_id, mock_queue)

		assert job_id in sse_manager.active_connections
		assert mock_queue in sse_manager.active_connections[job_id]
		assert sse_manager.connection_count == 1

	@pytest.mark.asyncio
	async def test_disconnect_client(self, sse_manager):
		"""Test client disconnection."""
		mock_queue = asyncio.Queue()
		job_id = 1

		await sse_manager.connect(job_id, mock_queue)
		assert sse_manager.connection_count == 1

		sse_manager.disconnect(job_id, mock_queue)
		assert job_id not in sse_manager.active_connections
		assert sse_manager.connection_count == 0

	@pytest.mark.asyncio
	async def test_multiple_connections_same_job(self, sse_manager):
		"""Test multiple clients connecting to same job."""
		queue1 = asyncio.Queue()
		queue2 = asyncio.Queue()
		job_id = 1

		await sse_manager.connect(job_id, queue1)
		await sse_manager.connect(job_id, queue2)

		assert len(sse_manager.active_connections[job_id]) == 2
		assert sse_manager.connection_count == 2

	@pytest.mark.asyncio
	async def test_multiple_connections_different_jobs(self, sse_manager):
		"""Test clients connecting to different jobs."""
		queue1 = asyncio.Queue()
		queue2 = asyncio.Queue()

		await sse_manager.connect(1, queue1)
		await sse_manager.connect(2, queue2)

		assert 1 in sse_manager.active_connections
		assert 2 in sse_manager.active_connections
		assert sse_manager.connection_count == 2

	@pytest.mark.asyncio
	async def test_broadcast_to_job(self, sse_manager):
		"""Test broadcasting event to all clients of a job."""
		queue1 = asyncio.Queue()
		queue2 = asyncio.Queue()
		job_id = 1
		event_data = {"status": "OCR_STARTED", "timestamp": "2026-03-09T10:00:00Z"}

		await sse_manager.connect(job_id, queue1)
		await sse_manager.connect(job_id, queue2)

		await sse_manager.broadcast(job_id, "status_update", event_data)

		message1 = await queue1.get()
		message2 = await queue2.get()

		assert "event: status_update" in message1
		assert "OCR_STARTED" in message1
		assert "event: status_update" in message2
		assert "OCR_STARTED" in message2

	@pytest.mark.asyncio
	async def test_broadcast_to_nonexistent_job(self, sse_manager):
		"""Test broadcasting to job with no connections."""
		event_data = {"status": "OCR_STARTED"}

		result = await sse_manager.broadcast(999, "status_update", event_data)

		assert result == 0

	@pytest.mark.asyncio
	async def test_disconnect_nonexistent_job(self, sse_manager):
		"""Test disconnecting from nonexistent job doesn't raise error."""
		queue = asyncio.Queue()

		sse_manager.disconnect(999, queue)

	@pytest.mark.asyncio
	async def test_concurrent_clients_receive_events(self, sse_manager):
		"""Test multiple concurrent clients all receive broadcast events."""
		queues = [asyncio.Queue() for _ in range(5)]
		job_id = 1

		for queue in queues:
			await sse_manager.connect(job_id, queue)

		event_data = {"status": "OCR_STARTED"}

		await sse_manager.broadcast(job_id, "status_update", event_data)

		for queue in queues:
			message = await asyncio.wait_for(queue.get(), timeout=1.0)
			assert "event: status_update" in message

	@pytest.mark.asyncio
	async def test_broadcast_to_isolated_jobs(self, sse_manager):
		"""Test broadcast to one job doesn't affect others."""
		queue1 = asyncio.Queue()
		queue2 = asyncio.Queue()

		await sse_manager.connect(1, queue1)
		await sse_manager.connect(2, queue2)

		event_data = {"status": "OCR_STARTED"}

		await sse_manager.broadcast(1, "status_update", event_data)

		message1 = await asyncio.wait_for(queue1.get(), timeout=0.5)
		assert "event: status_update" in message1

		with pytest.raises(asyncio.TimeoutError):
			await asyncio.wait_for(queue2.get(), timeout=0.5)

	@pytest.mark.asyncio
	async def test_connection_cleanup_on_disconnect(self, sse_manager):
		"""Test connections are properly cleaned up."""
		queue = asyncio.Queue()
		job_id = 1

		await sse_manager.connect(job_id, queue)
		assert sse_manager.connection_count == 1

		sse_manager.disconnect(job_id, queue)
		assert sse_manager.connection_count == 0

		result = await sse_manager.broadcast(
			job_id, "status_update", {"status": "test"}
		)
		assert result == 0


class TestSSEEventFormats:
	"""Test SSE event format compliance."""

	@pytest.mark.asyncio
	async def test_status_update_event_format(self, sse_manager):
		"""Test status_update event format."""
		queue = asyncio.Queue()
		await sse_manager.connect(1, queue)

		event_data = {
			"job_id": 1,
			"status": "OCR_STARTED",
			"phase": "ocr",
			"timestamp": "2026-03-09T10:00:00Z",
		}

		await sse_manager.broadcast(1, "status_update", event_data)

		message = await queue.get()

		lines = message.strip().split("\n")
		assert lines[0] == "event: status_update"
		assert lines[1].startswith("data: ")
		import json

		data = json.loads(lines[1].replace("data: ", ""))
		assert data["job_id"] == 1
		assert data["status"] == "OCR_STARTED"

	@pytest.mark.asyncio
	async def test_matching_progress_event_format(self, sse_manager):
		"""Test matching_progress event format."""
		queue = asyncio.Queue()
		await sse_manager.connect(1, queue)

		event_data = {
			"job_id": 1,
			"processed": 50,
			"total": 250,
			"timestamp": "2026-03-09T10:12:00Z",
		}

		await sse_manager.broadcast(1, "matching_progress", event_data)

		message = await queue.get()

		assert "event: matching_progress" in message
		import json

		lines = message.strip().split("\n")
		data = json.loads(lines[1].replace("data: ", ""))
		assert data["processed"] == 50
		assert data["total"] == 250

	@pytest.mark.asyncio
	async def test_job_complete_event_format(self, sse_manager):
		"""Test job_complete event format."""
		queue = asyncio.Queue()
		await sse_manager.connect(1, queue)

		event_data = {
			"job_id": 1,
			"status": "MATCHING_COMPLETED",
			"summary": {
				"total_crops": 250,
				"high_confidence": 200,
				"medium_confidence": 40,
				"low_confidence": 10,
			},
			"timestamp": "2026-03-09T10:15:00Z",
		}

		await sse_manager.broadcast(1, "job_complete", event_data)

		message = await queue.get()

		assert "event: job_complete" in message
		import json

		lines = message.strip().split("\n")
		data = json.loads(lines[1].replace("data: ", ""))
		assert data["status"] == "MATCHING_COMPLETED"
		assert data["summary"]["total_crops"] == 250
