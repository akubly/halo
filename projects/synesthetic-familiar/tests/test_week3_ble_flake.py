"""
Week 3 BLE flake-tolerance tests — Juanita Wave 2 (2026-06-13).

BLE is inherently flaky.  These tests verify that the host survives the failure
modes that occur without real hardware:

  1. Garbled / unknown bytes from device → dispatch_device_message returns None,
     logs warning, does NOT raise.
  2. Extreme / NaN sensor float values → compute_mood does not raise or hang.
  3. Heap-guard observability gap → documented as a coverage gap for Ng.

Test philosophy (Juanita):
  - "Flake-recoverable" = host loop continues; tested with mock streams.
  - "Hard-fail" = exception propagates out of run(); currently expected
     only for unrecoverable transport errors (not tested here — SDK gap).
  - Hardware NOT required; all tests use FakeTransport / direct function calls.

Coverage gap (Ng):
  FAMILIAR_ACK carries only `last_received_seq` — no heap field.  The host has
  NO protocol-level visibility into device heap pressure.  If the device hits
  OOM, the host observes it only as a BLE silence (no more ACKs).  The existing
  both-fail fallback (10 s → NEUTRAL) is the only safety net at this layer.
  See TestHeapGuardObservability for the structural assertion.

  OWNER: Ng.  Fix: add a heap-status byte to FAMILIAR_ACK, or define a new
  DEVICE_STATUS message.  Until then, the gap is documented (not paper-over'd).
"""
from __future__ import annotations

import math
import unittest

import pytest

# ── Import guards ─────────────────────────────────────────────────────────────
try:
    from host.familiar_protocol import (
        dispatch_device_message,
        FamiliarAck,
        FamiliarReset,
        OPCODE_FAMILIAR_ACK,
        OPCODE_FAMILIAR_RESET,
    )
    _PROTOCOL_IMPORT_ERROR: str | None = None
except ImportError as _e:
    _PROTOCOL_IMPORT_ERROR = str(_e)
    dispatch_device_message = FamiliarAck = FamiliarReset = None  # type: ignore
    OPCODE_FAMILIAR_ACK = 0x02
    OPCODE_FAMILIAR_RESET = 0x01

try:
    from host.inference import compute_mood
    _INFERENCE_IMPORT_ERROR: str | None = None
except ImportError as _e:
    _INFERENCE_IMPORT_ERROR = str(_e)
    compute_mood = None  # type: ignore


@pytest.fixture(autouse=True)
def _require_protocol() -> None:
    if _PROTOCOL_IMPORT_ERROR:
        pytest.fail(f"host.familiar_protocol not importable: {_PROTOCOL_IMPORT_ERROR}")


# ═════════════════════════════════════════════════════════════════════════════
# 1. Garbled / unknown device messages — must not crash
# ═════════════════════════════════════════════════════════════════════════════

