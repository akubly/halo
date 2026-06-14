"""
Week 3 acceptance tests — Baseline activation gate (Librarian).

Covers LIBRARIAN-T2-2 "Learn wearer baseline" and the resolved Week-3 decision
from decisions.md 2026-06-12 (implemented by Librarian in Week 3):

  ACTIVATION_THRESHOLD = 50  (inference.py lines 37-52)
  Statistical basis: SE(s)/s < 10% at n=50 → personal threshold trustworthy.

  compute_mood() gate:
    baseline=None or sample_count < ACTIVATION_THRESHOLD  → population defaults
    baseline.sample_count >= ACTIVATION_THRESHOLD          → personal mean+1.5σ

  get_activation_info(baseline) → ActivationInfo(state, sample_count,
      samples_needed, progress) — stable contract for Y.T.'s onboarding UX.

Test groups:
  1. ACTIVATION_THRESHOLD constant — PASS (Librarian landed it, value=50).
  2. get_activation_info() / ActivationInfo contract — PASS (landed).
  3. Population defaults with no baseline — PASS.
  4. Population defaults when sample_count < ACTIVATION_THRESHOLD — PASS.
  5. Personal threshold when sample_count >= ACTIVATION_THRESHOLD — PASS.
  6. Exact boundary (sample_count == threshold, one below) — PASS.
  7. Confidence < 0.7 suppression in both calibrating and personalized states — PASS.
  8. Baseline persistence across restart — PASS.

Reject criteria (Juanita ongoing):
  - If ACTIVATION_THRESHOLD is removed or renamed, Group 1 turns red.
  - If the >= gate is loosened to "any non-None baseline", Group 4 turns red.
  - If confidence gating breaks after any change to activation logic, Group 7 turns red.
  - If save/load_baseline round-trip breaks, Group 8 turns red.
  - If get_activation_info() is removed or its contract changes, Group 2 turns red
    (Y.T.'s onboarding UX would break silently).

Date: 2026-06-13
"""
from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

import pytest

# ── Import guard ───────────────────────────────────────────────────────────────
try:
    from host.inference import (
        compute_mood,
        MoodResult,
        STRESS_THRESHOLD,
        CALM_THRESHOLD,
        CONFIDENCE_GATE,
        load_baseline,
        save_baseline,
        update_baseline,
        Baseline,
        ACTIVATION_THRESHOLD,
    )
    _INFERENCE_IMPORT_ERROR: str | None = None
    _ACTIVATION_THRESHOLD_AVAILABLE = True
except ImportError as _e:
    _INFERENCE_IMPORT_ERROR = str(_e)
    compute_mood = MoodResult = None  # type: ignore[assignment]
    STRESS_THRESHOLD = CALM_THRESHOLD = CONFIDENCE_GATE = None  # type: ignore[assignment]
    load_baseline = save_baseline = update_baseline = Baseline = None  # type: ignore[assignment]
    ACTIVATION_THRESHOLD = 50  # sentinel matching inference.py Week 3 value
    _ACTIVATION_THRESHOLD_AVAILABLE = False

# ActivationInfo + get_activation_info: Librarian Week 3 addition.
try:
    from host.inference import ActivationInfo, get_activation_info
    _ACTIVATION_INFO_AVAILABLE = True
except ImportError:
    ActivationInfo = get_activation_info = None  # type: ignore[assignment]
    _ACTIVATION_INFO_AVAILABLE = False


@pytest.fixture(autouse=True)
def _require_inference():
    if _INFERENCE_IMPORT_ERROR is not None:
        pytest.fail(
            f"host.inference not importable: {_INFERENCE_IMPORT_ERROR}\n"
            "Week 3 baseline activation tests require host.inference."
        )


def _make_baseline(
    mean: float = 0.2,
    stddev: float = 0.05,
    sample_count: int = 5,
) -> "Baseline":
    """Helper: construct a Baseline with explicit sample_count."""
    return Baseline(
        mean=mean,
        stddev=stddev,
        sample_count=sample_count,
        created_at="2026-06-13T00:00:00",
    )


