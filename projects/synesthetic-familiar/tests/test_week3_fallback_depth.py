"""
Week 3 fallback-depth tests — Juanita Wave 2 (2026-06-13).

Deepens graceful-fallback verification beyond the existing both-fail and
confidence-hold smoke tests.  Covers:
  1. Exact timeout boundaries (strictly-greater-than semantics).
  2. Recovery: host leaves fallback state when a good sensor frame arrives.
  3. FAMILIAR_RESET arriving *during* an active both-fail state.

ARD references: §5.4 (both-fail 10 s, confidence-hold 30 s), §5.2 (RESET).
Contracts: §2.4 (I2 confidence-hold), §2.5 (both-fail), JUANITA-T2-5 (RESET).

All tests must PASS against current code.  Any xfail below is marked with a
reason that names the responsible owner.
"""
from __future__ import annotations

import asyncio
from typing import Callable

import pytest

# ── Import guards ─────────────────────────────────────────────────────────────
try:
    from host.main import run, BOTH_FAIL_TIMEOUT_S, CONFIDENCE_HOLD_TIMEOUT_S
    _RUN_IMPORT_ERROR: str | None = None
except ImportError as _e:
    _RUN_IMPORT_ERROR = str(_e)
    run = None  # type: ignore[assignment]
    BOTH_FAIL_TIMEOUT_S = 10.0
    CONFIDENCE_HOLD_TIMEOUT_S = 30.0

try:
    from host.sensors import SensorFrame
    _SENSORS_IMPORT_ERROR: str | None = None
except ImportError as _e:
    _SENSORS_IMPORT_ERROR = str(_e)
    SensorFrame = None  # type: ignore[assignment]

from helpers import FakeTransport, FakeClock, FakeSensorStream, noop_sleep


@pytest.fixture(autouse=True)
def _require_run_and_sensors() -> None:
    if _RUN_IMPORT_ERROR:
        pytest.fail(f"host.main.run not importable: {_RUN_IMPORT_ERROR}")
    if _SENSORS_IMPORT_ERROR:
        pytest.fail(f"host.sensors.SensorFrame not importable: {_SENSORS_IMPORT_ERROR}")


# ── Frame factories ───────────────────────────────────────────────────────────

def _both_fail_frame() -> "SensorFrame":
    """Both sensors down; zeroed signal per contract §1.1."""
    return SensorFrame(
        audio_rms=0.0, audio_pitch_variance=0.0,
        imu_acceleration=0.0, imu_rotation=0.0,
        mic_ok=False, imu_ok=False,
    )


def _gated_frame() -> "SensorFrame":
    """Mic fails → confidence *= 0.6 → max 0.6 < CONFIDENCE_GATE(0.7) → gated."""
    return SensorFrame(
        audio_rms=0.5, audio_pitch_variance=0.5,
        imu_acceleration=0.5, imu_rotation=0.5,
        mic_ok=False, imu_ok=True,
    )


def _stressed_ungated_frame() -> "SensorFrame":
    """High tension (1.0 > STRESS_THRESHOLD 0.65), both sensors ok → confidence=0.8 → not gated."""
    return SensorFrame(
        audio_rms=0.5, audio_pitch_variance=1.0,
        imu_acceleration=1.0, imu_rotation=1.0,
        mic_ok=True, imu_ok=True,
    )


def _run(transport, stream, *, step: float = 1.0) -> None:
    asyncio.run(run(
        transport, stream,
        clock=FakeClock(step=step),
        sleep=noop_sleep,
        baseline=None,
    ))


# ── Helper: transport + stream that fires FAMILIAR_RESET mid-both-fail ────────

class _CaptureCallbackTransport(FakeTransport):
    """FakeTransport that also stores the on_receive callback in a shared list."""

    def __init__(self, recv_cb_ref: list) -> None:
        super().__init__()
        self._recv_cb_ref = recv_cb_ref

    def on_receive(self, callback: Callable) -> None:
        super().on_receive(callback)
        self._recv_cb_ref[0] = callback


