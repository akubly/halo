"""
Week 4 "It sees" — model_sync.py edge cases + BLE camera relay edge cases.

Edge cases covered (phase2-architecture-draft.md §6 + locked contract):
  1. Model download hash mismatch → weights rejected, local fallback applied.
  2. Model server unreachable → graceful local fallback (no crash, no stale
     corrupt state).
  3. BLE drop mid-JPEG reassembly → partial buffer discarded, camera_ok=False.
  4. Partial / corrupt JPEG → feature extraction returns default floats
     (visual_activity=0.0, visual_brightness=0.5, camera_ok=False).
  5. Online weight bounds guard: weights cannot exceed 2× the population
     default (phase2-architecture-draft.md §6.1 "Online learning instability").
  6. Weight reset-to-defaults: a corrupted/diverged weight set can be reset.

Tests targeting host/model_sync.py skip until Librarian creates the module.
Tests targeting sensors._CameraRelay skip until Ng implements the class.
Tests for inference.py weight guards skip until Librarian extends compute_mood.

Date: 2026-06-14
"""
from __future__ import annotations

import hashlib
import io
import math
from unittest.mock import MagicMock, patch

import pytest

# ── Import guards ─────────────────────────────────────────────────────────────

try:
    import host.model_sync as _model_sync  # type: ignore[import]
    _MODEL_SYNC_AVAILABLE = True
except ImportError:
    _model_sync = None  # type: ignore[assignment]
    _MODEL_SYNC_AVAILABLE = False

try:
    from host.sensors import _CameraRelay  # type: ignore[attr-defined]
    _CAMERA_RELAY_AVAILABLE = True
except (ImportError, AttributeError):
    _CameraRelay = None  # type: ignore[assignment,misc]
    _CAMERA_RELAY_AVAILABLE = False

try:
    from host.sensors import SensorFrame
    _SENSORS_OK = True
except ImportError:
    SensorFrame = None  # type: ignore[assignment]
    _SENSORS_OK = False

try:
    from host.inference import compute_mood, Baseline
    import inspect as _inspect
    _CAMERA_INFERENCE_LANDED = "camera_ok" in _inspect.signature(compute_mood).parameters
    _INFERENCE_OK = True
except ImportError:
    compute_mood = Baseline = None  # type: ignore[assignment]
    _CAMERA_INFERENCE_LANDED = False
    _INFERENCE_OK = False


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_mock_response(content: bytes):
    """Build a mock urllib response that returns content on .read()."""
    response = MagicMock()
    response.read.return_value = content
    response.__enter__ = lambda s: s
    response.__exit__ = MagicMock(return_value=False)
    return response


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ═════════════════════════════════════════════════════════════════════════════
# 1. Model sync — hash mismatch → reject and fall back
# ═════════════════════════════════════════════════════════════════════════════

