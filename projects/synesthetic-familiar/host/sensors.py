"""
Sensor capture for the Synesthetic Familiar host app.

Responsibilities:
- Mic audio capture from host via sounddevice (16kHz mono)
- IMU relay from Halo device via BLE SDK (SDK gap: degrades gracefully)

Privacy gate I7 (ARD §5.3, §5.6 — MERGE-BLOCKING):
  - Rolling audio buffer holds ≤1 second of float32 samples in memory.
  - Buffer is ZEROED immediately after feature extraction (RMS + pitch variance).
  - SensorFrame exposes EXTRACTED FEATURES ONLY — no raw bytes, no ndarray, no
    sample arrays on the public API.  Raw audio is never logged, written to disk,
    or transmitted.  This is the SensorSourcePort boundary.

Owner: Ng
"""
from __future__ import annotations

import asyncio
import dataclasses
import logging
import math
import threading
from typing import AsyncIterator, Sequence

import numpy as np

logger = logging.getLogger("familiar.sensors")

# ---------------------------------------------------------------------------
# Normalisation constants
# ---------------------------------------------------------------------------

# Full-scale sine wave in float32 range [-1, 1] has RMS ≈ 0.707.
# Dividing by this maps a clipping-level signal to 1.0.
_RMS_NORM: float = 0.707

# ZCR variance for conversational speech typically sits in [0.0, 0.01].
# Dividing by this scale maps high-variance speech to ~1.0.
_PITCH_VAR_SCALE: float = 0.01

# Number of sub-frames for ZCR-based pitch-variance estimation.
_N_PITCH_FRAMES: int = 10

# IMU normalisation: Halo IMU reports acceleration in g; typical dynamic range ≤ 4g.
_IMU_ACCEL_NORM: float = 4.0
# Gyroscope in °/s; typical dynamic range ≤ 500 °/s.
_IMU_ROT_NORM: float = 500.0


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class SensorInitError(Exception):
    """Raised by SensorStream.start() when audio device cannot be opened."""


# ---------------------------------------------------------------------------
# SensorFrame — Privacy gate I7 SensorSourcePort boundary
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class SensorFrame:
    """
    One sample of sensor data delivered at ~10Hz.

    Privacy gate I7: all public fields are extracted features only.
    No raw audio bytes, no ndarray, no sample arrays ever appear here.
    """
    audio_rms: float             # Root-mean-square of ≤1s audio window (0.0–1.0)
    audio_pitch_variance: float  # Pitch variance over window (0.0–1.0)
    imu_acceleration: float      # Scalar magnitude of accelerometer (0.0–1.0)
    imu_rotation: float          # Scalar magnitude of gyroscope (0.0–1.0)
    mic_ok: bool = True          # False if mic capture failed this frame
    imu_ok: bool = True          # False if IMU relay failed this frame


# ---------------------------------------------------------------------------
# Feature extraction (module-private — raw arrays never leave this boundary)
# ---------------------------------------------------------------------------

def _compute_rms(samples: np.ndarray) -> float:
    """Normalized RMS (0.0–1.0) from float32 audio samples."""
    if len(samples) == 0:
        return 0.0
    rms = float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))
    return min(1.0, rms / _RMS_NORM)


def _compute_pitch_variance(samples: np.ndarray) -> float:
    """
    Pitch-variance proxy (0.0–1.0) using zero-crossing rate over sub-frames.

    Splits the window into _N_PITCH_FRAMES equal frames, computes ZCR for each,
    then returns the scaled variance.  ZCR is a robust, low-latency pitch proxy
    that avoids FFT allocation on every tick.
    """
    if len(samples) < _N_PITCH_FRAMES * 2:
        return 0.0
    frame_size = len(samples) // _N_PITCH_FRAMES
    zcr_values: list[float] = []
    for i in range(_N_PITCH_FRAMES):
        frame = samples[i * frame_size:(i + 1) * frame_size].astype(np.float64)
        if len(frame) < 2:
            zcr_values.append(0.0)
            continue
        zcr = float(np.mean(np.abs(np.diff(np.sign(frame))) / 2.0))
        zcr_values.append(zcr)
    variance = float(np.var(zcr_values))
    return min(1.0, variance / _PITCH_VAR_SCALE)


# ---------------------------------------------------------------------------
# IMU relay (SDK gap — degrades gracefully)
# ---------------------------------------------------------------------------

