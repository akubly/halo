"""
Integration test for confidence-hold timeout in host/main.py.

I2 — Confidence-Hold Timeout (contract §2.4, ARD §8):

After ~30 seconds of continuously gated (suppressed) updates, the main loop
must send the last computed mood regardless of confidence.  This prevents the
"stuck creature" scenario: if the host is in a quiet room with borderline
confidence, the creature never updates past frame 0.

Seams required (Ng must implement, contract §4.1):
    - run(transport, sensor_stream, *, clock=time.monotonic) — injectable clock
    - FakeTransport via Transport Protocol seam (contract §4.2)
    - SensorFrame with mic_ok/imu_ok fields (contract §1.1)
    - CONFIDENCE_HOLD_TIMEOUT_S exported from host.main (contract §2.4)
"""

import asyncio
import struct
import unittest
import unittest.mock

import pytest

# ── Import guard ─────────────────────────────────────────────────────────────
try:
    from host.main import run
    _RUN_IMPORT_ERROR: str | None = None
except ImportError as _e:
    _RUN_IMPORT_ERROR = str(_e)
    run = None  # type: ignore[assignment]

try:
    from host.main import CONFIDENCE_HOLD_TIMEOUT_S
    _TIMEOUT_S: float = CONFIDENCE_HOLD_TIMEOUT_S
except ImportError:
    _TIMEOUT_S = 30.0  # contract default — use if not yet exported

try:
    from host.sensors import SensorFrame
    _SENSORS_IMPORT_ERROR: str | None = None
except ImportError as _e:
    _SENSORS_IMPORT_ERROR = str(_e)
    SensorFrame = None  # type: ignore[assignment]

try:
    from host.familiar_protocol import Mood
    _PROTOCOL_IMPORT_ERROR: str | None = None
except ImportError as _e:
    _PROTOCOL_IMPORT_ERROR = str(_e)
    Mood = None  # type: ignore[assignment]


@pytest.fixture(autouse=True)
def _require_week2_modules() -> None:
    """Fail with a clear message if Week-2 modules are not yet importable."""
    if _RUN_IMPORT_ERROR is not None:
        pytest.fail(
            f"host.main.run not importable: {_RUN_IMPORT_ERROR}\n"
            "test_confidence_hold_timeout_resends_after_30s requires Week-2 run()."
        )
    if _SENSORS_IMPORT_ERROR is not None:
        pytest.fail(
            f"host.sensors not importable: {_SENSORS_IMPORT_ERROR}\n"
            "This test requires SensorFrame with mic_ok/imu_ok fields."
        )
    if _PROTOCOL_IMPORT_ERROR is not None:
        pytest.fail(
            f"host.familiar_protocol not importable: {_PROTOCOL_IMPORT_ERROR}\n"
            "This test requires Mood enum."
        )


# ── Test infrastructure ───────────────────────────────────────────────────────