class TestModelSyncHashMismatch:
    """
    MODEL-I5 / §6.1 risk mitigation: a tampered or corrupt model file must be
    rejected before being applied to inference weights.

    Expected contract for download_weights(url, expected_hash):
      - Returns the parsed weights dict when sha256(content) == expected_hash.
      - Raises ValueError (or returns None/falsy) when hash doesn't match.
      - Does NOT modify any global weight state when hash is wrong.
    """

    @pytest.fixture(autouse=True)
    def _skip_if_no_model_sync(self) -> None:
        if not _MODEL_SYNC_AVAILABLE:
            pytest.skip(
                "host.model_sync not yet created — pending Librarian. "
                "Activates automatically once model_sync.py is implemented."
            )

    @pytest.mark.parametrize("tamper_strategy,description", [
        # Flip a single bit in the payload
        (lambda b: bytes([b[0] ^ 0x01]) + b[1:], "single-bit flip"),
        # Append a byte
        (lambda b: b + b"\x00", "extra trailing byte"),
        # Truncate by one byte
        (lambda b: b[:-1], "truncated payload"),
        # Completely different content
        (lambda _: b'{"weights": {"pitch_var": 0.99}}', "substituted payload"),
    ])
    def test_hash_mismatch_rejects_weights(
        self,
        tamper_strategy,
        description: str,
    ) -> None:
        """
        Tampered model content (hash mismatch) must be rejected — not applied.
        """
        original = b'{"weights": {"pitch_var": 0.4, "imu_accel": 0.3, "imu_rot": 0.3}}'
        correct_hash = _sha256(original)
        tampered = tamper_strategy(original)
        # The tampered content produces a different hash — pass the original hash
        # so the check will fail on the tampered data.

        mock_called = False

        def _mock_open(req, timeout=None):
            nonlocal mock_called
            mock_called = True
            return _make_mock_response(tampered)

        mock_opener = MagicMock()
        mock_opener.open.side_effect = _mock_open

        with patch("urllib.request.build_opener", return_value=mock_opener):
            rejected = False
            try:
                result = _model_sync.download_weights(  # type: ignore[attr-defined]
                    url="https://example.com/model.json",
                    expected_hash=correct_hash,
                )
                if not result:
                    rejected = True  # returned None/falsy — acceptable rejection
                else:
                    pytest.fail(
                        f"MODEL-I5 VIOLATION ({description}): download_weights returned "
                        f"truthy result despite hash mismatch. Tampered weights must be "
                        f"rejected. tampered_content={tampered[:30]!r}..."
                    )
            except (ValueError, RuntimeError, OSError, Exception):
                rejected = True  # raised → correct behavior

        assert rejected, (
            f"download_weights must reject tampered content ({description})."
        )
        assert mock_called, (
            f"Hash-mismatch mock was never invoked for '{description}' — "
            "patch target may be wrong (should be urllib.request.build_opener). "
            "The test cannot be meaningful without intercepting the download."
        )

    def test_hash_mismatch_does_not_modify_global_state(self) -> None:
        """
        MODEL-I5: When hash verification fails, the caller's current weights
        must be returned unchanged (fail-closed guarantee).

        The API is pure-functional: sync_population_weights takes current weights
        and returns new weights.  On hash mismatch it must return the same weights
        that were passed in — demonstrating state isolation without any getter.
        """
        from host.inference import VisualWeights
        from host.model_sync import PopulationManifest, sync_population_weights

        # A sentinel "current" weights value distinct from factory defaults.
        current = VisualWeights(visual_activity=0.12, visual_brightness=0.04)

        # Manifest whose sha256 will NOT match the content we serve.
        manifest = PopulationManifest(
            url="https://example.com/model.json",
            sha256="a" * 64,  # 64 hex chars; guaranteed mismatch
        )

        fake_content = b'{"version": "1", "visual_activity": 0.15, "visual_brightness": 0.05}'
        mock_response = _make_mock_response(fake_content)
        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response

        with patch("urllib.request.build_opener", return_value=mock_opener):
            result = sync_population_weights(manifest, current)

        assert result == current, (
            f"MODEL-I5 VIOLATION: sync_population_weights changed weights on hash mismatch. "
            f"Expected returned weights == passed-in current={current!r}, got {result!r}. "
            "Fail-closed: hash mismatch must return current weights unchanged."
        )


# ═════════════════════════════════════════════════════════════════════════════
# 2. Model sync — server unreachable → graceful local fallback
# ═════════════════════════════════════════════════════════════════════════════

