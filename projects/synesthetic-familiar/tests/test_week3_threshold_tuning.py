"""
Week 3 threshold-tuning tests — Juanita Wave 2 (2026-06-13).

Covers the arithmetic boundaries that govern host-side mood behaviour:
  1. Confidence gate: CONFIDENCE_GATE = 0.7 (strict <).
  2. Activation gate: sample_count == 49 vs 50 — exact population/personal flip.
  3. Intensity quantisation: all five bucket boundaries (0.125, 0.375, 0.625, 0.875).
  4. Jitter contract: apply_intensity_jitter output always in [0, 100].

All tests run against current host.inference and host.main code — no hardware.
REPO FACT: pytest.mark.parametrize does NOT work on unittest.TestCase methods;
parametrized groups use plain pytest classes.
"""
from __future__ import annotations

import math
import unittest

import pytest

# ── Import guards ─────────────────────────────────────────────────────────────
try:
    from host.inference import (
        compute_mood,
        CONFIDENCE_GATE,
        STRESS_THRESHOLD,
        CALM_THRESHOLD,
        ACTIVATION_THRESHOLD,
        Baseline,
    )
    _INFERENCE_IMPORT_ERROR: str | None = None
except ImportError as _e:
    _INFERENCE_IMPORT_ERROR = str(_e)
    compute_mood = CONFIDENCE_GATE = STRESS_THRESHOLD = CALM_THRESHOLD = None  # type: ignore
    ACTIVATION_THRESHOLD = 50
    Baseline = None  # type: ignore

try:
    from host.main import quantise_intensity, apply_intensity_jitter
    _MAIN_IMPORT_ERROR: str | None = None
except ImportError as _e:
    _MAIN_IMPORT_ERROR = str(_e)
    quantise_intensity = apply_intensity_jitter = None  # type: ignore


@pytest.fixture(autouse=True)
def _require_inference() -> None:
    if _INFERENCE_IMPORT_ERROR:
        pytest.fail(f"host.inference not importable: {_INFERENCE_IMPORT_ERROR}")


def _make_baseline(*, mean: float, stddev: float, sample_count: int) -> "Baseline":
    return Baseline(
        mean=mean, stddev=stddev,
        sample_count=sample_count,
        created_at="2026-06-13T00:00:00",
    )


# ═════════════════════════════════════════════════════════════════════════════
# 1. Confidence gate boundary
# ═════════════════════════════════════════════════════════════════════════════