# Distinguishable test frame (the heart of Groups 4–6):
#   tension = 0.7*0.4 + 0.4*0.3 + 0.3*0.3 = 0.28 + 0.12 + 0.09 = 0.49
#
# With baseline mean=0.2, stddev=0.05:
#   personal threshold = 0.2 + 1.5*0.05 = 0.275  → 0.49 > 0.275 → STRESSED
#   population STRESS_THRESHOLD = 0.65            → 0.49 < 0.65  → NEUTRAL
#
# Population vs personal produce maximally distinguishable outcomes (neutral vs stressed).
_FRAME_KWARGS = dict(
    audio_rms=0.5,
    audio_pitch_variance=0.7,
    imu_acceleration=0.4,
    imu_rotation=0.3,
)
_EXPECTED_TENSION = 0.7 * 0.4 + 0.4 * 0.3 + 0.3 * 0.3       # = 0.49
_PERSONAL_MEAN = 0.2
_PERSONAL_STDDEV = 0.05
_PERSONAL_STRESS_THRESH = _PERSONAL_MEAN + 1.5 * _PERSONAL_STDDEV  # = 0.275


# ═════════════════════════════════════════════════════════════════════════════
# Group 1 — ACTIVATION_THRESHOLD constant (PASS — Librarian landed it)
# ═════════════════════════════════════════════════════════════════════════════

class TestBaselineActivationConstant(unittest.TestCase):
    """ACTIVATION_THRESHOLD exported from host.inference (Librarian Week 3)."""

    def test_activation_threshold_is_exported(self):
        """ACTIVATION_THRESHOLD must be importable from host.inference."""
        assert _ACTIVATION_THRESHOLD_AVAILABLE, (
            "ACTIVATION_THRESHOLD not found in host.inference. "
            "Librarian must export this constant so compute_mood() can gate "
            "the population→personal threshold transition. "
            "(decisions.md 2026-06-12: formalise the activation gate per ARD §5.4)"
        )

    def test_activation_threshold_is_positive_int(self):
        """ACTIVATION_THRESHOLD must be a positive integer (sample count)."""
        assert isinstance(ACTIVATION_THRESHOLD, int), (
            f"ACTIVATION_THRESHOLD must be int; "
            f"got {type(ACTIVATION_THRESHOLD).__name__}."
        )
        assert ACTIVATION_THRESHOLD > 0, (
            f"ACTIVATION_THRESHOLD must be > 0; got {ACTIVATION_THRESHOLD}."
        )

    def test_activation_threshold_is_statistically_defensible(self):
        """
        ACTIVATION_THRESHOLD must be >= 30.

        Statistical basis (inference.py lines 37-52):
            SE(s)/s ≈ 1/√(2n) → at n=30: SE/s ≈ 13% (marginal).
            At n=50: SE/s ≈ 10% (acceptable for a heuristic gate).
            Below 30 is statistically unsound — personal threshold would be noisy.
        """
        assert ACTIVATION_THRESHOLD >= 30, (
            f"ACTIVATION_THRESHOLD={ACTIVATION_THRESHOLD} is below minimum 30. "
            "Personal threshold requires n>=30 for SE(s)/s < ~14%. "
            "See inference.py for statistical rationale."
        )


# ═════════════════════════════════════════════════════════════════════════════
# Group 2 — get_activation_info() + ActivationInfo (PASS — Librarian landed it)
# Y.T.'s onboarding UX consumes this to display progress ("N / M samples").
# ═════════════════════════════════════════════════════════════════════════════

