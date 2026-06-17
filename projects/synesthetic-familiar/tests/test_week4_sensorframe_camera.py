"""
Week 4 "It sees" — SensorFrame camera extension + additive-invariant tests.

Locked contract (phase2-architecture-draft.md §1.2):
  SensorFrame gains three new fields (Ng → host/sensors.py):
    visual_activity: float = 0.0    # scene movement/change (0.0–1.0)
    visual_brightness: float = 0.5  # ambient light proxy (0.0–1.0)
    camera_ok: bool = False         # False = camera unavailable (graceful degrade)

ADDITIVE INVARIANT (most important gate):
  When camera_ok=False, mood inference and behavior must be EXACTLY Phase-1
  behavior.  Camera absence is the normal default, never a degradation.  Tests
  in TestAdditiveInvariant cover this against compute_mood once Librarian adds
  visual parameters.

Camera inference rules (§1.4):
  mic_ok=True + imu_ok=True + camera_ok=False  →  Phase-1 behavior exactly
  camera_ok=True                               →  visual weights added (more data
                                                   may boost or reduce confidence)

Tests marked pytest.skip (pending implementers) activate automatically once
the code lands — no manual re-enabling required.

Owners: Ng (sensors.py fields + _CameraRelay), Librarian (compute_mood visual params)
Date: 2026-06-14
"""
from __future__ import annotations

import dataclasses
import math

import pytest

# ── Import guards ─────────────────────────────────────────────────────────────

try:
    from host.sensors import SensorFrame
    _SENSORS_IMPORT_ERROR: str | None = None
except ImportError as _e:
    _SENSORS_IMPORT_ERROR = str(_e)
    SensorFrame = None  # type: ignore[assignment]

try:
    from host.inference import compute_mood, MoodResult, CONFIDENCE_GATE, Baseline
    _INFERENCE_IMPORT_ERROR: str | None = None
except ImportError as _e:
    _INFERENCE_IMPORT_ERROR = str(_e)
    compute_mood = MoodResult = CONFIDENCE_GATE = Baseline = None  # type: ignore[assignment]

# Detect whether the Phase-2 camera fields exist on SensorFrame yet
_CAMERA_FIELDS_LANDED = (
    SensorFrame is not None
    and hasattr(SensorFrame, "__dataclass_fields__")
    and "camera_ok" in SensorFrame.__dataclass_fields__
)

# Detect whether compute_mood accepts visual_activity / camera_ok
_COMPUTE_MOOD_CAMERA_LANDED = False
if compute_mood is not None:
    import inspect as _inspect
    _COMPUTE_MOOD_CAMERA_LANDED = "camera_ok" in _inspect.signature(compute_mood).parameters


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _require_sensors() -> None:
    if _SENSORS_IMPORT_ERROR is not None:
        pytest.fail(
            f"host.sensors is not importable: {_SENSORS_IMPORT_ERROR}\n"
            "These tests require Ng's sensors.py to be importable."
        )


@pytest.fixture(autouse=True)
def _require_inference() -> None:
    if _INFERENCE_IMPORT_ERROR is not None:
        pytest.fail(
            f"host.inference is not importable: {_INFERENCE_IMPORT_ERROR}\n"
            "These tests require Librarian's inference.py to be importable."
        )


# ═════════════════════════════════════════════════════════════════════════════
# 1. SensorFrame camera fields — presence, types, defaults (Ng contract)
# ═════════════════════════════════════════════════════════════════════════════

