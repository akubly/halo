"""
Unit tests for host/familiar_protocol.py — BLE wire-format encoding/decoding.

Owner:         Juanita (Tester / QA)
ARD reference: docs/projects/synesthetic-familiar/ARD.md §5.2
Test strategy: docs/projects/synesthetic-familiar/TEST-STRATEGY.md Rev 2
Date:          2026-06-09

═══════════════════════════════════════════════════════════════════════════════
IMPORT ASSUMPTION (Juanita → Ng):

  This file imports the following names from host.familiar_protocol:

    encode_familiar_update(mood, intensity: int, confidence: int, seq: int) -> bytes
      Encodes a FAMILIAR_UPDATE message.  mood is a Mood enum member.
      intensity and confidence are 0–100 integers. seq is a uint16 (0–65535).

    decode_familiar_ack(raw: bytes) -> tuple[int, int]
      Returns (opcode, last_received_seq).  opcode must be 0x02.

    decode_familiar_reset(raw: bytes) -> int
      Returns the opcode (0x01).  No payload; caller verifies len(raw)==1.

    Mood  — enum with members NEUTRAL=0, CALM=1, STRESSED=2, ATTENTION=3.

    seq_is_newer(received: int, last_accepted: int) -> bool   [OPTIONAL]
      Returns True iff the received seq is strictly newer than last_accepted,
      using the ARD §5.2 signed-16 delta window:
        delta = (received - last_accepted) mod 65536 (interpreted as signed int16)
        delta 1..32767   → True  (accept)
        delta 0          → False (duplicate)
        delta 32768..65535 → False (stale / out-of-order)
      If Ng implements dedup entirely in Lua (busted), this symbol may not be
      exported.  TestSeqDedup is skipped automatically in that case — but the
      normative spec is still documented here for cross-reference.

  If any name above differs from Ng's implementation, please align to the above
  OR update the import aliases in this file and file a finding.

═══════════════════════════════════════════════════════════════════════════════
SPEC FLAGS (open questions that affect test expectations):

  FLAG-A (field-range policy):
    ARD §5.2 specifies intensity 0–100 and confidence 0–100 but does NOT specify
    whether out-of-range values are CLAMPED or REJECTED (ValueError).
    Tests below assume REJECTION (ValueError / OverflowError).  If Ng chooses
    clamping, update TestFamiliarUpdateBounds.test_*_raises tests and file a
    decision to .squad/decisions/inbox/.

  FLAG-B (seq_is_newer availability):
    ARD §5.2 dedup logic is normatively device-side (Lua, tested via busted).
    If Ng adds a Python helper for host-side sequence tracking, these tests
    cover it.  If not, TestSeqDedup is auto-skipped (see _SEQ_DEDUP_AVAILABLE).

═══════════════════════════════════════════════════════════════════════════════
B3 NOTE (false-positive guard — acceptance tier):

  The B3 finding (from TEST-STRATEGY Rev 2) applies to acceptance-tier tests
  that use FakeTransport.  This file contains ONLY classicist unit tests for
  pure byte-transformation — no transport instance is used.  The B3 single-
  instance rule is enforced in tests/acceptance/ where FamiliarApp is driven
  through a FakeTransport.  Reminder: use ONE FakeTransport() instance for
  both the FamiliarApp constructor argument and the assertion target; do NOT
  create a second FakeTransport() to assert against.
═══════════════════════════════════════════════════════════════════════════════
"""

import inspect
import struct

import pytest

# ── Import guard ─────────────────────────────────────────────────────────────
# If the module is not yet implemented, every test FAILS clearly (not errors
# on collection, not silently skips).  Once Ng's module lands, the same tests
# should all pass.
try:
    from host.familiar_protocol import (
        Mood,
        decode_familiar_ack,
        decode_familiar_reset,
        encode_familiar_update,
    )
    _IMPORT_ERROR: str | None = None
except ImportError as _e:
    _IMPORT_ERROR = str(_e)
    # Dummies prevent NameError at collection time; tests fail via fixture below.
    Mood = None  # type: ignore[assignment]
    encode_familiar_update = None  # type: ignore[assignment]
    decode_familiar_ack = None  # type: ignore[assignment]
    decode_familiar_reset = None  # type: ignore[assignment]

try:
    from host.familiar_protocol import seq_is_newer
    _SEQ_DEDUP_AVAILABLE = True
except ImportError:
    seq_is_newer = None  # type: ignore[assignment]
    _SEQ_DEDUP_AVAILABLE = False