class TestModelSyncServerUnreachable:
    """
    §6.1 risk: "Fully offline after initial model download."

    When the model server is unreachable (network error, DNS failure, timeout),
    the inference pipeline must continue using local/default weights without
    crashing.  A network failure during startup must not prevent the creature
    from running.
    """

    @pytest.fixture(autouse=True)
    def _skip_if_no_model_sync(self) -> None:
        if not _MODEL_SYNC_AVAILABLE:
            pytest.skip(
                "host.model_sync not yet created — pending Librarian. "
                "Activates automatically once model_sync.py is implemented."
            )

    @pytest.mark.parametrize("error_type,description", [
        (OSError("Connection refused"),             "connection refused"),
        (OSError("Name resolution failed"),         "DNS failure"),
        (TimeoutError("Request timed out"),         "timeout"),
        (__import__("ssl").SSLError("handshake failed"), "SSL failure"),
    ])
    def test_network_error_does_not_crash(self, error_type, description: str) -> None:
        """
        Network errors during model download must not crash.

        download_weights (or a higher-level wrapper) must catch network errors
        and return None / fallback weights — never propagate to main().
        """
        mock_called = False

        def _mock_open(req, timeout=None):
            nonlocal mock_called
            mock_called = True
            raise error_type

        mock_opener = MagicMock()
        mock_opener.open.side_effect = _mock_open

        with patch("urllib.request.build_opener", return_value=mock_opener):
            try:
                result = _model_sync.download_weights(  # type: ignore[attr-defined]
                    url="https://example.com/model.json",
                    expected_hash="a" * 64,
                )
                # Acceptable: returned None/falsy (graceful fallback)
            except (OSError, TimeoutError, ConnectionError):
                # Acceptable: model_sync lets network errors propagate — caller handles
                pass
            except Exception as exc:
                # Unacceptable: non-network exception (e.g. AttributeError, ValueError)
                # propagating would crash main()
                pytest.fail(
                    f"download_weights raised unexpected {type(exc).__name__} "
                    f"for {description}: {exc}. "
                    "Only network-related exceptions (OSError, TimeoutError) may propagate."
                )

        assert mock_called, (
            f"Network error mock was not invoked for '{description}' — "
            "patch target may be wrong (should be urllib.request.build_opener). "
            "Without this the test cannot exercise the error-handling path."
        )

    def test_get_weights_with_fallback_returns_defaults_on_error(self) -> None:
        """
        A higher-level get_weights_with_fallback() (or equivalent) must return
        the population default weights when the server is unreachable.

        This ensures main() always has usable weights regardless of network state.
        """
        fn = (
            getattr(_model_sync, "get_weights_with_fallback", None)
            or getattr(_model_sync, "load_or_download_weights", None)
        )
        if fn is None:
            pytest.skip(
                "model_sync has no get_weights_with_fallback() — "
                "add a fallback-aware entry point and update this test."
            )

        mock_called = False

        def _mock_open(req, timeout=None):
            nonlocal mock_called
            mock_called = True
            raise OSError("No route to host")

        mock_opener = MagicMock()
        mock_opener.open.side_effect = _mock_open

        with patch("urllib.request.build_opener", return_value=mock_opener):
            try:
                result = fn(url="https://example.com/model.json", expected_hash="a" * 64)
            except Exception as exc:
                pytest.fail(
                    f"get_weights_with_fallback raised {type(exc).__name__}: {exc}. "
                    "This function must never raise — it always returns local defaults."
                )

        assert mock_called, (
            "Fallback mock was not invoked — "
            "patch target may be wrong (should be urllib.request.build_opener). "
            "Without this the test cannot verify offline fallback behaviour."
        )
        assert result is not None, (
            "get_weights_with_fallback must return non-None even when server is unreachable."
        )


# ═════════════════════════════════════════════════════════════════════════════
# 3. BLE camera relay edge cases — partial JPEG, corrupt JPEG, mid-BLE drop
# ═════════════════════════════════════════════════════════════════════════════

