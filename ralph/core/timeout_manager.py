"""Timeout and cost guardrails for Ralph runs."""

from __future__ import annotations

import time


class TimeoutManager:
    """Track elapsed time and cumulative cost for a generation run."""

    def __init__(self, timeout_minutes: int, cost_limit_cents: int) -> None:
        if timeout_minutes <= 0:
            raise ValueError("timeout_minutes must be greater than 0")
        if cost_limit_cents < 0:
            raise ValueError("cost_limit_cents must be 0 or greater")

        self._timeout_seconds = timeout_minutes * 60
        self._cost_limit_cents = cost_limit_cents
        self._start_time = time.monotonic()

    def is_timeout_exceeded(self) -> bool:
        """Return True if the configured timeout has been reached."""
        elapsed = time.monotonic() - self._start_time
        return elapsed >= self._timeout_seconds

    def is_cost_limit_exceeded(self, cost_cents: int) -> bool:
        """Return True when the provided cost exceeds the configured limit."""
        if cost_cents < 0:
            raise ValueError("cost_cents must be 0 or greater")
        return cost_cents > self._cost_limit_cents
