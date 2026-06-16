"""
Local mood heuristic for the Synesthetic Familiar.

Computes mood from mic + IMU signals entirely on host (no cloud, no on-device ML).
Confidence gating: host is the single authority — if confidence < 0.7, do NOT
update Familiar state (silence is safer than hallucination, LIBRARIAN-T2-5-ERROR).

Phase-2 addition: optional camera modality (visual_activity + visual_brightness)
folded into tension as ADDITIVE terms when camera_ok=True.  camera_ok=False (the
default) produces EXACTLY the Phase-1 result — camera is purely additive.

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

# Phase-1 locked tension weights (ARD §5.4 — IMMUTABLE; never altered by online tuning).
# camera_ok=False path uses ONLY these three constants, guaranteeing exact Phase-1 output.
_W_PITCH: float = 0.4
_W_ACCEL: float = 0.3
_W_ROT: float = 0.3

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


# ── Visual weights (Phase-2 camera modality) ──────────────────────────────────
#
# Phase-2 adds a camera modality: visual_activity + visual_brightness are folded
# into the tension score as ADDITIVE terms, gated by camera_ok.
#
# ADDITIVE INVARIANT (locked): camera_ok=False → exact Phase-1 result.
# Visual weights are the ONLY tunable parameters; Phase-1 weights (_W_PITCH,
# _W_ACCEL, _W_ROT) are immutable constants — they never appear in VisualWeights.
#
# Tuning bound (Hiro risk mitigation, §6.1):
#   No weight may exceed MAX_VISUAL_WEIGHT_MULTIPLIER (2×) its default value.
#   EMA smoothing guards against oscillation; clamp enforces the hard bound.
#
# Formula when camera_ok=True (additive on top of Phase-1 tension):
#   tension += visual_activity × W_va  +  (1 − visual_brightness) × W_vb
#
#   Rationale:
#     visual_activity: high scene movement → more alert/stressed → positive weight
#     (1 − visual_brightness): dark scene → more tense; bright scene → calmer
#     Both terms map [0, 1] inputs with positive weights for clean arithmetic.

@dataclasses.dataclass
class VisualWeights:
    """
    Tunable additive weights for the camera modality (Phase-2).

    These are strictly ADDITIVE contributions to the Phase-1 tension score,
    applied only when camera_ok=True.  Phase-1 audio/IMU weights (_W_PITCH,
    _W_ACCEL, _W_ROT) are immutable constants — they are NOT in this class.

    Bounds: each weight must stay in [0, DEFAULT × MAX_VISUAL_WEIGHT_MULTIPLIER].
    use tune_visual_weights() and reset_visual_weights() to update safely.
    """
    visual_activity: float = 0.15    # scene movement → tension (positive weight)
    visual_brightness: float = 0.05  # applied as (1.0 − brightness) → tension


DEFAULT_VISUAL_WEIGHTS: VisualWeights = VisualWeights()
MAX_VISUAL_WEIGHT_MULTIPLIER: float = 2.0   # Hiro risk bound: no weight > 2× default
_EMA_ALPHA: float = 0.1                      # default EMA learning rate for weight tuning
_VISUAL_WEIGHTS_PATH: Path = Path("~/.vesper/visual_weights.json").expanduser()


def load_visual_weights(path: Path = _VISUAL_WEIGHTS_PATH) -> VisualWeights:
    """Load visual weights from disk. Returns DEFAULT_VISUAL_WEIGHTS on any error."""
    try:
        file_size = path.stat().st_size
        if file_size > 4096:
            raise ValueError(
                f"visual_weights file too large ({file_size} bytes) — skipping"
            )
        data = json.loads(path.read_text(encoding="utf-8"))
        va = data["visual_activity"]
        vb = data["visual_brightness"]
        def _is_bounded_real(v: object) -> bool:
            return (
                isinstance(v, (int, float)) and not isinstance(v, bool)
                and math.isfinite(float(v)) and float(v) >= 0.0
            )
        if not (_is_bounded_real(va) and _is_bounded_real(vb)):
            raise ValueError(
                f"visual weight out of range: visual_activity={va!r}, visual_brightness={vb!r}"
            )
        return VisualWeights(visual_activity=float(va), visual_brightness=float(vb))
    except (OSError, json.JSONDecodeError, TypeError, KeyError, ValueError) as exc:
        logger.warning(
            "[VisualWeights] failed to load from %s: %s — using defaults", path, exc
        )
        return VisualWeights()


def save_visual_weights(weights: VisualWeights, path: Path = _VISUAL_WEIGHTS_PATH) -> None:
    """Persist visual weights atomically (write tmp → rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(dataclasses.asdict(weights), indent=2), encoding="utf-8"
    )
    tmp.replace(path)