class _ResetCallbackStream:
    """
    Sensor stream that fires a FAMILIAR_RESET callback after yielding the
    `reset_at`'th frame (0-indexed: fires when self._idx first equals reset_at).

    The callback is looked up lazily from `recv_cb_ref` (set by
    _CaptureCallbackTransport.on_receive before the loop starts), so the
    transport registration order is irrelevant.
    """

    def __init__(
        self,
        frames: list,
        *,
        reset_at: int,
        recv_cb_ref: list,
    ) -> None:
        self._frames = frames
        self._reset_at = reset_at
        self._recv_cb_ref = recv_cb_ref
        self._idx = 0

    async def start(self) -> None:
        self._idx = 0

    async def stop(self) -> None:
        pass

    def __aiter__(self) -> "_ResetCallbackStream":
        return self

    async def __anext__(self) -> "SensorFrame":
        if self._idx >= len(self._frames):
            raise StopAsyncIteration
        frame = self._frames[self._idx]
        self._idx += 1
        # Fire RESET after advancing idx (i.e., after the Nth frame is yielded).
        # run() receives the frame, then checks _reset_flag immediately — the
        # callback fires BEFORE run() processes this frame.
        if self._idx == self._reset_at and self._recv_cb_ref[0] is not None:
            self._recv_cb_ref[0](bytes([0x01]))  # opcode 0x01 = FAMILIAR_RESET
        return frame


# ═════════════════════════════════════════════════════════════════════════════
# 1. Both-fail exact boundary (strictly > 10 s)
# ═════════════════════════════════════════════════════════════════════════════

class TestBothFailExactBoundary:
    """
    The both-fail condition fires at delta > BOTH_FAIL_TIMEOUT_S (strict).

    FakeClock(step=1.0): both_fail_start is set at frame 0 (tick=1.0).
      Frame 10: delta = 11.0 - 1.0 = 10.0  → NOT > 10.0 → no send.
      Frame 11: delta = 12.0 - 1.0 = 11.0  →  IS > 10.0 → NEUTRAL sent.
    """

    def test_at_exactly_10s_does_not_fire(self) -> None:
        """
        11 both-fail frames: last frame has delta exactly 10.0.
        Strictly-greater-than semantics → no NEUTRAL sent.
        """
        transport = FakeTransport()
        stream = FakeSensorStream([_both_fail_frame()] * 11)
        _run(transport, stream)
        assert len(transport.sent) == 0, (
            f"At delta=={BOTH_FAIL_TIMEOUT_S}s exactly, both-fail MUST NOT fire "
            f"(condition is strictly >, not >=). Got {len(transport.sent)} sends. "
            "ARD §5.4 / contract §2.5."
        )

    def test_just_after_10s_fires_neutral(self) -> None:
        """
        12 both-fail frames: frame 11 has delta = 11.0 > 10.0 → NEUTRAL sent.
        Mirrors the existing smoke test but explicitly names the boundary frame.
        """
        transport = FakeTransport()
        stream = FakeSensorStream([_both_fail_frame()] * 12)
        _run(transport, stream)
        assert len(transport.sent) == 1, (
            f"At delta > {BOTH_FAIL_TIMEOUT_S}s, exactly one NEUTRAL must be sent "
            f"(timer re-arms after each send). Got {len(transport.sent)} sends."
        )
        assert transport.sent[0][1] == 0, (
            f"Both-fail NEUTRAL must have mood byte 0 (NEUTRAL); "
            f"got {transport.sent[0][1]}."
        )


# ═════════════════════════════════════════════════════════════════════════════
# 2. Confidence-hold exact boundary (strictly > 30 s)
# ═════════════════════════════════════════════════════════════════════════════

class TestConfidenceHoldExactBoundary:
    """
    The confidence-hold fires at delta > CONFIDENCE_HOLD_TIMEOUT_S (strict).

    FakeClock(step=1.0): last_send_time initialised at t=0.0.
      Frame 29: tick=30.0, delta=30.0 → NOT > 30.0 → no send.
      Frame 30: tick=31.0, delta=31.0 →  IS > 30.0 → send.
    """

    def test_at_exactly_30s_does_not_fire(self) -> None:
        """
        30 gated frames: last frame tick=30.0, delta=30.0 — hold must NOT fire.
        """
        transport = FakeTransport()
        stream = FakeSensorStream([_gated_frame()] * 30)
        _run(transport, stream)
        assert len(transport.sent) == 0, (
            f"At delta=={CONFIDENCE_HOLD_TIMEOUT_S}s exactly, confidence-hold must NOT fire "
            f"(condition is strictly >). Got {len(transport.sent)} sends. "
            "I2 / contract §2.4."
        )

    def test_just_after_30s_fires_send(self) -> None:
        """
        31 gated frames: frame 30 has delta=31.0 > 30.0 → exactly one send.
        """
        transport = FakeTransport()
        stream = FakeSensorStream([_gated_frame()] * 31)
        _run(transport, stream)
        assert len(transport.sent) == 1, (
            f"At delta > {CONFIDENCE_HOLD_TIMEOUT_S}s, exactly one send (the stuck-creature "
            f"release). Timer must re-arm. Got {len(transport.sent)} sends."
        )
        assert len(transport.sent[0]) == 6, "Hold-release packet must be 6-byte FAMILIAR_UPDATE."
        assert transport.sent[0][0] == 0x80, "Hold-release opcode must be 0x80."