class TestGarbledDeviceMessages:
    """
    Device sends garbled bytes (lost bytes, bit-flip, or unknown opcode).

    Contract: dispatch_device_message() must NEVER raise — it logs a warning
    and returns None for any unrecognised input (ARD §5.2 "log-and-drop").

    These are the bytes the on_receive callback passes to dispatch_device_message
    in main.py's _make_device_msg_handler.  If dispatch raised, the callback
    would propagate the exception into the asyncio event loop.
    """

    @pytest.mark.parametrize("bad_bytes", [
        b"",                    # empty — no opcode at all
        bytes([0xFF]),          # unknown opcode
        bytes([0x7F]),          # unknown opcode (below 0x80)
        bytes([0x03]),          # unassigned opcode
        bytes([0x80]),          # FAMILIAR_UPDATE is Host→Device — reversed direction
        bytes([0x02, 0x00]),    # truncated FAMILIAR_ACK (needs 3 bytes: opcode + uint16)
        bytes([0x02, 0xAB, 0xCD, 0xEF]),  # over-length ACK
        bytes([0x01, 0xFF]),    # FAMILIAR_RESET with spurious extra byte → malformed
        bytes(100),             # large zeroed payload
        bytes(range(16)),       # arbitrary byte pattern
    ])
    def test_dispatch_does_not_raise(self, bad_bytes: bytes) -> None:
        """
        dispatch_device_message must return None without raising for any input.
        """
        try:
            result = dispatch_device_message(bad_bytes)
        except Exception as exc:  # noqa: BLE001
            pytest.fail(
                f"dispatch_device_message({bad_bytes.hex()!r}) raised "
                f"{type(exc).__name__}: {exc}. "
                "BLE flake: host must log-and-drop unknown/garbled packets, never crash."
            )
        assert result is None or isinstance(result, (FamiliarAck, FamiliarReset)), (
            f"dispatch_device_message must return None, FamiliarAck, or FamiliarReset; "
            f"got {type(result).__name__!r} for input {bad_bytes.hex()!r}."
        )

    def test_dispatch_unknown_opcode_returns_none(self) -> None:
        """Unknown opcodes must map to None — never raise, never fabricate a message."""
        for opcode in [0x00, 0x03, 0x7F, 0xFF]:
            result = dispatch_device_message(bytes([opcode]))
            assert result is None, (
                f"Unknown opcode 0x{opcode:02x}: expected None, got {result!r}."
            )

    def test_dispatch_valid_ack_still_works_after_garbled_sequence(self) -> None:
        """
        Host must recover and decode a valid FAMILIAR_ACK after seeing garbled bytes.

        Simulates: burst of bad frames, then a well-formed ACK.
        The host must decode the ACK correctly (not left in a broken state).
        """
        import struct
        # First pump some bad bytes through (no-op, should not corrupt state)
        for bad in [b"", bytes([0xFF]), bytes([0x00, 0x00])]:
            dispatch_device_message(bad)
        # Now a well-formed FAMILIAR_ACK: opcode 0x02 + last_seq uint16-LE = 0x0042
        good_ack = bytes([OPCODE_FAMILIAR_ACK]) + struct.pack("<H", 0x0042)
        result = dispatch_device_message(good_ack)
        assert isinstance(result, FamiliarAck), (
            f"After garbled bytes, valid FAMILIAR_ACK must decode correctly. "
            f"Got {result!r}."
        )
        assert result.last_received_seq == 0x0042, (
            f"FAMILIAR_ACK last_received_seq must be 0x0042; got {result.last_received_seq}."
        )


# ═════════════════════════════════════════════════════════════════════════════
# 2. Extreme sensor float values — compute_mood must not crash or hang
# ═════════════════════════════════════════════════════════════════════════════

