"""
Local mood heuristic for the Synesthetic Familiar.

Computes mood from mic + IMU signals entirely on host (no cloud, no on-device ML).
Confidence gating: host is the single authority — if confidence < 0.7, do NOT
update Familiar state (silence is safer than hallucination, LIBRARIAN-T2-5-ERROR).

Mood enum (matches wire format, ARD §5.2):
  0 = neutral
  1 = calm
  2 = stressed
  3 = attention
"""
from __future__ import annotations

import dataclasses
import datetime
import json
import logging
import math
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

# Tunable thresholds — ARD §5.4 population defaults (days 1–3).
# After day 3, baseline learning replaces STRESS_THRESHOLD with a personal value.
# CONFIDENCE_GATE is imported by Juanita's tests — do not rename.
STRESS_THRESHOLD: float = 0.65
CALM_THRESHOLD: float = 0.35
CONFIDENCE_GATE: float = 0.7

# §2.6 aliases (same values, distinct names for documentation clarity)
POPULATION_STRESS_THRESHOLD: float = STRESS_THRESHOLD
POPULATION_CALM_THRESHOLD: float = CALM_THRESHOLD

# Activation gate — ARD §5.4 "first 3 days: population defaults; after: personal mean+1.5σ".
#
# Threshold: n ≥ 50 Welford samples (resolved from OPEN decision 2026-06-12).
#
# Statistical basis: the standard error of the Welford sample-stddev estimator is
#   SE(s) ≈ s / √(2n)
# At n=50: SE(s)/s ≈ 1/√100 ≈ 10%  →  personal stress threshold (mean + 1.5σ) is within
# ~0.15σ of its asymptotic value — acceptable for a heuristic gate.
# At n<30: SE/s > 14%; threshold could be noisy enough to overshoot or undershoot the
# population default, defeating the intent of personalization.
# Calendar days (ARD §5.4) are aspirational; sample count gates when the math is sound,
# independent of device-off time (e.g., a 3-day-old baseline with 10 samples stays
# "calibrating" until 50 confident reads accumulate).
#
# Persists across restarts: sample_count lives in baseline.json — no ramp-up reset on launch.
ACTIVATION_THRESHOLD: int = 50

ActivationState = Literal["calibrating", "personalized"]

MoodEnum = Literal["neutral", "calm", "stressed", "attention"]
MOOD_TO_INT: dict[str, int] = {
    "neutral": 0,
    "calm": 1,
    "stressed": 2,
    "attention": 3,
}

_BASELINE_PATH: Path = Path("~/.vesper/baseline.json").expanduser()


@dataclasses.dataclass
class MoodResult:
    mood: MoodEnum
    mood_int: int        # Wire-format enum (0–3); matches familiar_protocol.Mood
    intensity: float     # 0.0–1.0 continuous
    confidence: float    # 0.0–1.0
    gated: bool          # True if confidence < CONFIDENCE_GATE (main loop must not send)
    tension: float       # Raw weighted tension score (locked contract §2.6 — B1 amendment)


@dataclasses.dataclass
class Baseline:
    """Personal tension baseline accumulated over time (§2.6)."""
    mean: float          # Running mean of tension signal
    stddev: float        # Sample stddev (0.0 until n≥2)
    sample_count: int    # Number of tension samples seen
    created_at: str      # ISO 8601 creation timestamp (set once, never updated)


@dataclasses.dataclass
class ActivationInfo:
    """
    Activation gate status — stable contract for Y.T.'s onboarding UX.

    state          "calibrating" until ACTIVATION_THRESHOLD samples have been
                   accumulated; "personalized" once the gate is crossed.
    sample_count   Samples seen so far (0 when no baseline exists yet).
    samples_needed ACTIVATION_THRESHOLD — use for progress display ("N / M samples").
    progress       Fraction 0.0–1.0; capped at 1.0 once personalized.
    """
    state: ActivationState
    sample_count: int
    samples_needed: int
    progress: float


# ── Baseline persistence ──────────────────────────────────────────────────────

def load_baseline(path: Path = _BASELINE_PATH) -> Baseline | None:
    """Load baseline from disk. Returns None if file is missing or corrupt."""
    try:
        file_size = path.stat().st_size
        if file_size > 4096:
            raise ValueError(
                f"baseline file too large ({file_size} bytes > 4096 byte limit) — skipping read"
            )
        data = json.loads(path.read_text(encoding="utf-8"))
        b = Baseline(**data)
        # Validate field types and values — rejects hostile/corrupt JSON that would
        # cause a deferred crash in compute_mood (e.g. mean="EVIL", negative stddev).
        def _is_real(v: object) -> bool:
            return isinstance(v, (int, float)) and not isinstance(v, bool)
        if not (
            _is_real(b.mean) and math.isfinite(b.mean)
            and _is_real(b.stddev) and math.isfinite(b.stddev) and b.stddev >= 0.0
            and isinstance(b.sample_count, int) and not isinstance(b.sample_count, bool) and b.sample_count >= 0
            and isinstance(b.created_at, str)
        ):
            raise ValueError(
                f"baseline fields out of range or wrong type: "
                f"mean={b.mean!r}, stddev={b.stddev!r}, sample_count={b.sample_count!r}"
            )
        return b
    except (OSError, json.JSONDecodeError, TypeError, KeyError, ValueError) as exc:
        logger.warning(
            "[Baseline] failed to load from %s: %s — using population defaults", path, exc
        )
        return None


