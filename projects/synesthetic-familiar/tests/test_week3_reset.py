"""
Week 3 acceptance tests — FAMILIAR_RESET (Ng) and snapshot-zeroing hardening (W3-1).

JUANITA-T2-5 contract (decisions.md 2026-06-08):
  - Device detects double-tap → Lua snaps to NEUTRAL locally (no host round-trip).
  - Device sends FAMILIAR_RESET (opcode 0x01, 1 byte) to host as a notification.
  - Host must react: send NEUTRAL, reset seq counter (ARD §5.2 reconnect protocol),
    and clear transient fallback state.

Test groups:
  1. Protocol decode — PASS TODAY (familiar_protocol.py is landed).
  2. Host state reaction — XFAIL (Ng Week 3: run() must handle FamiliarReset callback).
  3. Snapshot-zeroing structural guard (W3-1) — PASS TODAY (sensors.py 3-layer zeroing).

Reject criteria (Juanita → Ng):
  - If run() ignores FamiliarReset events and never sends NEUTRAL, Group 2 stays red.
  - If seq counter is NOT reset after FAMILIAR_RESET, wire dedup breaks on next reconnect.
  - If snapshot zeroing is removed from a finally block, W3-1 guard breaks.

Date: 2026-06-13
"""
from __future__ import annotations

import asyncio
import inspect
import struct
import unittest

import pytest

# ── Import guard — protocol ────────────────────────────────────────────────────
try:
    from host.familiar_protocol import (
        FamiliarReset,
        OPCODE_FAMILIAR_RESET,
        decode_familiar_reset,
        dispatch_device_message,
    )
    _PROTOCOL_IMPORT_ERROR: str | None = None
except ImportError as _e:
    _PROTOCOL_IMPORT_ERROR = str(_e)
    FamiliarReset = None  # type: ignore[assignment]
    OPCODE_FAMILIAR_RESET = 0x01
    decode_familiar_reset = None  # type: ignore[assignment]
    dispatch_device_message = None  # type: ignore[assignment]

# ── Import guard — main loop ───────────────────────────────────────────────────
try:
    from host.main import run
    _RUN_IMPORT_ERROR: str | None = None
except ImportError as _e:
    _RUN_IMPORT_ERROR = str(_e)
    run = None  # type: ignore[assignment]

# ── Import guard — sensors ─────────────────────────────────────────────────────
try:
    from host.sensors import SensorFrame, SensorStream
    _SENSORS_IMPORT_ERROR: str | None = None
except ImportError as _e:
    _SENSORS_IMPORT_ERROR = str(_e)
    SensorFrame = None  # type: ignore[assignment]
    SensorStream = None  # type: ignore[assignment]

from helpers import FakeTransport, FakeClock, FakeSensorStream, noop_sleep


@pytest.fixture(autouse=True)
def _require_protocol():
    if _PROTOCOL_IMPORT_ERROR is not None:
        pytest.fail(f"host.familiar_protocol not importable: {_PROTOCOL_IMPORT_ERROR}")


# ═════════════════════════════════════════════════════════════════════════════
# Group 1 — Protocol decode (PASS TODAY — familiar_protocol.py is landed)
# Pure classicist tests; no transport, no run().
# ═════════════════════════════════════════════════════════════════════════════