class _IMURelay:
    """
    IMU relay from Halo device BLE characteristic.

    SDK gap (ARD §10): The IMU BLE characteristic UUID and relay API are
    unconfirmed against current Halo firmware.  Degrades gracefully to
    imu_ok=False if the characteristic is unavailable, allowing the pipeline
    to continue in mic-only mode.
    """

    def __init__(self) -> None:
        self._accel: float = 0.0
        self._rotation: float = 0.0
        self._ok: bool = False

    async def start(self) -> None:
        """
        Subscribe to Halo IMU BLE characteristic.

        SDK gap (ARD §10): characteristic UUID unconfirmed — stays imu_ok=False
        until confirmed on real hardware.  Does not raise; caller checks .ok.
        """
        logger.debug(
            "[IMURelay] IMU BLE characteristic unconfirmed (ARD §10 SDK gap) — "
            "operating in mic-only mode (imu_ok=False)"
        )
        # TODO(ARD §10): subscribe to confirmed IMU characteristic here.
        # Until validated, hold imu_ok=False so main loop degrades gracefully.
        self._ok = False

    async def stop(self) -> None:
        self._ok = False

    @property
    def acceleration(self) -> float:
        return self._accel

    @property
    def rotation(self) -> float:
        return self._rotation

    @property
    def ok(self) -> bool:
        return self._ok


# ---------------------------------------------------------------------------
# SensorStream — real hardware, async iterator
# ---------------------------------------------------------------------------

class SensorStream:
    """
    Async iterator yielding SensorFrame at ~10Hz.

    Opens a sounddevice InputStream for mic capture and subscribes to the
    Halo IMU BLE characteristic via _IMURelay (SDK gap: degrades gracefully).

    Privacy gate I7: the rolling audio buffer is zeroed immediately after each
    feature-extraction cycle.  Raw audio never crosses this class boundary.
    """

    def __init__(self, sample_rate: int = 16_000) -> None:
        self.sample_rate = sample_rate
        # Rolling buffer: exactly one second of float32 samples.
        # Privacy gate I7: buffer is zeroed after each extraction.
        self._buffer: np.ndarray = np.zeros(sample_rate, dtype=np.float32)
        self._buffer_pos: int = 0
        self._audio_lock = threading.Lock()
        self._mic_ok: bool = False
        self._running: bool = False
        self._stream: object | None = None
        self._imu = _IMURelay()

    async def start(self) -> None:
        """
        Open audio device and IMU relay.

        Raises:
            SensorInitError: if audio device cannot be opened.
        """
        if self._running:
            return
        try:
            import sounddevice as sd  # type: ignore[import]
        except ImportError as exc:
            raise SensorInitError(
                "sounddevice not installed — run: pip install sounddevice"
            ) from exc

        block_size = max(1, int(self.sample_rate / 10))  # 100ms blocks at 10Hz
        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                callback=self._audio_callback,
                blocksize=block_size,
            )
            self._stream.start()  # type: ignore[union-attr]
            self._mic_ok = True
        except Exception as exc:
            if self._stream is not None:
                try:
                    self._stream.close()  # type: ignore[union-attr]
                except Exception:
                    pass
            self._stream = None
            self._mic_ok = False
            raise SensorInitError(f"Failed to open audio device: {exc}") from exc

        await self._imu.start()
        self._running = True
        logger.info(
            "[SensorStream] started (mic ok, IMU %s)",
            "ok" if self._imu.ok else "degraded (ARD §10 SDK gap)",
        )

    async def stop(self) -> None:
        """Close audio device and IMU relay. Idempotent."""
        self._running = False
        self._mic_ok = False
        if self._stream is not None:
            try:
                self._stream.stop()   # type: ignore[union-attr]
                self._stream.close()  # type: ignore[union-attr]
            except Exception:
                pass
            self._stream = None
        await self._imu.stop()
        # Zero the buffer on stop — privacy gate I7.
        with self._audio_lock:
            self._buffer[:] = 0.0
            self._buffer_pos = 0
        logger.info("[SensorStream] stopped")

    def __aiter__(self) -> AsyncIterator[SensorFrame]:
        return self

    async def __anext__(self) -> SensorFrame:
        """
        Yield next SensorFrame.

        Rate-pacing removed (B2): the main loop is the sole pacer at 10Hz.
        SensorStream is capture-driven by the audio device callback cadence.

        Raises:
            StopAsyncIteration: when stream is stopped.
        """
        if not self._running:
            raise StopAsyncIteration
        return self._extract_frame()

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: object,
        status: object,
    ) -> None:
        """sounddevice callback: fill rolling buffer with incoming samples."""
        if status:
            logger.warning("[SensorStream] audio callback status: %s", status)
            self._mic_ok = False
            return
        self._mic_ok = True
        mono = indata[:, 0] if indata.ndim > 1 else indata.ravel()
        n = len(mono)
        buf_len = len(self._buffer)
        with self._audio_lock:
            if n >= buf_len:
                self._buffer[:] = mono[-buf_len:]
                self._buffer_pos = 0
            else:
                end = self._buffer_pos + n
                if end <= buf_len:
                    self._buffer[self._buffer_pos:end] = mono
                    self._buffer_pos = end % buf_len
                else:
                    first = buf_len - self._buffer_pos
                    self._buffer[self._buffer_pos:] = mono[:first]
                    self._buffer[: n - first] = mono[first:]
                    self._buffer_pos = n - first

    def _extract_frame(self) -> SensorFrame:
        """
        Extract SensorFrame from current buffer and IMU relay.

        Privacy gate I7: buffer is ZEROED immediately after snapshot.
        Raw samples never leave this method.
        """
        with self._audio_lock:
            # Snapshot — copy so we can release the lock before heavy computation.
            samples = self._buffer.copy()
            # Zero immediately — privacy gate I7.
            self._buffer[:] = 0.0
            self._buffer_pos = 0
            # M1: read _mic_ok under lock — written by the sounddevice callback
            # thread; holding the lock here is zero extra cost.
            mic_ok = self._mic_ok

        try:
            if mic_ok:
                audio_rms = _compute_rms(samples)
                audio_pitch_variance = _compute_pitch_variance(samples)
            else:
                audio_rms = 0.0
                audio_pitch_variance = 0.0
        finally:
            # M2: three-layer zeroing — privacy gate I7, even on exception.
            # Layer 1: in-buffer zero (self._buffer[:]=0.0 above, under lock).
            # Layer 2: snapshot zero — overwrites the numpy copy in-place so the
            #   raw samples are not merely unreferenced but actively cleared before
            #   the allocator can reuse the memory region.
            # Layer 3: reference release (del) — drops the last reference.
            samples[:] = 0.0
            del samples

        # M2: finiteness guard — substitute 0.0 for NaN/inf from corrupt audio.
        if not math.isfinite(audio_rms):
            audio_rms = 0.0
        if not math.isfinite(audio_pitch_variance):
            audio_pitch_variance = 0.0

        return SensorFrame(
            audio_rms=audio_rms,
            audio_pitch_variance=audio_pitch_variance,
            imu_acceleration=self._imu.acceleration,
            imu_rotation=self._imu.rotation,
            mic_ok=mic_ok,
            imu_ok=self._imu.ok,
        )