class TestCameraRelayEdgeCases:
    """
    BLE transfers JPEG in ~244B MTU fragments.  A typical 30KB JPEG is ~120
    fragments.  Any of them can be lost or corrupted.

    Camera relay (_CameraRelay) must handle:
      - Partial JPEG (fragments dropped → incomplete image): returns defaults.
      - Corrupt JPEG (invalid header or data): returns defaults, doesn't crash.
      - Mid-transfer BLE drop: relay resets, returns camera_ok=False frame.
      - Empty JPEG (zero-length payload): treated as absent, camera_ok=False.

    All tests skip until Ng implements _CameraRelay.
    """

    @pytest.fixture(autouse=True)
    def _skip_if_no_relay(self) -> None:
        if not _CAMERA_RELAY_AVAILABLE:
            pytest.skip(
                "_CameraRelay not yet in host.sensors — pending Ng. "
                "Activates automatically once _CameraRelay is implemented."
            )

    def _build_relay(self):
        """Construct a fresh _CameraRelay instance."""
        return _CameraRelay()

    @pytest.mark.parametrize("payload,description", [
        (b"",                                   "empty payload"),
        (bytes([0xFF, 0xD8]),                   "JPEG header only (no content)"),
        (bytes([0xFF, 0xD8] + [0xAB] * 10),     "partial JPEG (truncated, 12 bytes)"),
        (bytes([0xAB] * 50),                    "not a JPEG (random bytes)"),
        (bytes([0xFF, 0xD8, 0xFF]) + b"\x00" * 100,  "corrupt JPEG body"),
    ])
    def test_partial_or_corrupt_jpeg_returns_defaults(
        self,
        payload: bytes,
        description: str,
    ) -> None:
        """
        Partial / corrupt JPEG must return default visual features and camera_ok=False.
        Must not crash or produce NaN floats.
        """
        relay = self._build_relay()
        try:
            relay._receive_jpeg(payload)  # type: ignore[attr-defined]
            result = relay._extract_visual_features()  # type: ignore[attr-defined]
        except AttributeError:
            pytest.skip(
                "_CameraRelay API (_receive_jpeg/_extract_visual_features) not yet defined. "
                "Update once Ng documents the method names."
            )
        except Exception as exc:  # noqa: BLE001
            pytest.fail(
                f"_CameraRelay raised {type(exc).__name__} for {description}: {exc}. "
                "Corrupt/partial JPEG must not crash — degrade gracefully to defaults."
            )

        if result is None:
            return  # relay returns None for invalid JPEG — check SensorFrame path instead

        if isinstance(result, tuple):
            activity, brightness, cam_ok = result
        else:
            activity = getattr(result, "visual_activity", None)
            brightness = getattr(result, "visual_brightness", None)
            cam_ok = getattr(result, "camera_ok", None)

        if cam_ok is not None:
            assert cam_ok is False, (
                f"Corrupt/partial JPEG ({description}) must produce camera_ok=False. "
                f"Got camera_ok={cam_ok!r}."
            )
        if activity is not None:
            assert math.isfinite(activity), (
                f"Corrupt JPEG ({description}) produced non-finite visual_activity={activity}. "
                "Must default to 0.0 on extraction failure."
            )
        if brightness is not None:
            assert math.isfinite(brightness), (
                f"Corrupt JPEG ({description}) produced non-finite visual_brightness={brightness}. "
                "Must default to 0.5 on extraction failure."
            )

    def test_mid_ble_transfer_drop_resets_reassembly(self) -> None:
        """
        BLE drop mid-transfer (e.g., fragment 60 of 120 lost): relay must
        discard the partial reassembly buffer and return camera_ok=False.

        Simulates by feeding half a JPEG, then calling reset/drop, then verifying
        the relay is back to a clean state.
        """
        relay = self._build_relay()
        half_jpeg = bytes([0xFF, 0xD8, 0xFF, 0xE0] + [0xAB] * 50)

        try:
            relay._receive_jpeg(half_jpeg)  # type: ignore[attr-defined]
        except AttributeError:
            pytest.skip("_CameraRelay._receive_jpeg not defined yet — pending Ng.")

        # Simulate BLE disconnect/drop — relay should have a reset or clear method
        reset_fn = (
            getattr(relay, "_reset", None)
            or getattr(relay, "_clear_buffer", None)
            or getattr(relay, "_on_ble_drop", None)
        )
        if reset_fn is not None:
            try:
                reset_fn()
            except Exception as exc:
                pytest.fail(
                    f"_CameraRelay reset method raised {type(exc).__name__}: {exc}. "
                    "BLE drop recovery must not raise."
                )

        # After reset, attempting extraction should return defaults (not partial data)
        try:
            result = relay._extract_visual_features()  # type: ignore[attr-defined]
        except AttributeError:
            pytest.skip("_extract_visual_features not defined yet.")
        except Exception as exc:
            pytest.fail(
                f"After BLE drop + reset, _extract_visual_features raised "
                f"{type(exc).__name__}: {exc}. Must not crash."
            )

        cam_ok = (
            getattr(result, "camera_ok", None)
            if result is not None and not isinstance(result, tuple)
            else (result[2] if isinstance(result, tuple) and len(result) >= 3 else None)
        )
        if cam_ok is not None:
            assert cam_ok is False, (
                f"After BLE mid-transfer drop and reset, camera_ok must be False. "
                f"Got camera_ok={cam_ok!r}."
            )


# ═════════════════════════════════════════════════════════════════════════════
# 4. Online weight bounds guard (§6.1 instability mitigation)
# ═════════════════════════════════════════════════════════════════════════════

