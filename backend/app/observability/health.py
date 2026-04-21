from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Callable

from app.settings.settings import get_settings


class CheckStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    status: CheckStatus
    checks: dict
    _start_time: float = field(default_factory=time.time, repr=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "version": get_settings().version,
            "uptime_seconds": round(time.time() - self._start_time, 1),
            "checks": self.checks,
        }


def _check_database(check_fn: Callable[[], float]) -> dict:
    try:
        latency = check_fn()
        return {"status": "ok", "latency_ms": round(latency, 1)}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def _determine_status(checks: dict) -> CheckStatus:
    db_check = checks.get("database", {})
    if db_check.get("status") == "error":
        return CheckStatus.UNHEALTHY
    for check in checks.values():
        if check.get("status") == "error":
            return CheckStatus.DEGRADED
    return CheckStatus.OK


@dataclass
class HealthChecker:
    db_check_fn: Callable[[], float]
    _start_time: float = field(default_factory=time.time, repr=False)

    def check(self) -> HealthCheckResult:
        checks: dict = {}
        checks["database"] = _check_database(self.db_check_fn)
        status = _determine_status(checks)
        return HealthCheckResult(status=status, checks=checks, _start_time=self._start_time)