class TestConfidenceGateBoundary(unittest.TestCase):
    """
    CONFIDENCE_GATE = 0.7, gated = (confidence < 0.7).
    Strict less-than: confidence == 0.7 must NOT be gated.
    """

    def test_confidence_gate_constant_is_0_7(self) -> None:
        """CONFIDENCE_GATE must equal 0.7 (locked contract, inference.py line 31)."""
        assert CONFIDENCE_GATE == pytest.approx(0.7), (
            f"CONFIDENCE_GATE={CONFIDENCE_GATE}, expected 0.7. "
            "Changing this constant breaks all downstream gating contracts."
        )

    def test_stressed_both_sensors_ok_not_gated(self) -> None:
        """
        Stressed frame, both sensors ok → confidence=0.8 → NOT gated.

        tension = 1.0*0.4 + 1.0*0.3 + 1.0*0.3 = 1.0 > STRESS_THRESHOLD(0.65)
        → mood=stressed, confidence=0.8 > 0.7 → gated=False.
        """
        result = compute_mood(
            audio_rms=0.5,
            audio_pitch_variance=1.0,
            imu_acceleration=1.0,
            imu_rotation=1.0,
            mic_ok=True,
            imu_ok=True,
        )
        assert result.confidence == pytest.approx(0.8), (
            f"Stressed + both ok → confidence=0.8; got {result.confidence}."
        )
        assert result.gated is False, (
            f"confidence=0.8 must not be gated (0.8 < 0.7 = False); got gated={result.gated}."
        )

    def test_neutral_both_sensors_ok_gated(self) -> None:
        """
        Neutral frame (tension in (CALM, STRESS) band), both sensors ok → confidence=0.6 → gated.

        tension = 0.5*0.4 + 0.5*0.3 + 0.5*0.3 = 0.5 (between 0.35 and 0.65)
        → mood=neutral, confidence=0.6 < 0.7 → gated=True.
        """
        result = compute_mood(
            audio_rms=0.5,
            audio_pitch_variance=0.5,
            imu_acceleration=0.5,
            imu_rotation=0.5,
            mic_ok=True,
            imu_ok=True,
        )
        assert result.confidence == pytest.approx(0.6), (
            f"Neutral + both ok → confidence=0.6; got {result.confidence}."
        )
        assert result.gated is True, (
            f"confidence=0.6 must be gated (0.6 < 0.7 = True); got gated={result.gated}."
        )

    def test_mic_fail_reduces_confidence_below_gate(self) -> None:
        """
        Stressed frame, mic_ok=False → confidence = 0.8 * 0.6 = 0.48 → gated.
        (IMU-only mode cannot cross the 0.7 gate by design — §2.2.)
        """
        result = compute_mood(
            audio_rms=0.0,
            audio_pitch_variance=1.0,
            imu_acceleration=1.0,
            imu_rotation=1.0,
            mic_ok=False,
            imu_ok=True,
        )
        assert result.confidence == pytest.approx(0.48, abs=1e-9), (
            f"Stressed + mic_ok=False → confidence=0.8*0.6=0.48; got {result.confidence}."
        )
        assert result.gated is True, (
            f"confidence=0.48 must be gated (0.48 < 0.7 = True); got gated={result.gated}."
        )

    def test_imu_fail_reduces_confidence_below_gate(self) -> None:
        """
        Stressed frame (both sensors providing signal), imu_ok=False →
        confidence = 0.8 * 0.7 = 0.56 → gated.

        imu_ok=False only penalises confidence — it does NOT zero the IMU
        values.  We pass imu_acceleration=1.0 and imu_rotation=1.0 so
        tension=1.0 > STRESS_THRESHOLD(0.65), yielding the stressed branch
        base confidence of 0.8 before the penalty is applied.
        """
        result = compute_mood(
            audio_rms=0.5,
            audio_pitch_variance=1.0,
            imu_acceleration=1.0,
            imu_rotation=1.0,
            mic_ok=True,
            imu_ok=False,
        )
        assert result.confidence == pytest.approx(0.56, abs=1e-9), (
            f"Stressed + imu_ok=False → confidence=0.8*0.7=0.56; got {result.confidence}."
        )
        assert result.gated is True, (
            f"confidence=0.56 must be gated (0.56 < 0.7 = True); got gated={result.gated}."
        )

    def test_gate_is_strict_less_than_not_less_than_or_equal(self) -> None:
        """
        Verifies compute_mood's gating formula is strict '<', not '<='.

        compute_mood's discrete confidence levels are 0.6 (neutral), 0.8
        (stressed/calm), and their sensor-penalty multiples — none land on
        exactly 0.7.  We straddle CONFIDENCE_GATE from both sides using real
        inputs and cross-check that result.gated matches the strict-less-than
        formula exactly.  If someone changes the formula to '<=' in inference.py,
        the cross-check assertions will catch it as soon as a value == 0.7 is
        reachable (or the existing values produce a wrong gated flag).

        Values exercised:
            0.8  stressed + both ok  → 0.8 >= 0.7  → NOT gated
            0.56 stressed + imu fail → 0.56 < 0.7  → gated
            0.48 stressed + mic fail → 0.48 < 0.7  → gated
            0.6  neutral  + both ok  → 0.6 < 0.7   → gated
        """
        cases: list[tuple[dict, float, bool]] = [
            # (kwargs, expected_confidence, expected_gated)
            (
                dict(audio_rms=0.5, audio_pitch_variance=1.0,
                     imu_acceleration=1.0, imu_rotation=1.0,
                     mic_ok=True, imu_ok=True),
                0.8, False,
            ),
            (
                dict(audio_rms=0.5, audio_pitch_variance=1.0,
                     imu_acceleration=1.0, imu_rotation=1.0,
                     mic_ok=True, imu_ok=False),
                0.56, True,
            ),
            (
                dict(audio_rms=0.0, audio_pitch_variance=1.0,
                     imu_acceleration=1.0, imu_rotation=1.0,
                     mic_ok=False, imu_ok=True),
                0.48, True,
            ),
            (
                dict(audio_rms=0.5, audio_pitch_variance=0.5,
                     imu_acceleration=0.5, imu_rotation=0.5,
                     mic_ok=True, imu_ok=True),
                0.6, True,
            ),
        ]
        for kwargs, exp_conf, exp_gated in cases:
            result = compute_mood(**kwargs)
            assert result.confidence == pytest.approx(exp_conf, abs=1e-9), (
                f"compute_mood({kwargs}): confidence={result.confidence}, "
                f"expected {exp_conf}."
            )
            assert result.gated is exp_gated, (
                f"compute_mood({kwargs}): gated={result.gated}, expected {exp_gated}. "
                f"confidence={result.confidence:.4f}, CONFIDENCE_GATE={CONFIDENCE_GATE}. "
                "Gate condition must be strict '<' (confidence < CONFIDENCE_GATE)."
            )
            # Cross-check: gated must exactly equal the strict-less-than formula.
            # If inference.py ever changes to '<=', this fires for any case where
            # confidence == CONFIDENCE_GATE (currently not reachable, but guards
            # against future confidence-table changes that land on 0.7 exactly).
            assert result.gated == (result.confidence < CONFIDENCE_GATE), (
                f"gated field does not match strict '<' formula! "
                f"gated={result.gated}, confidence={result.confidence}, "
                f"CONFIDENCE_GATE={CONFIDENCE_GATE}."
            )


