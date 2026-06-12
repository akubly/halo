"""
Integration test for both-sensors-fail fallback in host/main.py.

ARD §5.4 — Both-Sensors-Fail Fallback (contract §2.5):

If both mic_ok=False AND imu_ok=False for >10 seconds, the main loop must:
1. Send an explicit NEUTRAL packet.
2. NOT call compute_mood() (no meaningful signal to compute from).
3. Re-arm the timer after the neutral send (allows subsequent sends at 10s intervals).

This is a SEPARATE path from the confidence-hold timeout (§2.4).

Seams required (Ng must implement, contract §4.1/§4.2):
    - run(transport, sensor_stream, *, clock=time.monotonic) — injectable clock
    - FakeTransport via Transport Protocol seam
    - SensorFrame with mic_ok=False, imu_ok=False fields (contract §1.1)
    - BOTH_FAIL_TIMEOUT_S exported from host.main (contract §2.5)
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
    from host.main import BOTH_FAIL_TIMEOUT_S
    _FAIL_TIMEOUT_S: float = BOTH_FAIL_TIMEOUT_S
except ImportError:
    _FAIL_TIMEOUT_S = 10.0  # contract default — use if not yet exported

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

# M6: shared test infrastructure — single canonical source
from helpers import FakeTransport, FakeClock, FakeSensorStream, noop_sleep


@pytest.fixture(autouse=True)
def _require_week2_modules() -> None:
    """Fail with a clear message if Week-2 modules are not yet importable."""
    if _RUN_IMPORT_ERROR is not None:
        pytest.fail(
            f"host.main.run not importable: {_RUN_IMPORT_ERROR}\n"
            "test_both_sensors_fail_sends_neutral_after_10s requires Week-2 run()."
        )
    if _SENSORS_IMPORT_ERROR is not None:
        pytest.fail(
            f"host.sensors not importable: {_SENSORS_IMPORT_ERROR}\n"
            "This test requires SensorFrame with mic_ok=False, imu_ok=False."
        )
    if _PROTOCOL_IMPORT_ERROR is not None:
        pytest.fail(
            f"host.familiar_protocol not importable: {_PROTOCOL_IMPORT_ERROR}\n"
            "This test requires Mood enum to verify NEUTRAL packet."
        )


# ── Test infrastructure (imported from helpers — M6 dedup) ────────────────────

def _make_both_fail_frame():
    """
    Create a SensorFrame with both sensors failing.
    Handles both stub (no ok-fields) and contract-compliant SensorFrame.
    """
    try:
        return SensorFrame(
            audio_rms=0.0,            # zeroed per contract when mic_ok=False
            audio_pitch_variance=0.0, # zeroed per contract when mic_ok=False
            imu_acceleration=0.0,     # zeroed per contract when imu_ok=False
            imu_rotation=0.0,         # zeroed per contract when imu_ok=False
            mic_ok=False,
            imu_ok=False,
        )
    except TypeError:
        # Stub SensorFrame (Week 1) — missing ok-fields; test will fail at run()
        return SensorFrame(
            audio_rms=0.0,
            audio_pitch_variance=0.0,
            imu_acceleration=0.0,
            imu_rotation=0.0,
        )


# ── Test ──────────────────────────────────────────────────────────────────────

class TestBothSensorsFallback(unittest.TestCase):

    def test_both_sensors_fail_sends_neutral_after_10s(self) -> None:
        """
        ARD §5.4 — Both-Sensors-Fail Fallback (contract §2.5).

        Drive main loop with frames where both mic_ok=False and imu_ok=False
        for >10s of simulated time.

        Assert:
        1. A NEUTRAL packet is sent after >10s of total both-fail duration.
        2. compute_mood() is NOT called (both-fail is a direct bypass path).
        3. The NEUTRAL packet's mood byte is 0x00 (Mood.NEUTRAL).
        4. The timer re-arms — exactly 1 send in the first 15 frames.

        Seam: run(transport, sensor_stream, *, clock=...) — injectable clock.
        """
        transport = FakeTransport()
        both_fail_frame = _make_both_fail_frame()

        # 15 frames × 1.0s/call:
        #   frame 0: both_fail_start = 1.0 (set first time)
        #   frame 11: tick_start=12.0, delta=11.0 > 10.0 → SEND NEUTRAL
        #   frames 12–14: delta ≤ 3.0 (timer re-armed at 12.0), no second send
        frames = [both_fail_frame] * 15
        stream = FakeSensorStream(frames)
        fake_clock = FakeClock(step=1.0)

        compute_mood_call_count = [0]

        async def _drive() -> None:
            # Patch compute_mood to detect any accidental calls.
            # If host.main doesn't import compute_mood yet, the patch is a no-op.
            try:
                with unittest.mock.patch(
                    "host.main.compute_mood",
                    side_effect=lambda *a, **kw: (_ for _ in ()).throw(
                        AssertionError(
                            "compute_mood MUST NOT be called in the both-sensors-fail path "
                            "(contract §2.5: both_fail → continue before inference)"
                        )
                    )
                ):
                    try:
                        await run(transport, stream, clock=fake_clock, sleep=noop_sleep)
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
            except AttributeError:
                # host.main doesn't have compute_mood yet — run without patch
                try:
                    await run(transport, stream, clock=fake_clock, sleep=noop_sleep)
                except TypeError as e:
                    pytest.fail(
                        f"host.main.run() does not accept Week-2 signature: {e}"
                    )
                except NotImplementedError as e:
                    pytest.fail(f"Week-2 implementation incomplete: {e}")

        asyncio.run(_drive())

        # ── Assert 1: At least one send after >10s of both-fail ───────────────
        assert len(transport.sent) >= 1, (
            f"After {_FAIL_TIMEOUT_S}s of both-sensor failure, run() must send "
            f"a NEUTRAL packet. transport.sent is empty — fallback logic missing. "
            f"(contract §2.5, ARD §5.4)"
        )

        # ── Assert 4: Timer re-arms — exactly 1 send in 15 frames ────────────
        assert len(transport.sent) == 1, (
            f"Expected exactly 1 NEUTRAL send in first 15 both-fail frames; "
            f"got {len(transport.sent)}. Timer must re-arm after each send."
        )

        # ── Assert 3: The sent packet is NEUTRAL ─────────────────────────────
        sent_bytes = transport.sent[0]
        assert len(sent_bytes) == 6, (
            f"Fallback NEUTRAL packet must be 6-byte FAMILIAR_UPDATE; "
            f"got {len(sent_bytes)} bytes."
        )
        assert sent_bytes[0] == 0x80, (
            f"Fallback packet opcode must be 0x80 (FAMILIAR_UPDATE); "
            f"got 0x{sent_bytes[0]:02x}."
        )
        mood_byte = sent_bytes[1]
        assert mood_byte == 0, (  # Mood.NEUTRAL = 0
            f"Both-sensors-fail fallback must send NEUTRAL (mood_byte=0); "
            f"got mood_byte={mood_byte}. "
            f"compute_mood() must NOT be used for this value — "
            f"with both sensors failing, compute_mood result is meaningless. "
            f"(contract §2.5: 'Do NOT call compute_mood() when both sensors fail')"
        )


if __name__ == "__main__":
    unittest.main()
