"""
BLE wire-format encoding/decoding for the Synesthetic Familiar protocol.

This module is the single source of wire truth.  Juanita's tests and
host/main.py both import from here — never duplicate the format constants.

Message types (ARD §5.2, locked 2026-06-08):
  FAMILIAR_UPDATE  (Host → Device, opcode 0x80)  — 6 bytes
  FAMILIAR_ACK     (Device → Host, opcode 0x02)  — 3 bytes
  FAMILIAR_RESET   (Device → Host, opcode 0x01)  — 1 byte

All multi-byte fields are little-endian (LE).  BLE ATT is LE; ARM
Cortex-M55 is LE; Python struct '<' and Lua string.pack('<I2', ...) are
both native.  No byte-swapping anywhere in the pipeline.

Owner: Ng
"""
from __future__ import annotations

import dataclasses
import struct
from enum import IntEnum
from typing import Union

# ---------------------------------------------------------------------------
# Mood enum (ARD §5.2; wire byte value = integer value)
# ---------------------------------------------------------------------------

class Mood(IntEnum):
    NEUTRAL   = 0
    CALM      = 1
    STRESSED  = 2
    ATTENTION = 3


# ---------------------------------------------------------------------------
# Opcode constants (ARD §5.2, normative)
# ---------------------------------------------------------------------------
OPCODE_FAMILIAR_UPDATE: int = 0x80   # Host → Device
OPCODE_FAMILIAR_ACK:    int = 0x02   # Device → Host
OPCODE_FAMILIAR_RESET:  int = 0x01   # Device → Host

# Backward-compatible int aliases (existing callers unaffected; IntEnum IS int)
MOOD_NEUTRAL:   int = Mood.NEUTRAL
MOOD_CALM:      int = Mood.CALM
MOOD_STRESSED:  int = Mood.STRESSED
MOOD_ATTENTION: int = Mood.ATTENTION


# ---------------------------------------------------------------------------
# Decoded message dataclasses
# ---------------------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class FamiliarUpdate:
    """Decoded FAMILIAR_UPDATE payload (Host→Device)."""
    mood:       int   # 0–3
    intensity:  int   # 0–100
    confidence: int   # 0–100
    seq:        int   # uint16, 0–65535


@dataclasses.dataclass(frozen=True)
class FamiliarAck:
    """Decoded FAMILIAR_ACK payload (Device→Host)."""
    last_received_seq: int   # uint16


@dataclasses.dataclass(frozen=True)
class FamiliarReset:
    """Decoded FAMILIAR_RESET (Device→Host).

    No payload; the occurrence is the signal — device snapped to NEUTRAL
    on-device after double-tap.  Host should treat its local state as reset.
    """


# ---------------------------------------------------------------------------
# Sequence counter
# ---------------------------------------------------------------------------

class SequenceCounter:
    """
    Monotonically incrementing uint16 sequence counter for FAMILIAR_UPDATE.

    Wraps 0xFFFF → 0x0000.

    Reconnect protocol (ARD §5.2): call reset() when BLE reconnects.
    The counter re-starts at 0x0000; the device has reset last_accepted_seq
    to 0xFFFF on its side so the first received seq=0x0000 yields delta=1
    (accepted).
    """

    def __init__(self) -> None:
        # Internal state sits at 0xFFFF so the first next() call returns 0x0000.
        self._seq: int = 0xFFFF

    @property
    def current(self) -> int:
        return self._seq

    def next(self) -> int:
        """Advance and return the new sequence number."""
        self._seq = (self._seq + 1) & 0xFFFF
        return self._seq

    def reset(self) -> None:
        """Reset counter on reconnect — next() will return 0x0000."""
        self._seq = 0xFFFF


# ---------------------------------------------------------------------------
# Sequence dedup (ARD §5.2, signed-16 delta window)
# ---------------------------------------------------------------------------

def seq_is_newer(received: int, last_accepted: int) -> bool:
    """
    Return True iff *received* is strictly newer than *last_accepted*.

    Uses the ARD §5.2 wraparound-safe signed-16-bit delta window:

      delta = (received - last_accepted) mod 65536   (interpreted as signed int16)

      delta  1 .. 32767      →  True   (accept; includes 0xFFFF→0x0000 wraparound)
      delta  0               →  False  (duplicate)
      delta  32768 .. 65535  →  False  (stale / out-of-order; signed-negative half)

    This function is the Python mirror of the Lua is_newer_seq() in device/main.lua.
    Both must implement identical logic against the same spec.
    """
    delta = (received - last_accepted) & 0xFFFF
    return 1 <= delta <= 32767


