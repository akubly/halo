"""
Entry point for the Synesthetic Familiar host app.

Week 1 mock-send harness: cycles through mood states so the creature bobs
on the Halo display.  No real sensors until Week 2.

Transport injection (Transport Protocol seam):
  --mock (or no --device)  →  MockTransport: logs packets, no hardware needed
  --device ADDR            →  BrilliantBleTransport: wraps brilliant-ble

Both transports share the same Transport Protocol so Juanita's tests can
inject MockTransport directly without patching globals.

Owner: Ng
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import math
import time
from typing import Callable, Protocol, runtime_checkable

from host.familiar_protocol import (
    Mood,
    FamiliarAck, FamiliarReset,
    SequenceCounter,
    dispatch_device_message,
    encode_familiar_update,
)

logger = logging.getLogger("familiar.host")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

UPDATE_HZ: float = 10.0                   # ARD §5.2 max cadence
UPDATE_INTERVAL: float = 1.0 / UPDATE_HZ


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
            # connection API may differ entirely.  Validate on real hardware before
            # relying on targeted device selection via --device.
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
# Mock bobbing sequence (Week 1 — no real sensors yet)
# ---------------------------------------------------------------------------

def _mock_packet(t: float) -> tuple[int, int, int]:
    """
    Return (mood, intensity, confidence) as wire-format integers at time t.

    8-second cycle drives visible state changes so the creature bobs at
    each mood's frequency (§5.5: 0.25Hz neutral, 0.15Hz calm, 0.75Hz stressed).

    Phase  0–2 s   NEUTRAL   slow 0.25Hz bob
    Phase  2–4 s   CALM      slower 0.15Hz bob
    Phase  4–6 s   STRESSED  fast 0.75Hz bob
    Phase  6–8 s   NEUTRAL   back to slow
    """
    phase = t % 8.0
    if phase < 2.0:
        intensity = int(50 + 10 * math.sin(2 * math.pi * 0.25 * t))
        return Mood.NEUTRAL, max(0, min(100, intensity)), 85
    elif phase < 4.0:
        intensity = int(30 + 5 * math.sin(2 * math.pi * 0.15 * t))
        return Mood.CALM, max(0, min(100, intensity)), 90
    elif phase < 6.0:
        intensity = int(80 + 10 * math.sin(2 * math.pi * 0.75 * t))
        return Mood.STRESSED, max(0, min(100, intensity)), 88
    else:
        intensity = int(50 + 10 * math.sin(2 * math.pi * 0.25 * t))
        return Mood.NEUTRAL, max(0, min(100, intensity)), 85


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------

_MOOD_NAME = {0: "NEUTRAL", 1: "CALM", 2: "STRESSED", 3: "ATTENTION"}


async def run(transport: Transport) -> None:
    """Connect to transport and loop forever sending mock FAMILIAR_UPDATE at 10Hz."""
    seq = SequenceCounter()  # starts at 0xFFFF so first next() → 0x0000

    def on_device_msg(data: bytes) -> None:
        msg = dispatch_device_message(data)
        if isinstance(msg, FamiliarAck):
            logger.info("← FAMILIAR_ACK  last_seq=%d", msg.last_received_seq)
        elif isinstance(msg, FamiliarReset):
            logger.info("← FAMILIAR_RESET  (device snapped to neutral on double-tap)")
        elif msg is None:
            logger.warning("← unknown opcode 0x%02x — ignored", data[0] if data else 0)

    transport.on_receive(on_device_msg)
    await transport.connect()

    logger.info("Sending mock FAMILIAR_UPDATE at %.0fHz — creature should bob", UPDATE_HZ)
    start = time.monotonic()

    try:
        while True:
            tick_start = time.monotonic()
            elapsed = tick_start - start

            mood, intensity, confidence = _mock_packet(elapsed)
            s = seq.next()
            packet = encode_familiar_update(mood, intensity, confidence, s)

            await transport.send(packet)
            logger.info(
                "→ FAMILIAR_UPDATE  mood=%-8s intensity=%3d  confidence=%3d  seq=%5d  [%s]",
                _MOOD_NAME.get(mood, "?"),
                intensity,
                confidence,
                s,
                packet.hex(" "),
            )

            tick_elapsed = time.monotonic() - tick_start
            await asyncio.sleep(max(0.0, UPDATE_INTERVAL - tick_elapsed))

    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Interrupted — disconnecting")
    finally:
        await transport.disconnect()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Synesthetic Familiar — Week 1 mock-send harness.  "
            "Sends cycling FAMILIAR_UPDATE packets so the creature bobs on device."
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
    args = parser.parse_args()

    transport: Transport
    if args.mock or not args.device:
        transport = MockTransport()
    else:
        transport = BrilliantBleTransport(args.device)

    asyncio.run(run(transport))


if __name__ == "__main__":
    main()