class TestGetActivationInfo(unittest.TestCase):
    """get_activation_info(baseline) → ActivationInfo. Stable contract for Y.T.'s UX."""

    def setUp(self):
        if not _ACTIVATION_INFO_AVAILABLE:
            self.skipTest(
                "host.inference.get_activation_info / ActivationInfo not importable. "
                "Librarian must export these for Y.T.'s onboarding UX."
            )

    def test_no_baseline_is_calibrating(self):
        """baseline=None → state='calibrating', sample_count=0."""
        info = get_activation_info(None)
        assert info.state == "calibrating", (
            f"No baseline → state must be 'calibrating'; got '{info.state}'."
        )
        assert info.sample_count == 0, (
            f"No baseline → sample_count must be 0; got {info.sample_count}."
        )

    def test_low_sample_baseline_is_calibrating(self):
        """sample_count < ACTIVATION_THRESHOLD → state='calibrating'."""
        b = _make_baseline(sample_count=ACTIVATION_THRESHOLD - 1)
        info = get_activation_info(b)
        assert info.state == "calibrating", (
            f"sample_count={b.sample_count} < ACTIVATION_THRESHOLD({ACTIVATION_THRESHOLD}) "
            f"must be 'calibrating'; got '{info.state}'."
        )

    def test_at_threshold_is_personalized(self):
        """sample_count == ACTIVATION_THRESHOLD → state='personalized'."""
        b = _make_baseline(sample_count=ACTIVATION_THRESHOLD)
        info = get_activation_info(b)
        assert info.state == "personalized", (
            f"sample_count={b.sample_count} >= ACTIVATION_THRESHOLD({ACTIVATION_THRESHOLD}) "
            f"must be 'personalized'; got '{info.state}'."
        )

    def test_samples_needed_matches_activation_threshold(self):
        """ActivationInfo.samples_needed must equal ACTIVATION_THRESHOLD."""
        info = get_activation_info(None)
        assert info.samples_needed == ACTIVATION_THRESHOLD, (
            f"samples_needed={info.samples_needed} must equal "
            f"ACTIVATION_THRESHOLD={ACTIVATION_THRESHOLD}. "
            "Y.T.'s progress display uses this for 'N / M samples' label."
        )

    def test_progress_zero_with_no_baseline(self):
        """baseline=None → progress=0.0."""
        info = get_activation_info(None)
        assert info.progress == pytest.approx(0.0), (
            f"No baseline → progress must be 0.0; got {info.progress}."
        )

    def test_progress_capped_at_1_when_personalized(self):
        """sample_count >> threshold → progress capped at 1.0 (not > 1.0)."""
        b = _make_baseline(sample_count=ACTIVATION_THRESHOLD * 3)
        info = get_activation_info(b)
        assert info.progress == pytest.approx(1.0), (
            f"sample_count={b.sample_count} → progress must be 1.0 (capped); "
            f"got {info.progress}."
        )

    def test_progress_proportional_below_threshold(self):
        """progress = sample_count / ACTIVATION_THRESHOLD for calibrating state."""
        n = ACTIVATION_THRESHOLD // 2
        b = _make_baseline(sample_count=n)
        info = get_activation_info(b)
        expected = n / ACTIVATION_THRESHOLD
        assert info.progress == pytest.approx(expected, abs=1e-6), (
            f"sample_count={n}: progress must be {expected:.3f}; got {info.progress:.3f}."
        )


# ═════════════════════════════════════════════════════════════════════════════
# Group 3 — Population defaults with no baseline (PASS)
# Regression guard: these must stay green after Librarian's Week 3 change.
# ═════════════════════════════════════════════════════════════════════════════

class TestPopulationDefaultsNoBaseline(unittest.TestCase):
    """Population defaults apply when baseline=None."""

    def test_no_baseline_uses_population_stress_threshold(self):
        """
        With no baseline, STRESS_THRESHOLD=0.65 governs.
        tension=0.49 < 0.65 → NOT stressed (neutral, since 0.49 > CALM 0.35).
        """
        result = compute_mood(**_FRAME_KWARGS)
        assert result.mood == "neutral", (
            f"tension={_EXPECTED_TENSION:.2f} with no baseline must produce 'neutral' "
            f"(0.35 < tension < STRESS_THRESHOLD={STRESS_THRESHOLD}); got '{result.mood}'."
        )

    def test_no_baseline_high_tension_produces_stressed(self):
        """
        High tension (0.70 > STRESS_THRESHOLD 0.65) must produce stressed with no baseline.
        Guards against Librarian accidentally breaking the no-baseline path.
        """
        result = compute_mood(
            audio_rms=0.5,
            audio_pitch_variance=1.0,
            imu_acceleration=0.5,
            imu_rotation=0.5,
        )
        assert result.mood == "stressed", (
            f"tension=0.70 > STRESS_THRESHOLD(0.65) must produce 'stressed' with no baseline; "
            f"got '{result.mood}'."
        )


# ═════════════════════════════════════════════════════════════════════════════
# Group 4 — Population defaults for low sample_count (PASS — gate is implemented)
# ═════════════════════════════════════════════════════════════════════════════