class TestExtremeSensorValues:
    """
    BLE relay could, in theory, deliver corrupted IMU/mic values.

    compute_mood is pure Python arithmetic; we verify it handles edge cases
    without raising or producing undefined output.

    "Flake-recoverable" means: compute_mood returns a MoodResult (any valid
    mood) rather than raising ValueError/ZeroDivisionError/OverflowError.
    """

    @pytest.fixture(autouse=True)
    def _require_inference(self) -> None:
        if _INFERENCE_IMPORT_ERROR:
            pytest.skip(f"host.inference.compute_mood not importable: {_INFERENCE_IMPORT_ERROR}")

    @pytest.mark.parametrize("apv,accel,rot", [
        (1e300, 1e300, 1e300),   # near-overflow floats → huge tension
        (0.0,   0.0,   0.0),     # all-zero signal → calm/neutral
        (-1.0, -1.0,  -1.0),    # negative values (garbled — not valid sensor output)
        (1e-300, 1e-300, 1e-300), # near-zero floats
        (0.5,   0.5,   0.5),    # normal values (sanity check)
    ])
    def test_does_not_crash(
        self, apv: float, accel: float, rot: float
    ) -> None:
        """compute_mood must return a MoodResult for any finite float input."""
        try:
            result = compute_mood(
                audio_rms=0.5,
                audio_pitch_variance=apv,
                imu_acceleration=accel,
                imu_rotation=rot,
                mic_ok=True,
                imu_ok=True,
            )
        except Exception as exc:  # noqa: BLE001
            pytest.fail(
                f"compute_mood(apv={apv}, accel={accel}, rot={rot}) raised "
                f"{type(exc).__name__}: {exc}. "
                "Extreme floats must not crash the inference pipeline."
            )
        from host.inference import MoodResult
        assert isinstance(result, MoodResult), (
            f"compute_mood must always return a MoodResult; got {type(result).__name__!r}."
        )
        assert result.mood in ("neutral", "calm", "stressed", "attention"), (
            f"result.mood must be a valid enum value; got {result.mood!r}."
        )

    def test_nan_pitch_variance_falls_through_to_neutral(self) -> None:
        """
        NaN sensor values: Python float NaN comparisons are always False.
        Tension computation: NaN * 0.4 + ... = NaN.
        NaN > stress_threshold → False; NaN < calm_threshold → False
        → falls through to neutral branch, confidence=0.6 → gated.

        This is safe (gated NEUTRAL is correct — "no signal" is neutral).
        """
        result = compute_mood(
            audio_rms=0.5,
            audio_pitch_variance=float("nan"),
            imu_acceleration=0.5,
            imu_rotation=0.5,
            mic_ok=True,
            imu_ok=True,
        )
        # Must not raise; mood should be neutral (NaN falls through all comparisons)
        assert result.mood == "neutral", (
            f"NaN pitch_variance → tension=NaN → all comparisons False → neutral. "
            f"Got '{result.mood}'."
        )
        assert result.gated is True, (
            f"NaN-derived neutral has confidence=0.6 → must be gated. "
            f"Got gated={result.gated}."
        )

    def test_inf_acceleration_does_not_crash(self) -> None:
        """
        +Inf IMU acceleration: tension = 0.4*apv + 0.3*Inf + 0.3*rot = Inf.
        Inf > stress_threshold → True → stressed, confidence=0.8.
        Must not raise.
        """
        try:
            result = compute_mood(
                audio_rms=0.5,
                audio_pitch_variance=0.5,
                imu_acceleration=float("inf"),
                imu_rotation=0.5,
                mic_ok=True,
                imu_ok=True,
            )
        except Exception as exc:  # noqa: BLE001
            pytest.fail(
                f"compute_mood with imu_acceleration=Inf raised "
                f"{type(exc).__name__}: {exc}. "
                "BLE relay can produce corrupt float — host must survive."
            )
        # Inf tension → stressed
        assert result.mood == "stressed", (
            f"Inf acceleration → Inf tension → stressed. Got '{result.mood}'."
        )

    def test_nan_imu_does_not_poison_baseline_update(self) -> None:
        """
        update_baseline with NaN tension must return the original baseline unchanged.

        Guards the Welford accumulator against NaN poisoning (once NaN is in the
        mean, it propagates forever — baseline would be irreparably corrupt).
        """
        from host.inference import update_baseline, Baseline
        original = Baseline(mean=0.5, stddev=0.1, sample_count=10,
                            created_at="2026-06-13T00:00:00")
        result = update_baseline(original, float("nan"))
        assert result.sample_count == 10, (
            f"NaN tension must not increment sample_count; "
            f"got {result.sample_count}."
        )
        assert math.isfinite(result.mean), (
            f"NaN tension must not poison baseline mean; got {result.mean}."
        )
        assert math.isfinite(result.stddev), (
            f"NaN tension must not poison baseline stddev; got {result.stddev}."
        )


# ═════════════════════════════════════════════════════════════════════════════
# 3. Heap-guard host-observability gap — structural assertion + gap flag
# ═════════════════════════════════════════════════════════════════════════════

