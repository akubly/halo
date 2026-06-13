"""
Regression tests for B2 — run() is the SOLE pacer; SensorStream must not self-pace.

B2 blocker: SensorStream.__anext__ had its own asyncio.sleep(0.1) AND run() slept
on the normal-send path — but not on the gated or both-fail continue paths.
Result: ~200ms/iter on real hardware (5 Hz instead of 10 Hz), and gated/both-fail
frames spun without any rate-limiting.

B2a — STRUCTURAL: SensorStream.__anext__ must contain no sleep call.
      Verified via source inspection (non-flaky, instant).

B2b — BEHAVIORAL (gated path): run() must invoke sleep on every gated frame.
      Verified by injecting a spy sleeper and counting calls.

B2c — BEHAVIORAL (both-fail path): run() must invoke sleep on every both-fail frame.
      Verified by injecting a spy sleeper and counting calls.

Sleep is injectable (default asyncio.sleep) via run()'s sleep= parameter — this
makes the tests fast AND the assertions deterministic.
"""
from __future__ import annotations

import asyncio
import inspect
import unittest

import pytest

try:
    from host.main import run, CONFIDENCE_HOLD_TIMEOUT_S, BOTH_FAIL_TIMEOUT_S
    from host.sensors import SensorStream, SensorFrame, FakeSensorStream
    _IMPORT_ERROR: str | None = None
except ImportError as _e:
    _IMPORT_ERROR = str(_e)
    run = SensorStream = SensorFrame = FakeSensorStream = None  # type: ignore
    CONFIDENCE_HOLD_TIMEOUT_S = BOTH_FAIL_TIMEOUT_S = 30.0


@pytest.fixture(autouse=True)
def _require_modules():
    if _IMPORT_ERROR is not None:
        pytest.fail(f"Required modules not importable: {_IMPORT_ERROR}")


# ── B2a: Structural — SensorStream.__anext__ has no sleep ────────────────────

class TestSensorStreamNoPacing(unittest.TestCase):
    """
    B2a structural regression: SensorStream.__anext__ must not contain any
    asyncio.sleep or time.sleep call.

    The main loop's finally block is the SOLE pacer (B2 fix).  Any sleep in
    __anext__ creates a second pacer, halving the effective frame rate.

    Verified via source inspection — non-flaky, ~0ms.
    """

    def test_sensor_stream_anext_contains_no_sleep(self):
        """
        B2 regression (structural).

        Inspect the source of SensorStream.__anext__ and assert it contains
        no asyncio.sleep or time.sleep call.  If this test fails, the double-
        pacing bug has been re-introduced.
        """
        source = inspect.getsource(SensorStream.__anext__)

        assert "asyncio.sleep" not in source, (
            "B2 REGRESSION: SensorStream.__anext__ contains asyncio.sleep.  "
            "This re-introduces double-pacing (~200ms/iter instead of ~100ms).  "
            "Pacing belongs EXCLUSIVELY in run()'s unconditional finally block."
        )
        assert "time.sleep" not in source, (
            "B2 REGRESSION: SensorStream.__anext__ contains time.sleep.  "
            "Blocking sleep in an async iterator stalls the event loop.  "
            "Pacing belongs EXCLUSIVELY in run()'s unconditional finally block."
        )

    def test_sensor_stream_anext_docstring_documents_no_pacing(self):
        """
        B2 contract documentation: __anext__'s docstring must acknowledge that
        rate-pacing has been removed and the main loop owns it.

        Ng added this comment as part of the B2 fix.  If the doc disappears,
        the next developer won't know why there's no sleep here.
        """
        source = inspect.getsource(SensorStream.__anext__)
        # The doc should mention pacing/rate is owned by run() or main loop.
        # Accept any of several reasonable phrasings.
        indicators = ["pace", "rate", "run()", "main loop", "sole"]
        found = any(ind.lower() in source.lower() for ind in indicators)
        assert found, (
            "B2: SensorStream.__anext__ should document that pacing is removed "
            "and owned by the main loop.  Expected one of: "
            + str(indicators)
        )


# ── B2b/B2c: Behavioral — run() sleeps on ALL paths ──────────────────────────

def _make_gated_frame():
    """mic_ok=False → confidence *= 0.6 → max 0.6 < CONFIDENCE_GATE → gated."""
    return SensorFrame(
        audio_rms=0.5,
        audio_pitch_variance=0.5,
        imu_acceleration=0.5,
        imu_rotation=0.5,
        mic_ok=False,
        imu_ok=True,
    )


def _make_both_fail_frame():
    """Both mic_ok=False and imu_ok=False."""
    return SensorFrame(
        audio_rms=0.0,
        audio_pitch_variance=0.0,
        imu_acceleration=0.0,
        imu_rotation=0.0,
        mic_ok=False,
        imu_ok=False,
    )