@pytest.fixture(autouse=True)
def _require_protocol_module() -> None:
    """Fail every test with a human-readable message if the module is missing."""
    if _IMPORT_ERROR is not None:
        pytest.fail(
            f"host.familiar_protocol is not yet importable: {_IMPORT_ERROR}\n"
            "These tests will pass once Ng implements the module."
        )


# ═════════════════════════════════════════════════════════════════════════════
# Group 1 — FAMILIAR_UPDATE encode / round-trip
# Classicist: pure byte-transformation, no mocks.
# Coverage: ARD §5.2 wire format; B2 finding (every >H must be <H).
# ═════════════════════════════════════════════════════════════════════════════

class TestFamiliarUpdateEncode:
    """encode_familiar_update(mood, intensity, confidence, seq) -> bytes."""

    def test_total_length_is_6_bytes(self) -> None:
        payload = encode_familiar_update(mood=Mood.NEUTRAL, intensity=50, confidence=75, seq=1)
        assert len(payload) == 6, (
            f"FAMILIAR_UPDATE must be exactly 6 bytes per ARD §5.2; got {len(payload)}"
        )

    def test_opcode_byte_0_is_0x80(self) -> None:
        payload = encode_familiar_update(mood=Mood.NEUTRAL, intensity=50, confidence=75, seq=1)
        assert payload[0] == 0x80, (
            f"byte 0 must be opcode 0x80; got {payload[0]:#04x}"
        )

    @pytest.mark.parametrize("mood_name,expected_enum", [
        ("NEUTRAL",   0),
        ("CALM",      1),
        ("STRESSED",  2),
        ("ATTENTION", 3),
    ])
    def test_mood_enum_byte_1_encoding(self, mood_name: str, expected_enum: int) -> None:
        m = getattr(Mood, mood_name)
        payload = encode_familiar_update(mood=m, intensity=50, confidence=75, seq=1)
        assert payload[1] == expected_enum, (
            f"Mood.{mood_name} must encode as {expected_enum} in byte 1; got {payload[1]}"
        )

    def test_intensity_in_byte_2(self) -> None:
        payload = encode_familiar_update(mood=Mood.NEUTRAL, intensity=83, confidence=75, seq=1)
        assert payload[2] == 83, f"byte 2 must carry intensity=83; got {payload[2]}"

    def test_confidence_in_byte_3(self) -> None:
        payload = encode_familiar_update(mood=Mood.NEUTRAL, intensity=50, confidence=91, seq=1)
        assert payload[3] == 91, f"byte 3 must carry confidence=91; got {payload[3]}"

    # ── B2 FINDING: endianness is LITTLE-ENDIAN ──────────────────────────────

    def test_seq_bytes_4_5_are_little_endian_not_big_endian(self) -> None:
        """
        B2 finding: ALL multi-byte fields are LE.
        seq=0x0102 → wire bytes [0x02, 0x01], NOT [0x01, 0x02].
        Any struct.pack('>H', ...) in the implementation is wrong.
        """
        payload = encode_familiar_update(
            mood=Mood.NEUTRAL, intensity=50, confidence=75, seq=0x0102
        )
        low_byte  = payload[4]
        high_byte = payload[5]
        assert low_byte  == 0x02, (
            f"byte 4 (LE low byte) must be 0x02 for seq=0x0102; got {low_byte:#04x}. "
            "If 0x01, implementation used big-endian ('>H') — must switch to '<H'."
        )
        assert high_byte == 0x01, (
            f"byte 5 (LE high byte) must be 0x01 for seq=0x0102; got {high_byte:#04x}"
        )
        # Belt-and-suspenders: verify LE unpack yields original seq
        le_seq = struct.unpack("<H", payload[4:6])[0]
        be_seq = struct.unpack(">H", payload[4:6])[0]
        assert le_seq == 0x0102, (
            f"struct.unpack('<H', payload[4:6]) must yield 0x0102; got {le_seq:#06x}"
        )
        assert be_seq != 0x0102, (
            "struct.unpack('>H', ...) must NOT also yield 0x0102 for this seq — "
            "if it does, the test value 0x0102 is a palindrome and must be changed"
        )

    def test_seq_10_little_endian_low_byte_nonzero_high_zero(self) -> None:
        """seq=10 (0x000A): low byte=0x0A, high byte=0x00."""
        payload = encode_familiar_update(
            mood=Mood.NEUTRAL, intensity=50, confidence=75, seq=10
        )
        assert payload[4] == 0x0A, (
            f"byte 4 must be 0x0A for seq=10; got {payload[4]:#04x}"
        )
        assert payload[5] == 0x00, (
            f"byte 5 must be 0x00 for seq=10; got {payload[5]:#04x}"
        )

    def test_seq_0xff00_little_endian_low_zero_high_ff(self) -> None:
        """seq=0xFF00: low byte=0x00, high byte=0xFF — tests high-byte overflow path."""
        payload = encode_familiar_update(
            mood=Mood.NEUTRAL, intensity=50, confidence=75, seq=0xFF00
        )
        assert payload[4] == 0x00, (
            f"byte 4 must be 0x00 for seq=0xFF00; got {payload[4]:#04x}"
        )
        assert payload[5] == 0xFF, (
            f"byte 5 must be 0xFF for seq=0xFF00; got {payload[5]:#04x}"
        )

    def test_seq_max_uint16_0xffff(self) -> None:
        """seq=0xFFFF (65535): both bytes must be 0xFF."""
        payload = encode_familiar_update(
            mood=Mood.NEUTRAL, intensity=50, confidence=75, seq=0xFFFF
        )
        assert payload[4] == 0xFF
        assert payload[5] == 0xFF
        assert struct.unpack("<H", payload[4:6])[0] == 0xFFFF

    def test_seq_zero_encodes_as_two_null_bytes(self) -> None:
        """seq=0: bytes [0x00, 0x00]. Valid per ARD; used on reconnect."""
        payload = encode_familiar_update(
            mood=Mood.NEUTRAL, intensity=50, confidence=75, seq=0
        )
        assert payload[4] == 0x00
        assert payload[5] == 0x00

    def test_full_round_trip_stressed_seq_1337(self) -> None:
        """Full round-trip: encode, then manually unpack every field."""
        payload = encode_familiar_update(
            mood=Mood.STRESSED, intensity=85, confidence=82, seq=1337
        )
        assert len(payload) == 6
        assert payload[0] == 0x80     # opcode
        assert payload[1] == 2        # STRESSED
        assert payload[2] == 85       # intensity
        assert payload[3] == 82       # confidence
        seq = struct.unpack("<H", payload[4:6])[0]
        assert seq == 1337

    def test_return_type_is_bytes_or_bytearray(self) -> None:
        payload = encode_familiar_update(
            mood=Mood.NEUTRAL, intensity=50, confidence=75, seq=1
        )
        assert isinstance(payload, (bytes, bytearray)), (
            f"encode_familiar_update must return bytes or bytearray; "
            f"got {type(payload).__name__}"
        )


