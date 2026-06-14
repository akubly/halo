"""
Entry point for the Synesthetic Familiar host app.

Week 2: Real sensor→inference→encode→send loop at 10Hz.
Replaces Week-1 mock harness while preserving the Transport Protocol seam.

Week 3: First-launch onboarding UX, calibration-state surfacing, fallback
visibility, ATTENTION display, and mock-cycle harness for ATTENTION testing.

Transport injection (Transport Protocol seam):
  --mock (or no --device)  →  MockTransport: logs packets, no hardware needed
  --device ADDR            →  BrilliantBleTransport: wraps brilliant-ble

Both transports share the same Transport Protocol so Juanita's tests can
inject any conforming transport without patching globals.

Gate 2 helpers (MERGE-BLOCKING — must live here, not in inference or protocol):
  quantise_intensity(intensity: float) → int in {0, 25, 50, 75, 100}
  apply_intensity_jitter(quantised: int, rng=None) → int clamped 0–100

Week 3 onboarding helpers (testable — import directly from this module):
  get_calibration_status(baseline) → str
  print_onboarding(baseline, *, out=None) → None
  run_mock_cycle(transport, *, cycles, sleep) → Coroutine

Owner: Ng / Y.T. (Week 3 onboarding UX)
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import random
import sys
import time
from typing import AsyncIterator, Awaitable, Callable, Protocol, TextIO, runtime_checkable

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
    ACTIVATION_THRESHOLD,
    ActivationInfo,
    Baseline,
    MoodResult,
    compute_mood,
    get_activation_info,
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

# Sentinel — when passed as `baseline` kwarg to run(), means "load from disk".
# Tests inject baseline=None directly to use population defaults without touching
# ~/.vesper/baseline.json.
_LOAD_BASELINE_FROM_DISK: object = object()

# ---------------------------------------------------------------------------
# Week 3 onboarding helpers (public, testable)
# ---------------------------------------------------------------------------

def get_calibration_status(baseline: Baseline | None) -> str:
    """
    Return human-readable calibration state for onboarding and status display.

    "calibrating (n / 50 samples)" = population defaults active.
    "personalized"                  = personal mean+1.5σ threshold active (ARD §5.4).

    Driven by Librarian's get_activation_info() — pure function, no I/O.
    Testable: inject a Baseline dataclass to drive any state.
    """
    info = get_activation_info(baseline)
    if info.state == "personalized" and baseline is not None:
        return (
            f"personalized (n={info.sample_count} samples, "
            f"mean={baseline.mean:.3f}, stddev={baseline.stddev:.3f})"
        )
    return (
        f"calibrating ({info.sample_count} / {info.samples_needed} samples — "
        "population defaults active)"
    )


def print_onboarding(baseline: Baseline | None, *, out: TextIO | None = None) -> None:
    """
    Print first-launch onboarding or session-start status to `out` (default: stdout).

    First launch (baseline=None): explains the 3-day baseline ramp-up per ARD §5.4.
    Subsequent launches: shows current calibration state concisely.

    Testable: inject out=io.StringIO() to capture output without touching stdout.
    No hardware access — purely prints based on baseline state.
    """
    w = out if out is not None else sys.stdout
    status = get_calibration_status(baseline)
    if baseline is None:
        print("", file=w)
        print("╔══════════════════════════════════════════╗", file=w)
        print("║  VESPER  —  First Launch                 ║", file=w)
        print("╚══════════════════════════════════════════╝", file=w)
        print("", file=w)
        print("  Your familiar is waking up for the first time.", file=w)
        print("  Days 1–3: learning on population baselines.", file=w)
        print("  After day 3: it adapts to your personal rhythm.", file=w)
        print("", file=w)
        print(f"  Calibration: {status}", file=w)
        print("", file=w)
    else:
        print(f"\n[VESPER] Familiar online — {status}\n", file=w)


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

def _make_device_msg_handler(reset_flag: list[bool] | None = None) -> Callable[[bytes], None]:
    def on_device_msg(data: bytes) -> None:
        msg = dispatch_device_message(data)
        if isinstance(msg, FamiliarAck):
            logger.info("← FAMILIAR_ACK  last_seq=%d", msg.last_received_seq)
        elif isinstance(msg, FamiliarReset):
            logger.info("← FAMILIAR_RESET  (device snapped to neutral on double-tap)")
            print("[VESPER] Familiar reset — 'I'm fine' gesture acknowledged")
            if reset_flag is not None:
                reset_flag[0] = True  # Signal run loop to send NEUTRAL + seq.reset()
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
    # Surface ATTENTION prominently — it's a transient overlay, not a steady state.
    if result.mood_int == Mood.ATTENTION:
        print("⚡ [VESPER] ATTENTION — familiar is reacting to a notable moment")


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


async def _send_neutral_reset(
    transport: Transport,
    seq: SequenceCounter,
) -> None:
    """FAMILIAR_RESET reaction: send NEUTRAL to resync device state (JUANITA-T2-5 / ARD §5.2)."""
    q_intensity = quantise_intensity(0.5)
    j_intensity = apply_intensity_jitter(q_intensity)
    packet = encode_familiar_update(
        mood=Mood.NEUTRAL,
        intensity=j_intensity,
        confidence=50,
        seq=seq.next(),
    )
    await transport.send(packet)
    logger.info(
        "→ FAMILIAR_UPDATE  mood=NEUTRAL (FAMILIAR_RESET reaction)  seq=%5d",
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
    baseline: Baseline | None | object = _LOAD_BASELINE_FROM_DISK,
) -> None:
    """
    Real sensor→inference→encode→send loop at 10Hz.

    Args:
        transport:     Any Transport-conforming instance (MockTransport,
                       BrilliantBleTransport, or Juanita's FakeTransport).
        sensor_stream: Any SensorStreamPort-conforming instance (SensorStream,
                       FakeSensorStream, or test injection).
        clock:         Monotonic clock callable; injectable for test determinism.
                       clock is used ONLY for timeout arithmetic (confidence-hold 30s,
                       both-fail 10s) and must NOT be used for pacing — injectable
                       clocks (e.g. FakeClock) advance on every call, so using clock
                       for elapsed-time pacing would shift timeout thresholds by one
                       tick per frame; pacing uses time.monotonic().
                       Defaults to time.monotonic.
        sleep:         Async sleep callable; injectable for test determinism.
                       Drives the unconditional 10Hz pacer in the loop finally.
                       Defaults to asyncio.sleep.
        baseline:      Pre-loaded Baseline (or None for population defaults).
                       Default sentinel _LOAD_BASELINE_FROM_DISK loads from
                       ~/.vesper/baseline.json at startup (production path).
                       Tests pass baseline=None to bypass the real file.
    """
    seq = SequenceCounter()

    # Confidence-hold state (I2)
    last_send_time: float = clock()

    # Both-sensors-fail fallback state
    both_fail_start: float | None = None

    # FAMILIAR_RESET flag — set by the receive callback, consumed each loop frame.
    # A plain list[bool] is used so the closure in _make_device_msg_handler can
    # mutate it without a nonlocal declaration (all asyncio, single-threaded).
    _reset_flag: list[bool] = [False]

    # Baseline — injectable seam (pass baseline=None for population defaults, e.g. in tests).
    # _LOAD_BASELINE_FROM_DISK sentinel means "load from ~/.vesper/baseline.json" (production).
    if baseline is _LOAD_BASELINE_FROM_DISK:
        baseline = load_baseline()

    # Week 3 — first-launch onboarding UX (print to stdout; CLI playground).
    print_onboarding(baseline)

    transport.on_receive(_make_device_msg_handler(_reset_flag))
    await transport.connect()
    # I3: transport.disconnect() is guaranteed by the outer finally even if
    # sensor_stream.start() raises (SensorInitError, sounddevice missing, etc.).
    try:
        await sensor_stream.start()
        logger.info("Real sensor loop started at %.0fHz", UPDATE_HZ)
        try:
            async for frame in sensor_stream:
                tick_start = clock()
                pace_start = time.monotonic()
                try:
                    # FAMILIAR_RESET reaction (JUANITA-T2-5 / ARD §5.2 reconnect protocol):
                    # Device double-tap already snapped device to NEUTRAL; host must agree.
                    # seq.reset() re-syncs the sequence counter so the first post-reset
                    # packet has seq=0x0000 (device resets last_accepted_seq to 0xFFFF).
                    if _reset_flag[0]:
                        _reset_flag[0] = False
                        seq.reset()
                        await _send_neutral_reset(transport, seq)
                        last_send_time = tick_start
                        both_fail_start = None
                        continue  # finally (sleep pacer) still executes

                    # Both-sensors-fail fallback (10s → explicit NEUTRAL)
                    if not frame.mic_ok and not frame.imu_ok:
                        if both_fail_start is None:
                            both_fail_start = tick_start
                        elif (tick_start - both_fail_start) > BOTH_FAIL_TIMEOUT_S:
                            await _send_neutral_fallback(transport, seq)
                            print(
                                f"[VESPER] Sensor fallback active — both mic and IMU "
                                f"unavailable for >{BOTH_FAIL_TIMEOUT_S:.0f}s; "
                                f"familiar holding NEUTRAL"
                            )
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

                    # Confidence gating + hold timeout I2
                    if result.gated:
                        if (tick_start - last_send_time) > CONFIDENCE_HOLD_TIMEOUT_S:
                            # ~30s suppressed → force-send to prevent stuck creature.
                            await _send_update(transport, seq, result)
                            print(
                                f"[VESPER] Confidence hold released — "
                                f"{CONFIDENCE_HOLD_TIMEOUT_S:.0f}s of suppressed updates; "
                                f"familiar unstuck as "
                                f"{_MOOD_NAME.get(result.mood_int, '?')} "
                                f"(confidence={result.confidence:.2f})"
                            )
                            last_send_time = tick_start
                        # Intentionally skip baseline update — we don't learn from
                        # low-confidence data.
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
                    pace_elapsed = time.monotonic() - pace_start
                    await sleep(max(0.0, UPDATE_INTERVAL - pace_elapsed))

        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("Interrupted — stopping sensors and disconnecting")
    finally:
        await sensor_stream.stop()
        if baseline is not None:
            save_baseline(baseline)
        await transport.disconnect()


# ---------------------------------------------------------------------------
# Mock-cycle harness (Week 3 — ATTENTION path testing)
# ---------------------------------------------------------------------------

async def run_mock_cycle(
    transport: Transport,
    *,
    cycles: int = 3,
    delay_s: float = 1.0,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> None:
    """
    Mock harness: cycle through all four mood states including ATTENTION.

    Sends NEUTRAL → CALM → STRESSED → ATTENTION in sequence, repeating `cycles`
    times.  Use with --mock-cycle to exercise the ATTENTION display path and
    the full host-side pipeline without real sensors or BLE hardware.

    Device-side peak detection is Ng's (Lua, frame.imu.raw threshold).
    This harness provides the host-driven trigger needed for testing.

    Testable: inject sleep=noop_sleep to run instantly; inject a FakeTransport
    to capture packets.  Juanita: import and drive directly from acceptance tests:

        from host.main import run_mock_cycle
        asyncio.run(run_mock_cycle(FakeTransport(), cycles=1, sleep=noop_sleep))
    """
    seq = SequenceCounter()
    _cycle_moods: list[MoodResult] = [
        MoodResult(mood="neutral",   mood_int=Mood.NEUTRAL,   intensity=0.5, confidence=0.9, gated=False, tension=0.5),
        MoodResult(mood="calm",      mood_int=Mood.CALM,      intensity=0.8, confidence=0.9, gated=False, tension=0.2),
        MoodResult(mood="stressed",  mood_int=Mood.STRESSED,  intensity=0.9, confidence=0.9, gated=False, tension=0.8),
        MoodResult(mood="attention", mood_int=Mood.ATTENTION, intensity=1.0, confidence=0.9, gated=False, tension=1.0),
    ]
    transport.on_receive(_make_device_msg_handler())
    await transport.connect()
    try:
        for cycle_idx in range(cycles):
            logger.info("[MockCycle] cycle %d/%d", cycle_idx + 1, cycles)
            for result in _cycle_moods:
                await _send_update(transport, seq, result)
                await sleep(delay_s)
    finally:
        await transport.disconnect()




def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Synesthetic Familiar — host app.  "
            "Week 2: real sensor loop.  Week 3: + onboarding UX, --mock-cycle harness."
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
    parser.add_argument(
        "--mock-cycle",
        action="store_true",
        help=(
            "Run mock-cycle harness instead of real sensors: cycles through "
            "NEUTRAL → CALM → STRESSED → ATTENTION to exercise the ATTENTION "
            "display path.  Forces MockTransport.  Use to test without hardware."
        ),
    )
    parser.add_argument(
        "--mock-cycle-count",
        type=int,
        default=3,
        metavar="N",
        help="Number of complete mood cycles in --mock-cycle mode (default: 3).",
    )
    args = parser.parse_args()

    transport: Transport
    if args.mock or args.mock_cycle or not args.device:
        transport = MockTransport()
    else:
        transport = BrilliantBleTransport(args.device)

    if args.mock_cycle:
        asyncio.run(run_mock_cycle(transport, cycles=args.mock_cycle_count))
    else:
        sensor_stream = SensorStream(sample_rate=args.sample_rate)
        asyncio.run(run(transport, sensor_stream))


if __name__ == "__main__":
    main()