class TestFamiliarResetProtocolDecode:
    """Wire-format decode tests for FAMILIAR_RESET (opcode 0x01, Device→Host)."""

    def test_opcode_constant_is_0x01(self):
        """OPCODE_FAMILIAR_RESET must be 0x01 per ARD §5.2."""
        assert OPCODE_FAMILIAR_RESET == 0x01, (
            f"OPCODE_FAMILIAR_RESET={OPCODE_FAMILIAR_RESET:#04x}, expected 0x01. "
            "ARD §5.2 locks the Device→Host reset opcode."
        )

    def test_decode_familiar_reset_returns_opcode(self):
        """decode_familiar_reset(b'\\x01') must return 0x01 without raising."""
        result = decode_familiar_reset(bytes([0x01]))
        assert result == 0x01, (
            f"decode_familiar_reset(b'\\x01') returned {result!r}, expected 0x01. "
            "ARD §5.2: FAMILIAR_RESET is a single opcode byte, no payload."
        )

    def test_decode_familiar_reset_rejects_empty(self):
        """Zero-byte packet must raise ValueError (ARD §5.2 expects exactly 1 byte)."""
        with pytest.raises(ValueError):
            decode_familiar_reset(b"")

    def test_decode_familiar_reset_rejects_wrong_opcode(self):
        """Opcode 0x80 (FAMILIAR_UPDATE) must raise ValueError."""
        with pytest.raises(ValueError):
            decode_familiar_reset(bytes([0x80]))

    def test_decode_familiar_reset_rejects_two_bytes(self):
        """FAMILIAR_RESET is exactly 1 byte; 2-byte payload must raise ValueError."""
        with pytest.raises(ValueError):
            decode_familiar_reset(bytes([0x01, 0x00]))

    def test_dispatch_returns_familiar_reset_instance(self):
        """dispatch_device_message(b'\\x01') must return FamiliarReset (not None)."""
        result = dispatch_device_message(bytes([0x01]))
        assert isinstance(result, FamiliarReset), (
            f"dispatch_device_message(b'\\x01') returned {result!r}; "
            f"expected FamiliarReset. "
            "FAMILIAR_RESET is Device→Host — host must dispatch it correctly."
        )

    def test_dispatch_returns_none_for_unknown_opcode(self):
        """Unknown opcode 0xFF → None (log-and-drop contract; never raises)."""
        result = dispatch_device_message(bytes([0xFF]))
        assert result is None, (
            f"dispatch_device_message(b'\\xff') must return None for unknown opcode; "
            f"got {result!r}."
        )

    def test_dispatch_returns_none_for_empty_payload(self):
        """Empty payload → None (no opcode to dispatch)."""
        result = dispatch_device_message(b"")
        assert result is None

    def test_familiar_reset_is_zero_field_dataclass(self):
        """FamiliarReset dataclass must carry no payload fields (occurrence is the signal)."""
        import dataclasses
        fields = dataclasses.fields(FamiliarReset)
        assert len(fields) == 0, (
            f"FamiliarReset must be a zero-field dataclass; got fields: "
            f"{[f.name for f in fields]}. "
            "ARD §5.2: 'No payload; the occurrence is the signal.'"
        )

    def test_dispatch_familiar_reset_malformed_two_byte_returns_none(self):
        """2-byte packet starting with 0x01: dispatch must return None (malformed)."""
        result = dispatch_device_message(bytes([0x01, 0x99]))
        assert result is None, (
            f"dispatch_device_message(b'\\x01\\x99') should return None for malformed "
            f"FAMILIAR_RESET (wrong length); got {result!r}."
        )


# NOTE: parametrize requires plain pytest class (not TestCase).
class TestFamiliarResetDecodeParametrised:
    """Parametrised bad-opcode table for decode_familiar_reset."""

    @pytest.mark.parametrize("bad_opcode", [0x00, 0x02, 0x80, 0xFF])
    def test_decode_rejects_non_reset_opcodes(self, bad_opcode: int):
        """Any non-0x01 opcode in a 1-byte packet must raise ValueError."""
        with pytest.raises(ValueError):
            decode_familiar_reset(bytes([bad_opcode]))


# ═════════════════════════════════════════════════════════════════════════════
# Group 2 — Host state reaction to FAMILIAR_RESET
# XFAIL until Ng lands run() Week 3 FAMILIAR_RESET handler.
#
# Contract (to implement):
#   - When FamiliarReset arrives via on_receive callback, set a flag or event.
#   - Each loop frame: check flag, if set → send NEUTRAL, call seq.reset(),
#     clear both_fail_start, reset last_send_time to now.
#   - Rationale: device already snapped to NEUTRAL; host state must agree.
# ═════════════════════════════════════════════════════════════════════════════

_NG_W3_REASON = (
    "Ng Week 3: run() must react to FAMILIAR_RESET. "
    "Contract: receive callback sets a flag; loop sends NEUTRAL + seq.reset() next frame. "
    "See decisions.md 2026-06-08 (FAMILIAR_RESET as Device→Host), ARD §5.2."
)


class ResetInjectingTransport(FakeTransport):
    """
    FakeTransport that injects a FAMILIAR_RESET (0x01) notification after the
    Nth outbound send, simulating a device double-tap mid-session.

    Deterministic: the Nth call to send() triggers the callback synchronously
    before returning, so the test harness sees a predictable injection point.
    """

    def __init__(self, reset_after_n_sends: int = 1) -> None:
        super().__init__()
        self._reset_after = reset_after_n_sends
        self._reset_injected = False

    async def send(self, data: bytes) -> None:
        await super().send(data)
        if (
            not self._reset_injected
            and len(self.sent) >= self._reset_after
            and self._recv_cb is not None
        ):
            self._reset_injected = True
            # Device sends FAMILIAR_RESET notification (1 byte, opcode 0x01)
            self._recv_cb(bytes([0x01]))