# ═════════════════════════════════════════════════════════════════════════════
# Group 2 — Field bounds
# intensity 0–100, confidence 0–100, mood 0–3, seq 0–65535.
# FLAG-A: tests assume out-of-range → ValueError / OverflowError.
# ═════════════════════════════════════════════════════════════════════════════

class TestFamiliarUpdateBounds:

    # ── Valid boundary values ─────────────────────────────────────────────────

    def test_intensity_minimum_0_is_valid(self) -> None:
        payload = encode_familiar_update(
            mood=Mood.NEUTRAL, intensity=0, confidence=75, seq=1
        )
        assert payload[2] == 0

    def test_intensity_maximum_100_is_valid(self) -> None:
        payload = encode_familiar_update(
            mood=Mood.NEUTRAL, intensity=100, confidence=75, seq=1
        )
        assert payload[2] == 100

    def test_confidence_minimum_0_is_valid(self) -> None:
        payload = encode_familiar_update(
            mood=Mood.NEUTRAL, intensity=50, confidence=0, seq=1
        )
        assert payload[3] == 0

    def test_confidence_maximum_100_is_valid(self) -> None:
        payload = encode_familiar_update(
            mood=Mood.NEUTRAL, intensity=50, confidence=100, seq=1
        )
        assert payload[3] == 100

    def test_seq_minimum_0_is_valid(self) -> None:
        payload = encode_familiar_update(
            mood=Mood.NEUTRAL, intensity=50, confidence=75, seq=0
        )
        assert struct.unpack("<H", payload[4:6])[0] == 0

    def test_seq_maximum_65535_is_valid(self) -> None:
        payload = encode_familiar_update(
            mood=Mood.NEUTRAL, intensity=50, confidence=75, seq=65535
        )
        assert struct.unpack("<H", payload[4:6])[0] == 65535

    # ── Out-of-range values (FLAG-A: assumed to raise, not clamp) ────────────

    def test_intensity_101_raises(self) -> None:
        """intensity=101 exceeds ARD §5.2 max of 100; must be rejected."""
        with pytest.raises((ValueError, OverflowError)):
            encode_familiar_update(
                mood=Mood.NEUTRAL, intensity=101, confidence=75, seq=1
            )

    def test_intensity_negative_1_raises(self) -> None:
        with pytest.raises((ValueError, OverflowError)):
            encode_familiar_update(
                mood=Mood.NEUTRAL, intensity=-1, confidence=75, seq=1
            )

    def test_confidence_101_raises(self) -> None:
        with pytest.raises((ValueError, OverflowError)):
            encode_familiar_update(
                mood=Mood.NEUTRAL, intensity=50, confidence=101, seq=1
            )

    def test_confidence_negative_1_raises(self) -> None:
        with pytest.raises((ValueError, OverflowError)):
            encode_familiar_update(
                mood=Mood.NEUTRAL, intensity=50, confidence=-1, seq=1
            )

    def test_invalid_mood_integer_4_raises(self) -> None:
        """Mood value 4 is outside the ARD §5.2 enum (0–3); must be rejected."""
        with pytest.raises((ValueError, TypeError)):
            encode_familiar_update(
                mood=4, intensity=50, confidence=75, seq=1  # type: ignore[arg-type]
            )

    def test_seq_above_uint16_max_raises(self) -> None:
        """seq=65536 must not silently truncate to 0; must raise."""
        with pytest.raises((ValueError, OverflowError, struct.error)):
            encode_familiar_update(
                mood=Mood.NEUTRAL, intensity=50, confidence=75, seq=65536
            )

    def test_seq_negative_raises(self) -> None:
        with pytest.raises((ValueError, OverflowError, struct.error)):
            encode_familiar_update(
                mood=Mood.NEUTRAL, intensity=50, confidence=75, seq=-1
            )


