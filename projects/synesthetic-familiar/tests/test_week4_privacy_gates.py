"""
Week 4 "It sees" — Raven privacy gate tests.

Gates covered (phase2-architecture-draft.md §4.2):
  CAMERA-I1  Raw JPEG buffer zeroed after feature extraction (merge-blocking).
  CAMERA-I2  SensorFrame public surface exposes floats only — no JPEG bytes /
             pixel arrays / image objects on the public API.
  CAMERA-I6  No JPEG bytes / pixel content emitted in logs at INFO+ level.
  MODEL-I5   model_sync request contains NO user ID / device ID / baseline
             stats; downloaded weights are hash-verified before applying.

All tests are either:
  • Active now  — test SensorFrame surface which already exists.
  • Skip-pending — skip cleanly when the new module/class isn't landed yet,
                   activate automatically once the code exists.

Date: 2026-06-14
"""
from __future__ import annotations

import dataclasses
import logging
import types

import pytest

# ── Import guards ─────────────────────────────────────────────────────────────

try:
    from host.sensors import SensorFrame
    _SENSORS_IMPORT_ERROR: str | None = None
except ImportError as _e:
    _SENSORS_IMPORT_ERROR = str(_e)
    SensorFrame = None  # type: ignore[assignment]

# _CameraRelay is a private class Ng will add to host.sensors
try:
    from host.sensors import _CameraRelay  # type: ignore[attr-defined]
    _CAMERA_RELAY_AVAILABLE = True
except (ImportError, AttributeError):
    _CameraRelay = None  # type: ignore[assignment,misc]
    _CAMERA_RELAY_AVAILABLE = False

# model_sync is a new module Librarian will create
try:
    import host.model_sync as _model_sync  # type: ignore[import]
    _MODEL_SYNC_AVAILABLE = True
except ImportError:
    _model_sync = None  # type: ignore[assignment]
    _MODEL_SYNC_AVAILABLE = False

