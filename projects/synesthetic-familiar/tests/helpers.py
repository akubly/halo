"""
Shared test infrastructure for the VESPER test suite.

M6 fix: single canonical source for FakeTransport, FakeClock, and
FakeSensorStream.  Previously duplicated verbatim in test_confidence_gating.py
and test_fallback.py — both now import from here.

FakeSensorStream re-exports host.sensors.FakeSensorStream (the richer canonical
version with loop/delay params and proper start/stop lifecycle).
"""
from __future__ import annotations

from typing import Callable

# FakeSensorStream: use the richer canonical version from sensors.py
from host.sensors import FakeSensorStream  # noqa: F401 — re-exported for tests


class FakeTransport:
    """Records every send() call.  Implements the Transport Protocol seam."""

    def __init__(self) -> None:
        self.sent: list[bytes] = []
        self._recv_cb = None

    async def connect(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    async def send(self, data: bytes) -> None:
        self.sent.append(data)

    def on_receive(self, callback: Callable[[bytes], None]) -> None:
        self._recv_cb = callback


class FakeClock:
    """
    Injectable clock that advances by a fixed step on each call.

    With step=1.0, the loop's tick_start values are:
        last_send_time = clock()  → t=0.0  (initialization)
        frame 0: tick_start = 1.0  → delta = 1.0   (not > 30s)
        frame n: tick_start = n+1  → delta = n+1.0
        frame 30: tick_start = 31.0 → delta = 31.0 > 30s → SEND

    The clock advances once per __call__; one call per frame keeps timeout
    arithmetic clean (no extra advancement from a second clock() for elapsed).
    """

    def __init__(self, step: float = 1.0) -> None:
        self._t: float = 0.0
        self._step = step

    def __call__(self) -> float:
        t = self._t
        self._t += self._step
        return t


async def noop_sleep(seconds: float) -> None:
    """No-op async sleep for test injection — removes real wall-clock overhead.

    Pass as ``sleep=noop_sleep`` to run() to make pacing free in tests while
    still asserting that the pacer is invoked (spy-wrap if needed).
    """