# ---------------------------------------------------------------------------
# Encode (Host → Device)
# ---------------------------------------------------------------------------

def encode_familiar_update(
    mood:       int,
    intensity:  int,
    confidence: int,
    seq:        int,
) -> bytes:
    """
    Encode a FAMILIAR_UPDATE message (6 bytes, ARD §5.2).

    Wire layout:
      byte 0     opcode       0x80
      byte 1     mood_enum    0–3
      byte 2     intensity    0–100
      byte 3     confidence   0–100
      bytes 4–5  seq          uint16 LE

    Raises ValueError on out-of-range inputs.
    """
    if not 0 <= mood <= 3:
        raise ValueError(f"mood must be 0–3, got {mood}")
    if not 0 <= intensity <= 100:
        raise ValueError(f"intensity must be 0–100, got {intensity}")
    if not 0 <= confidence <= 100:
        raise ValueError(f"confidence must be 0–100, got {confidence}")
    if not 0 <= seq <= 0xFFFF:
        raise ValueError(f"seq must be 0–65535, got {seq}")
    return struct.pack("<BBBBH", OPCODE_FAMILIAR_UPDATE, mood, intensity, confidence, seq)


# ---------------------------------------------------------------------------
# Decode (Device → Host)
# ---------------------------------------------------------------------------

def decode_familiar_update(data: bytes) -> FamiliarUpdate:
    """
    Decode a FAMILIAR_UPDATE byte string (6 bytes) back into a dataclass.

    Useful for test symmetry: encode → decode round-trip must be lossless.
    """
    if len(data) != 6:
        raise ValueError(f"FAMILIAR_UPDATE expects 6 bytes, got {len(data)}")
    opcode, mood, intensity, confidence, seq = struct.unpack("<BBBBH", data)
    if opcode != OPCODE_FAMILIAR_UPDATE:
        raise ValueError(f"expected opcode 0x80, got 0x{opcode:02x}")
    return FamiliarUpdate(mood=mood, intensity=intensity, confidence=confidence, seq=seq)


def decode_familiar_ack(data: bytes) -> tuple[int, int]:
    """
    Decode a FAMILIAR_ACK message (3 bytes, ARD §5.2).

    Returns ``(opcode, last_received_seq)`` where opcode == 0x02.

    Wire layout:
      byte 0     opcode              0x02
      bytes 1–2  last_received_seq   uint16 LE
    """
    if len(data) != 3:
        raise ValueError(f"FAMILIAR_ACK expects 3 bytes, got {len(data)}")
    opcode, last_seq = struct.unpack("<BH", data)
    if opcode != OPCODE_FAMILIAR_ACK:
        raise ValueError(f"expected opcode 0x02, got 0x{opcode:02x}")
    return opcode, last_seq


def decode_familiar_reset(data: bytes) -> int:
    """
    Decode a FAMILIAR_RESET message (1 byte, ARD §5.2).

    Returns the opcode (0x01).  The occurrence is the signal; no payload.
    """
    if len(data) != 1:
        raise ValueError(f"FAMILIAR_RESET expects 1 byte, got {len(data)}")
    opcode = data[0]
    if opcode != OPCODE_FAMILIAR_RESET:
        raise ValueError(f"expected opcode 0x01, got 0x{opcode:02x}")
    return opcode


def dispatch_device_message(data: bytes) -> Union[FamiliarAck, FamiliarReset, None]:
    """
    Dispatch an incoming Device→Host message by opcode.

    Returns the decoded dataclass, or None if the opcode is unrecognised or
    the packet is malformed.  Never raises — malformed packets are logged and
    dropped (log-and-drop is caller's responsibility via the returned None).
    """
    if not data:
        return None
    opcode = data[0]
    if opcode == OPCODE_FAMILIAR_ACK:
        try:
            _, last_seq = decode_familiar_ack(data)
        except ValueError:
            return None
        return FamiliarAck(last_received_seq=last_seq)
    if opcode == OPCODE_FAMILIAR_RESET:
        try:
            decode_familiar_reset(data)  # validates length/opcode
        except ValueError:
            return None
        return FamiliarReset()
    return None