class TestSensorFrameCameraFields:
    """
    Gate: SensorFrame must have the three Phase-2 camera fields with correct
    types and defaults.  Tests in this class skip until Ng lands the fields;
    they become active automatically once sensors.py is updated.
    """

    def test_visual_activity_field_exists(self) -> None:
        """SensorFrame must have visual_activity: float = 0.0."""
        if not _CAMERA_FIELDS_LANDED:
            pytest.skip(
                "SensorFrame camera fields not yet present — pending Ng (sensors.py). "
                "Test activates automatically once visual_activity is added."
            )
        fields = {f.name: f for f in dataclasses.fields(SensorFrame)}
        assert "visual_activity" in fields, (
            "SensorFrame missing 'visual_activity' field (locked contract §1.2)"
        )
        f = fields["visual_activity"]
        assert f.default == 0.0, (
            f"visual_activity default must be 0.0 (camera absent → no activity); "
            f"got {f.default!r}"
        )

    def test_visual_brightness_field_exists(self) -> None:
        """SensorFrame must have visual_brightness: float = 0.5."""
        if not _CAMERA_FIELDS_LANDED:
            pytest.skip(
                "SensorFrame camera fields not yet present — pending Ng (sensors.py). "
                "Test activates automatically once visual_brightness is added."
            )
        fields = {f.name: f for f in dataclasses.fields(SensorFrame)}
        assert "visual_brightness" in fields, (
            "SensorFrame missing 'visual_brightness' field (locked contract §1.2)"
        )
        f = fields["visual_brightness"]
        assert f.default == 0.5, (
            f"visual_brightness default must be 0.5 (neutral ambient light); "
            f"got {f.default!r}"
        )

    def test_camera_ok_field_exists_and_defaults_false(self) -> None:
        """
        SensorFrame must have camera_ok: bool = False.

        False is the normal default — camera absence is not an error.
        The creature runs in Phase-1 mode when camera_ok is False.
        """
        if not _CAMERA_FIELDS_LANDED:
            pytest.skip(
                "SensorFrame camera fields not yet present — pending Ng (sensors.py). "
                "Test activates automatically once camera_ok is added."
            )
        fields = {f.name: f for f in dataclasses.fields(SensorFrame)}
        assert "camera_ok" in fields, (
            "SensorFrame missing 'camera_ok' field (locked contract §1.2)"
        )
        f = fields["camera_ok"]
        assert f.default is False, (
            f"camera_ok default must be False (camera is absent by default, not an error); "
            f"got {f.default!r}"
        )

    def test_camera_ok_is_bool_not_float(self) -> None:
        """camera_ok must be typed bool, not float (like mic_ok and imu_ok)."""
        if not _CAMERA_FIELDS_LANDED:
            pytest.skip("Camera fields not yet landed — pending Ng.")
        fields = {f.name: f for f in dataclasses.fields(SensorFrame)}
        f = fields["camera_ok"]
        assert f.type is bool or str(f.type).lower() in ("bool", "<class 'bool'>"), (
            f"camera_ok must be typed bool; got '{f.type}'. "
            "Mirrors mic_ok and imu_ok (contract §1.2)."
        )

    def test_phase1_fields_still_present_after_extension(self) -> None:
        """
        Phase-1 fields must still be present after camera extension.

        The camera extension is purely additive — no Phase-1 field may be
        removed or renamed.
        """
        if not _CAMERA_FIELDS_LANDED:
            pytest.skip("Camera fields not yet landed — skipping additive check.")
        phase1_fields = {
            "audio_rms", "audio_pitch_variance",
            "imu_acceleration", "imu_rotation",
            "mic_ok", "imu_ok",
        }
        field_names = {f.name for f in dataclasses.fields(SensorFrame)}
        missing = phase1_fields - field_names
        assert not missing, (
            f"Phase-1 SensorFrame fields removed by camera extension: {missing}. "
            "Camera is ADDITIVE — no existing fields may be removed. (§1.2)"
        )

    def test_sensorframe_instantiation_with_camera_defaults(self) -> None:
        """
        SensorFrame instantiated with Phase-1 positional args must still work
        after the camera extension (defaults cover the new fields).
        """
        if not _CAMERA_FIELDS_LANDED:
            pytest.skip("Camera fields not yet landed — pending Ng.")
        frame = SensorFrame(
            audio_rms=0.5,
            audio_pitch_variance=0.3,
            imu_acceleration=0.2,
            imu_rotation=0.1,
        )
        assert frame.camera_ok is False, (
            "camera_ok must default to False when not supplied — camera absence is default."
        )
        assert frame.visual_activity == 0.0, (
            f"visual_activity must default to 0.0; got {frame.visual_activity!r}."
        )
        assert frame.visual_brightness == 0.5, (
            f"visual_brightness must default to 0.5; got {frame.visual_brightness!r}."
        )

    def test_sensorframe_visual_fields_clamp_at_construction(self) -> None:
        """
        Out-of-range visual floats are not rejected at construction time (SensorFrame
        is a dumb data container — clamping happens in _CameraRelay before construction).
        This test verifies that over-range values at least don't break the dataclass.
        """
        if not _CAMERA_FIELDS_LANDED:
            pytest.skip("Camera fields not yet landed — pending Ng.")
        # Should not raise — SensorFrame is a plain dataclass, not a validator
        frame = SensorFrame(
            audio_rms=0.5,
            audio_pitch_variance=0.3,
            imu_acceleration=0.2,
            imu_rotation=0.1,
            visual_activity=2.0,    # intentionally over-range
            visual_brightness=-0.1, # intentionally under-range
            camera_ok=True,
        )
        assert isinstance(frame.visual_activity, float), (
            "visual_activity must be float even for out-of-range values."
        )


