"""
Unit tests for host/main.py — intensity quantisation and jitter helpers.

Gate 2 (MERGE-BLOCKING): Verifies the quantise_intensity → apply_intensity_jitter
pipeline mandated by hiro-week2-integration-contract.md §3.

Pipeline position (contract §3):
    compute_mood() → intensity (float 0.0–1.0)
        ↓  quantise_intensity()
    int in {0, 25, 50, 75, 100}
        ↓  apply_intensity_jitter(rng=...)
    int in 0–100 (±5, clamped)
        ↓  encode_familiar_update(..., intensity=..., ...)

Bucket boundaries (contract §3):
    0.0  – <0.125  → 0
    0.125– <0.375  → 25
    0.375– <0.625  → 50
    0.625– <0.875  → 75
    0.875– 1.0     → 100
"""

import random
import unittest

import pytest

# ── Import guard ─────────────────────────────────────────────────────────────
try:
    from host.main import quantise_intensity, apply_intensity_jitter
    _IMPORT_ERROR: str | None = None
except ImportError as _e:
    _IMPORT_ERROR = str(_e)
    quantise_intensity = None  # type: ignore[assignment]
    apply_intensity_jitter = None  # type: ignore[assignment]


@pytest.fixture(autouse=True)
def _require_main_module() -> None:
    """Fail every test with a human-readable message if the helpers are missing."""
    if _IMPORT_ERROR is not None:
        pytest.fail(
            f"host.main.quantise_intensity / apply_intensity_jitter not importable: "
            f"{_IMPORT_ERROR}\n"
            "These are Week-2 helpers (contract §3). Tests pass once Ng implements them."
        )


_VALID_QUANTISED: frozenset[int] = frozenset({0, 25, 50, 75, 100})


class TestQuantiseIntensity(unittest.TestCase):
    """
    Gate 2 — quantise_intensity(float) → int in {0, 25, 50, 75, 100}.

    Boundary table (contract §3):
        < 0.125   → 0
        0.125–<0.375 → 25
        0.375–<0.625 → 50
        0.625–<0.875 → 75
        ≥ 0.875   → 100
    """

    def test_intensity_quantised_before_encode(self) -> None:
        """
        Gate 2 (MERGE-BLOCKING).

        quantise_intensity() maps every float in [0.0, 1.0] to one of the
        five discrete levels.  This test drives the full set of bucket
        representatives and all boundary values.
        """
        # Representative mid-bucket values
        mid_bucket_cases = [
            (0.0,    0),
            (0.05,   0),
            (0.1,    0),
            (0.2,    25),
            (0.25,   25),
            (0.3,    25),
            (0.5,    50),
            (0.6,    50),
            (0.7,    75),
            (0.75,   75),
            (0.8,    75),
            (0.9,    100),
            (0.95,   100),
            (1.0,    100),
        ]
        for intensity, expected in mid_bucket_cases:
            result = quantise_intensity(intensity)
            assert result == expected, (
                f"quantise_intensity({intensity}) → {result}, expected {expected}. "
                f"Check bucket boundaries (contract §3)."
            )
            assert result in _VALID_QUANTISED, (
                f"quantise_intensity({intensity}) = {result} is not in {_VALID_QUANTISED}"
            )

    def test_quantise_always_returns_valid_level(self) -> None:
        """Every value in [0.0, 1.0] must map to one of the 5 levels."""
        for i in range(0, 101):
            intensity = i / 100.0
            result = quantise_intensity(intensity)
            assert result in _VALID_QUANTISED, (
                f"quantise_intensity({intensity}) = {result} not in {_VALID_QUANTISED}"
            )
            assert isinstance(result, int), (
                f"quantise_intensity must return int; got {type(result).__name__}"
            )


# NOTE: pytest.mark.parametrize requires plain pytest class (not unittest.TestCase)
class TestQuantiseIntensityBoundaries:
    """Paranoid boundary coverage for quantise_intensity."""

    @pytest.mark.parametrize("intensity,expected", [
        # Lower bound of each bucket (inclusive boundary per contract)
        (0.0,     0),
        (0.125,   25),   # 0.125 is the first value NOT in bucket-0
        (0.375,   50),   # first value NOT in bucket-25
        (0.625,   75),   # first value NOT in bucket-50
        (0.875,   100),  # first value NOT in bucket-75
        # Just-below each boundary (still in lower bucket)
        (0.1249,  0),
        (0.3749,  25),
        (0.6249,  50),
        (0.8749,  75),
        # Maximum
        (1.0,     100),
    ])
    def test_quantise_intensity_bucket_boundaries(self, intensity: float, expected: int) -> None:
        """Paranoid boundary coverage: every bucket transition point."""
        result = quantise_intensity(intensity)
        assert result == expected, (
            f"quantise_intensity({intensity}) → {result}, expected {expected}. "
            f"Boundary: contract §3 bucket table."
        )