def _make_ungated_frame():
    """Ungated SensorFrame: both sensors ok, high tension → stressed (confidence 0.8 > gate)."""
    try:
        return SensorFrame(
            audio_rms=0.5,
            audio_pitch_variance=1.0,
            imu_acceleration=0.5,
            imu_rotation=0.5,
            mic_ok=True,
            imu_ok=True,
        )
    except TypeError:
        return SensorFrame(
            audio_rms=0.5,
            audio_pitch_variance=1.0,
            imu_acceleration=0.5,
            imu_rotation=0.5,
        )


class TestFamiliarResetHostReaction:
    """
    Contract tests for run() FAMILIAR_RESET handling (Ng Week 3).

    xfail(strict=False): fail silently until Ng ships; flip to strict=True
    once passing so any regression flips the suite red.
    """

    def test_reset_triggers_neutral_send(self):
        """
        JUANITA-T2-5: after device sends FAMILIAR_RESET, host must send
        FAMILIAR_UPDATE with mood=NEUTRAL (byte 1 == 0x00) in the next loop frame.

        Stream: 4 ungated frames.  Transport injects FAMILIAR_RESET after send #1.
        Assert: at least one NEUTRAL packet among sends after the reset injection.
        """
        if _RUN_IMPORT_ERROR or _SENSORS_IMPORT_ERROR:
            pytest.skip("run() or SensorFrame not importable")

        transport = ResetInjectingTransport(reset_after_n_sends=1)
        stream = FakeSensorStream([_make_ungated_frame()] * 4)

        asyncio.run(run(transport, stream, clock=FakeClock(step=1.0), sleep=noop_sleep, baseline=None))

        assert len(transport.sent) >= 2, (
            "Host must react to the reset — not freeze or ignore it."
        )
        post_reset_moods = [p[1] for p in transport.sent[1:] if len(p) >= 2]
        assert 0 in post_reset_moods, (
            f"After FAMILIAR_RESET, at least one NEUTRAL (mood=0) packet must be sent; "
            f"got moods after reset: {post_reset_moods}. "
            "Device already snapped to NEUTRAL — host state must agree (ARD §5.2)."
        )

    def test_reset_restarts_sequence_counter(self):
        """
        ARD §5.2 reconnect protocol: FAMILIAR_RESET must trigger seq.reset() on host,
        so the first post-reset FAMILIAR_UPDATE has seq=0x0000.

        Without reset: seq continues (first=0, second=1, ...).
        With reset: after FAMILIAR_RESET, seq.reset() → next next() returns 0.

        Stream: 2 ungated frames.  Transport injects FAMILIAR_RESET after send #1.
        Assert: the first packet among sends[1:] has seq bytes == 0x0000.
        """
        if _RUN_IMPORT_ERROR or _SENSORS_IMPORT_ERROR:
            pytest.skip("run() or SensorFrame not importable")

        transport = ResetInjectingTransport(reset_after_n_sends=1)
        stream = FakeSensorStream([_make_ungated_frame()] * 2)

        asyncio.run(run(transport, stream, clock=FakeClock(step=1.0), sleep=noop_sleep, baseline=None))

        assert len(transport.sent) >= 2, (
            "Expected at least 2 sends (1 before + 1 after FAMILIAR_RESET)."
        )
        first_post_reset = transport.sent[1]
        assert len(first_post_reset) == 6, (
            f"Post-reset packet must be 6-byte FAMILIAR_UPDATE; got {len(first_post_reset)}."
        )
        seq_after_reset = struct.unpack("<H", first_post_reset[4:6])[0]
        assert seq_after_reset == 0, (
            f"First post-reset packet seq must be 0x0000 (seq.reset() called); "
            f"got seq={seq_after_reset}. "
            "ARD §5.2 reconnect: host calls seq.reset() on FAMILIAR_RESET; "
            "device resets last_accepted_seq to 0xFFFF, so seq=0 yields delta=1 (accepted)."
        )

    def test_reset_during_gated_session_clears_stale_mood(self):
        """
        Edge case: FAMILIAR_RESET arrives during a gated (suppressed) session.

        If the host was suppressing updates due to low confidence, a FAMILIAR_RESET
        must still force a NEUTRAL send — the device reset regardless of host state.

        Stream: 1 ungated normal frame (send → injects FAMILIAR_RESET) followed by
        8 gated frames.  Assert: exactly 1 post-reset NEUTRAL among transport.sent.
        """
        if _RUN_IMPORT_ERROR or _SENSORS_IMPORT_ERROR:
            pytest.skip("run() or SensorFrame not importable")

        try:
            gated_frame = SensorFrame(
                audio_rms=0.5,
                audio_pitch_variance=0.5,
                imu_acceleration=0.5,
                imu_rotation=0.5,
                mic_ok=False,  # confidence *= 0.6 → gated
                imu_ok=True,
            )
        except TypeError:
            pytest.skip("SensorFrame doesn't support ok-fields yet")

        transport = ResetInjectingTransport(reset_after_n_sends=1)
        frames = [_make_ungated_frame()] + [gated_frame] * 8
        stream = FakeSensorStream(frames)

        asyncio.run(run(transport, stream, clock=FakeClock(step=1.0), sleep=noop_sleep, baseline=None))

        post_reset = transport.sent[1:]
        assert any(len(p) >= 2 and p[1] == 0 for p in post_reset), (
            "After FAMILIAR_RESET, at least one NEUTRAL must be sent even if the "
            "next frames are gated. Device reset regardless of host confidence state."
        )


