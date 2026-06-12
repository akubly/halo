"""
Entry point for the Synesthetic Familiar host app.

Week 2: Real sensor→inference→encode→send loop at 10Hz.
Replaces Week-1 mock harness while preserving the Transport Protocol seam.

Transport injection (Transport Protocol seam):
  --mock (or no --device)  →  MockTransport: logs packets, no hardware needed
  --device ADDR            →  BrilliantBleTransport: wraps brilliant-ble

Both transports share the same Transport Protocol so Juanita's tests can
inject any conforming transport without patching globals.

Gate 2 helpers (MERGE-BLOCKING — must live here, not in inference or protocol):
  quantise_intensity(intensity: float) → int in {0, 25, 50, 75, 100}
  apply_intensity_jitter(quantised: int, rng=None) → int clamped 0–100

Owner: Ng
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import random
import time
from typing import AsyncIterator, Awaitable, Callable, Protocol, runtime_checkable

from host.familiar_protocol import (
    FamiliarAck,
    FamiliarReset,
    Mood,
    OPCODE_FAMILIAR_ACK,
    OPCODE_FAMILIAR_RESET,
    SequenceCounter,
    dispatch_device_message,
    encode_familiar_update,
)
from host.sensors import FakeSensorStream, SensorFrame, SensorInitError, SensorStream
from host.inference import (
    Baseline,
    CONFIDENCE_GATE,
    MoodResult,
    compute_mood,
    load_baseline,
    save_baseline,
    update_baseline,
)


logger = logging.getLogger("familiar.host")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

UPDATE_HZ: float = 10.0
UPDATE_INTERVAL: float = 1.0 / UPDATE_HZ

# Confidence-hold timeout I2 (ARD §5.4): after this many seconds of suppressed
# updates, force-send the last computed result to prevent "stuck creature".
CONFIDENCE_HOLD_TIMEOUT_S: float = 30.0

# Both-sensors-fail fallback (ARD §5.4): send explicit NEUTRAL after this many
# seconds with both mic_ok=False AND imu_ok=False.
BOTH_FAIL_TIMEOUT_S: float = 10.0

_MOOD_NAME = {0: "NEUTRAL", 1: "CALM", 2: "STRESSED", 3: "ATTENTION"}


# ---------------------------------------------------------------------------
# Transport seam (dependency-injected, testable)
# ---------------------------------------------------------------------------

@runtime_checkable
class Transport(Protocol):
    """Minimal BLE transport interface.  Real impl wraps brilliant-ble."""

    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def send(self, data: bytes) -> None: ...
    def on_receive(self, callback: Callable[[bytes], None]) -> None: ...


@runtime_checkable
class SensorStreamPort(Protocol):
    """Duck-typed async sensor stream seam — SensorStream and FakeSensorStream both conform."""

    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    def __aiter__(self) -> AsyncIterator[SensorFrame]: ...
    async def __anext__(self) -> SensorFrame: ...


class MockTransport:
    """
    No-hardware fallback transport.

    Logs every TX to stdout.  Never emits receive events (no real device).
    Use with --mock flag, or omit --device, to run without Halo hardware.
    """

    def __init__(self) -> None:
        self._recv_cb: Callable[[bytes], None] | None = None

    async def connect(self) -> None:
        logger.info("[MockTransport] connected (no hardware — mock mode)")

    async def disconnect(self) -> None:
        logger.info("[MockTransport] disconnected")

    async def send(self, data: bytes) -> None:
        logger.info("[MockTransport] TX %d bytes: %s", len(data), data.hex(" "))

    def on_receive(self, callback: Callable[[bytes], None]) -> None:
        self._recv_cb = callback


class BrilliantBleTransport:
    """
    Real transport wrapping brilliant-ble (frame_sdk).

    SDK gap (ARD §10): The exact import path and connect/send/receive API
    for the current Halo SDK has not been confirmed against live firmware.
    This wrapper targets the frame_sdk pattern from CitizenOneX examples
    (decisions.md 2026-06-02).  Adjust method names if the SDK differs.
    """

    def __init__(self, device_address: str) -> None:
        self._address = device_address
        self._frame: object | None = None
        self._recv_cb: Callable[[bytes], None] | None = None

    async def connect(self) -> None:
        try:
            import frame_sdk  # type: ignore[import]  # SDK gap: confirm module name
            # TODO(ARD §10): --device ADDR binding is UNVERIFIED against the live Halo
            # SDK.  frame_sdk.Frame() may not accept an address argument, or the
            # connection API may differ entirely.  Validate on real hardware.
            if self._address:
                logger.warning(
                    "[BrilliantBLE] --device ADDR binding is UNVERIFIED (ARD §10 SDK gap). "
                    "frame_sdk.Frame() may not support address targeting; connecting "
                    "without address filter.  Validate on real hardware."
                )
            self._frame = frame_sdk.Frame()
            await self._frame.connect()  # type: ignore[union-attr]
            await self._frame.bluetooth.set_data_response_handler(self._on_data)  # type: ignore[union-attr]
            logger.info("[BrilliantBLE] connected (address filter UNVERIFIED — ARD §10)")
        except ImportError as exc:
            raise RuntimeError(
                "brilliant-ble / frame_sdk not installed or import path differs.  "
                "Run with --mock, or install requirements.txt and confirm SDK module "
                "name against current Halo firmware.  (ARD §10 SDK gap)"
            ) from exc
        except (AttributeError, TypeError) as exc:
            raise RuntimeError(
                "SDK API mismatch (ARD §10): frame_sdk API differs from expected shape.  "
                "Confirm connect/send/receive method names against current Halo firmware.  "
                "Run with --mock to bypass hardware."
            ) from exc

    async def disconnect(self) -> None:
        if self._frame is not None:
            await self._frame.disconnect()  # type: ignore[union-attr]
            logger.info("[BrilliantBLE] disconnected")

    async def send(self, data: bytes) -> None:
        if self._frame is None:
            logger.warning(
                "[BrilliantBLE] send() called before connect() — dropping %d bytes", len(data)
            )
            return
        await self._frame.bluetooth.send_data(data)  # type: ignore[union-attr]

    def on_receive(self, callback: Callable[[bytes], None]) -> None:
        self._recv_cb = callback

    async def _on_data(self, data: bytes) -> None:
        if self._recv_cb is not None:
            self._recv_cb(data)


# ---------------------------------------------------------------------------
# Gate 2 helpers: quantise + jitter (MUST live in main.py per contract §3)
# ---------------------------------------------------------------------------

def quantise_intensity(intensity: float) -> int:
    """
    Convert continuous 0.0–1.0 intensity to {0, 25, 50, 75, 100}.

    Buckets (ARD §5.6 anti-robotic + privacy, contract §3 Gate 2):
        0.000 – 0.125  →   0
        0.125 – 0.375  →  25
        0.375 – 0.625  →  50
        0.625 – 0.875  →  75
        0.875 – 1.000  → 100
    """
    if intensity < 0.125:
        return 0
    elif intensity < 0.375:
        return 25
    elif intensity < 0.625:
        return 50
    elif intensity < 0.875:
        return 75
    else:
        return 100


def apply_intensity_jitter(
    quantised: int,
    rng: random.Random | None = None,
) -> int:
    """
    Add ±5 random jitter to quantised intensity; clamp result to 0–100.

    Uses injected RNG for test determinism; falls back to module-level random.
    """
    r = rng if rng is not None else random
    jitter = r.randint(-5, 5)
    return max(0, min(100, quantised + jitter))


# ---------------------------------------------------------------------------
# Device message handler
# ---------------------------------------------------------------------------

def _make_device_msg_handler() -> Callable[[bytes], None]:
    def on_device_msg(data: bytes) -> None:
        msg = dispatch_device_message(data)
        if isinstance(msg, FamiliarAck):
            logger.info("← FAMILIAR_ACK  last_seq=%d", msg.last_received_seq)
        elif isinstance(msg, FamiliarReset):
            logger.info("← FAMILIAR_RESET  (device snapped to neutral on double-tap)")
        elif msg is None:
            opcode = data[0] if data else 0
            if opcode in (OPCODE_FAMILIAR_ACK, OPCODE_FAMILIAR_RESET):
                name = (
                    "FAMILIAR_ACK" if opcode == OPCODE_FAMILIAR_ACK else "FAMILIAR_RESET"
                )
                logger.warning(
                    "← malformed %s packet (len=%d) — ignored", name, len(data)
                )
            else:
                logger.warning("← unknown opcode 0x%02x — ignored", opcode)

    return on_device_msg


# ---------------------------------------------------------------------------
# Send helpers
# ---------------------------------------------------------------------------

async def _send_update(
    transport: Transport,
    seq: SequenceCounter,
    result: MoodResult,
) -> None:
    """Quantise → jitter → encode → send a mood update."""
    q_intensity = quantise_intensity(result.intensity)
    j_intensity = apply_intensity_jitter(q_intensity)
    conf_int = max(0, min(100, int(result.confidence * 100)))
    packet = encode_familiar_update(
        mood=result.mood_int,
        intensity=j_intensity,
        confidence=conf_int,
        seq=seq.next(),
    )
    await transport.send(packet)
    logger.info(
        "→ FAMILIAR_UPDATE  mood=%-8s intensity=%3d  confidence=%3d  seq=%5d",
        _MOOD_NAME.get(result.mood_int, "?"),
        j_intensity,
        conf_int,
        seq.current,
    )


async def _send_neutral_fallback(
    transport: Transport,
    seq: SequenceCounter,
    rng: random.Random | None = None,
) -> None:
    """Both-sensors-fail fallback: send explicit NEUTRAL (ARD §5.4).

    Routes intensity through quantise_intensity → apply_intensity_jitter so the
    Gate 2 pipeline is always exercised (no special-case wire path).
    RNG is injectable for test determinism.
    """
    q_intensity = quantise_intensity(0.5)       # 0.5 → bucket 50
    j_intensity = apply_intensity_jitter(q_intensity, rng=rng)
    packet = encode_familiar_update(
        mood=Mood.NEUTRAL,
        intensity=j_intensity,
        confidence=50,
        seq=seq.next(),
    )
    await transport.send(packet)
    logger.info(
        "→ FAMILIAR_UPDATE  mood=NEUTRAL (both-sensors-fail fallback)  seq=%5d",
        seq.current,
    )


# ---------------------------------------------------------------------------
# Main loop (Week 2 — replaces _mock_packet harness)
# ---------------------------------------------------------------------------

async def run(
    transport: Transport,
    sensor_stream: SensorStreamPort,
    *,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> None:
    """
    Real sensor→inference→encode→send loop at 10Hz.

    Args:
        transport:     Any Transport-conforming instance (MockTransport,
                       BrilliantBleTransport, or Juanita's FakeTransport).
        sensor_stream: Any SensorStreamPort-conforming instance (SensorStream,
                       FakeSensorStream, or test injection).
        clock:         Monotonic clock callable; injectable for test determinism.
                       Drives timeout logic only — pacing uses time.monotonic().
                       Defaults to time.monotonic.
        sleep:         Async sleep callable; injectable for test determinism.
                       Drives the unconditional 10Hz pacer in the loop finally.
                       Defaults to asyncio.sleep.
    """
    seq = SequenceCounter()

    # Confidence-hold state (I2)
    last_send_time: float = clock()
    last_computed_result = None

    # Both-sensors-fail fallback state
    both_fail_start: float | None = None

    # Baseline — load once at startup; updated per successfully sent frame.
    baseline = load_baseline()

    transport.on_receive(_make_device_msg_handler())
    await transport.connect()
    # I3: transport.disconnect() is guaranteed by the outer finally even if
    # sensor_stream.start() raises (SensorInitError, sounddevice missing, etc.).
    try:
        await sensor_stream.start()
        logger.info("Real sensor loop started at %.0fHz", UPDATE_HZ)
        try:
            async for frame in sensor_stream:
                tick_start = clock()
                _pace_start = time.monotonic()
                try:
                    # Both-sensors-fail fallback (10s → explicit NEUTRAL)
                    if not frame.mic_ok and not frame.imu_ok:
                        if both_fail_start is None:
                            both_fail_start = tick_start
                        elif (tick_start - both_fail_start) > BOTH_FAIL_TIMEOUT_S:
                            await _send_neutral_fallback(transport, seq)
                            last_send_time = tick_start
                            both_fail_start = tick_start  # Re-arm
                        continue
                    both_fail_start = None  # Reset on any good sensor frame

                    # Inference
                    result = compute_mood(
                        audio_rms=frame.audio_rms,
                        audio_pitch_variance=frame.audio_pitch_variance,
                        imu_acceleration=frame.imu_acceleration,
                        imu_rotation=frame.imu_rotation,
                        mic_ok=frame.mic_ok,
                        imu_ok=frame.imu_ok,
                        baseline=baseline,
                    )
                    last_computed_result = result

                    # Confidence gating + hold timeout I2
                    if result.gated:
                        if (tick_start - last_send_time) > CONFIDENCE_HOLD_TIMEOUT_S:
                            # ~30s suppressed → force-send to prevent stuck creature.
                            await _send_update(transport, seq, result)
                            last_send_time = tick_start
                        continue

                    # Normal send path
                    await _send_update(transport, seq, result)
                    last_send_time = tick_start

                    # Baseline update — only on successfully sent frames.
                    # B1: use raw tension (not mood-transformed intensity).
                    baseline = update_baseline(baseline, result.tension)

                finally:
                    # B2: sole rate-limiter — unconditional pacer covers every path
                    # (normal send, confidence-gated continue, both-sensors-fail continue).
                    # Uses time.monotonic() so the injectable clock drives timeout logic
                    # only; FakeClock tests see no extra clock() calls per frame.
                    # sleep is injectable (default asyncio.sleep) for test determinism.
                    _pace_elapsed = time.monotonic() - _pace_start
                    await sleep(max(0.0, UPDATE_INTERVAL - _pace_elapsed))

        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("Interrupted — stopping sensors and disconnecting")
    finally:
        await sensor_stream.stop()
        if baseline is not None:
            save_baseline(baseline)
        await transport.disconnect()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Synesthetic Familiar — Week 2 real sensor loop.  "
            "Sends sensor-derived FAMILIAR_UPDATE packets so the creature reacts."
        )
    )
    parser.add_argument(
        "--device",
        metavar="ADDR",
        help="Halo BLE address (e.g. AA:BB:CC:DD:EE:FF).  Omit to use MockTransport.",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Force MockTransport (no hardware) even if --device is given.",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16_000,
        metavar="HZ",
        help="Mic sample rate in Hz (default: 16000).",
    )
    args = parser.parse_args()

    transport: Transport
    if args.mock or not args.device:
        transport = MockTransport()
    else:
        transport = BrilliantBleTransport(args.device)

    sensor_stream = SensorStream(sample_rate=args.sample_rate)

    asyncio.run(run(transport, sensor_stream))


if __name__ == "__main__":
    main()