# ═════════════════════════════════════════════════════════════════════════════
# 3. Recovery after fallback
# ═════════════════════════════════════════════════════════════════════════════

class TestFallbackRecovery:
    """
    After a fallback fires, a good sensor frame must resume normal inference.

    Recovery contracts:
      - After both-fail timeout: both_fail_start is re-armed; a subsequent
        good frame clears it and goes through inference normally.
      - After confidence-hold: last_send_time is reset; a subsequent
        non-gated frame sends via the normal path.
    """

    def test_good_frame_after_both_fail_sends_inference_result(self) -> None:
        """
        12 both-fail frames (NEUTRAL sent at frame 11), then 1 stressed-ungated frame.

        Assert:
          - 2 total sends (1 fallback NEUTRAL + 1 inference result).
          - First packet is NEUTRAL (mood=0).
          - Second packet is NOT NEUTRAL (stressed inference result).
        """
        transport = FakeTransport()
        # 12 both-fail → NEUTRAL at frame 11; then stressed → inference send
        frames = [_both_fail_frame()] * 12 + [_stressed_ungated_frame()]
        stream = FakeSensorStream(frames)
        _run(transport, stream)

        assert len(transport.sent) == 2, (
            f"Expected 2 sends (fallback NEUTRAL + inference send); "
            f"got {len(transport.sent)}. "
            "A good frame after both-fail must resume normal inference."
        )
        assert transport.sent[0][1] == 0, (
            "First send must be the fallback NEUTRAL (mood byte=0)."
        )
        # stressed mood_int = 2; jitter on a stressed packet won't make mood byte 0
        assert transport.sent[1][1] != 0, (
            f"Second send (after recovery) must reflect inference (stressed=2), "
            f"not NEUTRAL. mood byte={transport.sent[1][1]}."
        )

    def test_good_frame_after_confidence_hold_sends_again(self) -> None:
        """
        30 gated frames (hold fires at frame 30), then 1 stressed-ungated frame.

        Assert:
          - 2 total sends (1 hold-release + 1 normal inference).
          - Both are valid 6-byte FAMILIAR_UPDATE packets.
        """
        transport = FakeTransport()
        # 31 gated frames → hold fires at frame 30; then stressed-ungated → normal send
        frames = [_gated_frame()] * 31 + [_stressed_ungated_frame()]
        stream = FakeSensorStream(frames)
        _run(transport, stream)

        assert len(transport.sent) == 2, (
            f"Expected 2 sends (hold-release + recovery inference); "
            f"got {len(transport.sent)}. "
            "A good frame after confidence-hold must send via normal path."
        )
        for i, pkt in enumerate(transport.sent):
            assert len(pkt) == 6, (
                f"Packet {i} must be 6-byte FAMILIAR_UPDATE; got {len(pkt)} bytes."
            )
            assert pkt[0] == 0x80, (
                f"Packet {i} opcode must be 0x80; got 0x{pkt[0]:02x}."
            )

    def test_both_fail_timer_clears_on_good_frame(self) -> None:
        """
        Regression guard: both_fail_start resets when a good frame arrives.

        Scenario: 8 both-fail frames (timer starts, 7.0 s elapsed — not fired),
        then 2 good frames (timer cleared), then 9 more both-fail frames
        (timer restarts from scratch — new elapsed = 9.0 s, < 10.0 s, no fire).

        Total sends must be 2 (the 2 stressed-frame inference sends), NOT 3
        (which would indicate the timer carried over across the good frames).
        """
        transport = FakeTransport()
        frames = (
            [_both_fail_frame()] * 8
            + [_stressed_ungated_frame()] * 2
            + [_both_fail_frame()] * 9
        )
        stream = FakeSensorStream(frames)
        _run(transport, stream)

        assert len(transport.sent) == 2, (
            f"Expected 2 sends (2 stressed inference frames); got {len(transport.sent)}. "
            "If both_fail_start carries over across good frames, the timer would fire "
            "prematurely on the second both-fail block (regression: §2.5 timer must reset)."
        )