class TestApplyIntensityJitter(unittest.TestCase):
    """
    Gate 2 — apply_intensity_jitter(quantised, rng=None) → int in [0, 100].

    Contract §3:
    - Adds ±5 random jitter
    - Clamped to [0, 100]
    - RNG injectable for test determinism (rng: random.Random | None)
    """

    def test_intensity_jitter_applied_before_encode(self) -> None:
        """
        Gate 2 (MERGE-BLOCKING).

        apply_intensity_jitter() with a seeded RNG:
        - Produces a result within ±5 of the input
        - Clamps to [0, 100]
        - Is deterministic given the same seed
        """
        # Verify ±5 range with seeded RNG across multiple quantised inputs
        quantised_inputs = [0, 25, 50, 75, 100]
        for q in quantised_inputs:
            rng_local = random.Random(42)
            result = apply_intensity_jitter(q, rng=rng_local)
            assert 0 <= result <= 100, (
                f"apply_intensity_jitter({q}) = {result} — must be in [0, 100] (clamped)"
            )
            assert abs(result - q) <= 5 or (q == 0 and result >= 0) or (q == 100 and result <= 100), (
                f"apply_intensity_jitter({q}) = {result} — jitter must be ≤ 5 before clamp. "
                f"pre-clamp value was likely {result} (|{result} - {q}| = {abs(result - q)})"
            )

    def test_jitter_deterministic_with_seeded_rng(self) -> None:
        """Same seed must produce same result every time (RNG injection contract §3)."""
        for q in [0, 25, 50, 75, 100]:
            r1 = apply_intensity_jitter(q, rng=random.Random(99))
            r2 = apply_intensity_jitter(q, rng=random.Random(99))
            assert r1 == r2, (
                f"apply_intensity_jitter({q}) is non-deterministic with same seed: "
                f"{r1} != {r2}. Injectable RNG must control all randomness."
            )

    def test_jitter_clamps_at_zero_lower_bound(self) -> None:
        """
        With quantised=0 and rng always returning -5, result must be 0 (not -5).
        """
        class AlwaysMinusFiveRng:
            def randint(self, a: int, b: int) -> int:
                return -5

        result = apply_intensity_jitter(0, rng=AlwaysMinusFiveRng())  # type: ignore[arg-type]
        assert result == 0, (
            f"apply_intensity_jitter(0, jitter=-5) should clamp to 0; got {result}. "
            f"Lower clamp boundary: contract §3."
        )

    def test_jitter_clamps_at_100_upper_bound(self) -> None:
        """
        With quantised=100 and rng always returning +5, result must be 100 (not 105).
        """
        class AlwaysPlusFiveRng:
            def randint(self, a: int, b: int) -> int:
                return 5

        result = apply_intensity_jitter(100, rng=AlwaysPlusFiveRng())  # type: ignore[arg-type]
        assert result == 100, (
            f"apply_intensity_jitter(100, jitter=+5) should clamp to 100; got {result}. "
            f"Upper clamp boundary: contract §3."
        )

    def test_jitter_without_rng_returns_int_in_range(self) -> None:
        """Default RNG path (rng=None): result must still be in [0, 100]."""
        for q in [0, 25, 50, 75, 100]:
            result = apply_intensity_jitter(q)
            assert isinstance(result, int), (
                f"apply_intensity_jitter({q}) must return int; got {type(result).__name__}"
            )
            assert 0 <= result <= 100, (
                f"apply_intensity_jitter({q}) = {result} out of [0, 100] range"
            )


