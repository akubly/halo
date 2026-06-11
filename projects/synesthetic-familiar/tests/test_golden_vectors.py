"""
Golden byte-vector fixtures for the FAMILIAR_UPDATE wire format.

These vectors are the authoritative cross-language reference.  The Lua
device/main.lua decode_update() must produce identical field values when
fed these exact byte sequences.  Any Python encode change that breaks these
vectors is a protocol regression.

ARD §5.2 wire layout (6 bytes, all fields little-endian):
  byte 0     opcode      0x80
  byte 1     mood        0–3
  byte 2     intensity   0–100
  byte 3     confidence  0–100
  bytes 4–5  seq         uint16 LE

Owner: Ng
"""
import pytest

try:
    from host.familiar_protocol import encode_familiar_update, Mood
    _IMPORT_ERROR: str | None = None
except ImportError as _e:
    _IMPORT_ERROR = str(_e)
    encode_familiar_update = None  # type: ignore[assignment]
    Mood = None  # type: ignore[assignment]


@pytest.fixture(autouse=True)
def _require_protocol_module() -> None:
    if _IMPORT_ERROR is not None:
        pytest.fail(
            f"host.familiar_protocol is not importable: {_IMPORT_ERROR}"
        )


# ---------------------------------------------------------------------------
# Known (mood, intensity, confidence, seq) → expected hex byte string.
#
# To verify against device/main.lua manually:
#   local msg = decode_update(bytes)
#   assert msg.mood == mood
#   assert msg.intensity == intensity
#   assert msg.confidence == confidence
#   assert msg.seq == seq
# ---------------------------------------------------------------------------

GOLDEN_VECTORS = [
    # (mood, intensity, confidence, seq, expected_hex)
    # NEUTRAL, mid-range values, seq=0 (reconnect first packet)
    (Mood.NEUTRAL,   50,  85, 0x0000, "80 00 32 55 00 00"),
    # CALM, low intensity, seq=1
    (Mood.CALM,      30,  90, 0x0001, "80 01 1e 5a 01 00"),
    # STRESSED, high intensity, seq=1337 (0x0539 LE → 0x39 0x05)
    (Mood.STRESSED,  85,  88, 0x0539, "80 02 55 58 39 05"),
    # ATTENTION, max intensity/confidence, seq=0xFFFF (wraparound boundary)
    (Mood.ATTENTION, 100, 100, 0xFFFF, "80 03 64 64 ff ff"),
    # NEUTRAL, seq wraps: 0xFF00 LE → 0x00 0xFF
    (Mood.NEUTRAL,   0,   0,  0xFF00, "80 00 00 00 00 ff"),
]


@pytest.mark.parametrize(
    "mood,intensity,confidence,seq,expected_hex",
    GOLDEN_VECTORS,
    ids=[
        "neutral-seq0-reconnect",
        "calm-seq1",
        "stressed-seq1337",
        "attention-seq-max",
        "neutral-seq-ff00",
    ],
)
def test_golden_vector_encode(
    mood: int,
    intensity: int,
    confidence: int,
    seq: int,
    expected_hex: str,
) -> None:
    """
    Encode must produce the exact byte sequence specified in the golden vector.

    These fixtures are the authoritative cross-language reference:
    device/main.lua decode_update() must accept the same bytes and extract
    the same field values.  If this test fails, the Python encoder has
    drifted from the locked ARD §5.2 wire format.
    """
    expected = bytes.fromhex(expected_hex.replace(" ", ""))
    actual = encode_familiar_update(mood, intensity, confidence, seq)
    assert actual == expected, (
        f"Golden vector mismatch for mood={mood} intensity={intensity} "
        f"confidence={confidence} seq={seq:#06x}.\n"
        f"  expected: {expected.hex(' ')}\n"
        f"  actual:   {actual.hex(' ')}\n"
        "Wire format regression — update ARD §5.2 and Lua decode if intentional."
    )