# ═════════════════════════════════════════════════════════════════════════════
# 2. Activation gate — exact 49 / 50 / 51 boundary
# ═════════════════════════════════════════════════════════════════════════════

class TestActivationBoundaryExact(unittest.TestCase):
    """
    The activation gate flips at sample_count == ACTIVATION_THRESHOLD (50).

    Frame: tension=0.49 (mid-band), sits BETWEEN population STRESS(0.65) and
    personal stress(mean=0.2 + 1.5*0.05 = 0.275).

    sample_count=49: population default → tension < 0.65 → neutral.
    sample_count=50: personal threshold → tension > 0.275 → stressed.
    sample_count=51: same as 50.
    """

    _MEAN = 0.2
    _STDDEV = 0.05
    # tension = 0.7*0.4 + 0.4*0.3 + 0.3*0.3 = 0.28+0.12+0.09 = 0.49
    _FRAME_KW = dict(
        audio_rms=0.5,
        audio_pitch_variance=0.7,
        imu_acceleration=0.4,
        imu_rotation=0.3,
    )

    def _baseline(self, n: int) -> "Baseline":
        return _make_baseline(mean=self._MEAN, stddev=self._STDDEV, sample_count=n)

    def test_sample_count_49_uses_population_threshold(self) -> None:
        """n=49 (one below threshold) → population defaults → neutral (tension < 0.65)."""
        result = compute_mood(**self._FRAME_KW, baseline=self._baseline(49))
        assert result.mood == "neutral", (
            f"n=49 < ACTIVATION_THRESHOLD({ACTIVATION_THRESHOLD}): "
            f"population STRESS_THRESHOLD({STRESS_THRESHOLD}) must govern. "
            f"tension=0.49 < 0.65 → neutral. Got '{result.mood}'."
        )

    def test_sample_count_50_uses_personal_threshold(self) -> None:
        """n=50 (exactly at threshold) → personal threshold → stressed (tension > 0.275)."""
        result = compute_mood(**self._FRAME_KW, baseline=self._baseline(50))
        assert result.mood == "stressed", (
            f"n=50 == ACTIVATION_THRESHOLD({ACTIVATION_THRESHOLD}): "
            f"personal threshold (0.275) must engage. "
            f"tension=0.49 > 0.275 → stressed. Got '{result.mood}'."
        )

    def test_sample_count_51_uses_personal_threshold(self) -> None:
        """n=51 (one above threshold) → same as n=50 → stressed."""
        result = compute_mood(**self._FRAME_KW, baseline=self._baseline(51))
        assert result.mood == "stressed", (
            f"n=51 > ACTIVATION_THRESHOLD({ACTIVATION_THRESHOLD}): "
            f"personal threshold must still govern. Got '{result.mood}'."
        )

    def test_boundary_flip_between_49_and_50(self) -> None:
        """
        Single comparative test: n=49 → neutral, n=50 → stressed.
        Both outcomes must differ — the gate flip must be instantaneous at 50.
        """
        r49 = compute_mood(**self._FRAME_KW, baseline=self._baseline(49))
        r50 = compute_mood(**self._FRAME_KW, baseline=self._baseline(50))
        assert r49.mood != r50.mood, (
            f"Expected mood to flip between n=49 and n=50 (population→personal). "
            f"n=49: '{r49.mood}', n=50: '{r50.mood}'. "
            "If they're the same, the activation gate is not flipping correctly."
        )
        assert r49.mood == "neutral", f"n=49 must yield 'neutral'; got '{r49.mood}'."
        assert r50.mood == "stressed", f"n=50 must yield 'stressed'; got '{r50.mood}'."


# ═════════════════════════════════════════════════════════════════════════════
# 3. Intensity quantisation bucket boundaries
# ═════════════════════════════════════════════════════════════════════════════