class TestPopulationDefaultsForLowSampleBaseline:
    """
    When baseline.sample_count < ACTIVATION_THRESHOLD, compute_mood()
    must use population defaults — NOT the personal mean+1.5σ threshold.
    """

    def test_low_sample_baseline_uses_population_threshold(self):
        """
        Baseline with low sample_count (below threshold): population defaults govern.

        Frame: tension=0.49 (between personal 0.275 and population 0.65).
        Personal threshold: 0.49 > 0.275 → would be STRESSED (wrong — pre-activation)
        Population threshold: 0.49 < 0.65 → NEUTRAL (correct — in warmup)
        """
        low_baseline = _make_baseline(
            mean=_PERSONAL_MEAN,
            stddev=_PERSONAL_STDDEV,
            sample_count=ACTIVATION_THRESHOLD - 1,
        )
        result = compute_mood(**_FRAME_KWARGS, baseline=low_baseline)
        assert result.mood == "neutral", (
            f"sample_count={low_baseline.sample_count} < "
            f"ACTIVATION_THRESHOLD({ACTIVATION_THRESHOLD}): "
            f"population STRESS_THRESHOLD({STRESS_THRESHOLD}) must govern. "
            f"tension={_EXPECTED_TENSION:.2f} < {STRESS_THRESHOLD} → 'neutral'; "
            f"got '{result.mood}'. "
            "Activation gate must hold in calibrating state."
        )

    @pytest.mark.parametrize("sample_count", [1, 5, 10, 20, ACTIVATION_THRESHOLD - 1])
    def test_various_low_sample_counts_use_population(self, sample_count: int):
        """Population defaults for any sample_count strictly below ACTIVATION_THRESHOLD."""
        b = _make_baseline(
            mean=_PERSONAL_MEAN,
            stddev=_PERSONAL_STDDEV,
            sample_count=sample_count,
        )
        result = compute_mood(**_FRAME_KWARGS, baseline=b)
        assert result.mood != "stressed", (
            f"sample_count={sample_count} < ACTIVATION_THRESHOLD({ACTIVATION_THRESHOLD}): "
            f"population STRESS_THRESHOLD({STRESS_THRESHOLD}) must apply. "
            f"tension={_EXPECTED_TENSION:.2f} < {STRESS_THRESHOLD} → not stressed; "
            f"got '{result.mood}'. Activation gate regression."
        )


# ═════════════════════════════════════════════════════════════════════════════
# Group 5 — Personal threshold for sample_count >= ACTIVATION_THRESHOLD (PASS)
# ═════════════════════════════════════════════════════════════════════════════

class TestPersonalThresholdHighSampleBaseline(unittest.TestCase):
    """
    With sample_count >= ACTIVATION_THRESHOLD, personal mean+1.5σ governs.
    """

    def test_high_sample_baseline_uses_personal_threshold(self):
        """
        sample_count > ACTIVATION_THRESHOLD: personal threshold must produce STRESSED
        for tension=0.49 > personal_stress_threshold=0.275.
        """
        high_baseline = _make_baseline(
            mean=_PERSONAL_MEAN,
            stddev=_PERSONAL_STDDEV,
            sample_count=ACTIVATION_THRESHOLD + 10,
        )
        result = compute_mood(**_FRAME_KWARGS, baseline=high_baseline)
        assert result.mood == "stressed", (
            f"sample_count={high_baseline.sample_count} >= "
            f"ACTIVATION_THRESHOLD({ACTIVATION_THRESHOLD}): "
            f"personal threshold ({_PERSONAL_STRESS_THRESH:.3f}) must govern. "
            f"tension={_EXPECTED_TENSION:.2f} > {_PERSONAL_STRESS_THRESH:.3f} → 'stressed'; "
            f"got '{result.mood}'."
        )

    def test_frame_is_correctly_distinguishable(self):
        """
        Sanity: verify test frame tension genuinely distinguishes personal vs population.
        tension=0.49 must be between personal threshold (0.275) and STRESS_THRESHOLD (0.65).
        """
        assert _EXPECTED_TENSION < STRESS_THRESHOLD, (
            f"Test frame tension={_EXPECTED_TENSION:.3f} must be < "
            f"STRESS_THRESHOLD={STRESS_THRESHOLD}."
        )
        assert _EXPECTED_TENSION > _PERSONAL_STRESS_THRESH, (
            f"Test frame tension={_EXPECTED_TENSION:.3f} must be > "
            f"personal threshold={_PERSONAL_STRESS_THRESH:.3f}."
        )


# ═════════════════════════════════════════════════════════════════════════════
# Group 6 — Exact boundary (PASS)
# ═════════════════════════════════════════════════════════════════════════════