class TestRunPacingUnconditional(unittest.TestCase):
    """
    B2b/B2c behavioral regression: run()'s sleep must be invoked unconditionally —
    on the normal-send path AND on gated/both-fail continue paths.

    Injects a spy sleeper (sleep=spy_sleep) so assertions are:
    - Instant (no real 0.1s overhead)
    - Deterministic (count == frames fed)

    FakeClock with small step keeps timeout counters below CONFIDENCE_HOLD and
    BOTH_FAIL thresholds, so neither timeout fires during the test window.
    """

    def _run_with_spy(self, frames: list, n_frames: int) -> list[float]:
        """
        Run the main loop feeding `n_frames` copies of each frame in `frames`,
        injecting a spy sleeper.  Returns the list of sleep durations called.
        """
        from helpers import FakeTransport, FakeClock

        transport = FakeTransport()
        stream = FakeSensorStream(frames * n_frames)
        sleep_calls: list[float] = []

        async def spy_sleep(seconds: float) -> None:
            sleep_calls.append(seconds)

        # step=0.5 keeps tick_start well below all timeouts for small frame counts
        fake_clock = FakeClock(step=0.5)

        import unittest.mock
        async def _drive():
            with unittest.mock.patch("host.main.load_baseline", return_value=None), \
                 unittest.mock.patch("host.main.save_baseline"):
                await run(transport, stream, clock=fake_clock, sleep=spy_sleep)

        asyncio.run(_drive())
        return sleep_calls

    def test_run_sleeps_on_gated_path(self):
        """
        B2b regression: run() must sleep on every confidence-gated frame.

        If sleep is missing on the gated path, continuous low-confidence
        periods spin the event loop at CPU speed (busy-wait).  This test
        would have caught the original B2 bug where sleep only lived in
        the normal-send path.
        """
        n_frames = 5
        sleep_calls = self._run_with_spy([_make_gated_frame()], n_frames)

        assert len(sleep_calls) == n_frames, (
            f"B2 REGRESSION (gated path): expected sleep called {n_frames} times "
            f"(once per gated frame), got {len(sleep_calls)}.  "
            f"run()'s pacer must be unconditional — in finally, not only on normal-send path."
        )
        for i, s in enumerate(sleep_calls):
            assert s >= 0.0, (
                f"B2: sleep call {i} received negative duration {s:.4f}. "
                "max(0.0, ...) must clamp negative elapsed times."
            )

    def test_run_sleeps_on_both_fail_path(self):
        """
        B2c regression: run() must sleep on every both-sensors-fail frame.

        Both-fail takes an early `continue` before inference.  Without the
        unconditional finally-block pacer, this path would spin at CPU speed.
        """
        n_frames = 5
        sleep_calls = self._run_with_spy([_make_both_fail_frame()], n_frames)

        assert len(sleep_calls) == n_frames, (
            f"B2 REGRESSION (both-fail path): expected sleep called {n_frames} times "
            f"(once per both-fail frame), got {len(sleep_calls)}.  "
            f"run()'s pacer must cover the both-sensors-fail continue path."
        )
        for i, s in enumerate(sleep_calls):
            assert s >= 0.0, (
                f"B2: sleep call {i} received negative duration {s:.4f}."
            )

    def test_run_sleeps_on_normal_send_path(self):
        """
        Sanity: run() also sleeps on the normal (ungated) send path.

        A normal send is: mic_ok=True, imu_ok=True, low tension → calm → ungated.
        """
        calm_frame = SensorFrame(
            audio_rms=0.2,
            audio_pitch_variance=0.0,
            imu_acceleration=0.0,
            imu_rotation=0.0,
            mic_ok=True,
            imu_ok=True,
        )
        n_frames = 3
        sleep_calls = self._run_with_spy([calm_frame], n_frames)

        assert len(sleep_calls) == n_frames, (
            f"run() must sleep on the normal send path too: expected {n_frames} "
            f"sleep calls, got {len(sleep_calls)}."
        )

    def test_sleep_duration_is_non_negative(self):
        """
        run() must never pass a negative duration to sleep — max(0, ...) guards it.

        Drive a mix of gated and both-fail frames and verify every sleep call ≥ 0.
        """
        mixed = [_make_gated_frame(), _make_both_fail_frame()]
        sleep_calls = self._run_with_spy(mixed, 4)  # 8 frames total

        negative = [s for s in sleep_calls if s < 0.0]
        assert not negative, (
            f"B2: {len(negative)} sleep calls had negative durations: {negative}.  "
            "run() must clamp with max(0.0, UPDATE_INTERVAL - elapsed)."
        )


if __name__ == "__main__":
    unittest.main()