class FakeTransport:
    """Records every send() call. Implements the Transport Protocol seam."""

    def __init__(self) -> None:
        self.sent: list[bytes] = []
        self._recv_cb = None

    async def connect(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    async def send(self, data: bytes) -> None:
        self.sent.append(data)

    def on_receive(self, callback) -> None:
        self._recv_cb = callback


class FakeClock:
    """
    Injectable clock that advances by a fixed step on each call.

    With step=1.0, the loop's tick_start values are:
        last_send_time = clock()  → t=0.0  (initialization)
        frame 0: tick_start = 1.0  → delta = 1.0   (not > 30s)
        frame n: tick_start = n+1  → delta = n+1.0
        frame 30: tick_start = 31.0 → delta = 31.0 > 30s → SEND

    The clock is stateless-ish: each __call__ returns the next value.
    """

    def __init__(self, step: float = 1.0) -> None:
        self._t: float = 0.0
        self._step = step

    def __call__(self) -> float:
        t = self._t
        self._t += self._step
        return t


class FakeSensorStream:
    """
    Yields a fixed list of SensorFrame objects, then stops.

    Allows the test to drive the main loop with controlled inputs.
    """

    def __init__(self, frames: list) -> None:
        self._frames = list(frames)
        self._idx = 0

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._idx >= len(self._frames):
            raise StopAsyncIteration
        frame = self._frames[self._idx]
        self._idx += 1
        return frame


def _make_gated_frame():
    """
    Create a SensorFrame that causes compute_mood() to return a gated result.

    mic_ok=False → confidence *= 0.6 → max 0.6 < CONFIDENCE_GATE(0.7) → gated.
    Handles both stub (no ok-fields) and contract-compliant SensorFrame.
    """
    try:
        return SensorFrame(
            audio_rms=0.5,
            audio_pitch_variance=0.5,
            imu_acceleration=0.5,
            imu_rotation=0.5,
            mic_ok=False,   # confidence *= 0.6 → gated
            imu_ok=True,
        )
    except TypeError:
        # Stub SensorFrame (Week 1) — missing ok-fields; test will fail at run()
        return SensorFrame(
            audio_rms=0.5,
            audio_pitch_variance=0.5,
            imu_acceleration=0.5,
            imu_rotation=0.5,
        )


# ── Test ──────────────────────────────────────────────────────────────────────

class TestConfidenceHoldTimeout(unittest.TestCase):

    def test_confidence_hold_timeout_resends_after_30s(self) -> None:
        """
        I2 — Confidence-Hold Timeout (contract §2.4, ARD §8).

        Drive main loop with gated frames for >30s of simulated time.
        Assert:
        1. A send occurs after ~30s of suppression.
        2. The 30s timer resets on that send (no duplicate send immediately after).

        Seam requirements:
        - run(transport, sensor_stream, *, clock=...) — injectable clock
        - Transport.send() called once for the timeout send
        """
        transport = FakeTransport()
        gated_frame = _make_gated_frame()

        # 40 frames × 1.0s/call = frame 30 triggers timeout (tick_start=31.0 > 30.0)
        frames = [gated_frame] * 40
        stream = FakeSensorStream(frames)
        fake_clock = FakeClock(step=1.0)

        async def _drive() -> None:
            try:
                await run(transport, stream, clock=fake_clock)
            except TypeError as e:
                pytest.fail(
                    f"host.main.run() does not accept Week-2 signature "
                    f"run(transport, sensor_stream, *, clock=...): {e}\n"
                    f"Ng must add 'clock=time.monotonic' injectable param (contract §4.1)."
                )
            except NotImplementedError as e:
                pytest.fail(
                    f"host.main.run() or a dependency raised NotImplementedError: {e}\n"
                    f"Week-2 implementation is incomplete (module not ready)."
                )

        asyncio.run(_drive())

        # ── Assert: at least one send after 30s of gating ────────────────────
        assert len(transport.sent) >= 1, (
            f"After {_TIMEOUT_S}s of gated frames, run() must send at least one packet. "
            f"Confidence-hold timeout prevents stuck creature (ARD §8, contract §2.4). "
            f"transport.sent is empty — timeout logic missing in main loop."
        )

        # ── Assert: exactly one send in first 40 gated frames ────────────────
        # With FakeClock(step=1.0): frame 30 triggers (tick_start=31.0 > 30.0).
        # Frame 31–39: tick_start=32–40, delta from NEW last_send_time (~31.0) is 1–9s,
        # so no second send within 40 frames.
        assert len(transport.sent) == 1, (
            f"Expected exactly 1 send (at ~30s timeout); got {len(transport.sent)}. "
            f"Timer must reset on send so the next timeout is also ~30s out."
        )

        # ── Assert: the sent packet is a valid FAMILIAR_UPDATE ────────────────
        sent_bytes = transport.sent[0]
        assert len(sent_bytes) == 6, (
            f"Timeout send packet must be 6-byte FAMILIAR_UPDATE; got {len(sent_bytes)} bytes."
        )
        assert sent_bytes[0] == 0x80, (
            f"Timeout send packet opcode must be 0x80 (FAMILIAR_UPDATE); "
            f"got 0x{sent_bytes[0]:02x}."
        )


if __name__ == "__main__":
    unittest.main()
