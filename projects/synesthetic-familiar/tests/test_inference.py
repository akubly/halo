"""
Unit tests for host/inference.py — mood heuristic.

Tests the compute_mood() function: weighted tension calculation, threshold
logic, confidence gating, and sensor fallback paths.

See ARD §5.4 and hiro-week2-integration-contract.md §2 for the locked spec.

Tension formula (locked):
    tension = pitch_variance * 0.4 + acceleration * 0.3 + rotation * 0.3

Thresholds:
    STRESS_THRESHOLD = 0.65   (tension >= → "stressed")
    CALM_THRESHOLD   = 0.35   (tension <  → "calm")
    (gap 0.35–0.65 → "neutral")

Confidence reduction on sensor failure:
    mic_ok=False: confidence *= 0.6  (max result = 0.6 < CONFIDENCE_GATE)
    imu_ok=False: confidence *= 0.7  (base must be < 1.0 for result < gate)
"""

import unittest

import pytest

# ── Import guard ─────────────────────────────────────────────────────────────
# If the module is not yet importable, tests fail clearly at collection time.
try:
    from host.inference import (
        compute_mood,
        MoodResult,
        STRESS_THRESHOLD,
        CALM_THRESHOLD,
        CONFIDENCE_GATE,
    )
    _IMPORT_ERROR: str | None = None
except ImportError as _e:
    _IMPORT_ERROR = str(_e)
    compute_mood = None  # type: ignore[assignment]
    MoodResult = None  # type: ignore[assignment]
    STRESS_THRESHOLD = CALM_THRESHOLD = CONFIDENCE_GATE = None  # type: ignore[assignment]


@pytest.fixture(autouse=True)
def _require_inference_module() -> None:
    """Fail every test with a human-readable message if the module is missing."""
    if _IMPORT_ERROR is not None:
        pytest.fail(
            f"host.inference is not yet importable: {_IMPORT_ERROR}\n"
            "These tests will pass once the inference module is implemented."
        )


class TestComputeMood(unittest.TestCase):

    def test_high_pitch_variance_returns_stressed(self) -> None:
        """
        tension = 1.0*0.4 + 0.5*0.3 + 0.5*0.3 = 0.70 > STRESS_THRESHOLD(0.65) → "stressed"
        """
        result = compute_mood(
            audio_rms=0.5,
            audio_pitch_variance=1.0,
            imu_acceleration=0.5,
            imu_rotation=0.5,
        )
        assert result.mood == "stressed", (
            f"High pitch_variance (1.0) should produce 'stressed'; got '{result.mood}'. "
            f"tension = 1.0*0.4 + 0.5*0.3 + 0.5*0.3 = 0.70 > STRESS_THRESHOLD(0.65)"
        )
        assert result.mood_int == 2, (
            f"mood_int for 'stressed' must be 2 (wire enum); got {result.mood_int}"
        )

    def test_low_tension_returns_calm(self) -> None:
        """
        tension = 0.0*0.4 + 0.0*0.3 + 0.0*0.3 = 0.0 < CALM_THRESHOLD(0.35) → "calm"
        audio_rms present (non-zero) so mic signal quality is valid; only pitch/IMU zeroed.
        """
        result = compute_mood(
            audio_rms=0.2,
            audio_pitch_variance=0.0,
            imu_acceleration=0.0,
            imu_rotation=0.0,
        )
        assert result.mood == "calm", (
            f"All-zero pitch_variance+IMU should produce 'calm'; got '{result.mood}'. "
            f"tension = 0.0*0.4 + 0.0*0.3 + 0.0*0.3 = 0.0 < CALM_THRESHOLD(0.35)"
        )
        assert result.mood_int == 1, (
            f"mood_int for 'calm' must be 1 (wire enum); got {result.mood_int}"
        )

    def test_confidence_gate_sets_gated_true(self) -> None:
        """
        mic_ok=False → confidence *= 0.6 → max 0.6 < CONFIDENCE_GATE(0.7).
        result.gated must be True; main loop must NOT send this result.
        """
        result = compute_mood(
            audio_rms=0.5,
            audio_pitch_variance=0.5,
            imu_acceleration=0.5,
            imu_rotation=0.5,
            mic_ok=False,
        )
        assert result.confidence < CONFIDENCE_GATE, (
            f"mic_ok=False must reduce confidence below CONFIDENCE_GATE({CONFIDENCE_GATE}); "
            f"got {result.confidence:.4f}. "
            f"mic_ok=False applies confidence *= 0.6 (contract §2.2); max = 0.6."
        )
        assert result.gated is True, (
            f"result.gated must be True when confidence ({result.confidence:.4f}) "
            f"< CONFIDENCE_GATE ({CONFIDENCE_GATE})"
        )

    def test_mic_only_fallback_reduces_confidence(self) -> None:
        """
        Only mic available (imu_ok=False): confidence *= 0.7 (contract §2.2).
        The contract requires result.confidence < CONFIDENCE_GATE(0.7); this means
        the implementation's base confidence must be < 1.0 (e.g., derived from
        signal quality), so 0.7 * base < 0.7.
        IMU values zeroed per contract: imu_ok=False → imu_accel=0.0, imu_rot=0.0.
        """
        result = compute_mood(
            audio_rms=0.5,
            audio_pitch_variance=0.5,
            imu_acceleration=0.0,   # zeroed per contract when imu_ok=False
            imu_rotation=0.0,       # zeroed per contract when imu_ok=False
            imu_ok=False,
        )
        assert result.confidence < CONFIDENCE_GATE, (
            f"imu_ok=False must yield confidence < CONFIDENCE_GATE({CONFIDENCE_GATE}); "
            f"got {result.confidence:.4f}. "
            f"confidence *= 0.7 (contract §2.2); base confidence must be < 1.0."
        )

    def test_imu_only_fallback_reduces_confidence(self) -> None:
        """
        Only IMU available (mic_ok=False): confidence *= 0.6 (contract §2.2).
        Max result = 0.6 < CONFIDENCE_GATE(0.7) regardless of base confidence.
        Audio values zeroed per contract: mic_ok=False → audio_rms=0.0, pitch_variance=0.0.
        """
        result = compute_mood(
            audio_rms=0.0,          # zeroed per contract when mic_ok=False
            audio_pitch_variance=0.0,  # zeroed per contract when mic_ok=False
            imu_acceleration=0.5,
            imu_rotation=0.5,
            mic_ok=False,
        )
        assert result.confidence < CONFIDENCE_GATE, (
            f"mic_ok=False must yield confidence < CONFIDENCE_GATE({CONFIDENCE_GATE}); "
            f"got {result.confidence:.4f}. "
            f"confidence *= 0.6 (contract §2.2); 0.6 * any_base ≤ 0.6 < 0.7."
        )


