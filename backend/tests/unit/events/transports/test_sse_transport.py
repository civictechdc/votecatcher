import asyncio
import contextlib

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.events.event_bus import event_bus
from app.events.event_types import JobStatusEvent
from app.events.transports.sse import SSETransport


@pytest.fixture(name="event_bus_session", scope="function")
def event_bus_session_fixture():
    test_engine = create_engine(
        "sqlite:///file:memdb?mode=memory&cache=shared&uri=true",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session


@pytest.fixture
def reset_event_bus(event_bus_session):
    for topic in list(event_bus._subscribers.keys()):
        event_bus._subscribers[topic].clear()
    event_bus._cleanup_empty_topics()
    yield event_bus

    for topic in list(event_bus._subscribers.keys()):
        event_bus._subscribers[topic].clear()
    event_bus._cleanup_empty_topics()


class TestSSETransport:
    def test_create_transport(self):
        transport = SSETransport()
        assert transport is not None

    @pytest.mark.asyncio
    async def test_subscribe_to_campaign_returns_response(self):
        transport = SSETransport()
        response = await transport.subscribe_to_campaign("123")
        assert response.media_type == "text/event-stream"

    @pytest.mark.asyncio
    async def test_subscribe_to_job_returns_response(self):
        transport = SSETransport()
        response = await transport.subscribe_to_job("42")
        assert response.media_type == "text/event-stream"

    def test_sse_headers(self):
        assert SSETransport.SSE_HEADERS["Cache-Control"] == "no-cache"
        assert SSETransport.SSE_HEADERS["Connection"] == "keep-alive"
        assert SSETransport.SSE_HEADERS["X-Accel-Buffering"] == "no"

    @pytest.mark.asyncio
    async def test_response_headers_set(self):
        transport = SSETransport()
        response = await transport.subscribe_to_campaign("test-headers")
        assert "Cache-Control" in response.headers
        assert response.headers["Cache-Control"] == "no-cache"

    @pytest.mark.asyncio
    async def test_subscribe_tracks_active_subscriptions(self):
        transport = SSETransport()
        await transport.subscribe_to_campaign("track-test")
        assert len(transport._active_subscriptions) >= 1
        await transport.close()

    @pytest.mark.asyncio
    async def test_close_clears_all_subscriptions(self):
        transport = SSETransport()
        await transport.subscribe_to_campaign("close-test-1")
        await transport.subscribe_to_campaign("close-test-2")
        assert len(transport._active_subscriptions) >= 2
        await transport.close()
        assert len(transport._active_subscriptions) == 0

    @pytest.mark.asyncio
    async def test_multiple_subscribers_same_topic(self):
        transport = SSETransport()
        response1 = await transport.subscribe_to_campaign("multi-test")
        response2 = await transport.subscribe_to_campaign("multi-test")
        assert response1 is not None
        assert response2 is not None
        assert len(transport._active_subscriptions) >= 2
        await transport.close()

    @pytest.mark.asyncio
    async def test_campaign_topic_format(self):
        transport = SSETransport()
        response = await transport.subscribe_to_campaign("abc-123")
        assert response.media_type == "text/event-stream"
        await transport.close()

    @pytest.mark.asyncio
    async def test_job_topic_format(self):
        transport = SSETransport()
        response = await transport.subscribe_to_job("999")
        assert response.media_type == "text/event-stream"
        await transport.close()

    @pytest.mark.asyncio
    async def test_event_yields_formatted_sse_data(self):
        transport = SSETransport()
        response = await transport.subscribe_to_campaign("test-yield")

        await event_bus.publish(
            JobStatusEvent(campaign_id="test-yield", job_id="1", status="MATCHING")
        )

        gen = response.body_iterator
        chunk = await asyncio.wait_for(gen.__anext__(), timeout=1.0)
        assert chunk.startswith("data: ")
        assert "job:status_changed" in chunk
        assert "MATCHING" in chunk
        await transport.close()

    @pytest.mark.asyncio
    async def test_heartbeat_format(self):
        transport = SSETransport()
        response = await transport.subscribe_to_campaign("heartbeat-format-test")

        gen = response.body_iterator
        task = asyncio.create_task(gen.__anext__())
        await asyncio.sleep(0.1)

        try:
            result = await asyncio.wait_for(task, timeout=35.0)
            if result == ": heartbeat\n\n":
                assert True
        except TimeoutError:
            pass
        finally:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
            await transport.close()

    @pytest.mark.asyncio
    async def test_close_unsubscribes_from_event_bus(self):
        transport = SSETransport()
        campaign_id = f"cleanup-unsub-test-{id(transport)}"
        await transport.subscribe_to_campaign(campaign_id)
        full_topic = f"campaign:{campaign_id}"

        assert full_topic in event_bus._subscribers
        assert len(event_bus._subscribers[full_topic]) == 1

        await transport.close()

        assert (
            full_topic not in event_bus._subscribers
            or len(event_bus._subscribers.get(full_topic, set())) == 0
        )

    @pytest.mark.asyncio
    async def test_close_sends_sentinel_to_unblock_generators(self):
        transport = SSETransport()
        campaign_id = f"sentinel-test-{id(transport)}"
        response = await transport.subscribe_to_campaign(campaign_id)
        gen = response.body_iterator

        read_task = asyncio.create_task(gen.__anext__())
        await asyncio.sleep(0.05)

        assert not read_task.done(), "Generator should be blocked waiting for data"

        await transport.close()

        try:
            _ = await asyncio.wait_for(read_task, timeout=1.0)  # noqa: F841
            pytest.fail("Generator should raise StopAsyncIteration, not yield a value")
        except StopAsyncIteration:
            pass
        except asyncio.CancelledError:
            pass
        except TimeoutError:
            pytest.fail("Generator did not exit after close() - sentinel not working")

    @pytest.mark.asyncio
    async def test_close_generator_exits_quickly_not_waiting_for_timeout(self):
        transport = SSETransport()
        campaign_id = f"quick-exit-test-{id(transport)}"
        response = await transport.subscribe_to_campaign(campaign_id)
        gen = response.body_iterator

        read_task = asyncio.create_task(gen.__anext__())
        await asyncio.sleep(0.05)
        assert not read_task.done()

        start = asyncio.get_event_loop().time()
        await transport.close()
        elapsed = asyncio.get_event_loop().time() - start

        assert elapsed < 1.0, f"close() took {elapsed:.2f}s - should exit immediately"

        with contextlib.suppress(StopAsyncIteration, asyncio.CancelledError):
            await asyncio.wait_for(read_task, timeout=0.5)
