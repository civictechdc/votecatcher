from abc import ABC, abstractmethod


class EventTransport(ABC):
	"""Abstract base for event transport implementations."""

	@abstractmethod
	async def subscribe_to_campaign(self, campaign_id: str):
		"""Subscribe to all events for a campaign."""
		...

	@abstractmethod
	async def subscribe_to_job(self, job_id: int):
		"""Subscribe to all events for a job."""
		...

	@abstractmethod
	async def close(self):
		"""Clean up subscriptions."""
		...