def reset_visual_weights() -> VisualWeights:
    """Return factory-default visual weights (does NOT write to disk)."""
    return VisualWeights()


def tune_visual_weights(
    current: VisualWeights,
    target: VisualWeights,
    alpha: float = _EMA_ALPHA,
) -> VisualWeights:
    """
    Bounded EMA blend of current visual weights toward target.

    EMA formula:  new_w = (1 − α) × current + α × target
    Hard bound:   each weight is clamped to [0, DEFAULT × MAX_VISUAL_WEIGHT_MULTIPLIER].

    Divergence guard: if a weight approaches the bound (≥ 90 % of max), a warning
    is emitted.  The caller may choose to reset_visual_weights() in response.

    Returns a NEW VisualWeights — does NOT mutate inputs.
    """
    max_va = DEFAULT_VISUAL_WEIGHTS.visual_activity * MAX_VISUAL_WEIGHT_MULTIPLIER
    max_vb = DEFAULT_VISUAL_WEIGHTS.visual_brightness * MAX_VISUAL_WEIGHT_MULTIPLIER

    new_va = (1.0 - alpha) * current.visual_activity + alpha * target.visual_activity
    new_vb = (1.0 - alpha) * current.visual_brightness + alpha * target.visual_brightness

    # Hard clamp — enforce the ≤ 2× bound
    new_va = max(0.0, min(new_va, max_va))
    new_vb = max(0.0, min(new_vb, max_vb))

    # Divergence guard: warn when approaching the bound
    if new_va >= max_va * 0.9 or new_vb >= max_vb * 0.9:
        logger.warning(
            "[VisualWeights] weight approaching bound — possible divergence. "
            "Consider reset_visual_weights(). va=%.4f (max %.4f), vb=%.4f (max %.4f)",
            new_va, max_va, new_vb, max_vb,
        )

    return VisualWeights(visual_activity=new_va, visual_brightness=new_vb)


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
    # Phase-2 camera inputs — camera_ok=False (default) → EXACT Phase-1 result.
    # The additive invariant is enforced structurally: visual terms are only added
    # inside the `if camera_ok:` block below.  No camera parameter touches the
    # Phase-1 tension formula or confidence path when camera_ok=False.
    visual_activity: float = 0.0,
    visual_brightness: float = 0.5,
    camera_ok: bool = False,
    visual_weights: VisualWeights | None = None,
) -> MoodResult:
    """
    Pure function: sensor inputs → MoodResult.  No I/O, no clock, no global state.

    Phase-1 weights (ARD §5.4, LOCKED):
        tension = pitch_variance × 0.4 + acceleration × 0.3 + rotation × 0.3

    Phase-2 camera augmentation (additive, gated by camera_ok):
        tension += visual_activity × W_va  +  (1 − visual_brightness) × W_vb
        W_va, W_vb from visual_weights (default DEFAULT_VISUAL_WEIGHTS).

    ADDITIVE INVARIANT: camera_ok=False returns EXACTLY the Phase-1 result.
    Proof: the camera block is inside `if camera_ok:` — it cannot execute when
    camera_ok=False.  The Phase-1 tension formula, threshold selection, mood
    classification, and confidence reduction are all unchanged.

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
        camera_ok=False → NO confidence reduction (camera absence is the default)

    Caller (main.py) is responsible for:
        • acting on .gated (do not send when True)
        • confidence-hold timeout (I2, ~30 s)
        • both-sensors-fail fallback (ARD §5.4, 10 s)
        • intensity quantisation + jitter before encode (Gate 2)
    """
    # audio_rms intentionally unused — ARD §5.4 tension formula excludes volume;
    # kept for interface stability / future confidence modulation.

    # ── Phase-1 tension (LOCKED weights, ARD §5.4) ──────────────────────────
    tension = (
        audio_pitch_variance * _W_PITCH
        + imu_acceleration * _W_ACCEL
        + imu_rotation * _W_ROT
    )

    # ── Phase-2 camera augmentation (additive — only when camera available) ──
    # ADDITIVE INVARIANT: this block is unreachable when camera_ok=False.
    if camera_ok:
        # Guard NaN/inf from corrupt JPEG → invalid feature extraction.
        # Non-finite inputs are substituted with neutral values (no contribution).
        va = visual_activity if math.isfinite(visual_activity) else 0.0
        vb = visual_brightness if math.isfinite(visual_brightness) else 0.5
        vw = visual_weights if visual_weights is not None else DEFAULT_VISUAL_WEIGHTS
        tension += va * vw.visual_activity + (1.0 - vb) * vw.visual_brightness

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
