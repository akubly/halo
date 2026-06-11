"""
Unit tests for host/inference.py — mood heuristic.

Tests the compute_mood() function: weighted tension calculation, threshold
logic, confidence gating, and sensor fallback paths.

See ARD §5.4 for the locked inference spec.
"""
# TODO: implement test cases once compute_mood body exists

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

    @pytest.mark.xfail(reason="Week 2 — compute_mood() not yet implemented")
    def test_high_pitch_variance_returns_stressed(self) -> None:
        # TODO: pass audio_pitch_variance above threshold; expect mood="stressed"
        raise NotImplementedError

    @pytest.mark.xfail(reason="Week 2 — compute_mood() not yet implemented")
    def test_low_tension_returns_calm(self) -> None:
        # TODO: pass all-low sensor values; expect mood="calm"
        raise NotImplementedError

    @pytest.mark.xfail(reason="Week 2 — compute_mood() not yet implemented")
    def test_confidence_gate_sets_gated_true(self) -> None:
        # TODO: construct inputs that yield confidence < CONFIDENCE_GATE;
        #       assert result.gated is True
        raise NotImplementedError

    @pytest.mark.xfail(reason="Week 2 — compute_mood() not yet implemented")
    def test_mic_only_fallback_reduces_confidence(self) -> None:
        # TODO: pass imu_acceleration=0, imu_rotation=0; confirm confidence < 0.7
        raise NotImplementedError

    @pytest.mark.xfail(reason="Week 2 — compute_mood() not yet implemented")
    def test_imu_only_fallback_reduces_confidence(self) -> None:
        # TODO: pass audio_rms=0, audio_pitch_variance=0; confirm confidence < 0.7
        raise NotImplementedError


if __name__ == "__main__":
    unittest.main()
