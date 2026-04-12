"""BDD tests for application startup lifecycle.

Scenarios covered:
  - Database is initialized on application startup
  - Configuration is validated on application startup
  - Background worker is launched on application startup
  - Background worker is stopped on application shutdown
  - Worker stopper is awaited during shutdown
"""

import asyncio

import pytest


async def _long_running_noop():
    """Simulates a long-running worker — blocks until cancelled."""
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass


class TestDatabaseInitializedOnStartup:
    """Scenario: Database is initialized during application startup."""

    @pytest.mark.asyncio
    async def test_db_initializer_invoked(self):
        """Given a db_initializer callback, when startup() runs, callback is invoked."""
        from app.startup import ApplicationStartup

        called = []
        startup = ApplicationStartup(
            db_initializer=lambda: called.append(True),
            worker_starter=_long_running_noop,
            config_validator=lambda: None,
        )
        await startup.startup()
        try:
            assert called == [True]
        finally:
            await startup.shutdown()


class TestConfigValidatedOnStartup:
    """Scenario: Configuration is validated during application startup."""

    @pytest.mark.asyncio
    async def test_config_validator_invoked(self):
        """Given a config_validator callback, when startup() runs, callback is invoked."""
        from app.startup import ApplicationStartup

        called = []
        startup = ApplicationStartup(
            db_initializer=lambda: None,
            worker_starter=_long_running_noop,
            config_validator=lambda: called.append(True),
        )
        await startup.startup()
        try:
            assert called == [True]
        finally:
            await startup.shutdown()


class TestWorkerLaunchedOnStartup:
    """Scenario: Background worker is launched during application startup."""

    @pytest.mark.asyncio
    async def test_worker_task_is_running_after_startup(self):
        """Given a worker_starter, when startup() runs, worker task is active."""
        from app.startup import ApplicationStartup

        startup = ApplicationStartup(
            db_initializer=lambda: None,
            worker_starter=_long_running_noop,
            config_validator=lambda: None,
        )
        await startup.startup()
        try:
            assert startup.is_worker_running is True
        finally:
            await startup.shutdown()


class TestWorkerStoppedOnShutdown:
    """Scenario: Background worker is stopped during application shutdown."""

    @pytest.mark.asyncio
    async def test_worker_no_longer_running_after_shutdown(self):
        """Given a running worker, when shutdown() runs, worker is no longer active."""
        from app.startup import ApplicationStartup

        startup = ApplicationStartup(
            db_initializer=lambda: None,
            worker_starter=_long_running_noop,
            config_validator=lambda: None,
        )
        await startup.startup()
        assert startup.is_worker_running is True

        await startup.shutdown()
        assert startup.is_worker_running is False

    @pytest.mark.asyncio
    async def test_worker_stopper_callback_awaited(self):
        """Given a worker_stopper, when shutdown() runs, stopper is awaited."""
        from app.startup import ApplicationStartup

        stopped = []

        async def record_stop():
            stopped.append(True)

        startup = ApplicationStartup(
            db_initializer=lambda: None,
            worker_starter=_long_running_noop,
            worker_stopper=record_stop,
            config_validator=lambda: None,
        )
        await startup.startup()
        await startup.shutdown()
        assert stopped == [True]


class TestStartupSequenceOrder:
    """Scenario: Startup steps execute in the correct order."""

    @pytest.mark.asyncio
    async def test_db_init_before_config_validation(self):
        """Given both callbacks, db_initializer runs before config_validator."""
        from app.startup import ApplicationStartup

        order = []

        startup = ApplicationStartup(
            db_initializer=lambda: order.append("db"),
            worker_starter=_long_running_noop,
            config_validator=lambda: order.append("config"),
        )
        await startup.startup()
        try:
            assert order == ["db", "config"]
        finally:
            await startup.shutdown()


class TestShutdownWithoutStartup:
    """Scenario: Shutdown called without prior startup does not error."""

    @pytest.mark.asyncio
    async def test_shutdown_is_safe_without_startup(self):
        """Given no prior startup, when shutdown() runs, no exception is raised."""
        from app.startup import ApplicationStartup

        startup = ApplicationStartup()
        await startup.shutdown()
        assert startup.is_worker_running is False