# NOTE: pytest.mark.parametrize requires plain pytest class (not unittest.TestCase)
class TestJitterParametrized:
    """Parametrised boundary table for apply_intensity_jitter."""

    @pytest.mark.parametrize("q,jitter,expected", [
        (0,   0,  0),   # no jitter
        (0,  -5,  0),   # clamp at 0
        (0,   5,  5),   # no clamp needed
        (50, -5, 45),   # mid, negative jitter
        (50,  5, 55),   # mid, positive jitter
        (100,  5, 100), # clamp at 100
        (100, -5, 95),  # no clamp needed
        (25,  5, 30),   # non-boundary
        (75, -5, 70),   # non-boundary
    ])
    def test_jitter_at_all_quantised_levels(self, q: int, jitter: int, expected: int) -> None:
        """Parametrised table: verify every level + clamp at both extremes."""
        class FixedRng:
            def __init__(self, val: int) -> None:
                self._val = val
            def randint(self, a: int, b: int) -> int:
                return self._val

        result = apply_intensity_jitter(q, rng=FixedRng(jitter))  # type: ignore[arg-type]
        assert result == expected, (
            f"apply_intensity_jitter({q}, jitter={jitter}) → {result}, expected {expected}. "
            f"max(0, min(100, {q} + {jitter})) = {max(0, min(100, q + jitter))}"
        )


# ── I5: _send_neutral_fallback uses quantise+jitter pipeline ─────────────────

class TestSendNeutralFallbackPipeline(unittest.TestCase):
    """
    I5 — _send_neutral_fallback must route intensity through the same
    quantise_intensity → apply_intensity_jitter pipeline as _send_update.

    No special-case wire path: 0.5 → quantise → 50 → jitter → [45, 55].
    With a seeded RNG the result is deterministic.
    """

    def setUp(self):
        try:
            from host.main import _send_neutral_fallback, quantise_intensity, apply_intensity_jitter
            from host.familiar_protocol import SequenceCounter
        except ImportError as e:
            self.skipTest(f"Required imports unavailable: {e}")
        self._send_neutral_fallback = _send_neutral_fallback
        self._quantise = quantise_intensity
        self._jitter = apply_intensity_jitter
        self._SequenceCounter = SequenceCounter

    def test_fallback_intensity_is_quantised_and_jittered(self):
        """
        I5 (MERGE-BLOCKING integrity): fallback packet intensity must equal
        quantise_intensity(0.5) → 50 → apply_intensity_jitter(50, rng).

        This proves _send_neutral_fallback has NO special wire path — it uses
        the same Gate 2 pipeline as normal sends.
        """
        import asyncio
        import random
        from helpers import FakeTransport

        transport = FakeTransport()
        seq = self._SequenceCounter()
        seed = 1234

        # Pre-compute expected: same seed, same call order
        expected_q = self._quantise(0.5)       # must be 50
        expected_j = self._jitter(expected_q, rng=random.Random(seed))

        asyncio.run(self._send_neutral_fallback(transport, seq, rng=random.Random(seed)))

        assert len(transport.sent) == 1, (
            "_send_neutral_fallback must send exactly one packet."
        )
        packet = transport.sent[0]
        assert len(packet) == 6, f"FAMILIAR_UPDATE must be 6 bytes; got {len(packet)}."
        assert packet[0] == 0x80, f"Opcode must be 0x80; got 0x{packet[0]:02x}."
        assert packet[1] == 0, f"Mood must be NEUTRAL (0); got {packet[1]}."

        intensity_byte = packet[2]
        assert intensity_byte == expected_j, (
            f"Fallback intensity={intensity_byte} must equal quantised+jittered={expected_j} "
            f"(bucket 50 ±5). _send_neutral_fallback must use the Gate 2 pipeline, "
            f"not a raw/hard-coded wire value. (I5)"
        )
        # Also verify it's in the expected bucket neighbourhood
        assert abs(intensity_byte - 50) <= 5, (
            f"Fallback intensity={intensity_byte} must be within ±5 of bucket 50. "
            f"quantise_intensity(0.5)=50 → jitter ∈ [45, 55]."
        )

    def test_fallback_quantise_bucket_is_50(self):
        """quantise_intensity(0.5) must map to bucket 50 (the neutral midpoint)."""
        assert self._quantise(0.5) == 50, (
            f"quantise_intensity(0.5) = {self._quantise(0.5)}, expected 50. "
            "Neutral fallback uses 0.5 → bucket 50 (contract §3)."
        )


if __name__ == "__main__":
    unittest.main()