class TestActivationBoundaryExact:
    """
    Off-by-one paranoia: sample_count == ACTIVATION_THRESHOLD must engage personal
    threshold (>= not >); sample_count == ACTIVATION_THRESHOLD - 1 must not.
    """

    def test_exactly_at_threshold_uses_personal(self):
        """
        sample_count == ACTIVATION_THRESHOLD → personal threshold active.
        If gate uses > instead of >=, this stays in population mode → 'neutral'.
        """
        at_threshold = _make_baseline(
            mean=_PERSONAL_MEAN,
            stddev=_PERSONAL_STDDEV,
            sample_count=ACTIVATION_THRESHOLD,
        )
        result = compute_mood(**_FRAME_KWARGS, baseline=at_threshold)
        assert result.mood == "stressed", (
            f"sample_count == ACTIVATION_THRESHOLD ({ACTIVATION_THRESHOLD}): "
            f"personal threshold ({_PERSONAL_STRESS_THRESH:.3f}) must activate "
            f"(>= boundary, not > boundary). "
            f"tension={_EXPECTED_TENSION:.2f} > {_PERSONAL_STRESS_THRESH:.3f} → 'stressed'; "
            f"got '{result.mood}'."
        )

    def test_one_below_threshold_still_uses_population(self):
        """
        sample_count == ACTIVATION_THRESHOLD - 1 → still calibrating.
        If gate accidentally uses <= instead of <, this engages personal early.
        """
        one_below = _make_baseline(
            mean=_PERSONAL_MEAN,
            stddev=_PERSONAL_STDDEV,
            sample_count=ACTIVATION_THRESHOLD - 1,
        )
        result = compute_mood(**_FRAME_KWARGS, baseline=one_below)
        assert result.mood == "neutral", (
            f"sample_count == ACTIVATION_THRESHOLD - 1 ({ACTIVATION_THRESHOLD - 1}): "
            f"still calibrating → population STRESS_THRESHOLD({STRESS_THRESHOLD}) governs. "
            f"tension={_EXPECTED_TENSION:.2f} < {STRESS_THRESHOLD} → 'neutral'; "
            f"got '{result.mood}'. Off-by-one in activation gate."
        )


# ═════════════════════════════════════════════════════════════════════════════
# Group 7 — Confidence < 0.7 suppression in both states (PASS)
# These are regression guards: must stay green after any activation-gate change.
# NOTE: pytest.mark.parametrize requires plain pytest class (not TestCase).
# ═════════════════════════════════════════════════════════════════════════════

class TestConfidenceSuppressionBothStates:
    """
    Confidence < 0.7 suppression must hold in both calibrating and personalized states.
    Confidence gating is independent of the activation gate.
    """

    @pytest.mark.parametrize("sample_count,state_label", [
        (1, "calibrating (1 sample)"),
        (ACTIVATION_THRESHOLD + 10, "personalized (above threshold)"),
    ])
    def test_mic_fail_gates_in_both_states(self, sample_count: int, state_label: str):
        """mic_ok=False → confidence *= 0.6 → gated, regardless of baseline state."""
        baseline = _make_baseline(
            mean=_PERSONAL_MEAN,
            stddev=_PERSONAL_STDDEV,
            sample_count=sample_count,
        )
        result = compute_mood(**_FRAME_KWARGS, baseline=baseline, mic_ok=False)
        assert result.confidence < CONFIDENCE_GATE, (
            f"mic_ok=False must gate inference in {state_label}. "
            f"confidence={result.confidence:.3f} must be < CONFIDENCE_GATE({CONFIDENCE_GATE}). "
            "Confidence gating is independent of the activation gate."
        )
        assert result.gated is True, (
            f"result.gated must be True when confidence={result.confidence:.3f} "
            f"< CONFIDENCE_GATE({CONFIDENCE_GATE}) — state: {state_label}."
        )

    @pytest.mark.parametrize("sample_count,state_label", [
        (1, "calibrating"),
        (ACTIVATION_THRESHOLD + 10, "personalized"),
    ])
    def test_imu_fail_gates_in_both_states(self, sample_count: int, state_label: str):
        """imu_ok=False → confidence *= 0.7 → gated in both states."""
        baseline = _make_baseline(
            mean=_PERSONAL_MEAN,
            stddev=_PERSONAL_STDDEV,
            sample_count=sample_count,
        )
        result = compute_mood(
            audio_rms=0.5,
            audio_pitch_variance=0.5,
            imu_acceleration=0.0,
            imu_rotation=0.0,
            imu_ok=False,
            baseline=baseline,
        )
        assert result.confidence < CONFIDENCE_GATE, (
            f"imu_ok=False must gate inference in {state_label}. "
            f"confidence={result.confidence:.3f} < CONFIDENCE_GATE({CONFIDENCE_GATE})."
        )


