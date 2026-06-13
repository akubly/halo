"""
Regression tests for B1 — baseline must learn raw tension, not intensity.

B1 blocker: run() was passing result.intensity to update_baseline() instead
of result.tension.  For a "calm" frame, intensity = 1 - tension, so the
baseline was learning the INVERSE signal.  This silently poisoned the personal
stress threshold (mean + 1.5 × stddev).

These tests would have CAUGHT the bug before landing.

B1a — compute_mood populates result.tension with the raw weighted score,
      and for a calm frame tension ≠ intensity (they are demonstrably different).

B1b — run() calls update_baseline(baseline, result.tension) NOT result.intensity.
      A spy on update_baseline verifies the exact value passed.
"""
from __future__ import annotations

import asyncio
import math
import unittest
import unittest.mock

import pytest

try:
    from host.inference import compute_mood, update_baseline, Baseline
    from host.main import run
    from host.sensors import SensorFrame
    _IMPORT_ERROR: str | None = None
except ImportError as _e:
    _IMPORT_ERROR = str(_e)
    compute_mood = update_baseline = Baseline = run = SensorFrame = None  # type: ignore


@pytest.fixture(autouse=True)
def _require_modules():
    if _IMPORT_ERROR is not None:
        pytest.fail(f"Required modules not importable: {_IMPORT_ERROR}")


# ── B1a: compute_mood populates tension correctly ─────────────────────────────

class TestComputeMoodTensionField(unittest.TestCase):
    """B1a — compute_mood must populate result.tension with the raw weighted score."""

    def test_tension_field_equals_weighted_formula(self):
        """
        B1 regression (B1a): result.tension must equal pitch*0.4 + accel*0.3 + rot*0.3.

        This is the locked ARD §5.4 / §2.6 contract.  A missing or
        mis-populated tension field would let the bug silently survive.
        """
        pitch_v = 0.6
        accel   = 0.4
        rot     = 0.2
        expected_tension = pitch_v * 0.4 + accel * 0.3 + rot * 0.3

        result = compute_mood(
            audio_rms=0.5,
            audio_pitch_variance=pitch_v,
            imu_acceleration=accel,
            imu_rotation=rot,
        )
        assert hasattr(result, "tension"), (
            "MoodResult must have a 'tension' field (locked §2.6 B1 amendment). "
            "Without it, run() cannot pass raw tension to update_baseline."
        )
        assert result.tension == pytest.approx(expected_tension, abs=1e-9), (
            f"result.tension={result.tension:.6f} must equal raw weighted score "
            f"{expected_tension:.6f} = pitch({pitch_v})*0.4 + accel({accel})*0.3 + "
            f"rot({rot})*0.3.  B1 contract §2.6."
        )

    def test_calm_frame_tension_differs_from_intensity(self):
        """
        B1 regression (B1a): for a CALM frame, tension ≠ intensity.

        This is the canary — the bug passed result.intensity instead of
        result.tension to update_baseline.  For calm: intensity = 1 - tension,
        so they are maximally different when tension is near 0.
        """
        result = compute_mood(
            audio_rms=0.2,
            audio_pitch_variance=0.0,   # → tension = 0.0 < CALM_THRESHOLD
            imu_acceleration=0.0,
            imu_rotation=0.0,
        )
        assert result.mood == "calm", (
            f"Expected 'calm' with zero sensor inputs; got '{result.mood}'. "
            "Test setup error — adjust inputs so mood is calm."
        )
        assert result.tension != pytest.approx(result.intensity, abs=1e-6), (
            f"For a calm frame, tension={result.tension:.4f} should DIFFER from "
            f"intensity={result.intensity:.4f}.  "
            f"calm: intensity=1-tension, so tension≈0 and intensity≈1 are distinct.  "
            f"If they are equal, the B1 invariant (tension field) is broken."
        )
        # Verify the specific relationship: for calm, intensity = 1 - tension
        assert result.intensity == pytest.approx(1.0 - result.tension, abs=1e-9), (
            f"For calm mood: intensity must equal 1 - tension.  "
            f"intensity={result.intensity:.4f}, 1-tension={1.0 - result.tension:.4f}."
        )


# ── B1b: run() passes tension (not intensity) to update_baseline ──────────────

class TestRunUsesRawTensionForBaseline(unittest.TestCase):
    """
    B1b — regression test that would have CAUGHT the B1 bug.

    Injects a calm SensorFrame (where tension ≠ intensity), spies on
    update_baseline, and asserts the second argument is tension, not intensity.
    """

    def _make_calm_frame(self):
        """Calm frame: all-zero sensor inputs → tension=0.0, intensity=1.0."""
        return SensorFrame(
            audio_rms=0.2,
            audio_pitch_variance=0.0,
            imu_acceleration=0.0,
            imu_rotation=0.0,
            mic_ok=True,
            imu_ok=True,
        )

    def test_run_baseline_update_receives_tension_not_intensity(self):
        """
        B1 regression test (MERGE-BLOCKING equivalent).

        For a calm frame: tension=0.0, intensity=1.0 (demonstrably different).
        Spies on update_baseline to capture the value passed by run().
        Asserts it equals tension (0.0), not intensity (1.0).

        The original bug: `update_baseline(baseline, result.intensity)` was
        called instead of `update_baseline(baseline, result.tension)`.
        """
        from helpers import FakeTransport, FakeClock, noop_sleep

        transport = FakeTransport()
        calm_frame = self._make_calm_frame()
        stream_frames = [calm_frame]

        # Pre-compute expected values for the calm frame
        expected_tension   = 0.0 * 0.4 + 0.0 * 0.3 + 0.0 * 0.3   # = 0.0
        expected_intensity = 1.0 - expected_tension                  # = 1.0 (calm: 1-tension)

        captured_calls: list[dict] = []
        real_update_baseline = update_baseline

        def spy_update_baseline(baseline, tension):
            captured_calls.append({"baseline": baseline, "tension": tension})
            return real_update_baseline(baseline, tension)

        from host.sensors import FakeSensorStream

        async def _drive() -> None:
            s = FakeSensorStream(stream_frames)
            with unittest.mock.patch("host.main.update_baseline",
                                     side_effect=spy_update_baseline), \
                 unittest.mock.patch("host.main.load_baseline", return_value=None), \
                 unittest.mock.patch("host.main.save_baseline"):
                await run(transport, s, clock=FakeClock(step=1.0), sleep=noop_sleep)

        asyncio.run(_drive())

        assert len(captured_calls) == 1, (
            f"Expected update_baseline called once for 1 calm ungated frame; "
            f"got {len(captured_calls)} calls.  "
            f"Ensure the calm frame is ungated (mic_ok=True, imu_ok=True → confidence=0.8)."
        )

        actual_value = captured_calls[0]["tension"]

        assert actual_value == pytest.approx(expected_tension, abs=1e-9), (
            f"B1 REGRESSION: update_baseline received value={actual_value:.6f} "
            f"but expected tension={expected_tension:.6f}.  "
            f"(intensity for this calm frame would be {expected_intensity:.6f}).  "
            f"run() must pass result.tension, not result.intensity, to update_baseline.  "
            f"This test would have CAUGHT the B1 bug (ARD §2.6)."
        )

        # Extra guard: verify it is NOT the intensity value
        assert actual_value != pytest.approx(expected_intensity, abs=1e-6), (
            f"B1 REGRESSION: update_baseline received intensity={expected_intensity} "
            f"instead of tension={expected_tension}.  "
            f"The B1 bug (result.intensity → update_baseline) is still present."
        )


if __name__ == "__main__":
    unittest.main()