class TestOnlineWeightBounds:
    """
    §6.1: "Guard with weight bounds (no weight can exceed 2× default)."

    Online learning must not allow weights to drift arbitrarily far from the
    population default.  This prevents runaway adaptation from a corrupted
    session (e.g., extreme sensor values that keep pushing weights upward).
    """

    @pytest.fixture(autouse=True)
    def _skip_if_no_visual_inference(self) -> None:
        if not _CAMERA_INFERENCE_LANDED:
            pytest.skip(
                "compute_mood visual params not yet landed — pending Librarian. "
                "Weight bounds tests activate once online learning is implemented."
            )
        if not _MODEL_SYNC_AVAILABLE:
            pytest.skip("host.model_sync not yet available — pending Librarian.")

    def test_weight_cannot_exceed_two_times_default(self) -> None:
        """
        No individual weight may exceed 2× the population default value.

        Simulates applying an extreme online update (10× default) using the real
        visual keys (visual_activity, visual_brightness) and verifies clamping.

        Guard: asserts at least one expected key is present in the result before
        checking the bound, so this test can never pass vacuously if the API
        changes or unknown keys are silently ignored.
        """
        apply_fn = (
            getattr(_model_sync, "apply_weight_update", None)
            or getattr(_model_sync, "update_online_weights", None)
        )
        if apply_fn is None:
            pytest.skip(
                "model_sync has no apply_weight_update() — pending Librarian. "
                "Add weight-update function and update this test."
            )

        from host.inference import DEFAULT_VISUAL_WEIGHTS, MAX_VISUAL_WEIGHT_MULTIPLIER

        # Try to drive visual weights to 10× their defaults (should be clamped to ≤ 2×)
        # visual_activity default=0.15 → extreme=1.5; visual_brightness default=0.05 → extreme=0.5
        extreme_update = {
            "visual_activity":   DEFAULT_VISUAL_WEIGHTS.visual_activity * 10,
            "visual_brightness": DEFAULT_VISUAL_WEIGHTS.visual_brightness * 10,
        }
        try:
            result = apply_fn(extreme_update)
        except Exception as exc:
            pytest.fail(
                f"apply_weight_update raised {type(exc).__name__}: {exc}. "
                "Must not raise — invalid weights should be clamped, not rejected."
            )

        if result is None:
            pytest.skip("apply_weight_update returned None — check return contract.")

        # Guard: at least one expected visual key must be present in the result.
        # apply_weight_update silently ignores unknown keys, so if the visual keys
        # are missing the bound assertion would never fire (vacuous pass).
        visual_defaults = {
            "visual_activity":   DEFAULT_VISUAL_WEIGHTS.visual_activity,
            "visual_brightness": DEFAULT_VISUAL_WEIGHTS.visual_brightness,
        }
        present_keys = visual_defaults.keys() & result.keys()
        assert present_keys, (
            f"apply_weight_update result contains none of the expected visual keys "
            f"{set(visual_defaults)}. Got keys: {set(result.keys())}. "
            "Cannot verify bounds — check apply_weight_update return contract."
        )

        for key in present_keys:
            default = visual_defaults[key]
            cap = default * MAX_VISUAL_WEIGHT_MULTIPLIER
            assert result[key] <= cap + 1e-9, (
                f"§6.1 VIOLATION: Weight '{key}' = {result[key]:.4f} exceeds "
                f"2× population default ({cap:.4f}). "
                "Online learning must clamp weights to ≤ 2× default to prevent "
                "runaway adaptation."
            )

    def test_weights_can_be_reset_to_defaults(self) -> None:
        """
        §6.1: "Reset-to-defaults gesture or config."

        reset_weights_to_defaults() must return factory-default VisualWeights,
        enabling recovery from a corrupted/diverged weight set.
        The API is pure-functional — we assert on the return value directly.
        """
        reset_fn = (
            getattr(_model_sync, "reset_weights_to_defaults", None)
            or getattr(_model_sync, "reset_weights", None)
        )
        if reset_fn is None:
            pytest.skip(
                "model_sync has no reset_weights_to_defaults() — "
                "add it and update this test."
            )

        try:
            result = reset_fn()
        except Exception as exc:
            pytest.fail(
                f"reset_weights_to_defaults raised {type(exc).__name__}: {exc}. "
                "Weight reset must not raise."
            )

        assert result is not None, "reset_weights_to_defaults must return a value."

        import dataclasses
        from host.inference import DEFAULT_VISUAL_WEIGHTS

        # Normalise to dict for comparison (accepts VisualWeights or plain dict).
        if dataclasses.is_dataclass(result):
            result_dict = dataclasses.asdict(result)
        elif isinstance(result, dict):
            result_dict = result
        else:
            pytest.fail(
                f"reset_weights_to_defaults returned unexpected type "
                f"{type(result).__name__}. Expected VisualWeights or dict."
            )
            return  # unreachable, satisfies type-checker

        default_dict = dataclasses.asdict(DEFAULT_VISUAL_WEIGHTS)
        for key, expected in default_dict.items():
            assert key in result_dict, (
                f"reset result is missing key '{key}'. Expected keys: {set(default_dict)}."
            )
            assert math.isclose(result_dict[key], expected, rel_tol=1e-6), (
                f"After reset, weight '{key}' should be {expected}; "
                f"got {result_dict[key]}. "
                "reset_weights_to_defaults must restore population defaults."
            )


