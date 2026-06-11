"""
Sensor capture for the Synesthetic Familiar host app.

Responsibilities:
- Mic audio capture from host via sounddevice (16kHz mono)
- IMU relay from Halo device via BLE SDK

Delivers a stream of SensorFrame objects consumed by inference.py.
"""
# TODO: implement SensorStream, AudioCapture, IMURelay

from __future__ import annotations

import dataclasses
from typing import AsyncIterator


@dataclasses.dataclass
class SensorFrame:
    """One sample of sensor data delivered at ~10Hz."""
    audio_rms: float           # Root-mean-square of recent audio window
    audio_pitch_variance: float  # Variance of pitch estimate over window
    imu_acceleration: float    # Scalar magnitude of IMU accelerometer
    imu_rotation: float        # Scalar magnitude of IMU gyroscope


class SensorStream:
    """Async iterator yielding SensorFrame at ~10Hz."""

    def __init__(self, sample_rate: int = 16_000) -> None:
        # TODO: initialise sounddevice input stream and BLE IMU relay
        self.sample_rate = sample_rate

    async def start(self) -> None:
        """Open audio device and IMU relay."""
        # TODO: open sounddevice InputStream; subscribe to BLE IMU characteristic
        raise NotImplementedError

    async def stop(self) -> None:
        """Close audio device and IMU relay."""
        # TODO: close streams cleanly
        raise NotImplementedError

    def __aiter__(self) -> AsyncIterator[SensorFrame]:
        return self

    async def __anext__(self) -> SensorFrame:
        # TODO: yield next SensorFrame; raise StopAsyncIteration on stop
        raise NotImplementedError