def save_baseline(baseline: Baseline, path: Path = _BASELINE_PATH) -> None:
    """Persist baseline atomically (write tmp → rename, ARD §5.4)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(dataclasses.asdict(baseline), indent=2), encoding="utf-8"
    )
    tmp.replace(path)


def update_baseline(baseline: Baseline | None, tension: float) -> Baseline:
    """
    Online Welford update of running mean and sample stddev.

    Creates a fresh Baseline on first call (baseline=None).  The Baseline
    dataclass fields are LOCKED (§2.6), so M2 is reconstructed from stored
    stddev rather than adding a new field:
        M2 = stddev² × (sample_count − 1)

    Non-finite tension (NaN/inf from a corrupt audio block) is silently dropped
    to prevent permanently poisoning the persisted mean/stddev.
    """
    # Guard: reject NaN/inf tension to avoid corrupting the running statistics.
    if not math.isfinite(tension):
        return baseline if baseline is not None else Baseline(
            mean=0.0,
            stddev=0.0,
            sample_count=0,
            created_at=datetime.datetime.now().isoformat(),
        )

    if baseline is None:
        return Baseline(
            mean=tension,
            stddev=0.0,
            sample_count=1,
            created_at=datetime.datetime.now().isoformat(),
        )

    n = baseline.sample_count + 1
    m2_prev = baseline.stddev ** 2 * max(baseline.sample_count - 1, 0)

    delta = tension - baseline.mean
    new_mean = baseline.mean + delta / n
    delta2 = tension - new_mean
    m2_new = m2_prev + delta * delta2

    # Variance floor clamp: FP cancellation can produce tiny negatives; sqrt(-ε) → ValueError.
    new_stddev = math.sqrt(max(0.0, m2_new) / (n - 1)) if n > 1 else 0.0

    return Baseline(
        mean=new_mean,
        stddev=new_stddev,
        sample_count=n,
        created_at=baseline.created_at,  # Preserve original timestamp
    )


# ── Activation gate ───────────────────────────────────────────────────────────

def get_activation_info(baseline: Baseline | None) -> ActivationInfo:
    """
    Pure function: derive activation state from persisted baseline.

    Y.T. calls this to drive onboarding UX:
        state == "calibrating"  → "Calibrating ({sample_count} / {samples_needed} samples)"
        state == "personalized" → "Personalized ✓"

    Restarts are transparent — sample_count persists in baseline.json (ARD §5.4).
    """
    n = baseline.sample_count if baseline is not None else 0
    activated = n >= ACTIVATION_THRESHOLD
    return ActivationInfo(
        state="personalized" if activated else "calibrating",
        sample_count=n,
        samples_needed=ACTIVATION_THRESHOLD,
        progress=min(1.0, n / ACTIVATION_THRESHOLD) if ACTIVATION_THRESHOLD > 0 else 1.0,
    )


# ── Mood inference ────────────────────────────────────────────────────────────

def compute_mood(
    audio_rms: float,
    audio_pitch_variance: float,
    imu_acceleration: float,
    imu_rotation: float,
    *,
    mic_ok: bool = True,
    imu_ok: bool = True,
    baseline: Baseline | None = None,
) -> MoodResult:
    """
    Pure function: sensor inputs → MoodResult.  No I/O, no clock, no global state.

    Weights (ARD §5.4, LOCKED):
        tension = pitch_variance × 0.4 + acceleration × 0.3 + rotation × 0.3

    Threshold strategy:
        baseline=None or sample_count < ACTIVATION_THRESHOLD (calibrating)
                         → population defaults (STRESS_THRESHOLD / CALM_THRESHOLD)
        baseline given AND sample_count ≥ ACTIVATION_THRESHOLD (personalized)
                         → personal stress threshold = mean + 1.5 × stddev
                           calm threshold stays at CALM_THRESHOLD (§2.6 defines
                           only a personal stress formula — no personal calm formula)

    Confidence reduction on sensor failure (§2.2):
        mic_ok=False  → confidence × 0.6
        imu_ok=False  → confidence × 0.7

    Caller (main.py) is responsible for:
        • acting on .gated (do not send when True)
        • confidence-hold timeout (I2, ~30 s)
        • both-sensors-fail fallback (ARD §5.4, 10 s)
        • intensity quantisation + jitter before encode (Gate 2)
    """
    # audio_rms intentionally unused — ARD §5.4 tension formula excludes volume;
    # kept for interface stability / future confidence modulation.
    # Weighted tension score (locked weights, ARD §5.4)
    tension = (
        audio_pitch_variance * 0.4
        + imu_acceleration * 0.3
        + imu_rotation * 0.3
    )

    # Select thresholds — activation gate (ARD §5.4; resolved OPEN decision 2026-06-12).
    # Population defaults hold until ACTIVATION_THRESHOLD Welford samples guarantee a
    # trustworthy personal stddev (SE(s)/s < 10%).  A baseline file that exists but has
    # accumulated fewer than ACTIVATION_THRESHOLD samples keeps using population defaults.
    if baseline is not None and baseline.sample_count >= ACTIVATION_THRESHOLD:
        stress_threshold = baseline.mean + 1.5 * baseline.stddev
    else:
        stress_threshold = STRESS_THRESHOLD
    calm_threshold = CALM_THRESHOLD

    # Classify mood with base confidence
    if tension > stress_threshold:
        mood: MoodEnum = "stressed"
        intensity = tension
        confidence = 0.8
    elif tension < calm_threshold:
        mood = "calm"
        intensity = 1.0 - tension
        confidence = 0.8
    else:
        mood = "neutral"
        intensity = 0.5
        confidence = 0.6

    # Sensor-failure confidence reduction (§2.2)
    if not mic_ok:
        confidence *= 0.6
    if not imu_ok:
        confidence *= 0.7

    return MoodResult(
        mood=mood,
        mood_int=MOOD_TO_INT[mood],
        intensity=intensity,
        confidence=confidence,
        gated=(confidence < CONFIDENCE_GATE),
        tension=tension,
    )