# Camera fields presence check
_CAMERA_FIELDS_LANDED = (
    SensorFrame is not None
    and hasattr(SensorFrame, "__dataclass_fields__")
    and "camera_ok" in SensorFrame.__dataclass_fields__
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _require_sensors() -> None:
    if _SENSORS_IMPORT_ERROR is not None:
        pytest.fail(
            f"host.sensors is not importable: {_SENSORS_IMPORT_ERROR}\n"
            "Privacy gate tests require sensors.py to be importable."
        )


# ═════════════════════════════════════════════════════════════════════════════
# CAMERA-I2 — SensorFrame public surface: floats only, no image data
# ═════════════════════════════════════════════════════════════════════════════

class TestCameraI2_SensorFramePublicSurface:
    """
    CAMERA-I2 (MERGE-BLOCKING): SensorFrame must expose only extracted visual
    features as plain floats.  No JPEG bytes, no pixel arrays, no image objects
    may appear on the public API.  Mirrors mic I7.

    Phase-1 fields are already clean; these tests verify the Phase-2 extension
    preserves that contract.
    """

    # Forbidden types: raw image data in any form
    _FORBIDDEN_TYPES: tuple[type, ...] = (bytes, bytearray, memoryview)
    _FORBIDDEN_FIELD_NAMES: frozenset[str] = frozenset({
        "jpeg", "jpg", "image", "img", "pixel", "pixels",
        "frame_data", "raw_frame", "raw_image", "raw_jpeg",
        "buffer", "img_buffer", "frame_buffer",
    })

    def test_sensorframe_has_no_bytes_fields(self) -> None:
        """
        CAMERA-I2: No field on SensorFrame may have type bytes/bytearray/memoryview.

        Verifies both Phase-1 fields (already clean) and any new camera fields.
        """
        assert dataclasses.is_dataclass(SensorFrame), (
            "SensorFrame must be a @dataclass."
        )
        fields = dataclasses.fields(SensorFrame)
        for field in fields:
            ann = field.type
            if isinstance(ann, type):
                assert ann not in self._FORBIDDEN_TYPES, (
                    f"CAMERA-I2 VIOLATION: SensorFrame.{field.name} has type "
                    f"{ann.__name__} — raw image bytes must not appear in SensorFrame. "
                    "Camera pixels must be extracted to floats before reaching SensorFrame."
                )
            ann_str = str(ann).lower()
            for forbidden in ("ndarray", "bytes", "bytearray", "memoryview", "image", "jpeg"):
                assert forbidden not in ann_str, (
                    f"CAMERA-I2 VIOLATION: SensorFrame.{field.name} annotation "
                    f"'{ann}' contains '{forbidden}'. "
                    "Only float/bool fields are permitted on SensorFrame."
                )

    def test_sensorframe_has_no_image_named_fields(self) -> None:
        """
        CAMERA-I2: No field on SensorFrame may have a name associated with raw
        image data (jpeg, pixels, image, buffer, etc.).
        """
        fields = dataclasses.fields(SensorFrame)
        field_names = {f.name.lower() for f in fields}
        violations = field_names & self._FORBIDDEN_FIELD_NAMES
        assert not violations, (
            f"CAMERA-I2 VIOLATION: SensorFrame has fields with raw-image names: "
            f"{violations}. These must not appear on the public SensorFrame API. "
            "Extract to floats (visual_activity, visual_brightness) before SensorFrame."
        )

    def test_sensorframe_instance_contains_no_image_typed_values(self) -> None:
        """
        CAMERA-I2: Instantiated SensorFrame must contain no bytes/array/image values.

        Constructs a Phase-1 frame (compatible before and after camera extension)
        and inspects all attribute values.
        """
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
            frame = SensorFrame(  # type: ignore[call-arg]
                audio_rms=0.5,
                audio_pitch_variance=0.2,
                imu_acceleration=0.3,
                imu_rotation=0.1,
            )

        for attr_name in vars(frame):
            val = getattr(frame, attr_name)
            assert not isinstance(val, (bytes, bytearray, memoryview)), (
                f"CAMERA-I2 VIOLATION: SensorFrame.{attr_name} = {type(val).__name__!r} "
                f"— raw image bytes must not appear in SensorFrame instances."
            )
            type_name = type(val).__name__.lower()
            for forbidden in ("array", "image", "jpeg"):
                if forbidden in type_name and not isinstance(val, bool):
                    pytest.fail(
                        f"CAMERA-I2 VIOLATION: SensorFrame.{attr_name} is type "
                        f"'{type(val).__name__}' — image/array types must not appear "
                        "in SensorFrame instances."
                    )

    def test_sensorframe_camera_fields_are_float_typed_when_present(self) -> None:
        """
        CAMERA-I2: When camera fields are present (Ng has landed), visual_activity
        and visual_brightness must be typed float, not image containers.
        """
        if not _CAMERA_FIELDS_LANDED:
            pytest.skip("Camera fields not yet landed — pending Ng. Test activates automatically.")
        fields = {f.name: f for f in dataclasses.fields(SensorFrame)}
        for fname in ("visual_activity", "visual_brightness"):
            f = fields[fname]
            assert f.type is float or str(f.type).lower() in ("float", "<class 'float'>"), (
                f"CAMERA-I2 VIOLATION: SensorFrame.{fname} must be typed float; "
                f"got '{f.type}'. Only extracted float features are permitted."
            )


# ═════════════════════════════════════════════════════════════════════════════
# CAMERA-I1 — Raw JPEG buffer zeroed after feature extraction
# ═════════════════════════════════════════════════════════════════════════════

class TestCameraI1_BufferZeroed:
    """
    CAMERA-I1 (MERGE-BLOCKING): Raw JPEG buffer must be zeroed immediately
    after visual feature extraction, not merely dereferenced.

    Same three-layer pattern as mic I7 (snapshot, zero in-place, del reference).
    Tests skip until Ng lands _CameraRelay in host/sensors.py.
    """

    @pytest.fixture(autouse=True)
    def _skip_if_no_relay(self) -> None:
        if not _CAMERA_RELAY_AVAILABLE:
            pytest.skip(
                "_CameraRelay not yet in host.sensors — pending Ng. "
                "Test activates automatically once _CameraRelay is implemented."
            )

    def test_camera_relay_zeros_buffer_after_extraction(self) -> None:
        """
        CAMERA-I1: After extracting visual features, the JPEG buffer held by
        _CameraRelay must be all-zero (not just dereferenced).

        Constructs a _CameraRelay, injects a fake JPEG buffer, calls the
        extraction method, then asserts the internal buffer is zeroed.
        """
        import numpy as np

        relay = _CameraRelay()
        # Inject a non-zero buffer simulating a received JPEG (if the relay
        # exposes a way to feed raw bytes, use it; otherwise call the internal
        # extraction path directly).
        fake_jpeg = bytes([0xFF, 0xD8, 0xFF, 0xE0] + [0xAB] * 100)  # minimal JPEG-ish header
        try:
            relay._receive_jpeg(fake_jpeg)  # type: ignore[attr-defined]
        except AttributeError:
            pytest.skip(
                "_CameraRelay has no _receive_jpeg() method yet — "
                "Ng may name it differently. Update this test when the API is defined."
            )

        # Extract features — after this, buffer must be zeroed
        try:
            relay._extract_visual_features()  # type: ignore[attr-defined]
        except AttributeError:
            pytest.skip(
                "_CameraRelay has no _extract_visual_features() method yet — "
                "update test when extraction API is defined."
            )

        # Assert internal buffer is all-zero
        buf = getattr(relay, "_jpeg_buffer", None) or getattr(relay, "_buffer", None)
        if buf is None:
            pytest.skip(
                "_CameraRelay has no _jpeg_buffer/_buffer attribute visible — "
                "cannot verify zeroing. Ng must document the buffer attribute name."
            )

        if hasattr(buf, "__len__"):
            if len(buf) > 0:
                if isinstance(buf, (bytes, bytearray)):
                    assert all(b == 0 for b in buf), (
                        "CAMERA-I1 VIOLATION: JPEG buffer is not zeroed after feature "
                        "extraction. Every byte must be 0x00 after extraction."
                    )
                elif hasattr(buf, "all"):  # numpy array
                    import numpy as np  # noqa: F811
                    assert np.all(buf == 0), (
                        "CAMERA-I1 VIOLATION: JPEG buffer numpy array is not zeroed "
                        "after feature extraction."
                    )

    def test_camera_relay_has_zeroing_contract_documented(self) -> None:
        """
        CAMERA-I1: _CameraRelay must document the zeroing contract (equivalent
        to sensors.py I7 comment block).

        Asserts that the class docstring or module docstring references the
        zeroing requirement — ensures the pattern isn't silently removed.
        """
        doc = (_CameraRelay.__doc__ or "") + (getattr(_CameraRelay, "__module__", "") or "")
        # We check the sensors module docstring too
        import host.sensors as _sensors_mod
        module_doc = _sensors_mod.__doc__ or ""
        combined = (doc + module_doc).lower()
        # Should mention zeroing or privacy gate for camera
        has_zero_ref = any(
            kw in combined
            for kw in ("zero", "zeroed", "camera-i1", "privacy gate", "buffer cleared")
        )
        if not has_zero_ref:
            pytest.fail(
                "CAMERA-I1: _CameraRelay and host.sensors module docs must reference "
                "the buffer-zeroing requirement (CAMERA-I1). "
                "Add a docstring comment equivalent to the I7 pattern in sensors.py. "
                "Expected keywords: 'zero', 'zeroed', 'CAMERA-I1', or 'buffer cleared'."
            )


# ═════════════════════════════════════════════════════════════════════════════
# CAMERA-I6 — No JPEG bytes / image data in INFO+ log records
# ═════════════════════════════════════════════════════════════════════════════

class TestCameraI6_NoImageDataInLogs:
    """
    CAMERA-I6: No JPEG bytes, image dimensions, or pixel content may appear
    in log records at INFO level or above.

    Rationale: INFO/WARNING/ERROR logs can be collected by external systems
    (log aggregators, cloud logging).  JPEG bytes in INFO+ logs would exfiltrate
    raw image data — a privacy failure even if the in-memory buffer is zeroed.

    Tests cover:
      • sensors.py logger ('familiar.sensors') during simulated camera extraction.
      • Any module-level logging triggered during SensorFrame construction.

    Tests skip until _CameraRelay exists; structural log-filter tests are active now.
    """

    _JPEG_MAGIC = bytes([0xFF, 0xD8])  # JPEG SOI marker
    _JPEG_MAGIC_HEX = "ffd8"

    def _collect_logs_above_debug(
        self,
        logger_name: str,
        action: "types.FunctionType",
    ) -> list[logging.LogRecord]:
        """Capture log records at INFO+ from the named logger during action()."""
        records: list[logging.LogRecord] = []

        class _Capture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                if record.levelno >= logging.INFO:
                    records.append(record)

        handler = _Capture()
        target_logger = logging.getLogger(logger_name)
        target_logger.addHandler(handler)
        try:
            action()
        finally:
            target_logger.removeHandler(handler)
        return records

    def test_sensorframe_construction_emits_no_image_bytes_in_logs(self) -> None:
        """
        CAMERA-I6: Constructing a SensorFrame (including Phase-2 camera fields)
        must not emit JPEG bytes or pixel data in INFO+ logs.

        This is a baseline test active before Ng's camera code lands.
        """
        def _construct() -> None:
            if _CAMERA_FIELDS_LANDED:
                SensorFrame(
                    audio_rms=0.5, audio_pitch_variance=0.3,
                    imu_acceleration=0.2, imu_rotation=0.1,
                    mic_ok=True, imu_ok=True,
                    camera_ok=True, visual_activity=0.4, visual_brightness=0.6,
                )
            else:
                SensorFrame(
                    audio_rms=0.5, audio_pitch_variance=0.3,
                    imu_acceleration=0.2, imu_rotation=0.1,
                )

        records = self._collect_logs_above_debug("familiar.sensors", _construct)
        for record in records:
            msg = record.getMessage().lower()
            assert self._JPEG_MAGIC_HEX not in msg, (
                f"CAMERA-I6 VIOLATION: INFO+ log record from familiar.sensors "
                f"contains JPEG magic bytes. Message: {record.getMessage()!r}"
            )
            assert "ffd8" not in msg and "\\xff\\xd8" not in msg, (
                f"CAMERA-I6 VIOLATION: JPEG SOI marker in log. "
                f"Message: {record.getMessage()!r}"
            )
            for banned in ("pixel", "jpeg", "jpg", "raw_frame", "image_data"):
                assert banned not in msg, (
                    f"CAMERA-I6 VIOLATION: log record contains '{banned}' at INFO+ level. "
                    f"Message: {record.getMessage()!r}. "
                    "Raw image terminology must not appear in INFO+ logs."
                )

    def test_camera_relay_extraction_logs_no_pixel_data(self) -> None:
        """
        CAMERA-I6: _CameraRelay._extract_visual_features() must not log
        JPEG bytes, pixel values, or image dimensions at INFO+ level.

        Skips until _CameraRelay is implemented by Ng.
        """
        if not _CAMERA_RELAY_AVAILABLE:
            pytest.skip("_CameraRelay not yet in host.sensors — pending Ng.")

        fake_jpeg = bytes([0xFF, 0xD8, 0xFF, 0xE0] + [0xAB] * 64)
        relay = _CameraRelay()

        def _run_extraction() -> None:
            try:
                relay._receive_jpeg(fake_jpeg)  # type: ignore[attr-defined]
                relay._extract_visual_features()  # type: ignore[attr-defined]
            except AttributeError:
                pass  # API not defined yet — nothing to log-check

        records = self._collect_logs_above_debug("familiar.sensors", _run_extraction)
        for record in records:
            msg_bytes = record.getMessage().encode("utf-8", errors="replace")
            assert self._JPEG_MAGIC not in msg_bytes, (
                f"CAMERA-I6 VIOLATION: JPEG magic bytes (0xFF 0xD8) found in "
                f"INFO+ log during camera extraction. Record: {record.getMessage()!r}"
            )
            msg = record.getMessage().lower()
            for banned in ("pixel", "0xff", "\\xd8", "jpeg bytes", "raw bytes"):
                assert banned not in msg, (
                    f"CAMERA-I6 VIOLATION: '{banned}' found in INFO+ log during "
                    f"camera extraction. Message: {record.getMessage()!r}"
                )


# ═════════════════════════════════════════════════════════════════════════════
# MODEL-I5 — model_sync request privacy + hash verification
# ═════════════════════════════════════════════════════════════════════════════

class TestModelI5_ModelSyncPrivacy:
    """
    MODEL-I5: Population model download (host/model_sync.py, Librarian) must:
      1. Send NO user ID, device ID, or baseline stats in the HTTP request.
      2. Verify the content-hash of downloaded weights before applying them.
      3. Reject (not apply) weights when the hash does not match.
      4. Use HTTPS only — no plaintext HTTP.

    All tests skip until Librarian creates host/model_sync.py.
    """

    @pytest.fixture(autouse=True)
    def _skip_if_no_model_sync(self) -> None:
        if not _MODEL_SYNC_AVAILABLE:
            pytest.skip(
                "host.model_sync not yet created — pending Librarian. "
                "Tests activate automatically once model_sync.py is implemented."
            )

    def test_download_request_contains_no_user_id(self) -> None:
        """
        MODEL-I5: The HTTP GET request to the model server must contain no
        user_id, device_id, or user-identifying query parameter.

        Patches urllib.request.build_opener so the Request object passed to
        opener.open() can be inspected — no real network traffic.
        """
        from unittest.mock import patch, MagicMock

        fake_weights = b'{"weights": {"pitch_var": 0.4, "imu_accel": 0.3, "imu_rot": 0.3}}'
        fake_hash = __import__("hashlib").sha256(fake_weights).hexdigest()

        captured_requests: list = []

        def _mock_open(req, timeout=None):
            captured_requests.append(req)
            response = MagicMock()
            response.read.return_value = fake_weights
            response.__enter__ = lambda s: s
            response.__exit__ = MagicMock(return_value=False)
            return response

        mock_opener = MagicMock()
        mock_opener.open.side_effect = _mock_open

        with patch("urllib.request.build_opener", return_value=mock_opener):
            try:
                _model_sync.download_weights(  # type: ignore[attr-defined]
                    url="https://example.com/model.json",
                    expected_hash=fake_hash,
                )
            except Exception as exc:
                pytest.fail(
                    f"download_weights raised unexpectedly: {type(exc).__name__}: {exc}"
                )

        assert captured_requests, "download_weights must make at least one HTTP request."
        for req in captured_requests:
            # Check URL for user-identifying query params
            full_url = getattr(req, "full_url", None) or str(req)
            for banned_param in ("user_id", "device_id", "user", "uid", "baseline", "stats"):
                assert banned_param not in full_url.lower(), (
                    f"MODEL-I5 VIOLATION: HTTP request URL contains '{banned_param}': "
                    f"{full_url!r}. No user data may be sent in the model download request."
                )
            # Check headers for user-identifying data
            headers = getattr(req, "headers", {}) or {}
            for header_name, header_val in headers.items():
                for banned in ("user_id", "device_id", "x-user", "x-device", "x-baseline"):
                    assert banned not in str(header_name).lower(), (
                        f"MODEL-I5 VIOLATION: Request header '{header_name}' contains "
                        f"user-identifying key. No user data in model download request."
                    )
                    assert banned not in str(header_val).lower(), (
                        f"MODEL-I5 VIOLATION: Request header value contains user-identifying "
                        f"data: '{header_val}'. No user data in model download request."
                    )

    def test_download_request_uses_https(self) -> None:
        """
        MODEL-I5: model_sync must use HTTPS — not HTTP — for the download.
        Population weights over plain HTTP are interceptable and injectable.
        """
        from unittest.mock import patch, MagicMock

        captured_requests: list = []
        fake_weights = b'{"weights": {}}'
        fake_hash = __import__("hashlib").sha256(fake_weights).hexdigest()

        def _mock_urlopen(req, *args, **kwargs):
            captured_requests.append(req)
            response = MagicMock()
            response.read.return_value = fake_weights
            response.__enter__ = lambda s: s
            response.__exit__ = MagicMock(return_value=False)
            return response

        # model_sync should reject or convert http:// to https://
        try:
            with patch("urllib.request.urlopen", side_effect=_mock_urlopen):
                _model_sync.download_weights(  # type: ignore[attr-defined]
                    url="http://example.com/model.json",  # intentionally HTTP
                    expected_hash=fake_hash,
                )
        except (ValueError, RuntimeError, Exception) as exc:
            # Acceptable: model_sync raises for HTTP URLs
            assert "https" in str(exc).lower() or "http" in str(exc).lower(), (
                f"MODEL-I5: download_weights raised {type(exc).__name__} for HTTP URL "
                f"but the message doesn't mention HTTPS: {exc}"
            )
            return

        # If it didn't raise, verify only HTTPS requests were made
        for req in captured_requests:
            full_url = getattr(req, "full_url", None) or str(req)
            assert full_url.startswith("https://"), (
                f"MODEL-I5 VIOLATION: download_weights made a non-HTTPS request: "
                f"{full_url!r}. Population model downloads must use HTTPS only."
            )

    def test_hash_verified_before_applying_weights(self) -> None:
        """
        MODEL-I5: Downloaded weights must be hash-verified before applying.
        A corrupt or tampered model must be rejected (not applied).

        Patches urllib.request.build_opener so opener.open() returns fake bytes
        whose hash does NOT match the expected hash — verifying the hash-before-apply
        gate is enforced fail-closed and that the mock is actually hit.
        """
        from unittest.mock import patch, MagicMock

        fake_weights = b'{"weights": {"pitch_var": 0.4}}'
        correct_hash = __import__("hashlib").sha256(fake_weights).hexdigest()
        wrong_hash = "a" * 64  # valid hex length, wrong content

        mock_called = False

        def _mock_open(req, timeout=None):
            nonlocal mock_called
            mock_called = True
            response = MagicMock()
            response.read.return_value = fake_weights
            response.__enter__ = lambda s: s
            response.__exit__ = MagicMock(return_value=False)
            return response

        mock_opener = MagicMock()
        mock_opener.open.side_effect = _mock_open

        with patch("urllib.request.build_opener", return_value=mock_opener):
            # Should raise (or return None/failure) when hash doesn't match
            try:
                result = _model_sync.download_weights(  # type: ignore[attr-defined]
                    url="https://example.com/model.json",
                    expected_hash=wrong_hash,
                )
                # If no exception raised, result must be falsy (None, False, {})
                if result:
                    pytest.fail(
                        "MODEL-I5 VIOLATION: download_weights returned a truthy result "
                        "despite hash mismatch. Tampered weights must be REJECTED, not applied. "
                        f"expected_hash={wrong_hash!r}, actual content hash would be "
                        f"{correct_hash!r}."
                    )
            except (ValueError, RuntimeError, OSError, Exception) as exc:
                # Acceptable — any exception on hash mismatch is correct behavior
                assert exc is not None  # suppress linter

        assert mock_called, (
            "MODEL-I5 VIOLATION: The download mock was never invoked — "
            "the hash-before-apply gate was not exercised. "
            "Patch target may be wrong (should be urllib.request.build_opener)."
        )

    def test_correct_hash_accepts_weights(self) -> None:
        """
        MODEL-I5: Correct hash → weights must be accepted and returned.

        Patches urllib.request.build_opener so the opener.open() call returns
        fake weights without touching the network.
        """
        from unittest.mock import patch, MagicMock

        fake_weights = b'{"weights": {"pitch_var": 0.4, "imu_accel": 0.3}}'
        correct_hash = __import__("hashlib").sha256(fake_weights).hexdigest()

        mock_response = MagicMock()
        mock_response.read.return_value = fake_weights
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response

        with patch("urllib.request.build_opener", return_value=mock_opener):
            try:
                result = _model_sync.download_weights(  # type: ignore[attr-defined]
                    url="https://example.com/model.json",
                    expected_hash=correct_hash,
                )
            except Exception as exc:
                pytest.fail(
                    f"download_weights raised for CORRECT hash: {type(exc).__name__}: {exc}. "
                    "A matching hash must be accepted."
                )
        assert result is not None, (
            "download_weights must return the weights (not None) when hash matches."
        )


# ═════════════════════════════════════════════════════════════════════════════
# MODEL-I5 — Negative-scheme rejection (M3 + I2 coverage)
# ═════════════════════════════════════════════════════════════════════════════

class TestModelI5_NegativeSchemeDownload:
    """
    MODEL-I5: download_weights must reject any non-HTTPS URL with ValueError
    before making a network connection.

    Plain pytest class (no TestCase) — required for pytest.mark.parametrize.
    """

    @pytest.fixture(autouse=True)
    def _skip_if_no_model_sync(self) -> None:
        if not _MODEL_SYNC_AVAILABLE:
            pytest.skip(
                "host.model_sync not yet created — pending Librarian. "
                "Tests activate automatically once model_sync.py is implemented."
            )

    @pytest.mark.parametrize("bad_url,description", [
        ("file:///etc/passwd",          "file:// scheme"),
        ("ftp://example.com/w.json",    "ftp:// scheme"),
        ("data:application/json,{}",    "data: scheme"),
        ("",                            "empty URL"),
    ])
    def test_non_https_url_raises_value_error(
        self, bad_url: str, description: str
    ) -> None:
        """
        MODEL-I5: download_weights must raise ValueError for any non-HTTPS URL.

        No mock needed — the scheme check fires before any network I/O.
        """
        with pytest.raises(ValueError):
            _model_sync.download_weights(  # type: ignore[attr-defined]
                url=bad_url,
                expected_hash="a" * 64,
            )

    def test_redirect_downgrade_to_http_raises_value_error(self) -> None:
        """
        MODEL-I5: If an HTTPS URL redirects to http://, download_weights must
        raise ValueError — no silent downgrade to plain HTTP.

        Simulates the scenario by making build_opener().open() raise ValueError
        with the message that _HTTPSOnlyRedirectHandler would produce, then
        verifying that download_weights propagates it.
        """
        from unittest.mock import patch, MagicMock

        redirect_error = ValueError(
            "MODEL-I5 violation: redirect to non-HTTPS scheme 'http' rejected "
            "(target: 'http://example.com/model.json')"
        )

        mock_opener = MagicMock()
        mock_opener.open.side_effect = redirect_error

        with patch("urllib.request.build_opener", return_value=mock_opener):
            with pytest.raises(ValueError, match=r"(?i)redirect|https|MODEL-I5"):
                _model_sync.download_weights(  # type: ignore[attr-defined]
                    url="https://example.com/model.json",
                    expected_hash="a" * 64,
                )
