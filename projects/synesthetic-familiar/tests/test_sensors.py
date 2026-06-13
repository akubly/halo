"""
Unit tests for host/sensors.py — SensorSourcePort privacy gate.

Gate I7 (MERGE-BLOCKING): Verifies that SensorFrame exposes ONLY extracted
float features and ok-flags — never raw audio bytes, numpy arrays, or sample
buffers.  Raw audio must not cross the SensorSourcePort boundary.

See hiro-week2-integration-contract.md §1.3 for the locked invariant.
"""

import dataclasses
import inspect
import types
import unittest

import pytest

# ── Import guard ─────────────────────────────────────────────────────────────
try:
    from host.sensors import SensorFrame, SensorStream
    _IMPORT_ERROR: str | None = None
except ImportError as _e:
    _IMPORT_ERROR = str(_e)
    SensorFrame = None  # type: ignore[assignment]
    SensorStream = None  # type: ignore[assignment]


@pytest.fixture(autouse=True)
def _require_sensors_module() -> None:
    """Fail every test with a human-readable message if the module is missing."""
    if _IMPORT_ERROR is not None:
        pytest.fail(
            f"host.sensors is not yet importable: {_IMPORT_ERROR}\n"
            "These tests will pass once Ng implements the sensors module."
        )


class TestSensorSourcePort(unittest.TestCase):
    """
    Gate I7 — SensorSourcePort exposes no raw audio.

    The SensorSourcePort boundary is the interface between raw hardware
    capture and the inference pipeline.  Everything downstream receives
    only SensorFrame (extracted float features + ok-flags).  Raw audio
    never crosses this port.
    """

    # ── Locked SensorFrame field set (contract §1.1) ─────────────────────────

    _REQUIRED_FRAME_FIELDS: frozenset[str] = frozenset({
        "audio_rms",
        "audio_pitch_variance",
        "imu_acceleration",
        "imu_rotation",
        "mic_ok",
        "imu_ok",
    })

    _FORBIDDEN_RAW_NAMES: frozenset[str] = frozenset({
        # Exact attribute names that would indicate raw audio leakage
        "audio", "raw", "samples", "pcm", "buffer", "audio_buffer",
        "raw_audio", "raw_samples", "raw_pcm", "mic_buffer",
        "waveform", "signal", "frames", "audio_frames",
    })

    # Types that indicate raw audio leakage
    _FORBIDDEN_TYPES: tuple[type, ...] = (bytes, bytearray, memoryview)

    def test_sensor_source_port_exposes_no_raw_audio(self) -> None:
        """
        Gate I7 (MERGE-BLOCKING).

        SensorFrame must have EXACTLY the locked field set from contract §1.1.
        No bytes, bytearray, memoryview, or ndarray attribute may exist.
        No attribute whose name suggests raw audio/samples may exist.

        Any violation means raw audio could escape the SensorSourcePort
        boundary and reach inference, protocol, or wire — a privacy failure.
        """
        # ── 1. SensorFrame must be a dataclass ───────────────────────────────
        assert dataclasses.is_dataclass(SensorFrame), (
            "SensorFrame must be a @dataclasses.dataclass (contract §1.1)"
        )

        fields = dataclasses.fields(SensorFrame)
        field_names = {f.name for f in fields}

        # ── 2. Required fields must all be present ────────────────────────────
        missing = self._REQUIRED_FRAME_FIELDS - field_names
        assert not missing, (
            f"SensorFrame is missing required fields: {missing}. "
            f"Contract §1.1 requires: {self._REQUIRED_FRAME_FIELDS}"
        )

        # ── 3. No EXTRA fields beyond the locked set ─────────────────────────
        extra = field_names - self._REQUIRED_FRAME_FIELDS
        assert not extra, (
            f"SensorFrame has extra fields not in the locked contract: {extra}. "
            f"Extra fields could leak raw or intermediate sensor data. "
            f"Contract §1.1 is closed — no extensions without ARD amendment."
        )

        # ── 4. No field type annotation is bytes/bytearray/ndarray ───────────
        for field in fields:
            ann = field.type
            # Check resolved type annotations (if available)
            if isinstance(ann, type):
                assert ann not in self._FORBIDDEN_TYPES, (
                    f"SensorFrame.{field.name} has type {ann.__name__} — "
                    f"raw audio bytes must NOT appear in SensorFrame. "
                    f"Only float/bool fields are permitted (contract §1.1)."
                )
            # Check string annotation for 'ndarray' or 'bytes'
            ann_str = str(ann).lower()
            assert "ndarray" not in ann_str, (
                f"SensorFrame.{field.name} annotation '{ann}' contains 'ndarray'. "
                f"NumPy arrays are raw sample buffers — must not cross SensorSourcePort."
            )
            assert "bytes" not in ann_str, (
                f"SensorFrame.{field.name} annotation '{ann}' contains 'bytes'. "
                f"Raw audio bytes must not appear in SensorFrame."
            )

        # ── 5. float fields must be typed as float (not sample containers) ───
        float_fields = {"audio_rms", "audio_pitch_variance", "imu_acceleration", "imu_rotation"}
        for fname in float_fields:
            matching = [f for f in fields if f.name == fname]
            assert matching, f"Expected field '{fname}' in SensorFrame"
            ann_str = str(matching[0].type).lower()
            assert "float" in ann_str or matching[0].type is float, (
                f"SensorFrame.{fname} must be typed float; got '{matching[0].type}'. "
                f"Feature fields must be normalized 0.0–1.0 floats (contract §1.1)."
            )

        # ── 6. bool fields must be typed as bool ─────────────────────────────
        bool_fields = {"mic_ok", "imu_ok"}
        for fname in bool_fields:
            matching = [f for f in fields if f.name == fname]
            assert matching, f"Expected field '{fname}' in SensorFrame"
            assert matching[0].type is bool or str(matching[0].type).lower() in ("bool", "<class 'bool'>"), (
                f"SensorFrame.{fname} must be typed bool; got '{matching[0].type}'. "
                f"Sensor-ok flags are boolean (contract §1.1)."
            )

    def test_sensor_stream_public_api_has_no_raw_audio_methods(self) -> None:
        """
        SensorStream's public API must match exactly the contract §1.2 interface.
        No public method may expose raw audio bytes, buffers, or arrays.
        """
        # Contract §1.2 LOCKED public API
        required_methods = {"start", "stop", "__aiter__", "__anext__"}
        # Permitted dunder attrs beyond required
        allowed_dunder = {"__init__", "__class__", "__doc__", "__module__",
                         "__dict__", "__weakref__"}

        public_members = {
            name
            for name in dir(SensorStream)
            if not name.startswith("_") or name in required_methods
        }

        # Filter to public (non-dunder) methods only
        non_dunder_public = {m for m in public_members if not m.startswith("_")}

        for name in non_dunder_public:
            lowered = name.lower()
            assert lowered not in self._FORBIDDEN_RAW_NAMES, (
                f"SensorStream has public attribute '{name}' — this name suggests "
                f"raw audio exposure. SensorStream must not expose raw sample data. "
                f"Gate I7 (contract §1.3)"
            )

        # Required dunder/lifecycle methods must exist
        for method in required_methods:
            assert hasattr(SensorStream, method), (
                f"SensorStream missing required method '{method}' (contract §1.2)"
            )

    def test_sensor_frame_instantiation_contains_only_feature_values(self) -> None:
        """
        Instantiate SensorFrame with contract-compliant values and verify
        no raw-audio-shaped value leaks into any attribute.
        """
        # mic_ok and imu_ok might not exist in stub — handle gracefully
        try:
            frame = SensorFrame(
                audio_rms=0.5,
                audio_pitch_variance=0.2,
                imu_acceleration=0.3,
                imu_rotation=0.1,
                mic_ok=True,
                imu_ok=True,
            )
        except TypeError:
            # Stub SensorFrame doesn't have mic_ok/imu_ok yet
            frame = SensorFrame(
                audio_rms=0.5,
                audio_pitch_variance=0.2,
                imu_acceleration=0.3,
                imu_rotation=0.1,
            )

        # Verify no attribute contains bytes/bytearray/ndarray value
        for attr_name in vars(frame):
            val = getattr(frame, attr_name)
            assert not isinstance(val, (bytes, bytearray, memoryview)), (
                f"SensorFrame.{attr_name} = {type(val).__name__!r} — "
                f"raw audio bytes must not appear in SensorFrame instances. "
                f"Gate I7 (contract §1.3)"
            )
            # Check for ndarray (numpy may not be imported here, use duck-typing)
            type_name = type(val).__name__.lower()
            assert "array" not in type_name or isinstance(val, bool), (
                f"SensorFrame.{attr_name} appears to be an array type "
                f"({type(val).__name__}) — raw samples must not cross SensorSourcePort."
            )


if __name__ == "__main__":
    unittest.main()