# ---------------------------------------------------------------------------
# FakeSensorStream — test injection (Juanita's contract)
# ---------------------------------------------------------------------------

class FakeSensorStream:
    """
    Inject synthetic SensorFrames for testing without real hardware.

    Yielded in order from the provided list.  When exhausted, raises
    StopAsyncIteration (or restarts from index 0 if loop=True).

    Usage (Juanita's tests):
        frames = [SensorFrame(0.8, 0.6, 0.0, 0.0, mic_ok=True, imu_ok=False)]
        stream = FakeSensorStream(frames)
        ...
        async for frame in stream: ...
    """

    def __init__(
        self,
        frames: Sequence[SensorFrame],
        *,
        loop: bool = False,
        delay: float = 0.0,
    ) -> None:
        self._frames = list(frames)
        self._loop = loop
        self._delay = delay
        self._idx: int = 0
        self._running: bool = False

    async def start(self) -> None:
        self._running = True
        self._idx = 0

    async def stop(self) -> None:
        self._running = False

    def __aiter__(self) -> AsyncIterator[SensorFrame]:
        return self

    async def __anext__(self) -> SensorFrame:
        if not self._running:
            raise StopAsyncIteration
        if self._idx >= len(self._frames):
            if self._loop:
                self._idx = 0
            else:
                raise StopAsyncIteration
        if self._delay > 0.0:
            await asyncio.sleep(self._delay)
        frame = self._frames[self._idx]
        self._idx += 1
        return frame