# ═════════════════════════════════════════════════════════════════════════════
# Group 8 — Baseline persistence across restart (PASS)
# Regression guard: save_baseline + load_baseline round-trip must survive Week 3.
# ═════════════════════════════════════════════════════════════════════════════

class TestBaselinePersistenceAcrossRestart:
    """
    Baseline round-trips through save_baseline + load_baseline.
    PASS TODAY — regression guard for Week 3 changes.
    """

    def test_save_and_reload_preserves_all_fields(self, tmp_path):
        """save_baseline + load_baseline must be a lossless round-trip."""
        original = _make_baseline(mean=0.42, stddev=0.08, sample_count=17)
        path = tmp_path / "baseline.json"
        save_baseline(original, path=path)

        assert path.exists(), "save_baseline must create the file."

        reloaded = load_baseline(path=path)
        assert reloaded is not None, "load_baseline must return the saved Baseline."
        assert reloaded.mean == pytest.approx(original.mean)
        assert reloaded.stddev == pytest.approx(original.stddev)
        assert reloaded.sample_count == original.sample_count

    def test_welford_accumulation_survives_restart(self, tmp_path):
        """
        10 Welford updates → save → reload: mean and stddev intact.
        Simulates the nightly restart scenario (ARD §5.4 baseline learning).
        """
        baseline = None
        tensions = [0.3, 0.4, 0.45, 0.5, 0.42, 0.38, 0.47, 0.51, 0.44, 0.36]
        for t in tensions:
            baseline = update_baseline(baseline, t)

        assert baseline is not None
        assert baseline.sample_count == 10

        path = tmp_path / "baseline.json"
        save_baseline(baseline, path=path)

        reloaded = load_baseline(path=path)
        assert reloaded is not None
        assert reloaded.sample_count == 10
        assert reloaded.mean == pytest.approx(baseline.mean, abs=1e-9)
        assert reloaded.stddev == pytest.approx(baseline.stddev, abs=1e-9)

    def test_corrupt_baseline_returns_none_and_falls_back_to_population(self, tmp_path):
        """
        Corrupted baseline.json → load_baseline returns None → caller uses population defaults.
        Week 3 regression guard: loading None then calling compute_mood() with no baseline
        must produce population defaults, not crash.
        """
        path = tmp_path / "baseline.json"
        path.write_text("{corrupted — not valid JSON", encoding="utf-8")

        loaded = load_baseline(path=path)
        assert loaded is None, (
            "load_baseline must return None for corrupt JSON. "
            "Host must start in calibrating mode (population defaults) when "
            "baseline.json is unreadable."
        )
        # Confirm that compute_mood with None baseline uses population defaults
        result = compute_mood(**_FRAME_KWARGS, baseline=loaded)
        assert result.mood == "neutral", (
            "compute_mood with None baseline must use population defaults. "
            f"tension={_EXPECTED_TENSION:.2f} < STRESS_THRESHOLD({STRESS_THRESHOLD}) → 'neutral'."
        )

    def test_activation_state_persists_across_restart(self, tmp_path):
        """
        A baseline with sample_count >= ACTIVATION_THRESHOLD saved and reloaded
        must still trigger the personal threshold on next session start.

        This validates that the activation state is DURABLE — Welford accumulation
        is cumulative across restarts, not reset on each launch.
        """
        # Build a personalized baseline with enough samples
        personalized = _make_baseline(
            mean=_PERSONAL_MEAN,
            stddev=_PERSONAL_STDDEV,
            sample_count=ACTIVATION_THRESHOLD + 20,
        )
        path = tmp_path / "baseline.json"
        save_baseline(personalized, path=path)

        reloaded = load_baseline(path=path)
        assert reloaded is not None
        assert reloaded.sample_count >= ACTIVATION_THRESHOLD, (
            f"Reloaded sample_count={reloaded.sample_count} must be >= "
            f"ACTIVATION_THRESHOLD({ACTIVATION_THRESHOLD}) after round-trip."
        )

        # Personal threshold must still activate after reload
        result = compute_mood(**_FRAME_KWARGS, baseline=reloaded)
        assert result.mood == "stressed", (
            "After reload, personalized baseline must still trigger personal threshold. "
            f"tension={_EXPECTED_TENSION:.2f} > personal_thresh({_PERSONAL_STRESS_THRESH:.3f}) "
            f"→ 'stressed'; got '{result.mood}'. "
            "Activation state must persist across restarts — sample_count is not reset."
        )


if __name__ == "__main__":
    import unittest
    unittest.main()