class TestHeapGuardObservability(unittest.TestCase):
    """
    ARD §5.1 / §10 Q3: Device monitors heap at 80% (reduce) and 95% (halt).
    decisions.md 2026-06-10 (B1): "No heap state surfaced in host-bound messages."

    The host has NO wire-level signal for device heap pressure.
    FAMILIAR_ACK carries only `last_received_seq` — no heap field.

    This class:
      a) Asserts the structural gap (FamiliarAck has no heap field) so the
         gap is visible in the test suite as a passing structural test.
      b) Documents the Ng action item.  If a heap field is added to
         FamiliarAck, test (a) will fail — prompting review of whether the
         gap has been closed and this file should be updated.

    FLAG for Ng (W3-B / W3-E owner):
      If `frame.system.get_heap_usage()` is unavailable (SDK gap Q3), the device
      cannot report heap to host anyway.  However, if/when the SDK confirms heap
      API availability, the wire format should be extended so the host can:
        1. Log heap warnings at 80%.
        2. Proactively back off send rate at 95%.
      Until then, the only host-observable failure mode is BLE silence → the
      existing both-fail 10 s → NEUTRAL fallback is the safety net.
    """

    def test_familiar_ack_has_no_heap_field(self) -> None:
        """
        Structural gap assertion: FamiliarAck must have ONLY `last_received_seq`.

        If this test fails, Ng has added a heap field — update the gap documentation
        and the host handler in main.py accordingly.
        """
        if _PROTOCOL_IMPORT_ERROR:
            self.skipTest(f"host.familiar_protocol not importable: {_PROTOCOL_IMPORT_ERROR}")

        import dataclasses
        fields = {f.name for f in dataclasses.fields(FamiliarAck)}
        assert fields == {"last_received_seq"}, (
            f"FamiliarAck fields: {fields}. "
            "Expected only {{'last_received_seq'}} (no heap field — decisions.md B1). "
            "If a heap field was added, remove this test and add host-side handling "
            "in main.py (log at 80%, back off at 95%)."
        )

    def test_heap_gap_is_documented_coverage_note(self) -> None:
        """
        Documents the coverage gap for CI visibility.

        The host's only response to device OOM is the both-fail 10 s → NEUTRAL
        fallback (BLE silence ≈ both-sensor timeout).  This is a weak proxy for
        heap exhaustion — the creature goes NEUTRAL rather than the host knowing
        why.

        This test always passes.  Its presence in the suite means the gap is
        tracked (not invisible).  Owner: Ng.
        """
        gap_description = (
            "COVERAGE GAP (Ng): FamiliarAck has no heap field.  "
            "If device hits OOM at 95%, host observes BLE silence → "
            "both-fail 10 s timeout → NEUTRAL.  No heap-pressure signal on wire.  "
            "ARD §5.1/§10 Q3.  Fix: add heap_status byte to FAMILIAR_ACK or "
            "define DEVICE_STATUS message."
        )
        # This assertion always passes — it's a documentation anchor.
        assert gap_description  # non-empty string is truthy

    def test_both_fail_fallback_is_heap_oom_proxy(self) -> None:
        """
        Verify that the both-fail 10 s → NEUTRAL fallback is actually exercisable
        (the safety net that catches device heap OOM as BLE silence).

        If the both-fail constant is removed or set to infinity, the heap-OOM
        proxy is broken.
        """
        from host.main import BOTH_FAIL_TIMEOUT_S
        assert isinstance(BOTH_FAIL_TIMEOUT_S, float), (
            f"BOTH_FAIL_TIMEOUT_S must be a float; got {type(BOTH_FAIL_TIMEOUT_S).__name__!r}."
        )
        assert BOTH_FAIL_TIMEOUT_S < float("inf"), (
            "BOTH_FAIL_TIMEOUT_S must be finite — it is the only host-side safety net "
            "against device OOM (BLE silence proxy). ARD §5.1/§5.4."
        )
        assert BOTH_FAIL_TIMEOUT_S > 0, (
            f"BOTH_FAIL_TIMEOUT_S={BOTH_FAIL_TIMEOUT_S} must be > 0."
        )
        # ARD §5.4 specifies 10 s.  If someone doubles it to 20 s or more, flag it.
        assert BOTH_FAIL_TIMEOUT_S <= 15.0, (
            f"BOTH_FAIL_TIMEOUT_S={BOTH_FAIL_TIMEOUT_S}s is > 15 s.  "
            "ARD §5.4 specifies 10 s for BLE timeout → NEUTRAL.  "
            "If you intentionally changed this, update this assertion and the ARD."
        )