# ═════════════════════════════════════════════════════════════════════════════
# Group 3 — Sequence number dedup (signed-16 delta window)
# ARD §5.2: wraparound-aware; MUST use mod-65536 arithmetic, NOT naive '>'.
# FLAG-B: auto-skipped if seq_is_newer not exported.
# ═════════════════════════════════════════════════════════════════════════════

@pytest.mark.skipif(
    not _SEQ_DEDUP_AVAILABLE,
    reason=(
        "seq_is_newer not exported from host.familiar_protocol. "
        "If dedup is Lua-only (busted), this skip is expected. "
        "Ng: export seq_is_newer to enable host-side dedup tests."
    ),
)
class TestSeqDedup:
    """
    Tests for seq_is_newer(received: int, last_accepted: int) -> bool.

    Normative spec (ARD §5.2):
      delta = (received - last_accepted) mod 65536  →  interpret as signed int16
      delta  1 ..  32767  →  True   (accept window, includes wraparound)
      delta  0            →  False  (duplicate)
      delta  32768 .. 65535  →  False  (stale / out-of-order; signed-negative)
    """

    # ── Accept window: delta 1..32767 ────────────────────────────────────────

    def test_delta_1_is_newer(self) -> None:
        assert seq_is_newer(received=1, last_accepted=0) is True

    def test_delta_32767_is_newer(self) -> None:
        """Upper boundary of the accept window."""
        assert seq_is_newer(received=32767, last_accepted=0) is True

    def test_incremental_seq_is_newer(self) -> None:
        assert seq_is_newer(received=5, last_accepted=4) is True

    def test_large_jump_within_accept_window(self) -> None:
        assert seq_is_newer(received=1000, last_accepted=999) is True

    # ── Reject: delta 0 (duplicate) ──────────────────────────────────────────

    def test_duplicate_same_seq_returns_false(self) -> None:
        assert seq_is_newer(received=42, last_accepted=42) is False

    def test_duplicate_at_zero_returns_false(self) -> None:
        assert seq_is_newer(received=0, last_accepted=0) is False

    # ── Reject: delta 32768..65535 (stale / signed-negative) ─────────────────

    def test_delta_32768_is_stale(self) -> None:
        """delta=32768 is the first stale value (signed int16: -32768)."""
        # received=32768, last_accepted=0 → delta=32768
        assert seq_is_newer(received=32768, last_accepted=0) is False

    def test_delta_65535_is_stale(self) -> None:
        """delta=65535: one-step-behind is stale."""
        # received=4, last_accepted=5 → (4-5) mod 65536 = 65535
        assert seq_is_newer(received=4, last_accepted=5) is False

    def test_one_step_behind_is_stale(self) -> None:
        assert seq_is_newer(received=9, last_accepted=10) is False

    # ── Wraparound: 0xFFFF → 0x0000 ──────────────────────────────────────────

    def test_wraparound_0xffff_to_0x0000_is_accepted(self) -> None:
        """
        ARD §5.2 reconnect case: device resets last_accepted_seq = 0xFFFF;
        host sends seq=0x0000.
        delta = (0x0000 - 0xFFFF) mod 65536 = 1  →  ACCEPT.

        Naive comparison (0 > 65535 = False) would WRONGLY drop this packet.
        This is the primary wraparound regression test.
        """
        assert seq_is_newer(received=0x0000, last_accepted=0xFFFF) is True, (
            "Wraparound seq=0x0000 after last=0xFFFF must be ACCEPTED (delta=1). "
            "Failure here means the implementation uses naive '>' — must use "
            "mod-65536 signed-int16 arithmetic per ARD §5.2."
        )

    def test_stale_one_below_last_near_wraparound(self) -> None:
        """
        last=0x0001, received=0xFFFF:
        delta = (0xFFFF - 0x0001) mod 65536 = 65534  (signed: -2)  →  STALE.
        """
        assert seq_is_newer(received=0xFFFF, last_accepted=0x0001) is False

    def test_accept_window_upper_bound_near_wraparound(self) -> None:
        """
        last=0x8000, received=0xFFFF:
        delta = (0xFFFF - 0x8000) mod 65536 = 0x7FFF = 32767  →  ACCEPT (max window).
        """
        assert seq_is_newer(received=0xFFFF, last_accepted=0x8000) is True

    def test_first_stale_value_past_accept_window(self) -> None:
        """
        last=0x8000, received=0x0000:
        delta = (0x0000 - 0x8000) mod 65536 = 0x8000 = 32768  →  STALE (first stale).
        """
        assert seq_is_newer(received=0x0000, last_accepted=0x8000) is False

    def test_naive_greater_than_would_wrongly_reject_wraparound(self) -> None:
        """
        Explicit regression guard against naive implementation.
        Naive: (received > last_accepted) = (0 > 65535) = False  →  WRONG (drops packet).
        Correct signed-delta: delta=1  →  True  (accept).
        """
        assert seq_is_newer(received=0, last_accepted=65535) is True, (
            "seq_is_newer(0, 65535) must return True. "
            "If False, the implementation is using naive integer '>' comparison."
        )


