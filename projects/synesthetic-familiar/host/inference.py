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
# TODO: implement compute_mood body, baseline learning, fallback paths

from __future__ import annotations

import dataclasses
from typing import Literal

# Tunable thresholds — ARD §5.4 population defaults.
# These are starting values derived from aggregate user studies; baseline
# learning (personal mean + 1.5σ after day 3) replaces them per-user.
# Do not hard-code call sites to these values; always import the constants.
STRESS_THRESHOLD: float = 0.65
CALM_THRESHOLD: float = 0.35
CONFIDENCE_GATE: float = 0.7

MoodEnum = Literal["neutral", "calm", "stressed", "attention"]
MOOD_TO_INT: dict[MoodEnum, int] = {
    "neutral": 0,
    "calm": 1,
    "stressed": 2,
    "attention": 3,
}


@dataclasses.dataclass
class MoodResult:
    mood: MoodEnum
    mood_int: int        # Wire-format enum (0-3)
    intensity: float     # 0.0–1.0
    confidence: float    # 0.0–1.0
    gated: bool          # True if confidence < CONFIDENCE_GATE (do not send)


def compute_mood(
    audio_rms: float,
    audio_pitch_variance: float,
    imu_acceleration: float,
    imu_rotation: float,
) -> MoodResult:
    """
    Compute mood from sensor inputs.

    Weights (locked, ARD §5.4):
      pitch_variance × 0.4 + acceleration × 0.3 + rotation × 0.3

    Returns MoodResult; caller must check .gated before sending to device.
    """
    # TODO: implement weighted tension score, threshold logic, confidence calc
    # TODO: implement baseline learning (pop defaults d1-3; personal mean+1.5σ after)
    raise NotImplementedError