# ═════════════════════════════════════════════════════════════════════════════
# 2. Additive invariant — camera_ok=False produces EXACT Phase-1 behavior
# ═════════════════════════════════════════════════════════════════════════════

class TestAdditiveInvariant:
    """
    The most important Week-4 gate: when camera_ok=False (the default), inference
    output must be IDENTICAL to Phase-1.  Camera absence is never a degradation.

    Tests compare:
      Phase-1 call: compute_mood(audio_rms, apv, accel, rot, mic_ok=X, imu_ok=Y)
      Phase-2 call: compute_mood(..., camera_ok=False, visual_activity=0.0,
                                   visual_brightness=0.5)

    If compute_mood doesn't accept visual params yet, these tests skip.
    They activate automatically once Librarian extends compute_mood.
    """

    @pytest.mark.parametrize("audio_rms,apv,accel,rot,mic_ok,imu_ok", [
        # Stressed signal (high pitch variance + movement)
        (0.8, 0.9, 0.8, 0.7, True,  True),
        # Calm signal
        (0.3, 0.1, 0.1, 0.0, True,  True),
        # Neutral signal (in dead-band)
        (0.5, 0.5, 0.5, 0.4, True,  True),
        # IMU missing (mic-only)
        (0.8, 0.9, 0.0, 0.0, True,  False),
        # Mic missing (IMU-only)
        (0.0, 0.0, 0.8, 0.7, False, True),
        # Both sensors missing
        (0.0, 0.0, 0.0, 0.0, False, False),
    ])
    def test_camera_absent_matches_phase1_output(
        self,
        audio_rms: float,
        apv: float,
        accel: float,
        rot: float,
        mic_ok: bool,
        imu_ok: bool,
    ) -> None:
        """
        camera_ok=False + visual defaults → result identical to Phase-1 call.

        This is the ADDITIVE INVARIANT: camera never degrades Phase-1 behavior.
        """
        if not _COMPUTE_MOOD_CAMERA_LANDED:
            pytest.skip(
                "compute_mood does not accept camera_ok yet — pending Librarian (inference.py). "
                "Test activates automatically once visual parameters are added."
            )

        # Phase-1 call (no camera params)
        phase1_result = compute_mood(
            audio_rms=audio_rms,
            audio_pitch_variance=apv,
            imu_acceleration=accel,
            imu_rotation=rot,
            mic_ok=mic_ok,
            imu_ok=imu_ok,
        )

        # Phase-2 call with camera absent (default state)
        phase2_result = compute_mood(
            audio_rms=audio_rms,
            audio_pitch_variance=apv,
            imu_acceleration=accel,
            imu_rotation=rot,
            mic_ok=mic_ok,
            imu_ok=imu_ok,
            camera_ok=False,
            visual_activity=0.0,
            visual_brightness=0.5,
        )

        assert phase1_result.mood == phase2_result.mood, (
            f"ADDITIVE INVARIANT VIOLATED: camera_ok=False changed mood "
            f"from '{phase1_result.mood}' to '{phase2_result.mood}'. "
            f"Inputs: apv={apv}, accel={accel}, rot={rot}, mic_ok={mic_ok}, imu_ok={imu_ok}"
        )
        assert phase1_result.mood_int == phase2_result.mood_int, (
            "camera_ok=False must not change mood_int (wire format unchanged)."
        )
        assert phase1_result.confidence == phase2_result.confidence, (
            f"ADDITIVE INVARIANT VIOLATED: camera_ok=False changed confidence "
            f"from {phase1_result.confidence} to {phase2_result.confidence}. "
            f"Camera absence must not penalise confidence."
        )
        assert phase1_result.gated == phase2_result.gated, (
            f"ADDITIVE INVARIANT VIOLATED: camera_ok=False changed gated flag "
            f"from {phase1_result.gated} to {phase2_result.gated}."
        )
        assert math.isclose(phase1_result.tension, phase2_result.tension, rel_tol=1e-9), (
            f"ADDITIVE INVARIANT VIOLATED: camera_ok=False changed tension "
            f"from {phase1_result.tension} to {phase2_result.tension}."
        )

    def test_camera_ok_false_does_not_reduce_confidence_vs_phase1(self) -> None:
        """
        camera_ok=False must NEVER reduce confidence below Phase-1.

        Regression guard: an incorrect implementation might multiply confidence
        by a camera-absent penalty factor.  Camera absence is the *default* —
        it cannot be penalised.
        """
        if not _COMPUTE_MOOD_CAMERA_LANDED:
            pytest.skip("compute_mood visual params not yet landed — pending Librarian.")

        # Stressed signal — high confidence in Phase 1
        phase1 = compute_mood(
            audio_rms=0.8, audio_pitch_variance=0.9,
            imu_acceleration=0.8, imu_rotation=0.7,
            mic_ok=True, imu_ok=True,
        )
        phase2 = compute_mood(
            audio_rms=0.8, audio_pitch_variance=0.9,
            imu_acceleration=0.8, imu_rotation=0.7,
            mic_ok=True, imu_ok=True,
            camera_ok=False,
        )
        assert phase2.confidence >= phase1.confidence, (
            f"camera_ok=False reduced confidence from {phase1.confidence} to "
            f"{phase2.confidence}. Camera absence is NOT a sensor failure — "
            f"it must not penalise confidence. (ADDITIVE INVARIANT, §1.4)"
        )