# ═════════════════════════════════════════════════════════════════════════════
# 4. FAMILIAR_RESET arriving during an active both-fail state
# ═════════════════════════════════════════════════════════════════════════════

class TestResetDuringFallback:
    """
    FAMILIAR_RESET arrives while the both-fail timer is running (< 10 s elapsed).

    Expected behaviour (ARD §5.2 + §5.4):
      - Host sends NEUTRAL (the RESET reaction, NOT the both-fail timeout).
      - The both-fail timer is explicitly cleared in the RESET handler
        (both_fail_start = None).  Subsequent both-fail frames restart from
        scratch rather than inheriting the pre-reset elapsed time.

    Uses _ResetCallbackStream to inject the FAMILIAR_RESET opcode via the
    on_receive transport callback after the Nth both-fail frame is yielded.
    """

    def test_reset_during_both_fail_sends_neutral_once(self) -> None:
        """
        8 both-fail frames; FAMILIAR_RESET fires after frame 3.

        FakeClock timing:
          Frame 0: both_fail_start = 1.0
          Frame 2: yields frame, then RESET fires → _reset_flag=True.
          Frame 2 (run loop): _reset_flag → send NEUTRAL (reset reaction).
          both_fail_start = None (cleared by reset handler).
          Frames 3–7: both_fail_start restarts at frame 3 (tick=4.0).
          By end: delta = 8.0 - 4.0 = 4.0 < 10.0 → no timeout fire.

        Assert: exactly 1 send (from RESET, not from timeout).
        """
        recv_cb_ref: list = [None]
        transport = _CaptureCallbackTransport(recv_cb_ref)
        stream = _ResetCallbackStream(
            [_both_fail_frame()] * 8,
            reset_at=3,  # fires after yielding frame 2 (0-indexed)
            recv_cb_ref=recv_cb_ref,
        )
        _run(transport, stream)

        assert len(transport.sent) == 1, (
            f"Expected exactly 1 send (RESET-reaction NEUTRAL); "
            f"got {len(transport.sent)}. "
            "FAMILIAR_RESET must fire before the 10 s both-fail timeout; "
            "sending extra packets indicates the timeout also fired (timer not cleared)."
        )
        assert transport.sent[0][1] == 0, (
            f"RESET reaction must send NEUTRAL (mood byte=0); "
            f"got mood byte={transport.sent[0][1]}."
        )

    def test_reset_clears_both_fail_timer_prevents_double_fire(self) -> None:
        """
        Both-fail timer at t=9.0 (one tick before timeout) when RESET arrives.

        Construction: 10 both-fail frames (timer at 9.0 s when RESET fires at frame 9),
        then 3 more both-fail frames (restarted timer at 1.0 s, no timeout).

        If the timer were NOT cleared, the next both-fail frame after RESET would
        fire a second NEUTRAL (delta would be 10.0 or 11.0).  With the timer cleared
        correctly, only the RESET reaction NEUTRAL is sent.

        FakeClock timing:
          Frame 0: both_fail_start = 1.0.
          Frames 0–8: both-fail, delta growing to 9.0 (no fire).
          Frame 9 (__anext__): RESET fires → _reset_flag=True; run() handles reset,
            sends NEUTRAL, both_fail_start = None.
          Frames 10–12: both_fail_start restarts (frame 10 tick=11.0).
            By end: delta = 13.0 - 11.0 = 2.0 < 10.0 → no timeout.

        Assert: 1 send total.
        """
        recv_cb_ref: list = [None]
        transport = _CaptureCallbackTransport(recv_cb_ref)
        # 10 frames before reset fires (idx=10 means after yielding frame index 9)
        stream = _ResetCallbackStream(
            [_both_fail_frame()] * 13,
            reset_at=10,
            recv_cb_ref=recv_cb_ref,
        )
        _run(transport, stream)

        assert len(transport.sent) == 1, (
            f"Expected 1 send (RESET reaction NEUTRAL only); got {len(transport.sent)}. "
            "If the both-fail timer is not cleared on RESET, the timer fires a second "
            "NEUTRAL as soon as delta crosses 10 s — a protocol violation (ARD §5.4/§5.2)."
        )