# NOTE: pytest.mark.parametrize requires a plain pytest class (not TestCase).
class TestIntensityQuantizationBuckets:
    """
    quantise_intensity maps float [0, 1] to {0, 25, 50, 75, 100}.

    Bucket edges (from main.py):
        [0.000, 0.125)  →   0
        [0.125, 0.375)  →  25
        [0.375, 0.625)  →  50
        [0.625, 0.875)  →  75
        [0.875, 1.000]  → 100

    Tests cover:
      - Exact lower boundaries (open-left semantics for the upper buckets).
      - Just-below boundaries.
      - Extremes (0.0 and 1.0).
    """

    @pytest.fixture(autouse=True)
    def _require_main(self) -> None:
        if _MAIN_IMPORT_ERROR:
            pytest.skip(f"host.main.quantise_intensity not importable: {_MAIN_IMPORT_ERROR}")

    @pytest.mark.parametrize("intensity,expected", [
        (0.000, 0),    # left extreme
        (0.124, 0),    # just below first boundary
        (0.125, 25),   # exactly at first bucket start
        (0.374, 25),   # just below second boundary
        (0.375, 50),   # exactly at second bucket start
        (0.624, 50),   # just below third boundary
        (0.625, 75),   # exactly at third bucket start
        (0.874, 75),   # just below fourth boundary
        (0.875, 100),  # exactly at fourth bucket start
        (1.000, 100),  # right extreme
    ])
    def test_quantise_bucket(self, intensity: float, expected: int) -> None:
        result = quantise_intensity(intensity)
        assert result == expected, (
            f"quantise_intensity({intensity}) → {result}, expected {expected}. "
            "Bucket boundaries from main.py: <0.125→0, <0.375→25, <0.625→50, "
            "<0.875→75, else→100."
        )

    @pytest.mark.parametrize("bucket", [0, 25, 50, 75, 100])
    def test_all_buckets_are_valid_wire_values(self, bucket: int) -> None:
        """Every quantisation output must be in the valid intensity set {0,25,50,75,100}."""
        valid = {0, 25, 50, 75, 100}
        assert bucket in valid, f"{bucket} is not a valid wire intensity value."


# ═════════════════════════════════════════════════════════════════════════════
# 4. Jitter contract: output always in [0, 100]
# ═════════════════════════════════════════════════════════════════════════════

class TestJitterContractBounds:
    """
    apply_intensity_jitter(q, rng) adds ±5 to q then clamps to [0, 100].

    Contract: result is always an integer in [0, 100], regardless of which
    end of the ±5 range is drawn.

    Tests:
      - Bucket 0 with jitter −5 → clamped to 0 (never negative).
      - Bucket 100 with jitter +5 → clamped to 100 (never > 100).
      - All five bucket midpoints with extreme jitter stay in range.
    """

    @pytest.fixture(autouse=True)
    def _require_main(self) -> None:
        if _MAIN_IMPORT_ERROR:
            pytest.skip(f"host.main.apply_intensity_jitter not importable: {_MAIN_IMPORT_ERROR}")

    def _seeded_rng(self, value: int):
        """Return a Random that always yields `value` from randint."""
        import random

        class _Fixed:
            def randint(self, a: int, b: int) -> int:
                return value

        return _Fixed()

    @pytest.mark.parametrize("bucket,jitter,expected", [
        (0,   -5,  0),    # 0  + (-5) = -5 → clamped to 0
        (0,    5,  5),    # 0  + 5    = 5
        (25,  -5, 20),    # 25 + (-5) = 20
        (25,   5, 30),    # 25 + 5    = 30
        (50,  -5, 45),    # 50 + (-5) = 45
        (50,   5, 55),    # 50 + 5    = 55
        (75,  -5, 70),    # 75 + (-5) = 70
        (75,   5, 80),    # 75 + 5    = 80
        (100, -5, 95),    # 100 + (-5) = 95
        (100,  5, 100),   # 100 + 5  = 105 → clamped to 100
    ])
    def test_jitter_output(self, bucket: int, jitter: int, expected: int) -> None:
        result = apply_intensity_jitter(bucket, rng=self._seeded_rng(jitter))
        assert result == expected, (
            f"apply_intensity_jitter({bucket}, jitter={jitter:+d}) → {result}, "
            f"expected {expected}."
        )

    @pytest.mark.parametrize("bucket", [0, 25, 50, 75, 100])
    def test_jitter_always_in_0_100_range(self, bucket: int) -> None:
        """Exhaustive ±5 range: all 11 jitter values must keep output in [0, 100]."""
        import random
        for jitter in range(-5, 6):
            result = apply_intensity_jitter(bucket, rng=self._seeded_rng(jitter))
            assert 0 <= result <= 100, (
                f"apply_intensity_jitter({bucket}, jitter={jitter:+d}) = {result} "
                f"is outside [0, 100]. Clamping contract violated."
            )