# ═════════════════════════════════════════════════════════════════════════════
# 3. Camera present — visual signal does influence inference
# ═════════════════════════════════════════════════════════════════════════════

class TestCameraContribution:
    """
    When camera_ok=True, visual_activity/visual_brightness are real inputs.
    Tests verify directional behavior: more camera data → higher confidence,
    high visual_activity → elevated tension contribution.

    All tests skip until Librarian lands visual weights in compute_mood.
    """

    @pytest.fixture(autouse=True)
    def _skip_if_no_camera_params(self) -> None:
        if not _COMPUTE_MOOD_CAMERA_LANDED:
            pytest.skip(
                "compute_mood visual params not yet landed — pending Librarian. "
                "These tests activate once visual_activity/camera_ok are accepted."
            )

    def test_camera_ok_true_does_not_reduce_confidence(self) -> None:
        """
        camera_ok=True with neutral visual signal must not reduce confidence
        below camera_ok=False.  More data = same or better confidence.
        """
        base = compute_mood(
            audio_rms=0.8, audio_pitch_variance=0.9,
            imu_acceleration=0.8, imu_rotation=0.7,
            mic_ok=True, imu_ok=True,
            camera_ok=False,
        )
        with_camera = compute_mood(
            audio_rms=0.8, audio_pitch_variance=0.9,
            imu_acceleration=0.8, imu_rotation=0.7,
            mic_ok=True, imu_ok=True,
            camera_ok=True,
            visual_activity=0.5,
            visual_brightness=0.5,
        )
        assert with_camera.confidence >= base.confidence, (
            f"camera_ok=True with neutral visual should not reduce confidence. "
            f"Got base={base.confidence}, with_camera={with_camera.confidence}."
        )

    def test_all_dark_scene_does_not_crash(self) -> None:
        """
        All-dark scene: visual_brightness = 0.0, visual_activity = 0.0.
        Must not raise; mood and confidence must be finite and valid.
        """
        try:
            result = compute_mood(
                audio_rms=0.5, audio_pitch_variance=0.3,
                imu_acceleration=0.2, imu_rotation=0.1,
                mic_ok=True, imu_ok=True,
                camera_ok=True,
                visual_activity=0.0,
                visual_brightness=0.0,
            )
        except Exception as exc:  # noqa: BLE001
            pytest.fail(
                f"compute_mood with all-dark scene raised {type(exc).__name__}: {exc}. "
                "All-dark is a valid camera state — inference must not crash."
            )
        assert result.mood in ("neutral", "calm", "stressed", "attention"), (
            f"All-dark scene returned invalid mood '{result.mood}'."
        )
        assert math.isfinite(result.confidence), (
            f"All-dark scene produced non-finite confidence: {result.confidence}."
        )

    def test_high_visual_activity_elevates_tension_relative_to_low(self) -> None:
        """
        High visual_activity (1.0) vs low (0.0) should produce higher tension,
        all else equal.

        This validates that visual_activity is wired into the tension formula
        as a positive weight — not inverted or ignored.
        """
        low_activity = compute_mood(
            audio_rms=0.5, audio_pitch_variance=0.3,
            imu_acceleration=0.2, imu_rotation=0.1,
            mic_ok=True, imu_ok=True,
            camera_ok=True, visual_activity=0.0, visual_brightness=0.5,
        )
        high_activity = compute_mood(
            audio_rms=0.5, audio_pitch_variance=0.3,
            imu_acceleration=0.2, imu_rotation=0.1,
            mic_ok=True, imu_ok=True,
            camera_ok=True, visual_activity=1.0, visual_brightness=0.5,
        )
        assert high_activity.tension >= low_activity.tension, (
            f"High visual_activity (1.0) should not produce lower tension than "
            f"low visual_activity (0.0). Got high={high_activity.tension:.4f}, "
            f"low={low_activity.tension:.4f}. "
            "visual_activity must contribute positively to tension."
        )

    def test_camera_ok_transitions_false_to_true(self) -> None:
        """
        camera_ok transitioning False→True must not crash and must produce
        valid output.  Simulates the device camera coming online mid-session.
        """
        # First: camera absent (startup default)
        frame_no_cam = compute_mood(
            audio_rms=0.5, audio_pitch_variance=0.3,
            imu_acceleration=0.2, imu_rotation=0.1,
            mic_ok=True, imu_ok=True,
            camera_ok=False,
        )
        # Then: camera comes online
        frame_with_cam = compute_mood(
            audio_rms=0.5, audio_pitch_variance=0.3,
            imu_acceleration=0.2, imu_rotation=0.1,
            mic_ok=True, imu_ok=True,
            camera_ok=True,
            visual_activity=0.4,
            visual_brightness=0.6,
        )
        assert isinstance(frame_no_cam, MoodResult), "camera_ok=False must return MoodResult."
        assert isinstance(frame_with_cam, MoodResult), "camera_ok=True must return MoodResult."
        assert frame_with_cam.mood in ("neutral", "calm", "stressed", "attention"), (
            f"After camera_ok True, mood must be valid; got '{frame_with_cam.mood}'."
        )

    def test_camera_ok_transitions_true_to_false(self) -> None:
        """
        camera_ok transitioning True→False (camera disconnects mid-session).
        Must fall back to Phase-1 behavior exactly (additive invariant).
        """
        # Camera active
        with_cam = compute_mood(
            audio_rms=0.6, audio_pitch_variance=0.4,
            imu_acceleration=0.3, imu_rotation=0.2,
            mic_ok=True, imu_ok=True,
            camera_ok=True,
            visual_activity=0.5, visual_brightness=0.5,
        )
        # Camera drops out
        no_cam = compute_mood(
            audio_rms=0.6, audio_pitch_variance=0.4,
            imu_acceleration=0.3, imu_rotation=0.2,
            mic_ok=True, imu_ok=True,
            camera_ok=False,
        )
        # Phase-1 reference
        phase1 = compute_mood(
            audio_rms=0.6, audio_pitch_variance=0.4,
            imu_acceleration=0.3, imu_rotation=0.2,
            mic_ok=True, imu_ok=True,
        )
        assert no_cam.mood == phase1.mood, (
            f"After camera_ok False, mood must match Phase-1 ('{phase1.mood}'). "
            f"Got '{no_cam.mood}'. Camera dropout is not a degradation."
        )
        assert no_cam.confidence == phase1.confidence, (
            f"After camera_ok False, confidence must match Phase-1 ({phase1.confidence}). "
            f"Got {no_cam.confidence}."
        )

    def test_nan_visual_activity_does_not_crash(self) -> None:
        """
        NaN visual_activity (corrupt JPEG → invalid feature) must not crash.
        The inference pipeline must treat it like a camera-absent frame.
        """
        try:
            result = compute_mood(
                audio_rms=0.5, audio_pitch_variance=0.3,
                imu_acceleration=0.2, imu_rotation=0.1,
                mic_ok=True, imu_ok=True,
                camera_ok=True,
                visual_activity=float("nan"),
                visual_brightness=0.5,
            )
        except Exception as exc:  # noqa: BLE001
            pytest.fail(
                f"compute_mood with NaN visual_activity raised {type(exc).__name__}: {exc}. "
                "Corrupt JPEG → NaN feature must not crash inference."
            )
        assert result.mood in ("neutral", "calm", "stressed", "attention"), (
            f"NaN visual_activity produced invalid mood '{result.mood}'."
        )