# ═════════════════════════════════════════════════════════════════════════════
# Group 4 — FAMILIAR_ACK decode
# Coverage: ARD §5.2 (Device → Host, opcode 0x02, 3 bytes, seq LE).
# ═════════════════════════════════════════════════════════════════════════════

class TestFamiliarAckDecode:
    """decode_familiar_ack(raw: bytes) -> (opcode: int, last_received_seq: int)."""

    def test_opcode_is_0x02(self) -> None:
        raw = bytes([0x02, 0x0A, 0x00])
        opcode, _ = decode_familiar_ack(raw)
        assert opcode == 0x02, (
            f"FAMILIAR_ACK opcode must be 0x02; got {opcode:#04x}"
        )

    def test_seq_10_little_endian(self) -> None:
        """seq=10: wire bytes position 1-2 = [0x0A, 0x00] (LE)."""
        raw = bytes([0x02, 0x0A, 0x00])
        _, seq = decode_familiar_ack(raw)
        assert seq == 10, f"seq must be 10; got {seq}"

    def test_seq_zero(self) -> None:
        raw = bytes([0x02, 0x00, 0x00])
        _, seq = decode_familiar_ack(raw)
        assert seq == 0

    def test_seq_max_uint16_0xffff(self) -> None:
        raw = bytes([0x02, 0xFF, 0xFF])
        _, seq = decode_familiar_ack(raw)
        assert seq == 0xFFFF

    def test_seq_high_byte_paranoid_little_endian(self) -> None:
        """
        B2 FINDING guard: seq=0x0201.
        LE wire bytes: [0x01, 0x02] → position 1=0x01 (low), position 2=0x02 (high).
        decode must yield 0x0201 = 513.
        If it yields 0x0102 = 258, the implementation reads big-endian ('>H').
        """
        raw = bytes([0x02, 0x01, 0x02])  # LE: low=0x01, high=0x02 → 0x0201
        _, seq = decode_familiar_ack(raw)
        assert seq == 0x0201, (
            f"seq must be 0x0201 (513); got {seq} ({seq:#06x}). "
            "If seq=0x0102 (258), decode_familiar_ack is reading big-endian — "
            "must use '<H', not '>H'."
        )

    def test_returns_two_element_tuple(self) -> None:
        """Return type must be a tuple/sequence of exactly (opcode, seq)."""
        raw = bytes([0x02, 0x05, 0x00])
        result = decode_familiar_ack(raw)
        assert result is not None
        opcode, seq = result  # must unpack to exactly two values
        assert isinstance(opcode, int)
        assert isinstance(seq, int)

    def test_total_raw_length_consumed_is_3_bytes(self) -> None:
        """ACK is exactly 3 bytes; function must not raise on a 3-byte input."""
        raw = bytes([0x02, 0x07, 0x00])
        assert len(raw) == 3
        decode_familiar_ack(raw)  # must not raise