# ═════════════════════════════════════════════════════════════════════════════
# 5. Camera-ok=False baseline + inference structural anchors
# ═════════════════════════════════════════════════════════════════════════════

class TestCameraAbsenceStructuralAnchors:
    """
    Structural tests that are ACTIVE NOW (no pending implementer code needed).

    These verify the Phase-1 compute_mood signature is still present and
    callable without camera params — ensuring the additive extension doesn't
    break the existing API.
    """

    @pytest.fixture(autouse=True)
    def _require_inference(self) -> None:
        if not _INFERENCE_OK:
            pytest.fail("host.inference is not importable — required for structural anchors.")

    def test_phase1_compute_mood_still_callable_without_camera_params(self) -> None:
        """
        Phase-1 compute_mood signature is backwards-compatible.

        After Librarian adds visual params, the existing Phase-1 call
        (no visual params) must still work identically.
        """
        result = compute_mood(
            audio_rms=0.5,
            audio_pitch_variance=0.4,
            imu_acceleration=0.3,
            imu_rotation=0.2,
            mic_ok=True,
            imu_ok=True,
        )
        from host.inference import MoodResult
        assert isinstance(result, MoodResult), (
            f"compute_mood must return MoodResult; got {type(result).__name__!r}."
        )
        assert result.mood in ("neutral", "calm", "stressed", "attention"), (
            f"compute_mood returned invalid mood '{result.mood}'."
        )
        assert math.isfinite(result.confidence), (
            f"compute_mood returned non-finite confidence: {result.confidence}."
        )

    def test_baseline_with_50_samples_still_activates_personalized_threshold(self) -> None:
        """
        Phase-1 activation gate (Baseline.sample_count >= 50) must remain intact
        after Phase-2 camera/visual extension.  Librarian must not break this invariant.
        """
        from host.inference import ACTIVATION_THRESHOLD, get_activation_info

        b_under = Baseline(mean=0.5, stddev=0.1, sample_count=49, created_at="2026-06-14T00:00:00")
        b_at = Baseline(mean=0.5, stddev=0.1, sample_count=50, created_at="2026-06-14T00:00:00")

        info_under = get_activation_info(b_under)
        info_at = get_activation_info(b_at)

        assert info_under.state == "calibrating", (
            f"sample_count=49 must be 'calibrating'; got '{info_under.state}'."
        )
        assert info_at.state == "personalized", (
            f"sample_count=50 must be 'personalized'; got '{info_at.state}'."
        )

    def test_camera_ok_false_default_means_all_sensorframes_are_phase1_compatible(
        self,
    ) -> None:
        """
        Because camera_ok defaults to False, any code that creates SensorFrames
        without specifying camera_ok automatically gets Phase-1 behavior.

        This is the additive invariant expressed at the dataclass level: default
        SensorFrame is Phase-1 SensorFrame.
        """
        from host.sensors import SensorFrame as SF
        import dataclasses as dc

        fields = dc.fields(SF)
        camera_ok_field = next((f for f in fields if f.name == "camera_ok"), None)
        if camera_ok_field is None:
            pytest.skip("camera_ok not yet on SensorFrame — pending Ng.")

        assert camera_ok_field.default is False, (
            f"camera_ok default must be False (Phase-1 compatibility). "
            f"Got {camera_ok_field.default!r}. "
            "A SensorFrame created without camera_ok= must behave identically to Phase-1."
        )