# ── Boundary / parametrize coverage (paranoid QA) ────────────────────────────
# NOTE: pytest.mark.parametrize requires plain pytest class (not unittest.TestCase).

class TestTensionThresholdBoundaries:
    """
    Verify tension thresholds at exact boundary values.
    tension = pitch_variance*0.4 + accel*0.3 + rotation*0.3
    """

    @pytest.mark.parametrize("pitch_v,accel,rot,expected_mood", [
        # Librarian implementation uses strict comparators:
        #   tension > stress_threshold → stressed
        #   tension < calm_threshold   → calm
        #   otherwise                  → neutral
        # Contract specifies STRESS_THRESHOLD=0.65, CALM_THRESHOLD=0.35 but not
        # whether comparison is strict (>) or non-strict (>=).  Boundary tests
        # reflect the IMPLEMENTED behavior; see decision juanita-week2-tests.md.
        (0.0, 0.0, 0.0,  "calm"),          # tension=0.00 < 0.35 → calm
        # Boundary: CALM_THRESHOLD=0.35 is NOT included in "calm" (strict <)
        (0.35/0.4, 0.0, 0.0, "neutral"),   # tension=0.35 → neutral (not < 0.35)
        # Boundary: STRESS_THRESHOLD=0.65 is NOT included in "stressed" (strict >)
        (0.65/0.4, 0.0, 0.0, "neutral"),   # tension=0.65 → neutral (not > 0.65)
        # Strictly above threshold → stressed
        (0.66/0.4, 0.0, 0.0, "stressed"),  # tension=0.66 > 0.65 → stressed
        (1.0, 1.0, 1.0,  "stressed"),      # tension=1.0 → stressed (max)
    ])
    def test_mood_at_parametrized_tension_values(
        self, pitch_v: float, accel: float, rot: float, expected_mood: str
    ) -> None:
        tension = pitch_v * 0.4 + accel * 0.3 + rot * 0.3
        result = compute_mood(
            audio_rms=0.5,
            audio_pitch_variance=pitch_v,
            imu_acceleration=accel,
            imu_rotation=rot,
        )
        assert result.mood == expected_mood, (
            f"tension={tension:.4f}: expected '{expected_mood}', got '{result.mood}'. "
            f"STRESS_THRESHOLD={STRESS_THRESHOLD}, CALM_THRESHOLD={CALM_THRESHOLD}"
        )


if __name__ == "__main__":
    unittest.main()