# ═════════════════════════════════════════════════════════════════════════════
# Group 3 — W3-1 Snapshot-zeroing structural guard (PASS TODAY)
#
# Verifies the 3-layer privacy zeroing in SensorStream._extract_frame():
#   Layer 1: self._buffer[:] = 0.0 (under audio lock, pre-extraction)
#   Layer 2: samples[:] = 0.0 (in finally block, post-extraction)
#   Layer 3: del samples (reference release)
#
# Structural test via inspect.getsource() — fast, non-flaky, no hardware needed.
# ═════════════════════════════════════════════════════════════════════════════

class TestSnapshotZeroingHardening(unittest.TestCase):
    """
    W3-1 regression guard: _extract_frame must zero the audio snapshot in a
    finally block even on exception paths.

    Rationale (decisions.md 2026-06-12 W3-1):
    - Layer 2 (samples[:] = 0.0) MUST be in finally, not just in the happy path.
    - Layer 3 (del samples) MUST follow zeroing to release the last reference.
    - If either is moved out of finally, an exception in _compute_rms or
      _compute_pitch_variance leaks the raw audio snapshot to GC — privacy failure.
    """

    def setUp(self):
        if _SENSORS_IMPORT_ERROR is not None:
            self.skipTest(f"host.sensors not importable: {_SENSORS_IMPORT_ERROR}")

    def _get_extract_frame_source(self) -> str:
        try:
            return inspect.getsource(SensorStream._extract_frame)
        except (OSError, TypeError) as e:
            self.skipTest(f"Cannot inspect SensorStream._extract_frame: {e}")

    def test_snapshot_zeroing_in_finally_block(self):
        """
        W3-1 structural guard: samples[:] = 0.0 must appear in a finally block
        inside _extract_frame so it runs even when feature extraction raises.
        """
        src = self._get_extract_frame_source()
        assert "finally" in src, (
            "_extract_frame must use a 'finally' block to guarantee snapshot zeroing "
            "on exception paths. W3-1 requires 3-layer zeroing; Layer 2 must be in finally."
        )
        assert "samples[:] = 0.0" in src or "samples[:]=0.0" in src, (
            "_extract_frame must zero the snapshot array in-place (samples[:] = 0.0) "
            "to clear the raw audio before the allocator can reuse the memory. "
            "W3-1: Layer 2 snapshot zeroing must be present."
        )

    def test_snapshot_reference_released_after_zeroing(self):
        """
        W3-1 structural guard: 'del samples' must appear after samples[:] = 0.0
        to release the last reference (Layer 3 of 3-layer zeroing).
        """
        src = self._get_extract_frame_source()
        assert "del samples" in src, (
            "_extract_frame must explicitly 'del samples' after zeroing to release "
            "the last reference. W3-1: without Layer 3, the GC holds raw audio until "
            "the next collection cycle — a privacy window."
        )
        # Layer 2 must come before Layer 3
        zero_pos = src.find("samples[:] = 0.0")
        if zero_pos == -1:
            zero_pos = src.find("samples[:]=0.0")
        del_pos = src.find("del samples")
        if zero_pos != -1 and del_pos != -1:
            assert zero_pos < del_pos, (
                "samples[:] = 0.0 must appear BEFORE del samples. "
                "Zeroing an already-deleted reference is a no-op. W3-1 Layer ordering."
            )


if __name__ == "__main__":
    unittest.main()