# ═════════════════════════════════════════════════════════════════════════════
# Group 5 — FAMILIAR_RESET decode
# Coverage: ARD §5.2 (Device → Host ONLY, opcode 0x01, 1 byte, no payload).
# ═════════════════════════════════════════════════════════════════════════════

class TestFamiliarResetDecode:
    """decode_familiar_reset(raw: bytes) -> int (opcode)."""

    def test_opcode_is_0x01(self) -> None:
        raw = bytes([0x01])
        opcode = decode_familiar_reset(raw)
        assert opcode == 0x01, (
            f"FAMILIAR_RESET opcode must be 0x01; got {opcode:#04x}"
        )

    def test_total_length_is_1_byte(self) -> None:
        """FAMILIAR_RESET carries no payload; 1 byte exactly per ARD §5.2."""
        raw = bytes([0x01])
        decode_familiar_reset(raw)  # must not raise on 1-byte input
        assert len(raw) == 1        # raw itself is 1 byte — confirming spec

    def test_no_encode_familiar_reset_function_exists(self) -> None:
        """
        Device → Host direction ONLY.  No Host → Device reset opcode exists.
        Quick-reset ownership decision (2026-06-08): double-tap is detected on
        device; device snaps to NEUTRAL locally; device NOTIFIES host via
        FAMILIAR_RESET.  Host never sends a reset command.
        If encode_familiar_reset exists, that is a spec violation.
        """
        import host.familiar_protocol as _proto
        assert not hasattr(_proto, "encode_familiar_reset"), (
            "encode_familiar_reset must NOT exist: FAMILIAR_RESET is Device→Host only. "
            "No host-originated reset exists in ARD §5.2. "
            "See quick-reset ownership decision (2026-06-08)."
        )


# ═════════════════════════════════════════════════════════════════════════════
# Group 6 — Privacy / payload shape guards (RAVEN-T2-1)
# No raw biometric data may appear in FAMILIAR_UPDATE payload.
# ═════════════════════════════════════════════════════════════════════════════

class TestPrivacyProtocol:
    """
    RAVEN-T2-1: The 6-byte FAMILIAR_UPDATE payload is
    opcode / mood_enum / intensity / confidence / seq — nothing else.
    Raw sensor readings (audio_rms, pitch_variance, IMU values) must
    never appear on the wire, even accidentally via function signature.
    """

    def test_encode_signature_has_no_raw_biometric_params(self) -> None:
        """
        If encode_familiar_update accepted audio_rms or imu_accel, a caller
        could inadvertently route raw biometric data toward the wire.
        The function signature is the first privacy gate.
        """
        params = inspect.signature(encode_familiar_update).parameters
        forbidden = {
            "audio_rms", "pitch_variance", "audio_pitch_variance",
            "imu_accel", "imu_acceleration", "imu_rot", "imu_rotation",
        }
        leaked = forbidden & set(params.keys())
        assert not leaked, (
            f"encode_familiar_update must NOT accept raw biometric parameters; "
            f"found: {leaked}.  Raw sensor values must not reach the wire."
        )

    def test_payload_is_exactly_6_bytes_no_extra_fields(self) -> None:
        """
        Any extra byte beyond 6 could carry undocumented (biometric) information.
        Spec is closed: 6 bytes, no extensions without an ARD amendment.
        """
        payload = encode_familiar_update(
            mood=Mood.NEUTRAL, intensity=50, confidence=75, seq=1
        )
        assert len(payload) == 6, (
            f"FAMILIAR_UPDATE must be exactly 6 bytes; got {len(payload)}. "
            "Extra bytes indicate an undocumented field — privacy review required."
        )

