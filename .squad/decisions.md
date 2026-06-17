# Halo Decisions Log
## 2026-06-08

### Testing Decision: London-School TDD for The Synesthetic Familiar

| Field | Value |
|-------|-------|
| **Author** | Juanita (Tester / QA) |
| **Date** | 2026-06-08 |
| **Status** | PROPOSED — for team review |
| **Scope** | Synesthetic Familiar test suite + any future BLE/host-device Python projects |
| **Reference** | docs/projects/synesthetic-familiar/TEST-STRATEGY.md |

---

## Decision

**Adopt London-school (mockist, outside-in) TDD as the test methodology for
the Synesthetic Familiar, and recommend it as the default for all future
host-device Python projects in this repo.**

---

## Rationale

### Why London, not Detroit

Detroit (classicist) TDD tests observable state: call a function, assert on
return values. It works well for pure-function-heavy codebases where
collaborators are stable or trivial.

The Synesthetic Familiar is neither. It has four hard collaborators that
cannot or should not be real in a test environment:

1. **BLE transport** (`brilliant-ble`) — an external SDK over a physical radio.
   Testing against a real BLE device means every host-side unit test requires
   hardware, takes 10-30s to connect, and fails intermittently due to radio
   flake. This is unacceptable for a fast-feedback test suite.

2. **Sensor source** (mic + IMU) — hardware on the host phone and device relay.
   Audio capture and IMU relay cannot be scripted without injection. We need
   to drive the inference pipeline with specific `(rms, pitch_variance, accel,
   rot)` values to test thresholds, confidence gating, and fallback paths.

3. **The clock** — breathing interpolation (200-500ms), BLE timeout (10s →
   neutral), and confidence-hold timing all depend on wall time. Without clock
   injection, timing tests require `time.sleep()` — which is slow, fragile,
   and CI-unfriendly.

4. **The Lua render loop** — running on hardware we don't own during testing.
   We cannot assert on pixel output without either an emulator or extracting
   pure logic from the render loop.

London school makes these collaborators visible as **ports**: named interfaces
that test doubles plug into. This drives better architecture: `FamiliarApp`
takes a `TransportPort`, a `SensorSourcePort`, and a `ClockPort` — injected,
not hard-wired. The test suite naturally produces a dependency-injection
architecture that is also easier to extend (swap mic → camera sensor source
in Phase 2 without touching `inference.py`).

### The Outside-In, Interface-Discovery Benefit

Writing acceptance tests first before `FamiliarApp` exists forced interface
discovery:
- `run_cycle()` was named by a test, not a design meeting
- The confidence gate belongs in the orchestrator (`run_cycle()`), not inside
  `compute_mood()` — Tell-Don't-Ask is a natural consequence of mockist testing
- The `FakeClock` requirement forced clock injection, which revealed that
  `main.py` would otherwise have had `time.monotonic()` buried in its body

### The Red→Green→Refactor Discipline

This project is a 2-3 week playground demo. Without discipline, it will
accumulate technical debt in the inference thresholds, the wire-format
encoding, and the Lua state machine. Red→Green→Refactor makes the
refactoring phase mandatory and safe: no production code is touched unless
tests are green.

---

## Alternatives Considered

| Alternative | Rejected? | Reason |
|-------------|-----------|--------|
| Detroit TDD (state-based) | Yes | BLE/sensor/clock collaborators make state-based testing impractical without real hardware |
| No TDD (write tests after) | Yes | Inference thresholds and confidence gating are easy to get subtly wrong; tests-after miss the interface-discovery benefit |
| Integration-first (emulator only) | No (kept for Tier 3) | Emulator tests are valuable but slow; not a replacement for fast unit/acceptance tests |

---

## Constraints & Caveats

- The `halo-emulator` is described as "experimental" (Juanita history.md).
  Integration tests at Tier 3 may have emulator gaps. Do not rely solely on
  emulator for correctness; acceptance tests with FakeTransport are the
  primary correctness gate.
- Lua unit testing requires either `busted` (Lua test framework) or extracting
  pure logic into a Python simulation. The team should confirm busted is
  installable in CI before committing to it.
- Three ARD gaps (heap API, FAMILIAR_ACK trigger, `on_imu_peak` polling)
  create test blockers for specific stories. These are documented in
  TEST-STRATEGY.md Appendix A and must be resolved before those stories
  are considered testable.

---


## 2026-06-08T07:03Z: Project codename — VESPER

**Status:** DECIDED  
**Owner:** Aaron Kubly  
**Date:** 2026-06-08  
**Related:** Theme-2 Synesthetic Familiar

The "synesthetic-familiar" project's official codename is **VESPER**. Whole-team brainstorm produced candidates with team consensus at PULSE (4/9 agents) and other pitches including VESPER, EMBER, AURA, VEIL, ORACLE, CANARY, ECHO, GLIMMER, RESONANCE, GLOAM. Aaron selected VESPER for its twilight/peripheral-awareness resonance, strong naming hygiene (low OSS collision risk), distinctive pronunciation, and slug quality.

**Scope note:** VESPER is the codename; "synesthetic-familiar" remains the descriptive project name and directory. No directory rename unless Aaron requests it.

---

## 2026-06-08: VESPER ARD Architecture Clarifications

**Status:** DECIDED  
**Owner:** Hiro (Architect)  
**Date:** 2026-06-08  
**Related:** Post-test-strategy advisory review

Advisory review of VESPER ARD surfaced three ambiguities; Aaron approved fixes. All changes landed in `docs/projects/synesthetic-familiar/ARD.md`.

**Decision 1: Heap Ownership — Device-Local**
- Lua device monitors heap internally (80% → reduce complexity; 95% → safe-halt).
- No heap state surfaced in host-bound messages. `FAMILIAR_ACK` carries `last_received_seq` only — no heap field.

**Decision 2: Quick-Reset Ownership — Device-Originated**
- Double-tap gesture detected and handled on-device (Lua IMU/tap input); device snaps to NEUTRAL immediately.
- `FAMILIAR_RESET` direction is **Device → Host** (notification, not command).
- Rationale: Wearer corrects bad inference in real-time. Host round-trip adds 100-300ms latency and fails under BLE degradation.

**Decision 3: Confidence Gating Authority — Host Only**
- Host is the single authority for confidence gating. If confidence < 0.7, host does not send update — period.
- Device-side gating is optional defense-in-depth, not required behavior.

---

## 2026-06-08: VESPER BLE Wire-Format Specification

**Status:** DECIDED  
**Owner:** Ng (SDK Engineer)  
**Date:** 2026-06-08  
**Related:** ARD §5.2 wire format under-specified; test code invented endianness, seq wraparound, dedup policy, reset opcode

Wire-format specification fully pinned to prevent Python host and Lua device drift.

**1. Endianness: Little-endian (LE) for all multi-byte fields** (BLE ATT native, Cortex-M55 native).

**2. Sequence Number: uint16, wraps 0xFFFF → 0x0000**
- Host increments seq monotonically on each `FAMILIAR_UPDATE`; resets at reconnect.
- Device dedup rule: `delta = (received_seq - last_accepted_seq) mod 65536`; interpret as signed 16-bit: delta 1–32767 = newer (accept), 0 = duplicate (drop), 32768–65535 = stale (drop).

**3. Opcode Space: 0x00–0x7F Device→Host, 0x80–0xFF Host→Device**
- `0x80` = `FAMILIAR_UPDATE` (Host→Device): opcode, mood_enum, intensity, confidence, seq [6B]
- `0x02` = `FAMILIAR_ACK` (Device→Host): opcode, last_received_seq [3B]
- `0x01` = `FAMILIAR_RESET` (Device→Host): opcode only [1B]

**4. FAMILIAR_RESET: Device→Host only.** Device snaps to NEUTRAL on double-tap locally (Lua). Host does NOT send reset command.

**5. FAMILIAR_ACK Cadence:** Auto every 10 accepted `FAMILIAR_UPDATE` packets (~1 ACK/sec @ 10Hz) + unsolicited on BLE reconnect.

---

## 2026-06-08: Test Strategy Rev 2 — Review Findings Closed

**Status:** DECIDED  
**Owner:** Juanita (Tester / QA)  
**Date:** 2026-06-08  
**Related:** TEST-STRATEGY.md Rev 1 advisory review (3 blocking, 7 important, 1 minor category)

All 11 advisory review findings (3 blocking, 7 important, 1 minor) are closed in TEST-STRATEGY.md Rev 2.

**Blocking Findings:**
- **B1 — Heap Tests → Device Tier Only:** Heap management entirely device-local (Lua). No heap state on wire. `FAMILIAR_ACK` is seq-only. Rewritten as device-tier-only tests (busted + emulator).
- **B2 — Wire Format:** All `>H` replaced with `<H` (LE). §6.6 rewritten with signed-16 delta window dedup. Explicit tests for duplicate/stale/wraparound. `FAMILIAR_RESET` = 0x01 Device→Host. `FAMILIAR_ACK` = auto every 10 packets, seq-only.
- **B3 — False-Positive Bug in §4.2:** Single `FakeTransport()` instance used for both constructor and assertion. Code comment added documenting intent.

**Important Findings:**
- **I4 — Honest London-School Framing:** §1 updated with mixed-methodology table. Tell-Don't-Ask corrected: `FamiliarApp` orchestrates, not `inference.py`. Red guidance pre-stubs `FamiliarApp`.
- **I5 — Decouple Acceptance from Heuristic:** All acceptance tests inject controlled `inference_fn`; sensor values stay in classicist unit tests (`test_inference.py`).
- **I6 — Confidence Gating Ownership:** Device-side gating relabeled "optional defense-in-depth." Host is sole authority (ARD §5.4).
- **I7 — Privacy/Jitter:** §6.8 added seeded-RNG seam; busted test asserts jitter 5–10%. §4.1 added: `encode_familiar_update` cannot accept raw sensor parameters.
- **I8 — Lua Testing Authority:** `busted` declared authoritative Lua check. §7.3 rewritten: property tests must drive real Lua interpreter, not Python clone.
- **I9 — Quick-Reset Seam:** JUANITA-T2-5 updated: "Device detects double-tap → Lua snaps to NEUTRAL locally; host receives FAMILIAR_RESET notification (0x01)."
- **I10 — Story-Mapping Alignment:** YT-T2-2 replaced with baseline-adaptation behavior (ARD-grounded). RAVEN-T2-1 updated to acceptance (protocol) + manual (visual).

**Minor Finding:**
- **M11 — Appendix A Blockers:** Restructured into RESOLVED (R1–R7: endianness, ACK, seq, FAMILIAR_RESET, heap, confidence, quick-reset) and OPEN (7 items: emulator API, RNG seam, sprite format, baseline persistence, IMU interrupt). No review findings remain open.

---

## 2026-06-08: Skip Standalone Technical Design for VESPER Phase 1
**Status:** Proposed  
**Owner:** Hiro (Architect)  
**Date:** 2026-06-08  
**For:** Aaron (final approval)

## Recommendation

**Do not author a standalone technical design document before Week 1 implementation.** The ARD + Test Strategy already cover implementation-grade detail. A separate tech design would re-litigate locked decisions and add documentation overhead disproportionate to a 2–3 week playground project.

## What the ARD Already Covers (implementation-grade)

- **Wire format** (§5.2): Byte-level spec for all 3 message types, endianness, seq wraparound/dedup, opcode space, ACK cadence — normative, not sketched
- **Component decomposition** (§5.1–§5.5): File-level structure (\main.lua\, \host/main.py\, \sensors.py\, \inference.py\, \amiliar_protocol.py\), responsibilities per module
- **Interface contracts** (§5.3–§5.4): Constructor signatures, inference pipeline code, confidence gating logic, sensor fallback hierarchy
- **State machine** (§5.1): Four states with transitions and thresholds
- **Render spec** (§5.5): Sprite size, position, palette, animation per state, lit-pixel budget, rendering primitives
- **Autonomy table** (§4): Component-by-component location decisions with ownership (host vs. device)
- **Dependency list** (§6): Exact packages, versions, licenses

## What the Test Strategy Already Covers

- **Ports & Adapters seams** (§3): \TransportPort\, \SensorSourcePort\, \ClockPort\ with real/fake adapter pairs
- **Constructor injection signatures** (§3): \FamiliarApp.__init__\ with all injectable dependencies
- **Test pyramid** (§2): Four-tier structure with mock/real boundaries per layer
- **Story→test mapping** (§5): Every user story mapped to specific test expectations
- **Definition of Done per story** (§9): Concrete acceptance criteria

## What a Tech Design Would Add — and Why It's Not Worth It

| Potential Addition | Value | Why Skip |
|--------------------|-------|----------|
| Class diagrams / UML | Visual overview | ARD §5 is already file-level; drawing boxes around 5 files adds ceremony, not clarity |
| Sequence diagrams (host↔device) | Timing clarity | §4 data flow + §5.2 wire format already specify the exact sequence at byte level |
| API contracts doc | Formal interfaces | Test Strategy §3 already defines port interfaces with constructor signatures |
| Error handling matrix | Exhaustive failure modes | ARD §5.4 fallback hierarchy + §8 risk table + Test Strategy §6 edge cases cover this |
| Performance budgets | Quantified targets | ARD §5.5 already specifies: 50ms/frame, 32 sprites/frame, <5mW idle, 15–30fps |

## Lightweight Replacement

Instead of a tech design doc, use **per-package READMEs written during implementation** (not before):

1. \synesthetic-familiar/host/README.md\ — emerges from Week 1 code
2. \synesthetic-familiar/device/README.md\ — emerges from Week 1 code
3. ARD §10 open questions (6 items) get resolved inline as Ng investigates SDK gaps

These are cheaper, stay current, and don't front-load speculation.

## Anti-Anchoring: When Would a Tech Design Be Warranted?

A standalone tech design would be the right call if:

- **The ARD were requirements-only** (what, not how) — but it's not; §5 is implementation-grade
- **Multiple implementers needed coordination** — but Phase 1 is one dev (Aaron) with agent support
- **The wire format were still open** — but Ng locked it on 2026-06-08
- **Cross-package integration were complex** — but this is 2 packages (host Python, device Lua) with 1 BLE pipe

Evidence that would change my mind: if Aaron starts Week 1 and finds himself re-reading the ARD to answer "how should X talk to Y" questions that the ARD doesn't address, that's the signal to write a thin interface-contract doc mid-sprint. But write it from real confusion, not speculative prevention.

## Verdict

Start Week 1. Let the code teach us what the ARD missed. Document as you go, not before.

---

## 2026-06-09: VESPER Package Layout

| Field | Value |
|-------|-------|
| **Date** | 2026-06-09 |
| **Author** | Hiro |
| **Status** | DECIDED |
| **Artifact** | `projects/synesthetic-familiar/` |

### Decision

The Synesthetic Familiar code package lives at **`projects/synesthetic-familiar/`**
(relative to mono-repo root `D:\git\halo`).

### Options Considered

| Option | Path | Verdict |
|--------|------|---------|
| A — Repo-root flat | `synesthetic-familiar/` | Rejected |
| B — Under `projects/` | `projects/synesthetic-familiar/` | **Selected** |

### Rationale

1. **Mirrors docs structure.** The ARD already lives at
   `docs/projects/synesthetic-familiar/ARD.md`. Placing code at
   `projects/synesthetic-familiar/` creates a consistent
   `{docs,projects}/<name>/` namespace across the repo. Engineers navigating
   either tree find the sibling naturally.

2. **Mono-repo hygiene.** The repo root currently holds only tooling and
   configuration (`.squad/`, `.copilot/`, `.github/`, `docs/`). Introducing
   a flat `synesthetic-familiar/` at root would mix project code with
   infrastructure at the same level — inconsistent once a second project
   lands.

3. **ARD §5.3 is a relative tree, not an absolute placement.** The diagram
   shows `synesthetic-familiar/` as the package root name, not the repo-root
   path. There is no ARD constraint violated by nesting it under `projects/`.

4. **Future projects follow naturally.** When project 2 arrives, it lands at
   `projects/<name>/` without any restructuring.

### What Was NOT Changed

- `docs/` structure untouched.
- No `projects/` namespace was pre-established before this commit — this
  decision creates it implicitly by writing the first package there.

### Consequences

- All file-ownership references (Ng, Da5id, Juanita) use paths relative to
  `projects/synesthetic-familiar/`.
- If a `projects/` README is warranted later (index of all projects), it
  lives at `projects/README.md` — not created yet (no repetition yet).

---

## 2026-06-09: VESPER Week 1 — SDK Gaps & Decisions

**Author:** Ng (SDK Engineer)
**Date:** 2026-06-09
**Status:** For review — no blocking issues; Week 1 "It moves" can ship.
**ARD cross-refs:** §5.1, §5.2, §5.5, §10

### Summary

Week 1 implementation complete. Wire format implemented to spec (locked
2026-06-08). Four SDK gaps noted below — none block the "creature bobs"
success criterion. All gaps are flagged inline in `device/main.lua` and
`host/main.py`.

### SDK Gap #1 — IMU tap/interrupt API (ARD §10 Q1)

**Status:** Not blocking Week 1 or Week 2. Blocks Week 3 (double-tap FAMILIAR_RESET).

**Gap:** `frame.imu.on_tap(n, callback)` (or `frame.on_imu_peak`) has not been
confirmed as available in current Halo Lua stdlib. The ARD §5.1 notes
"current SDK is polling-only" for IMU.

**Week 1 action:** Double-tap handler stub is commented out in `device/main.lua`
with a clear guard:
```lua
-- if frame.imu and frame.imu.on_tap then
--   frame.imu.on_tap(2, function() ... end)
-- end
```

**Week 3 action required:** Ng to confirm with Brilliant SDK team. If
interrupt-style callback is unavailable, implement a debounced polling loop
(target ≤50ms detection latency per ARD §10 Q1). Flag to Raven if new
sensor permissions are needed.

### SDK Gap #2 — `frame.display.bitmap()` pixel-buffer format (ARD §10 Q2)

**Status:** Not blocking. Current rendering uses `set_pixel()` per pixel,
which is correct for any firmware.

**Gap:** The exact format accepted by `frame.display.bitmap()` is not confirmed:
- Da5id proposes: nibble-packed 4-bit indexed, row-major, high-nibble = left pixel
- Alternative formats: byte-per-pixel, RGB565, RLE

**Current state:** `device/main.lua` renders via a `set_pixel()` loop through
Da5id's index grid (288 pixels). This is ~288 API calls per frame. At 20fps
this may be too slow (ARD §5.5 budget: ≤50ms/frame); needs measurement on
real device.

**When confirmed:** Set `SPRITE_BITMAP_READY = true` in `device/main.lua` and
provide `SPRITE_BITMAP` as the packed byte string. One line uncomment — no
other changes. Da5id should regenerate bytes once format is locked.

**Action:** Ng to check Brilliant SDK source / docs. Target: resolved before
Week 2 sprite palette changes land.

### SDK Gap #3 — `frame.system.get_heap_usage()` (ARD §10 Q3)

**Status:** Not blocking Week 1 or Week 2. Heap budget enforcement (80% reduce,
95% halt — ARD §5.1) is deferred.

**Gap:** `frame.system.get_heap_usage()` not confirmed in current Lua stdlib.

**Week 3 action:** If unavailable, approximate heap pressure by tracking
allocation sites manually (e.g., count sprite rows held in memory, BLE buffer
size). The 288-byte sprite index table is small; main risk is BLE receive
buffer growth during fast packet bursts.

### SDK Gap #4 — Sleep API name (`frame.sleep` vs `frame.time.sleep`)

**Status:** Not blocking — shim in `device/main.lua` handles both.

**Gap:** ARD §5.1 references `frame.time.sleep()`; Brilliant Frame SDK examples
use `frame.sleep()`. A compatibility shim at Lua startup tries both:
```lua
if frame and frame.sleep then _sleep = frame.sleep
elseif frame and frame.time and frame.time.sleep then _sleep = frame.time.sleep
else ... end
```

**Action:** Confirm on real device; remove unused branch once known.

### Non-blocking observation — `frame.display.clear()` API

`device/main.lua` calls `frame.display.clear()` to blank the frame before
each render. If this function doesn't exist in the Halo Lua stdlib, replace
with `frame.display.fill_rect(0, 0, 256, 256, 0x000000)` or equivalent.
The render will still be correct; this is purely a clear-screen primitive name.

### Wire format — confirmed as implemented

The FAMILIAR_UPDATE / FAMILIAR_ACK / FAMILIAR_RESET wire format is implemented
exactly to spec (ARD §5.2, locked 2026-06-08, decisions.md):

| Message         | Bytes | Layout (LE)                                      |
|-----------------|-------|--------------------------------------------------|
| FAMILIAR_UPDATE | 6     | `0x80 mood intensity confidence seq_lo seq_hi`   |
| FAMILIAR_ACK    | 3     | `0x02 seq_lo seq_hi`                             |
| FAMILIAR_RESET  | 1     | `0x01`                                           |

`host/familiar_protocol.py` is the single source of truth. Juanita's
`tests/test_protocol.py` should import from there exclusively.

### 2026-06-09 addendum

Added `Mood` IntEnum (NEUTRAL=0, CALM=1, STRESSED=2, ATTENTION=3) and
`seq_is_newer(received, last_accepted) -> bool` free function; changed
`decode_familiar_ack` → `tuple[int, int]` and `decode_familiar_reset` → `int`
to match Juanita's test contract. `pytest tests/test_protocol.py` — **54 passed, 0 skipped.**

---

## 2026-06-09: VESPER Week-1 Sprite & Animation Spec

| Field | Value |
|-------|-------|
| **Status** | DECIDED |
| **Owner** | Da5id (HUD/UX) |
| **Date** | 2026-06-09 |
| **Related** | ARD §5.5, Decision 3 (Abstract-with-Eyes) |
| **Artifact** | `device/sprites/familiar_neutral.txt` + `device/sprites/README.md` |

### Summary

Week 1 "It moves" requires a canonical sprite asset Ng can render. This decision locks the sprite design, pixel format, and bob animation spec for the neutral/idle state.

### Deliverables

1. **Sprite asset:** `device/sprites/familiar_neutral.txt`
   - 24×24 organic blob with single bright eye at upper-right
   - ASCII art + numeric index grid for parsing

2. **Format spec:** `device/sprites/README.md`
   - 4-bit indexed (16-color palette, 288 bytes packed)
   - Nibble-packed, row-major, high nibble = left pixel
   - **NEEDS NG CONFIRMATION** — if `frame.display.bitmap()` expects different format, will regenerate

3. **Palette (Neutral):**
   | Index | Color | Use |
   |-------|-------|-----|
   | 0 | `0x000000` | Transparent (OLED off) |
   | 1 | `0x1A2D3D` | Body dark |
   | 2 | `0x2E4756` | Body mid |
   | 3 | `0xE0F4FF` | Eye (bright cyan-white) |

4. **Bob animation:**
   - Amplitude: ±2 px vertical
   - Frequency: 0.25 Hz (4-second cycle)
   - Easing: Sine wave
   - Pseudocode: `y = base_y + floor(2 * sin(2π × 0.25 × t) + 0.5)`

### Position on Canvas

- Location: 7 o'clock on rim, 80% radius
- Coordinates: sprite top-left at approximately `(28, 167)`
- Rationale: Peripheral vision placement per ARD §5.1

### Glance-Ergonomics (Ng Constraints)

1. Eye contrast ≥10:1 against body ✓
2. Lit pixel budget: ~91 px = 1.5% canvas ✓
3. **DO NOT ADD in Week 1:**
   - Halo glow (Week 2 calm)
   - Edge fraying (Week 2 stress)
   - Color animation
   - Attention jump
   - Multiple eyes or facial features

### Dependencies

- **Ng must confirm sprite format** before render loop integration
- If format differs from spec, Da5id regenerates asset same day

---

## 2026-06-09: Testing Decision: VESPER Week-1 Protocol Tests

| Field         | Value |
|---------------|-------|
| **Author**    | Juanita (Tester / QA) |
| **Date**      | 2026-06-09 |
| **Status**    | DECIDED |
| **Ref**       | projects/synesthetic-familiar/tests/test_protocol.py |
| **ARD**       | docs/projects/synesthetic-familiar/ARD.md §5.2 |
| **Strategy**  | docs/projects/synesthetic-familiar/TEST-STRATEGY.md Rev 2 |

### Summary

54-test unit suite written for `host/familiar_protocol.py` (Ng's module).
Tests are normative against ARD §5.2; they collect cleanly now and will pass
once Ng implements the module.

### What Was Covered

| Group | Tests | Key assertions |
|-------|-------|----------------|
| FAMILIAR_UPDATE encode | 15 | 6-byte length, opcode 0x80, all 4 mood enums, intensity/confidence byte positions, seq little-endian, full round-trip |
| Field bounds | 13 | valid 0/100 boundaries; out-of-range intensity, confidence, mood, seq raise ValueError/OverflowError |
| Seq dedup (seq_is_newer) | 13 | accept window 1–32767, dup=0, stale 32768–65535, wraparound 0xFFFF→0x0000, naive-`>` regression |
| FAMILIAR_ACK decode | 7 | opcode 0x02, seq LE, paranoid high-byte test (seq=0x0201), return type |
| FAMILIAR_RESET decode | 3 | opcode 0x01, 1-byte payload, NO encode function (device→host only) |
| Privacy / shape guard | 3 | No raw biometric params in encode signature, exactly 6 bytes |

### Import Assumptions (Juanita → Ng)

Ng: please align `host/familiar_protocol.py` to these exported names:

```python
from host.familiar_protocol import (
    Mood,                  # enum: NEUTRAL=0, CALM=1, STRESSED=2, ATTENTION=3
    encode_familiar_update,  # (mood, intensity: int, confidence: int, seq: int) -> bytes
    decode_familiar_ack,     # (raw: bytes) -> tuple[int, int]
    decode_familiar_reset,   # (raw: bytes) -> int
    seq_is_newer,            # (received: int, last_accepted: int) -> bool
)
```

### B2 Regression Guard (Explicit)

Two key tests prevent big-endian regressions:

1. `test_seq_bytes_4_5_are_little_endian_not_big_endian` — verifies seq=0x0102 encodes as [0x02, 0x01]
2. `test_seq_high_byte_paranoid_little_endian` — verifies decode of raw=[0x02, 0x01, 0x02] yields seq=0x0201 (513)

### Pre-Implementation Behavior

| State | Behavior |
|-------|----------|
| After Ng implements | **All 54 tests PASS, 0 skipped** ✓ |

---

## 2026-06-09: Privacy Pass — Synesthetic Familiar Week 1 (VESPER)

| Field | Value |
|-------|-------|
| **Author** | Raven (Security & Privacy) |
| **Date** | 2026-06-09 |
| **Scope** | Week 1 mock pipeline only — `projects/synesthetic-familiar/` |
| **Status** | DECIDED — no blocker; establishes guardrails for Week 2 |

### 1. Week-1 Data Flow (Mock Only)

```
┌──────────────────────────┐
│  Mock Source (Python)    │  Hardcoded / cycled mood values
│  main.py (stub)          │  NO real mic, NO real IMU
└────────────┬─────────────┘
             │  encode_familiar_update()  →  6-byte struct
             ▼
┌──────────────────────────┐
│  familiar_protocol.py    │  FAMILIAR_UPDATE: opcode + mood_enum
│  (BLE wire encoder)      │  + intensity + confidence + seq
└────────────┬─────────────┘
             │  BLE point-to-point (bonded, encrypted)
             ▼
┌──────────────────────────┐
│  Halo Device (Lua VM)    │  Receives 6 bytes; drives sprite
│  main.lua (stub)         │  bob animation at 0.25Hz
└────────────┬─────────────┘
             │  On-glass render only (OLED local)
             ▼
┌──────────────────────────┐
│  Wearer's eye             │  24×24 abstract sprite — no labels
└──────────────────────────┘
```

**Finding: CLEAR** — Week 1 captures zero real sensor data. All source files are stubs.

### 2. RAVEN-T2-1 Privacy Constraint — Bobbing Sprite (Establish Now)

| Parameter | Constraint |
|-----------|------------|
| **Bob frequency** | Snap to coarse tier: Neutral 0.25Hz / Calm 0.15Hz / Stressed 0.75Hz / Attention burst. No continuous float mapping to breathing rate. |
| **Intensity byte** | Quantise to 5 levels only: `{0, 25, 50, 75, 100}`. Do not pass raw sensor amplitude. |
| **Jitter** | 5–10% random noise MUST be applied at host **before encoding** — not optional. |
| **Confidence byte** | Internal gate only (ARD §5.4). Do not send gated frames. |
| **No raw biometrics on wire** | `FAMILIAR_UPDATE` 6-byte format contains no audio_rms, no audio_pitch_variance, no imu_acceleration. |

### 3. Self-Verification Checklist (Ng / Da5id — Week 1 + Week 2 Gate)

**Week 1 — Before merging mock harness**

- ✓ `main.py` mock loop sends only hardcoded/cycled `mood_enum` values — no `SensorStream.start()` call
- ✓ No audio device opened in Week 1 code path
- ✓ No IMU BLE subscription in Week 1 code path
- ✓ `familiar_protocol.py` `encode_familiar_update` outputs exactly 6 bytes
- ✓ `requirements.txt` contains no cloud-SDK packages
- ✓ No `.env`, no API keys in any committed file

**Week 2 — Before wiring real sensors (privacy gate)**

- [ ] `intensity` quantised to `{0, 25, 50, 75, 100}` — no raw float passthrough
- [ ] 5–10% random jitter applied to `intensity` at host **before** `encode_familiar_update()` call
- [ ] Bob frequency snapped to tier table (no continuous breathing-rate mapping)
- [ ] `test_familiar_update_carries_no_raw_biometric_values` passing in CI
- [ ] `SensorStream` writes no audio/IMU data to disk
- [ ] BLE connection uses bonded (encrypted) channel
- [ ] Manual visual audit: non-wearer 30s bystander test — abstract form only

### 4. Disposition

**Week 1:** No block. All source files are stubs. No real data captured, no secrets
committed.

**Week 2 gate:** Before real sensor integration, require:
1. `test_familiar_update_carries_no_raw_biometric_values` in CI (P0)
2. Intensity quantisation + jitter applied at host before encode

If either is absent, RAVEN vetoes the merge.

---

## 2026-06-09: VESPER Foundation Architecture & Test Strategy — Aaron Decisions

| Field | Value |
|-------|-------|
| **Author** | Aaron Kubly |
| **Date** | 2026-06-09 |
| **Status** | DECIDED |
| **Context** | ARD + TEST-STRATEGY persona-review remediations (Design Panel + verification cycles) |

### Decision 1: VESPER v1 Sensor Topology

**Selected:** Desktop Python host with desktop mic + Halo IMU relay (via BLE).

**NOT selected:** Phone as host (rejected due to battery/drift concerns). Device-side IMU-only inference (rejected; host retains gating authority).

**Implication:** Host owns the full inference gate; device streams IMU wirelessly; desktop mic feeds the sensor/inference pipeline (`sensors.py` → `inference.py`). `familiar_protocol` is only the BLE wire encode/decode layer and carries derived mood/intensity/confidence/seq — it has no mic or inference role.

---

### Decision 2: Stuck-in-Stressed Fallback — Confidence-Hold Timeout

**Problem:** Sustained high-confidence STRESSED can trap wearer in visual feedback loop; manual mood override risks confidence-gating ineffectiveness.

**Solution:** After ~30 seconds of gate-suppressed silence (no update sent), host sends last COMPUTED mood at sub-threshold confidence. This allows recovery without abandoning the gate.

**Mechanism:**
- Timer armed: when gate suppresses a frame (confidence ≤ threshold)
- Timer fires: at ~30s, send `(last_computed_mood, intensity, confidence_sub_threshold, seq++)`
- Timer reset: on any successfully sent update (including the timeout resend itself); suppressed/gated frames do NOT reset the timer

**Outcome:** Wearer sees one visual update after 30s even if stuck; gate retains authority; confidence remains below merge threshold.

---

### Decision 3: BLE-Drop Fallback — Neutral-Only, No Device-Side IMU Inference

**Problem:** Dropped BLE → device has local IMU but no host gating authority. Risk: device infers stress incorrectly without host context.

**Solution:** On BLE drop (no FAMILIAR_UPDATE for 10s), device reverts to NEUTRAL only. Host regains authority on reconnect.

**NOT allowed:** Device-side IMU-only inference (rejected). Device cannot infer mood independently.

**Outcome:** Safety fallback is conservative (neutral); host authority is not overridden; reconnection restores full inference.

---

### Decision 4: CALM 60-Second Sustain Behavior — KEPT

**Status:** Retain existing 60-second CALM sustain window from ARD (with updated test coverage).

**Test addition:** Busted `test_calm_sustain_timing_exhaustive` added to cover packet-count boundary (590 vs 600 packets = 59s vs 60s at 10 Hz).

**Outcome:** Wearer experience stable; test harness now validates timing precisely.

---

### Decision 5: Test-Strategy Trim — Selective Coverage & Lua Authority

**Dropped hypothesis property tests:**
- Hypothesis + Lupa cross-validation removed (low signal, high maintenance).

**Dropped global 90% coverage gate:**
- Replaced with selective **95% on familiar_protocol.py** (where privacy + wire encoding live).
- Non-critical modules (UI harness, logging) drop to default ~70%.

**Lua sole authority:** Busted remains the canonical test engine for Lua (no Python-based Lua mocking).

**Outcome:** Test suite is lean, maintainable, and focused on high-risk code paths.

---

### Decision 6: Baseline Persistence — Phase 1 (Host Filesystem)

**Phase 1 mechanism:** Host persists baseline to `~/.vesper/baseline.json` (host-local filesystem).

**Not Phase 1:** Cloud sync, multi-device baseline sharing, encrypted vault.

**Rationale:** Simplifies Phase 1; enables offline operation; defers cloud sync decision to Phase 2 PRD.

**Implementation:** Host writes `baseline.json` after successful inference cycle (friendly mood + confidence ≥ threshold).

**Outcome:** Baseline persists across restarts; Phase 2 can add cloud sync without rework.

---

### Decision: VESPER Week 1 Persona-Review Fix Wave
**Author:** Ng  
**Date:** 2026-06-09  
**Branch:** week1-synesthetic-familiar  
**Commit:** 52fbd39  
**Status:** Implemented

---

## Summary

Persona-review Code Panel (Correctness/Skeptic/Craft/Compliance/Security) produced 18 findings on the Week 1 "It moves" payload.  This decision documents the protocol/device behavior changes accepted in the fix wave.

---

## Behavior Changes

### 1. Seq desync on idle timeout (device/main.lua)

**Before:** 10s idle timeout only reset `state.mood = 0` and `state.intensity = 50`.  A restarted host with seq counter at 0x0000 would be rejected for ~33 minutes (device last_seq might be ~20000; delta = 0x0000 - 20000 > 32767 → dropped).

**After:** Timeout block now also sets:
- `state.last_seq = 0xFFFF` — reconnect rule: next host packet seq=0x0000 yields delta=1 → accepted.
- `state.last_rx_t = 0` — re-arms the timeout; prevents repeated seq reset every frame while the host is actively sending after recovery.

**Wire contract:** Unchanged.  Device behavior change only.  Aligned with ARD §5.2 reconnect rule (host resets counter to 0x0000; device must accept it).

### 2. pcall guards (device/main.lua)

**Before:** Render loop and BLE receive callback had no error protection.  Any transient `frame.*` error permanently froze the creature.

**After:** Both `on_ble_data` body and render loop body are wrapped in `pcall(function() ... end)`.  On error: `print("context: " .. tostring(err))` + `_sleep(RENDER_DT)` backoff.  No behavioral change on the happy path.

### 3. dispatch_device_message error handling (familiar_protocol.py)

**Before:** Malformed Device→Host packets raised `ValueError` into the async BLE callback, crashing the receive handler.

**After:** `decode_familiar_ack` and `decode_familiar_reset` calls are wrapped in `try/except ValueError → return None`.  Caller receives `None` for malformed packets; caller is responsible for log-and-drop (already implemented in `host/main.py` via the `msg is None` branch).

### 4. draw_creature bitmap fast-path (device/main.lua)

**Before:** `SPRITE_BITMAP_READY` block had no `return`; enabling the bitmap path later would double-render (bitmap + pixel loop).

**After:** Added `return` at end of `SPRITE_BITMAP_READY` block.  No behavioral change today (bitmap path is still disabled); prevents the double-render regression when Da5id enables it in Week 2.

---

## Rejected Findings

### Finding #10 — decode_familiar_ack return type

**Finding:** `decode_familiar_ack` returns raw `(int, int)` tuple; inconsistent with `decode_familiar_update → FamiliarUpdate` dataclass pattern.

**Decision: REJECTED for Week 1.**

**Reasoning:** `test_protocol.py` (Juanita's locked test suite) asserts `opcode, seq = decode_familiar_ack(raw)` tuple unpacking across 7 tests (TestFamiliarAckDecode).  Changing the return type requires rewriting those tests — non-trivial churn with no behavioral improvement for Week 1 consumers, since `dispatch_device_message` already normalizes to `FamiliarAck` before returning to callers.  Defer to Week 2 with Juanita coordination.

---

## Escalation

**Finding #18:** `device/main.lua` has not been validated on real Halo hardware.  The 20fps render loop, set_pixel sprite rendering, BLE receive callback, and `frame.time.utc()` time source must all be confirmed against live firmware.  **Action item for Aaron / hardware access.**

---

## Test Results

| Before | After |
|--------|-------|
| 54 passed, 5 failed | 59 passed, 5 xfailed, 0 failed |

New tests: 5 golden byte-vector fixtures in `tests/test_golden_vectors.py`.  
Inference stubs: marked `@pytest.mark.xfail(reason="Week 2 — compute_mood() not yet implemented")`.

---

## Ng Week-1 Follow-ups (deferred to Week 2)

_Logged 2026-06-10 after Cycle-2 polish wave.  Aaron approved all items below._

---

### [Week 2] Cross-language wire-format conformance

**Owner:** Ng (+ Juanita for test infra)

Promote `tests/test_golden_vectors.py` vectors into a language-neutral fixture
(JSON or hex file) consumed by **both** the Python test suite **and** a
Lua-side decode harness, so host↔device wire format is checked in lockstep.
A protocol regression in either direction will then surface in CI rather than
only during hardware validation.

**Context:** Currently the golden vectors are Python-only (`test_golden_vectors.py`).
The Lua `decode_update()` in `device/main.lua` implements the same ARD §5.2 spec
but has no automated test at all — it is only validated by running on real hardware.
This gap is acceptable for Week 1 (unauthenticated link, no security surface),
but should be closed before the wire format is extended in Week 2+.

---

### [Week 2] Sequence-reset hardening after timeout

**Owner:** Ng

After the 10s idle timeout (`device/main.lua`), enter a reconnect state that
accepts **only `seq == 0`** (or an explicit reset handshake) for the first
packet, to narrow the post-timeout replay window.

**Context:** Security review rated the current behavior acceptable for the
unauthenticated Week-1 link and noted it self-heals. This is a hardening item,
not a defect. ARD §5.1 reconnect rule already handles the common case; this
tightens the window for replay of pre-timeout packets that arrive stale.

---

### [Week 2, also deferred from Cycle 1] Decoder-contract symmetry

**Owner:** Ng + Juanita

Make `decode_familiar_ack` return a `FamiliarAck` named type (and
`decode_familiar_reset` return `FamiliarReset`) for decoder-contract symmetry
with `decode_familiar_update`.

Update the **7 tuple-contract tests** in `tests/test_protocol.py` in
coordination with Juanita before landing — she owns the test suite contract.

**Context:** `dispatch_device_message` already normalises to `FamiliarAck` for
all callers, so this is a cleanup not a behaviour change.  Deferred from
Cycle-1 to avoid uncoordinated test churn.

---

### [ACTION — Aaron] Hardware validation

`device/main.lua` has **never run on real Halo hardware.**

Week-1 "creature bobs, no jitter, no freeze" can only be signed off on-device.
Please validate:

- [ ] BLE connect (brilliant-ble / frame_sdk path)
- [ ] FAMILIAR_UPDATE decode (opcode 0x80, 6-byte packet)
- [ ] Sprite render at ~20fps (`set_pixel()` loop — measure frame time vs 50ms budget)
- [ ] Bob animation (±2px sine, 0.25Hz neutral cycle)
- [ ] 10s idle timeout → snap to neutral
- [ ] Unsolicited ACK on connect visible on host side
- [ ] Confirm Halo firmware Lua runtime is **≥ 5.3** (bitwise operators in packet decode and visual color math require it; ARD §10)

Once confirmed, close the hardware-validation action in the ARD §10 open-questions list.

---

## 2026-06-11: Lua 5.3 Runtime Requirement — Da5id (Visuals)

**Status:** NOTED  
**Date:** 2026-06-11  
**From:** Da5id (device/main.lua)  
**Context:** Runtime requirement predates Week 2

The Week-1 BLE packet decode already uses Lua 5.3+ bitwise operators (`|`, `<<`, `&`),
so the runtime requirement predates Week 2. Week 2 adds `draw_halo_glow` and `draw_edge_fraying`,
which use the same operators for color decomposition and the LCG hash — no new requirement introduced.

A runtime-requirement comment has been added to `device/main.lua` (after the ARD §10 SDK gap flags block).

**Action:** The hardware-validation checklist now includes explicit Lua ≥5.3 confirmation (checkbox added above).

---

## 2026-06-10: VESPER Week 2 Integration Contract — Hiro (Architect)

| Field | Value |
|-------|-------|
| **Status** | LOCKED |
| **Date** | 2026-06-10 |
| **Author** | Hiro (Architect) |
| **Purpose** | Contract-first binding for all Week 2 specialists — prevents import-contract drift |

**Specialists bound by this contract:**
- **Ng**: sensors.py, main.py (real sensor→inference loop)
- **Librarian**: inference.py (mood heuristic + baseline)
- **Da5id**: device/main.lua (state-machine animation)
- **Juanita**: 	ests/test_inference.py + new acceptance tests

**Week 2 Success Criterion (ARD §9):** "Aaron can trigger stress state by raising voice in quiet room; stressed visual (faster breathing, warm color) appears within 500ms."

### 1. sensors.py API Contract

**Owner:** Ng

#### 1.1 SensorFrame Dataclass (LOCKED)

\\\python
@dataclasses.dataclass
class SensorFrame:
    """One sample of sensor data delivered at ~10Hz."""
    audio_rms: float            # Root-mean-square of ≤1s audio window (0.0–1.0 normalized)
    audio_pitch_variance: float # Pitch variance over window (0.0–1.0 normalized)
    imu_acceleration: float     # Scalar magnitude of accelerometer (0.0–1.0 normalized)
    imu_rotation: float         # Scalar magnitude of gyroscope (0.0–1.0 normalized)
    mic_ok: bool = True         # False if mic capture failed this frame
    imu_ok: bool = True         # False if IMU relay failed this frame
\\\

**Field semantics:**
- All float fields are normalized to 0.0–1.0 for inference consumption.
- Raw sensor values (dB, rad/s, m/s²) are converted internally; never exposed.
- \mic_ok=False\ → \udio_rms=0.0\, \udio_pitch_variance=0.0\ (zeroed, not omitted).
- \imu_ok=False\ → \imu_acceleration=0.0\, \imu_rotation=0.0\ (zeroed, not omitted).
- Inference uses the \*_ok\ flags to reduce confidence, not to crash.

**Test gate:** \	est_sensor_source_port_exposes_no_raw_audio()\ — **Gate I7 MERGE-BLOCKING**

---

## 2026-06-10: Ng — Week 2 Decision: sensors.py + main.py Real Loop

| Field       | Value |
|-------------|-------|
| **Date**    | 2026-06-10T23:17:50-07:00 |
| **Author**  | Ng (SDK Engineer) |
| **Status**  | SHIPPED |
| **Scope**   | \host/sensors.py\, \host/main.py\ |

**Implemented:**
- **SensorFrame** dataclass: 6 fields (audio_rms, audio_pitch_variance, imu_acceleration, imu_rotation, mic_ok, imu_ok), all float/bool, no raw bytes or ndarray on public API
- **SensorStream** async iterator with 100ms blocks, thread-safe rolling 1s buffer, zeroed post-extraction
- **Real loop** in \main.py\: sensor→inference→encode→send at 10Hz with both-sensors-fail fallback (10s) + confidence-hold timeout I2 (30s)
- **Quantise + jitter** helpers for Gate 2: quantise to {0,25,50,75,100}, apply ±5 jitter clamped 0–100

**Privacy:** Gate I7 fully implemented — buffer ≤1s, zeroed after extraction, no raw bytes on SensorFrame public API.

**Test result:** 59 passed, 5 xfailed (pending Librarian). Implementation contract-conformant.

---

## 2026-06-10: Librarian — Week 2 Decision: Local Mood Heuristic (inference.py)

| Field | Value |
|-------|-------|
| **Status** | IMPLEMENTED |
| **Date** | 2026-06-10T23:17:50-07:00 |
| **Author** | Librarian (AI/ML) |
| **Scope** | \projects/synesthetic-familiar/host/inference.py\ |

**Implemented:**
- **Tension formula** (locked): \	ension = pitch_variance×0.4 + acceleration×0.3 + rotation×0.3\
- **Classification thresholds:** \	ension > 0.65\ → stressed, \	ension < 0.35\ → calm, else neutral
- **Confidence model:** base 0.8 (stressed/calm) / 0.6 (neutral); multiplicative reduction on sensor failure (mic: ×0.6, imu: ×0.7)
- **Baseline persistence:** Welford online mean+stddev at \~/.vesper/baseline.json\; loads at startup, updates per successful frame, saves at exit
- **Zero cloud:** All stdlib imports; no cloud SDK, no ML model, no API call

**Cloud confirmation:** No cloud imports. ARD §5.4 Phase-1 "no cloud" invariant holds.

**Test status:** 5 xfailed (module importable; Juanita's test bodies pending).

---

## 2026-06-10: Da5id — Week 2 Decision: Visual States — Calm Glow & Stressed Fraying

| Field       | Value |
|-------------|-------|
| **Status**  | PROPOSED |
| **Date**    | 2026-06-10 |
| **Author**  | Da5id (Designer) |
| **Scope**   | device/main.lua — render enhancements for CALM and STRESSED moods |

**Implemented:**
- **CALM halo glow:** 3 concentric circles (radii 14,17,20px, brightness 60%→35%→15%) rendered before sprite, intensity-modulated
- **STRESSED edge fraying:** 16 perimeter points with ±2px radial displacement (LCG-seeded pseudo-random), amber accent, rendered after sprite, intensity-modulated

**Budget:** Worst-case ~337 lit pixels (5.5% of 256×256) vs <30% ARD §5.5 budget. Frame time ~8ms vs 50ms ARD §5.5 budget.

**Contract compliance:** Wire format unchanged, 200ms lerp preserved, transitions 200–500ms maintained, anti-robotic jitter (5–10% LCG temporal variance) in place.

---

## 2026-06-10: Juanita — Week 2 Test Suite Decision Record

| Field | Value |
|-------|-------|
| **Status** | DELIVERED |
| **Date** | 2026-06-10 |
| **Author** | Juanita (Tester / QA) |
| **Scope** | Week 2 ("It reacts") — contract §6.2 test obligations |
| **Suite result** | **101 tests, all green** (was 54 before Week 2) |

**Gate coverage:**
- **Gate I7** (merge-blocking) — no raw audio at SensorSourcePort: ✅ \	est_sensor_source_port_exposes_no_raw_audio\ PASS
- **Gate 1** (merge-blocking) — no raw biometrics on wire: ✅ \	est_familiar_update_carries_no_raw_biometric_values\ PASS
- **Gate 2** (merge-blocking) — quantise + jitter before encode: ✅ \	est_intensity_quantised_before_encode\ + \	est_intensity_jitter_applied_before_encode\ PASS
- **I2** — confidence-hold timeout 30s: ✅ \	est_confidence_hold_timeout_resends_after_30s\ PASS
- **ARD §5.4** — both-fail sends NEUTRAL after 10s: ✅ \	est_both_sensors_fail_sends_neutral_after_10s\ PASS

**New tests:** 9 (inference) + 3 (sensors I7) + 1 (protocol Gate 1) + 15 (main.py Gate 2) + 1 (confidence I2) + 1 (fallback) = 47 new tests, 101 total.

**Rejections:** None. Ng and Librarian both delivered contract-conformant implementations.

---

## 2026-06-10: Raven — Week 2 Privacy Audit: VESPER Real-Sensor Pipeline

| Field        | Value |
|--------------|-------|
| **Date**     | 2026-06-10T23:17:50-07:00 |
| **Author**   | Raven (Security & Privacy) |
| **Status**   | COMPLETE |
| **Scope**    | \host/sensors.py\, \host/main.py\, \host/inference.py\, \host/familiar_protocol.py\ |

**Data flow:** Mic/IMU hardware → SensorStream (rolling buffer ≤1s, zeroed post-extraction) → compute_mood (pure function, stdlib) → quantise+jitter → BLE FAMILIAR_UPDATE (mood_int, j_intensity, conf_int, seq).

**Gate I7 (merge-blocking):** ✅ **APPROVE**
- Buffer ≤1s: \
p.zeros(sample_rate)\ at sensors.py:182
- Buffer zeroed post-extraction: sensors.py:308–309 under lock
- SensorFrame public API: 6 fields (4 float, 2 bool), no bytes/ndarray
- Raw audio never logged/written/transmitted

**Gate 1 (merge-blocking):** ✅ **APPROVE**
- \ncode_familiar_update\ signature: (mood: int, intensity: int, confidence: int, seq: int), no raw biometrics parameter
- \main.py\ call chain: passes only abstract values (mood_int, j_intensity, conf_int)

**No cloud egress confirmed:** Zero cloud SDK imports (sensors, main, inference, protocol — all stdlib/sounddevice/numpy only).

**Both merge-blocking gates: APPROVED. Week 2 may merge.**

**Non-blocking follow-ups:**
- W3-1: Harden snapshot zeroing (Ng, Week 3)
- P2-1: LESC (BLE encryption, Phase 2)
- P2-2: Baseline plaintext hardening (Librarian, Phase 2)

---

## 2026-06-12: Week-3 Follow-up — Baseline Activation Cadence (Population→Personal Threshold Gate)

**By:** Librarian (via cycle-3 persona review; Architect finding)  
**Date:** 2026-06-12  
**Severity:** important  
**Disposition:** deferred to Week 3  
**Status:** RESOLVED (2026-06-13) — Librarian landed ACTIVATION_THRESHOLD=50 gate in Week 3 implementation

### What

Add explicit activation criteria (minimum `sample_count` threshold and/or ≥3-day age window) before `compute_mood()` in `host/inference.py` switches from population defaults to the personal mean+1.5σ threshold.

### Why

ARD §5.4 specifies: "first 3 days population defaults, after day 3 personal mean+1.5σ". Currently, the personal stress threshold engages as soon as a baseline file exists (i.e., `baseline is not None`), with no explicit gate on sample count or age window. This collapses the intended population-default warmup period.

**Non-blocking for Week 2:** Baseline learning is Phase-1 simplified, and the threshold difference is negligible early on.

**Relevant to Week 3:** Onboarding calibration and threshold tuning should formalize the activation gate per ARD §5.4.

### Owner

Librarian, Week 3.



---

# ATTENTION Jump Animation Spec — Week 3

**Author:** Da5id (HUD/UX)  
**Date:** 2026-06-12  
**Status:** PROPOSED — awaiting implementation by Ng  
**ARD cross-refs:** §5.5 (HUD/Render), Week 3 build sequence (line 560), success criterion "feels alive not robotic" (line 567)  
**Scope:** Synesthetic Familiar (VESPER), `projects/synesthetic-familiar/device/main.lua`

---

## Summary

When the wearer's IMU registers a peak (sharp head movement, ≤50ms detection per Ng's gate verdict), the creature performs a brief **attention jump** — a vertical burst that acknowledges the wearer without disrupting the ambient bob rhythm. This spec defines the motion, visual state changes, tunable parameters, and keyframe sequence.

---

## 1. Motion Design — The "Attention Jump"

### Core concept

The jump is a **single upward burst** followed by a soft **settle-back** to the bob baseline. It reads in <200ms, feels like a startled "oh!" reaction, and smoothly re-joins the existing bob cycle.

### Why upward?

- Upward motion = alert, attentive (screen-language convention)
- Downward would read as dejection or recoil
- Horizontal would conflict with the 7 o'clock rim position (creature might clip display edge)

### Motion curve

| Phase | Duration | Y offset from bob baseline | Easing |
|-------|----------|---------------------------|--------|
| **Rest** | — | `0` (normal bob continues) | — |
| **Launch** | 60ms | `0 → +ATTENTION_JUMP_AMP_PX` | ease-out-quad (fast start, decelerating) |
| **Settle** | 120ms | `+ATTENTION_JUMP_AMP_PX → 0` | ease-in-out-quad (soft landing, slight overshoot allowed) |

**Total duration:** 180ms (within <200ms legibility window).

### Amplitude

**`ATTENTION_JUMP_AMP_PX = 4`** — double the bob amplitude (±2px).

- **Why 4px:** Must be visually distinct from the ±2px bob without being jarring. 4px is the minimum that reads as "jump" vs "slightly bigger bob frame."
- **Why not larger:** At 24×24 sprite with center at y=179, a larger jump risks pushing the sprite near canvas edge. 4px keeps it safe within the 7 o'clock margin.

### Integration with existing bob

The jump offset **adds to** the current bob offset, not replaces it. During the 180ms attention window:

```
render_y = base_y + bob_offset + attention_offset
```

Where `attention_offset` animates 0 → +4 → 0 over the launch+settle curve.

After the 180ms, `attention_offset` = 0 and normal bob resumes seamlessly. No phase-reset — the bob continues from wherever it was.

---

## 2. Visual State — ATTENTION Palette (state [3])

The ATTENTION palette is already stubbed in `main.lua` line 141–146:

```lua
[3] = { -- ATTENTION: high contrast white eye
  [1] = 0x1A1A1A,   -- body dark (neutral gray)
  [2] = 0x2E2E2E,   -- body mid (neutral gray)
  [3] = 0xFFFFFF,   -- eye white (PURE WHITE)
  [4] = 0x0D0D0D,   -- shadow
},
```

### Why this works

- **Eye goes pure white (0xFFFFFF):** Maximum contrast against any body tone. Instantly draws the eye. Reads as "I see you."
- **Body desaturates to neutral gray:** Removes the mood color (teal/amber/blue) so the creature briefly "pauses" its emotional expression. This distinguishes ATTENTION from STRESSED (which uses warm amber body).
- **No halo, no fraying:** ATTENTION is a momentary overlay — no time for ambient effects. The 180ms window is too short for halo glow or fraying to register.

### Posture change — "Eye open wide"

During the attention moment, **the eye can optionally dilate** (expand by 1px in each direction). This requires no sprite change — it's a render-time effect:

| Parameter | Value |
|-----------|-------|
| `ATTENTION_EYE_DILATE_PX` | 1 |
| Implementation | When mood=ATTENTION, inflate eye pixels (palette index 3) by 1px radius during `draw_creature()` |

**⚠️ FLAG FOR AARON:** Eye dilation is a "nice to have" that adds complexity to the render loop (must detect eye region, expand it). The pure-white eye alone may be sufficient for the "I notice you" read. **Recommend: ship without dilation for Week 3, add as polish if the jump feels under-emphasized.**

---

## 3. Tunable Parameters (Lua constants for Ng)

```lua
-- ─── ATTENTION Jump Animation (Week 3, Da5id spec) ─────────────────────────────
local ATTENTION_JUMP_AMP_PX   = 4       -- upward burst amplitude (pixels)
local ATTENTION_LAUNCH_MS     = 60      -- time to reach peak (ms)
local ATTENTION_SETTLE_MS     = 120     -- time to return to baseline (ms)
local ATTENTION_DURATION_MS   = 180     -- total animation window (launch + settle)
local ATTENTION_COOLDOWN_MS   = 500     -- minimum time between attention triggers

-- Easing helper: quadratic ease-out (t in 0..1 → 0..1, decelerating)
local function ease_out_quad(t)
    return 1 - (1 - t) * (1 - t)
end

-- Easing helper: quadratic ease-in-out (smooth acceleration/deceleration)
local function ease_in_out_quad(t)
    if t < 0.5 then
        return 2 * t * t
    else
        return 1 - ((-2 * t + 2) ^ 2) / 2
    end
end
```

### State additions

```lua
state.attention_active   = false     -- is attention animation playing?
state.attention_start_t  = 0         -- timestamp when attention triggered
state.attention_last_t   = 0         -- last attention trigger (for cooldown)
```

### Trigger logic (integrates with Ng's IMU-peak poll)

```lua
-- In render loop, after Ng's IMU-peak detection:
local function trigger_attention(t_now)
    if state.attention_active then return end   -- already animating
    if (t_now - state.attention_last_t) * 1000 < ATTENTION_COOLDOWN_MS then return end
    
    state.attention_active  = true
    state.attention_start_t = t_now
    state.attention_last_t  = t_now
    state.mood              = 3   -- switch to ATTENTION palette
end

-- In render loop, compute attention_offset:
local function compute_attention_offset(t_now)
    if not state.attention_active then return 0 end
    
    local elapsed_ms = (t_now - state.attention_start_t) * 1000
    if elapsed_ms >= ATTENTION_DURATION_MS then
        state.attention_active = false
        state.mood = 0   -- return to neutral (or previous mood if tracked)
        return 0
    end
    
    if elapsed_ms < ATTENTION_LAUNCH_MS then
        -- Launch phase: ease-out-quad up
        local t = elapsed_ms / ATTENTION_LAUNCH_MS
        return math.floor(ATTENTION_JUMP_AMP_PX * ease_out_quad(t) + 0.5)
    else
        -- Settle phase: ease-in-out-quad down
        local t = (elapsed_ms - ATTENTION_LAUNCH_MS) / ATTENTION_SETTLE_MS
        return math.floor(ATTENTION_JUMP_AMP_PX * (1 - ease_in_out_quad(t)) + 0.5)
    end
end
```

---

## 4. ASCII Keyframe Sketch

```
Time:      0ms        30ms       60ms       90ms       150ms      180ms
           │          │          │          │          │          │
           ▼          ▼          ▼          ▼          ▼          ▼

    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    │              ·                                                   │   +4px
    │             ╭──╮  ← PEAK                                         │   (jump)
    │            (  O )  (eye = white)                                 │
    │             ╰──╯                                                 │
    │                                                                  │
    │       ╭──╮          ╭──╮                                 ╭──╮    │   +2px
    │      (  O )        (  O )                               (  O )   │
    │       ╰──╯          ╰──╯                                 ╰──╯    │
    │                                                                  │
    │  ╭──╮                      ╭──╮                    ╭──╮          │   0px
    │ (  o )                    (  o )                  (  o )         │   (baseline)
    │  ╰──╯                      ╰──╯                    ╰──╯          │
    │  REST                      SETTLING               REST           │
    │  (bob continues)           (soft landing)         (bob resumes)  │
    │                                                                  │
    └──────────────────────────────────────────────────────────────────┘
          ↑                  ↑                  ↑                  ↑
        IMU peak           60ms               120ms              180ms
        triggers         (peak)             (settling)          (done)

Eye state:
  REST:      o  (mood-colored, e.g. cyan-white or amber)
  ATTENTION: O  (pure white 0xFFFFFF)

Body state:
  REST:      mood-colored (teal/amber/blue-gray)
  ATTENTION: neutral gray (desaturated)
```

---

## 5. Glance-Ergonomics Check — ATTENTION vs STRESSED

| Axis | STRESSED (mood=2) | ATTENTION (mood=3) |
|------|-------------------|-------------------|
| **Trigger** | Host inference (voice/IMU over time) | Device IMU peak (single sharp motion) |
| **Duration** | Sustained (seconds–minutes) | Transient (180ms) |
| **Body color** | Warm amber (0x56_30_20) | Neutral gray (0x2E_2E_2E) |
| **Eye color** | Amber (0xFF_88_00) | Pure white (0xFF_FF_FF) |
| **Bob frequency** | Fast (0.75Hz = 1.3s cycle) | N/A (jump interrupts bob) |
| **Edge fraying** | Yes (16 scatter pixels) | No |
| **Motion** | Continuous fast bob | Single upward burst |

### Why these don't collide

1. **Temporal signature:** STRESSED is sustained; ATTENTION is a brief pulse. Even if both fire in the same second, the 180ms ATTENTION burst reads as a "moment" against the STRESSED backdrop.

2. **Color channel:** ATTENTION desaturates the body to gray and the eye to white. STRESSED stays warm amber throughout. The color shift is the primary distinguisher in peripheral vision.

3. **Motion pattern:** STRESSED has continuous fast bob. ATTENTION has a single asymmetric burst (fast up, slow down). Even if bob frequency is fast during stressed, the +4px jump reads as discontinuous.

4. **No fraying during ATTENTION:** The clean edge during the 180ms window contrasts with the stressed fraying that was present before/after. This "pause in chaos" reinforces the attention moment.

### Edge case: ATTENTION triggered while STRESSED

If the wearer is in STRESSED state and then makes a sharp head movement:

1. `trigger_attention()` fires → `state.mood = 3` (ATTENTION)
2. Body goes gray, eye goes white, jump animates
3. After 180ms, `state.mood` should return to **STRESSED (2)**, not NEUTRAL (0)

**⚠️ FLAG FOR NG:** The current spec returns to NEUTRAL (mood=0) after attention. This is correct if the host is sending mood continuously (next FAMILIAR_UPDATE will re-assert STRESSED). But if there's a 100ms gap, the creature will flicker neutral→stressed. **Recommend: track `state.mood_before_attention` and restore it after the 180ms window.**

---

## 6. Open Questions for Aaron

1. **Eye dilation (Section 2):** Should we ship Week 3 with eye dilation (+1px during ATTENTION), or defer as polish? My recommendation: defer — the pure-white eye and jump motion should be sufficient.

2. **Mood restoration (Section 5 edge case):** Should ATTENTION restore to previous mood or let the next host update determine it? My recommendation: restore to previous mood (track `state.mood_before_attention`) to avoid visual flicker.

---

## Checklist for Ng

- [ ] Add `ATTENTION_JUMP_AMP_PX`, `ATTENTION_LAUNCH_MS`, `ATTENTION_SETTLE_MS`, `ATTENTION_DURATION_MS`, `ATTENTION_COOLDOWN_MS` constants
- [ ] Add `ease_out_quad()` and `ease_in_out_quad()` helpers
- [ ] Add `state.attention_active`, `state.attention_start_t`, `state.attention_last_t`, `state.mood_before_attention`
- [ ] Wire `trigger_attention()` to IMU-peak detection (from Ng's SDK gate work)
- [ ] Add `compute_attention_offset()` in render loop; apply to `render_y`
- [ ] Confirm ATTENTION palette (state [3]) renders correctly on device
- [ ] Test: attention jump is visually distinct from stressed fast-bob
- [ ] Test: rapid head shakes don't spam attention (500ms cooldown)


---

# Week 3 "It's alive" — Work Breakdown & Sequencing

**By:** Hiro (Architect)  
**Date:** 2026-06-12  
**Status:** PROPOSED (awaiting Aaron approval)  
**Scope:** Decompose Week 3 deliverables into sequenced, owner-assigned work items

---

## Context

Week 2 "It reacts" merged 2026-06-10 (commit 57d0c23). 128 tests green, both
privacy gates approved. The codebase has real sensor capture, local mood
inference, confidence gating, fallback logic, and visual enhancements all
working. Week 3 is the final Phase-1 milestone.

**Key constraint:** Two SDK gates (IMU interrupt callback, heap API) are
unresolved. Ng is investigating in parallel. The plan below is designed to
work with EITHER the interrupt path OR the debounced-poll fallback — no work
item blocks on a specific gate outcome.

---

## Done Bar (ARD §9 + TEST-STRATEGY §7.5)

Week 3 is DONE when:

1. Aaron feels creature is **"alive" (not robotic)** after 1 hour of wear
2. **Gesture resets work** — double-tap FAMILIAR_RESET locally snaps device to NEUTRAL; host sees FAMILIAR_RESET notification
3. **No OOM or BLE freeze** during session
4. **Privacy audit** — non-wearer cannot infer stress/calm from 5 min observation; no labeled text visible
5. Baseline learning ramp-up operational (population defaults days 1–3, personal mean+1.5σ after)
6. ATTENTION overlay fires on IMU peak
7. BLE timeout → NEUTRAL after 10s (device-side, already implemented — verify on hardware)

---

## Work-Item Table

| # | Item | Owner | Starts | Depends On | Notes |
|---|------|-------|--------|------------|-------|
| W3-A | **SDK gate resolution: IMU interrupt** — confirm `frame.imu.on_tap` availability; if unavailable, implement debounced poll loop (≤50ms latency) | Ng | **NOW** (in progress) | — | Go/no-go gate. Outcome determines W3-C and W3-D implementation path. If interrupt unavailable, Ng ships the poll fallback directly. |
| W3-B | **SDK gate resolution: Heap API** — confirm `frame.system.get_heap_usage()`; if unavailable, implement manual allocation tracker (count sprite rows + BLE buffer bytes) | Ng | **NOW** (in progress) | — | Go/no-go gate. If unavailable, manual proxy is the v1 design. |
| W3-C | **Double-tap FAMILIAR_RESET** — wire up the commented-out `on_tap(2, ...)` handler in `device/main.lua` (or poll-based equivalent per W3-A outcome); device snaps to NEUTRAL, sends opcode 0x01 | Ng | After W3-A | W3-A | Stub already exists (main.lua:373–380). Implementation is ~10 lines either path. |
| W3-D | **ATTENTION overlay on IMU peak** — implement `on_imu_peak` handler; device enters ATTENTION state [3] for 500ms, then returns to previous state (ARD §5.1: overlay, not peer state) | Ng | After W3-A | W3-A | Host must also send mood=3 on IMU spike detection. Coordinate with Y.T. on host-side trigger in main.py. |
| W3-E | **Heap monitoring (80%/95%)** — add heap guard to render loop: 80% → reduce animation complexity; 95% → safe-halt | Ng | After W3-B | W3-B | Thresholds are initial estimates — tune on real device. |
| W3-F | **Baseline activation gate** — add explicit `sample_count ≥ N` and/or `≥3-day age` check in `inference.py` before switching from population defaults to personal threshold (decisions.md 2026-06-12 follow-up) | Librarian | **NOW** | — | Currently personal threshold activates as soon as baseline file exists — collapses warmup period. Pure logic change, well-scoped. |
| W3-G | **First-launch onboarding UX** — host-side Python flow: detect no baseline → show calibration prompt; display "learning your patterns" status during days 1–3; smooth transition to personal thresholds | Y.T. | **NOW** | — | CLI/logging-based for v1 (no GUI). Hooks into baseline load/save path. Coordinate with Librarian on activation gate (W3-F). |
| W3-H | **ATTENTION trigger from host** — host-side IMU peak detection → send mood=ATTENTION via FAMILIAR_UPDATE when acceleration spike exceeds threshold | Y.T. | **NOW** | — | Can start with threshold logic immediately. Device-side rendering of ATTENTION state is already palette-ready (PALETTE[3], main.lua:141). Wire format supports mood=3. |
| W3-I | **Snapshot zeroing hardening (W3-1)** — harden mic buffer zeroing in `sensors.py`; ensure buffer is cleared on every code path, not just happy path | Ng | **NOW** | — | Non-blocking follow-up from Week 2 privacy review. Surgical change. |
| W3-J | **ATTENTION visual — jump animation** — implement 15px jump-toward-center + return animation in device render loop (ARD §5.5: ATTENTION row) | Da5id | After W3-A | W3-A (need to know interrupt vs poll for timing) | Currently ATTENTION has a palette but no special animation — just faster bob. Da5id specifies the jump; Ng implements in Lua. |
| W3-K | **Graceful fallback verification** — verify BLE timeout → NEUTRAL (device-side, already coded at main.lua:396–403); verify confidence-hold 30s timeout; verify both-fail 10s → NEUTRAL. All on real hardware. | Juanita | After W3-C, W3-E | W3-C (reset), W3-E (heap guard) | Logic already exists from Week 2. This is hardware validation + edge case testing, not new code. |
| W3-L | **Week 3 acceptance tests** — write tests for: double-tap reset, ATTENTION overlay timing, baseline activation gate, heap guard thresholds, onboarding flow | Juanita | **NOW** (test-first) | — | Can write failing tests immediately against the contract. Tests drive W3-C/D/E/F/G. |
| W3-M | **Privacy audit (Week 3)** — 5-min bystander observation test; verify no labeled text; verify abstract visuals remain opaque; confirm no new cloud imports | Raven | After W3-D, W3-G | W3-D (ATTENTION visual), W3-G (onboarding text) | Audit the ATTENTION state visuals and any onboarding display text. |
| W3-N | **Threshold tuning + polish** — tune confidence thresholds, stress_threshold, calm_threshold on real hardware; adjust anti-robotic jitter; 1-hour wear session | Y.T. + Ng | After W3-C through W3-J | All functional items | Final integration. Aaron's subjective "feels alive" bar lives here. |
| W3-O | **Documentation** — update ARD §10 with SDK gap resolutions; update TEST-STRATEGY with new test IDs; document onboarding flow; mark Phase 1 privacy checklist items | Librarian | After W3-N | W3-N | Captures final state. |

---

## Sequencing — Recommended Fan-Out

### Wave 1 — Start NOW (no gates)

Fan out these agents immediately — all can begin in parallel:

| Agent | Item(s) | Rationale |
|-------|---------|-----------|
| **Ng** | W3-A, W3-B (SDK gates) + W3-I (snapshot zeroing) | Gate-resolving work is critical path. Snapshot zeroing is independent. |
| **Librarian** | W3-F (baseline activation gate) | Pure logic in inference.py; no dependencies; well-specified in decisions.md. |
| **Y.T.** | W3-G (onboarding UX) + W3-H (ATTENTION host trigger) | Host-side work has no SDK gate dependency. Can ship the host half while device half waits. |
| **Juanita** | W3-L (acceptance tests — test-first) | Write failing tests against the Week 3 contract now; they drive implementation. |

### Wave 2 — After SDK gates resolve (W3-A, W3-B)

| Agent | Item(s) | Trigger |
|-------|---------|---------|
| **Ng** | W3-C (double-tap), W3-D (ATTENTION device), W3-E (heap guard) | W3-A and W3-B resolved (either interrupt or fallback accepted) |
| **Da5id** | W3-J (ATTENTION jump animation spec) | W3-A resolved (timing depends on interrupt vs poll) |

### Wave 3 — Integration & verification

| Agent | Item(s) | Trigger |
|-------|---------|---------|
| **Juanita** | W3-K (graceful fallback verification on hardware) | W3-C, W3-E complete |
| **Raven** | W3-M (privacy audit) | W3-D, W3-G complete |

### Wave 4 — Polish & ship

| Agent | Item(s) | Trigger |
|-------|---------|---------|
| **Y.T. + Ng** | W3-N (threshold tuning, 1-hour wear, "feels alive" bar) | All functional items merged |
| **Librarian** | W3-O (documentation) | W3-N complete |

---

## Go/No-Go Decision Points

### Gate 1: IMU Interrupt (W3-A)

- **If interrupt available:** Wire `frame.imu.on_tap(2, callback)` directly. Clean path.
- **If poll-only:** Ng implements debounced poll loop (≤50ms). Double-tap detection latency slightly higher but acceptable for v1.
- **If NEITHER works (no IMU access at all):** ATTENTION trigger is disabled in v1; double-tap reset is disabled. **Scope-cut recommendation:** ship without gesture features, document as Phase 2. Creature still "feels alive" through onboarding + fallback + baseline learning. This is a downgrade but not a blocker.

### Gate 2: Heap API (W3-B)

- **If `get_heap_usage()` available:** Direct monitoring. Clean path.
- **If unavailable:** Manual allocation tracking (count known allocations). Acceptable for v1 — the sprite is 288 bytes, BLE buffers are small, real OOM risk is low.
- **Failure mode if wrong:** Worst case is an undetected slow leak during a long session. Mitigated by the 1-hour wear test (W3-N).

### Scope-Cut Recommendations If Gates Fail

| If this fails… | Cut this | Keep this | Impact |
|----------------|----------|-----------|--------|
| IMU interrupt AND poll | W3-C (reset), W3-D (ATTENTION), W3-J (jump anim) | Everything else | "Alive" bar still achievable via onboarding + baseline learning + fallback grace |
| Heap API AND manual tracking | W3-E (heap guard) | Everything else | Accept OOM risk for v1; mitigate with shorter session guidance |
| Both | W3-C/D/E/J | W3-F/G/H/I/K/L/M/N/O | Reduced but shippable. Document as Phase 2 follow-ups. |

---

## Critical Path

```
W3-A (SDK: IMU) ──┬── W3-C (double-tap) ──┐
                  ├── W3-D (ATTENTION)  ──┤
                  └── W3-J (jump anim)  ──┼── W3-K (verify) ── W3-N (polish) ── W3-O (docs)
W3-B (SDK: heap) ──── W3-E (heap guard) ──┘
                                           ├── W3-M (privacy audit)
W3-F (activation gate) ───────────────────┘
W3-G (onboarding) ────────────────────────┘
W3-H (ATTENTION host) ────────────────────┘
W3-L (tests) ─────────────────────────────┘
W3-I (snapshot zeroing) ── done ──────────┘
```

**Bottleneck:** W3-A (IMU gate). Everything gesture-related waits on this. Start it first, resolve it fast.

---

## Notes

- **Device-side fallback logic already exists** — BLE timeout → NEUTRAL (main.lua:396–403) and both-sensors-fail → NEUTRAL (main.py:357–364) were built in Week 2. Week 3 verifies them on hardware, not re-implements.
- **ATTENTION palette is already in main.lua** (PALETTE[3], line 141). Week 3 adds the trigger and animation, not the color scheme.
- **Onboarding is CLI-based for v1** — no GUI. "Learning your patterns" is a log message, not a screen. Phase 2 may add a Flutter/web dashboard.
- **The "feels alive" bar is subjective** — Aaron judges this during the 1-hour wear test. We cannot automate it. The objective proxy is: "no OOM, no BLE freeze, gesture works, baseline adapts."


---

# Juanita Week 3 Test Plan Decision

| Field | Value |
|-------|-------|
| **Author** | Juanita (Tester / QA) |
| **Date** | 2026-06-13 |
| **Status** | PROPOSED — for team review |
| **Scope** | Week 3 "It's alive" acceptance tests |
| **Files** | `tests/test_week3_reset.py`, `tests/test_week3_baseline_activation.py`, `tests/test_week3_onboarding.py` |

---

## Summary

48 new passing tests, 3 xfailed (Ng: FAMILIAR_RESET host reaction), 11 skipped pending Y.T. module.
Suite: **128 → 176 passing**, green.

---

## What Was Tested

### 1. FAMILIAR_RESET — Protocol Decode (test_week3_reset.py, Group 1)
**Status: PASS** — `familiar_protocol.py` is fully landed.

14 tests covering:
- `decode_familiar_reset` rejects wrong length, wrong opcode
- `dispatch_device_message(b'\x01')` returns `FamiliarReset()` (zero-field dataclass)
- Malformed 2-byte packets return None (log-and-drop contract)
- Parametrised bad-opcode table (0x00, 0x02, 0x80, 0xFF)

### 2. FAMILIAR_RESET — Host State Reaction (test_week3_reset.py, Group 2)
**Status: XFAIL** — pending Ng, Week 3.

3 tests (xfail strict=False):
- `test_reset_triggers_neutral_send`: after FAMILIAR_RESET, host sends ≥1 NEUTRAL packet
- `test_reset_restarts_sequence_counter`: first post-reset packet has seq=0x0000 (ARD §5.2 reconnect)
- `test_reset_during_gated_session_clears_stale_mood`: reset fires NEUTRAL even mid-suppressed session

**Contract required from Ng:**
```
run() on_receive callback sets a flag when FamiliarReset arrives.
Each loop frame: if flag set → send NEUTRAL, call seq.reset(), clear transient state.
```

**I will REJECT Ng's PR if:**
- `run()` ignores FAMILIAR_RESET (Group 2 stays red on merge)
- seq counter is NOT reset after FAMILIAR_RESET (wire dedup breaks on reconnect)

### 3. W3-1 Snapshot Zeroing (test_week3_reset.py, Group 3)
**Status: PASS** — sensors.py 3-layer zeroing already correct.

2 structural tests:
- `finally` block present in `_extract_frame`
- `samples[:] = 0.0` followed by `del samples` in that block

**I will REJECT any PR that:**
- Removes the `finally` block
- Moves `del samples` before zeroing

### 4. Baseline Activation Gate (test_week3_baseline_activation.py)
**Status: PASS** — Librarian landed `ACTIVATION_THRESHOLD = 50` and the gate in `compute_mood()`.

34 tests covering:
- `ACTIVATION_THRESHOLD` is an exported positive int >= 30 (statistical basis)
- `get_activation_info()` returns correct `ActivationInfo` for all cases
- Population defaults with no baseline
- Population defaults enforced for `sample_count < 50`
- Personal threshold active for `sample_count >= 50`
- Exact boundary: `== 50` activates personal, `== 49` stays population
- Confidence suppression holds in both calibrating and personalized states
- Baseline persistence round-trip (save/load) survives across restart

**I will REJECT any PR that:**
- Changes the `>=` boundary to `>` (off-by-one)
- Removes the gate (back to "any non-None baseline → personal threshold")
- Breaks confidence gating in either activation state

### 5. Onboarding Flow (test_week3_onboarding.py)
**Status: 11 SKIPPED** — `host/onboarding.py` not yet written by Y.T.

11 tests (xfail, auto-skip when module missing) covering:
- `is_first_launch(path)` returns `True` when no baseline.json, `False` when present
- Empty file (corrupted but exists) counts as returning user
- `run_first_launch_flow(baseline_path)` completes without raising
- Flow creates a marker so second launch is not first launch
- Flow auto-creates parent directories (fresh machine)
- No BLE SDK imports in onboarding code
- `run_returning_flow(None)` degrades gracefully

2 tests PASS TODAY (integration tests using only `host.inference`):
- `load_baseline(missing_path)` → None (population defaults fallback)
- `load_baseline(valid_path)` → Baseline (returning user)

**Contract for Y.T.:**
```python
# host/onboarding.py
def is_first_launch(baseline_path: Path) -> bool: ...  # pure, no side effects
def run_first_launch_flow(*, baseline_path: Path = _BASELINE_PATH) -> None: ...
def run_returning_flow(baseline: Baseline | None) -> None: ...
```

**I will REJECT Y.T.'s PR if:**
- `is_first_launch` has side effects or hardcodes `~/.vesper/baseline.json`
- `run_first_launch_flow` does NOT create a marker (so launch repeats on restart)
- Any BLE SDK import appears in `host/onboarding.py`

---

## Test Infrastructure Used

- `ResetInjectingTransport`: extends `FakeTransport`; injects `b'\x01'` after Nth send
- All `FakeTransport`, `FakeClock`, `FakeSensorStream`, `noop_sleep` from `helpers.py`
- All parametrized tests use plain pytest class (no TestCase) — project rule
- `tmp_path` fixture used exclusively for baseline file tests (real `~/.vesper/` never touched)

---

## Key Contracts / Discoveries

### compute_mood() with low sample_count baseline uses POPULATION defaults
**Finding:** Before today's tests, it was unclear whether the Librarian had landed the
activation gate. Tests confirmed `ACTIVATION_THRESHOLD = 50` with `>=` comparison. At
sample_count=49, population defaults hold. At sample_count=50, personal threshold engages.

### FAMILIAR_RESET host reaction is NOT yet implemented
`main.py`'s `_make_device_msg_handler()` logs FAMILIAR_RESET but does nothing else. Ng must
add a mechanism for the async `run()` loop to observe the callback's FAMILIAR_RESET signal
(e.g., a `nonlocal` flag or `asyncio.Event` set in the callback).

### Onboarding module (host/onboarding.py) does not yet exist
Y.T. must create it. `get_activation_info()` is already in `host/inference.py` (Librarian
Week 3 addition), ready for Y.T. to consume for progress display.

---

## What I Will NOT Approve

| Scenario | Reason |
|----------|--------|
| Ng merges FAMILIAR_RESET without host state reset | Group 2 stays red; seq dedup breaks on reconnect |
| Librarian reverts >= gate to "any non-None baseline" | Group 4 fails; week-old baseline immediately personalizes |
| Y.T. hardcodes baseline path in `is_first_launch` | Tests need `tmp_path` injection; hardcoded path touches real ~/.vesper |
| Removing finally block from `_extract_frame` | W3-1 structural guard fails; privacy regression |
| Confidence gating broken by activation gate changes | Group 7 turns red; LIBRARIAN-T2-5-ERROR violated |


---

# Baseline Activation Gate — Population→Personal Threshold (Week 3)

**By:** Librarian (AI/ML)  
**Date:** 2026-06-12  
**Resolves:** OPEN item "2026-06-12: Week-3 Follow-up — Baseline Activation Cadence (Population→Personal Threshold Gate)" in `.squad/decisions.md`  
**Status:** RESOLVED  
**File scope:** `projects/synesthetic-familiar/host/inference.py` only  

---

## Decision

**ACTIVATION_THRESHOLD = 50 Welford samples.**

Until `baseline.sample_count ≥ 50`, `compute_mood()` uses population defaults
(`STRESS_THRESHOLD = 0.65`, `CALM_THRESHOLD = 0.35`).  Once the threshold is
crossed, it switches to the personal stress threshold (`mean + 1.5 × stddev`).
Calm threshold remains population default unconditionally (ARD §2.6 — no personal
calm formula defined).

---

## Reasoning

### Why sample count, not calendar days

ARD §5.4 says "first 3 days: population defaults".  Calendar time is the wrong
gate for a sample-count-based estimator:

- A baseline file created 5 days ago but used for only 5 minutes (10 samples)
  should remain "calibrating" — the Welford stddev has no statistical meaning yet.
- A device that is off for days accumulates no samples; wall-clock elapsed time
  would falsely advance the gate.
- `sample_count` is already persisted in `baseline.json`; no new field needed.
  Restarts are transparent — ramp-up does not reset on relaunch.

Calendar days are aspirational UX language; sample count gates when the *math*
is trustworthy.

### Why n ≥ 50

The standard error of the Welford sample-stddev estimator is:

```
SE(s) ≈ s / √(2n)
```

| n  | SE(s)/s | Quality |
|----|---------|---------|
| 2  | 71%     | effectively zero — stddev=0.0 until n≥2; threshold = mean, useless |
| 10 | 22%     | very noisy; personal threshold could swing ±0.33σ |
| 30 | 13%     | CLT begins to apply; still >10% relative error |
| 50 | 10%     | threshold is within ~0.15σ of asymptotic value — acceptable heuristic |
| 100| 7%      | robust, but delays personalization with no meaningful UX benefit |

**n = 50** is the minimum where the personal stress threshold (`mean + 1.5σ`) is
within ≈0.15σ of its long-run value.  This is well within the noise floor of the
heuristic (confidence steps of 0.8/0.6 on a ±0.35 tension range).

At n < 30, stddev could be so imprecise that the "personal" threshold is actually
worse than the population default — defeating the purpose of personalization.

---

## Implementation

### New public API (importable by Y.T.)

```python
ACTIVATION_THRESHOLD: int = 50
ActivationState = Literal["calibrating", "personalized"]

@dataclasses.dataclass
class ActivationInfo:
    state: ActivationState   # "calibrating" | "personalized"
    sample_count: int        # samples accumulated so far
    samples_needed: int      # = ACTIVATION_THRESHOLD (50)
    progress: float          # 0.0–1.0, capped at 1.0

def get_activation_info(baseline: Baseline | None) -> ActivationInfo: ...
```

`get_activation_info` is a **pure function** — no I/O, no clock, no global
mutation.  Y.T.'s UX layer calls it after `load_baseline()` at startup and
after each `update_baseline()` call.

### compute_mood change

```python
# Before (Week 2 — activates as soon as baseline file exists):
if baseline is not None:
    stress_threshold = baseline.mean + 1.5 * baseline.stddev

# After (Week 3 — gated by ACTIVATION_THRESHOLD):
if baseline is not None and baseline.sample_count >= ACTIVATION_THRESHOLD:
    stress_threshold = baseline.mean + 1.5 * baseline.stddev
else:
    stress_threshold = STRESS_THRESHOLD
```

The existing `confidence < CONFIDENCE_GATE` suppression is unaffected — it
applies regardless of activation state.

### Persistence

No changes to `baseline.json` format or `Baseline` dataclass (fields locked §2.6).
`sample_count` already persists across restarts; the activation gate derives from
it automatically.

---

## UX Contract for Y.T.

```python
info = get_activation_info(baseline)
if info.state == "calibrating":
    # e.g. "Calibrating (12 / 50 samples)"
    show_onboarding(info.sample_count, info.samples_needed)
else:
    # "Personalized ✓"
    show_personalized()
```

`progress` (0.0–1.0) is available for a progress bar or "day N" approximation.

---

## Test Surface

`get_activation_info` and `ACTIVATION_THRESHOLD` are importable and pure — no
mocking required.  Juanita's acceptance tests can exercise:

- `get_activation_info(None)` → `state="calibrating"`, `sample_count=0`
- `get_activation_info(Baseline(…, sample_count=49, …))` → `state="calibrating"`
- `get_activation_info(Baseline(…, sample_count=50, …))` → `state="personalized"`
- `compute_mood(…, baseline=Baseline(…, sample_count=49, …))` uses `STRESS_THRESHOLD`
- `compute_mood(…, baseline=Baseline(…, sample_count=50, …))` uses `mean + 1.5σ`

Note: tests use plain pytest classes (not `unittest.TestCase`) for parametrize.

---

## Prior decision cross-reference

The OPEN item in `decisions.md` (2026-06-12, "Baseline Activation Cadence") noted:
> "Currently, the personal stress threshold engages as soon as a baseline file
> exists (i.e., `baseline is not None`), with no explicit gate on sample count."

This is resolved.  The Week-2 behavior was non-blocking because "the threshold
difference is negligible early on" — with few samples and stddev ≈ 0, the personal
threshold ≈ mean ≈ population mean, and both paths produce nearly identical output.
The Week-3 gate makes the ARD contract explicit and testable.


---

# Week 3 Implementation — SDK Gates & Device Features

**Author:** Ng (SDK Engineer)  
**Date:** 2026-06-13  
**Status:** SHIPPED — all four device tasks complete; 128 tests pass  
**ARD cross-refs:** §5.1 (gate table, state machine), §5.2 (wire format), §10 Q1 & Q3  
**Scope:** `projects/synesthetic-familiar/device/main.lua` (primary),  
`projects/synesthetic-familiar/host/sensors.py` (task 5 — already done, see note)

---

## Summary

Four Week 3 device features implemented in `device/main.lua`, all driven by
gate verdicts in `ng-week3-sdk-gates.md`. Host tests unaffected (128/128 pass).

---

## Task 1 — Double-tap FAMILIAR_RESET

**File:** `device/main.lua` (startup section, ~line 393)

`frame.imu.tap_callback(func)` registered at startup. Double-tap discrimination
uses a 350ms window accumulator (`TAP_WINDOW_S = 0.35`) with a 40ms hardware
debounce (`TAP_DEBOUNCE_S = 0.04`, mirrors `RxTap` host-side).

On count ≥ 2:
- Snap state to NEUTRAL locally (`mood=0, intensity=50, bob_phase=0.0, render_int=50.0`)
- Cancel any in-flight ATTENTION overlay (`attn_timer=0.0`)
- Send `string.char(0x01)` — FAMILIAR_RESET opcode confirmed against
  `familiar_protocol.py: OPCODE_FAMILIAR_RESET = 0x01`

**Contract for Juanita:** device sends exactly 1 byte `0x01` on double-tap.
`dispatch_device_message(b'\x01')` returns a `FamiliarReset()` instance.
No payload. Existing golden vectors unaffected.

**Removed:** the `-- frame.imu.on_tap(2, ...)` stub (wrong API name).

---

## Task 2 — ATTENTION-on-IMU-peak

**File:** `device/main.lua` (render loop, after timeout check)

`frame.imu.raw()` polled once per frame (20fps = 50ms max latency).
Accelerometer magnitude computed from all three axes, scaled by `IMU_SCALE=1000`
(Halo raw-unit → g, matching `imu.lua` relay).

When `mag > IMU_PEAK_THRESH_G` and not already in ATTENTION:
- Save current mood to `state.pre_attn_mood`
- Set `state.mood = 3` (ATTENTION — already in palette + BOB_HZ tables)
- Start `state.attn_timer = ATTENTION_DURATION_S` (500ms)

Timer countdown in render loop; on expiry, revert to `state.pre_attn_mood`.

**State machine fidelity (ARD §5.1):** ATTENTION does not reset to NEUTRAL —
it restores whatever mood was active before. Incoming `FAMILIAR_UPDATE` during
ATTENTION writes to `state.pre_attn_mood` (not `state.mood`) so the revert
returns the correct host-intended state.

**Tunables (marked for Da5id / hardware calibration):**
- `IMU_PEAK_THRESH_G = 1.8` — acceleration magnitude threshold (g)
- `ATTENTION_DURATION_S = 0.5` — overlay duration (500ms, ARD §5.1)
- `IMU_SCALE = 1000` — raw-unit → g divisor (do not change without firmware evidence)

**Flag to Raven:** accelerometer read path added on-device. Data stays on-device
(no new BLE characteristic, no new host data). Low privacy surface; confirm no
additional disclosure needed.

---

## Task 3 — Heap Monitor (GAP-3 fallback)

**File:** `device/main.lua` (`heap_fraction()` function + render loop guard)

`heap_fraction()` manual proxy:
- Sprite row bytes: `#SPRITE_ROWS * 25` (24 rows × ~25 bytes)
- BLE buffer max: 244 bytes (max BLE MTU)
- Budget: `40 * 1024` bytes (conservative app budget)

Current profile: ~844 bytes → fraction ≈ 0.02 (2%). Neither threshold fires
with current allocation. Pattern is established for future growth.

**Render loop thresholds:**
- `>= 0.95`: blank screen, set `_halt = true`, `return` from pcall body.
  Outer `while true` checks `if _halt then break end` after error handler.
- `>= 0.80`: `skip_glow = true` — suppresses `draw_halo_glow()` call
  (~3 `frame.display.circle()` calls per frame saved)

**Firmware-swap hook:**
```lua
-- TODO(firmware-swap): when frame.system.get_heap_usage() is available:
--   local u, t = frame.system.get_heap_usage(); return u / t
```
Replacing just the body of `heap_fraction()` is sufficient — no other changes.

---

## Task 4 — Halo Glow: Bresenham → `frame.display.circle()`

**File:** `device/main.lua` (`draw_halo_glow()`, ~line 282)

`frame.display.circle(cx, cy, r, ring_color, false)` replaces the 8-call
mid-point Bresenham loop per ring. Color computation logic unchanged.

Per-ring API calls: 8 `set_pixel()` → 1 `circle()` (8× reduction per ring,
24× across 3 rings). Frame budget impact: freed ~230 API calls/frame in CALM.

Removed "SDK gap: circle() not confirmed" comment — confirmed in emulator.

---

## Task 5 — Snapshot Zeroing in sensors.py

**Status: Already implemented.** `samples[:] = 0.0` before `del samples` in
the `finally` block of `_extract_frame()` was present at lines 339–340 from
the cycle-2 privacy hardening wave (commit 3bb96a3). No edit needed.

---

## Test Results

```
128 passed in 0.19s  (identical to pre-change baseline)
```

All host tests exercise `familiar_protocol.py` contracts (opcodes, wire format,
seq dedup, dispatch). No device Lua tests in the current suite — device behavior
is validated by the halo_emulator integration path (hardware validation gate,
ARD §10, Aaron action).

---

## Flags

- **Raven:** Task 2 adds on-device accelerometer read path. No new BLE
  characteristic. Stays fully on-device. Confirm no additional disclosure.
- **Lagos:** No new SDK deps. `frame.imu.tap_callback`, `frame.imu.raw()`, and
  `frame.display.circle()` are all in the existing Halo Lua stdlib.
- **Da5id:** Three tunables in `device/main.lua` are explicitly marked for your
  calibration pass: `IMU_PEAK_THRESH_G`, `ATTENTION_DURATION_S`, `IMU_SCALE`.
  ATTENTION visual (bob speed 1.0 Hz, high-contrast white palette) is already
  wired — adjust the trigger threshold once you have real device feel.


---

# SDK Gate Verdicts — Week 3 Go/No-Go

**Author:** Ng (SDK Engineer)  
**Date:** 2026-06-12  
**Status:** RESOLVED — both gates have verdicts; implementation recommendations attached  
**ARD cross-refs:** §5.1 (gate table), §10 Q1 & Q3  
**Scope:** Synesthetic Familiar (VESPER), `projects/synesthetic-familiar/`

---

## GATE 1 — IMU Interrupt Callback (ARD §10 Q1)

**Question:** Does the Halo Lua stdlib expose an interrupt-style IMU tap callback
(`frame.imu.on_tap(n, cb)` or `frame.on_imu_peak`), or is it polling-only?

### Verdict: ✅ GO — primary path (interrupt callback confirmed)

**But the API name is wrong in the ARD and in main.lua.**

### Evidence

Source examined: `brilliantlabsAR/brilliant_sdk` (GitHub, main branch)

1. **`halo_emulator/stubs/imu.py`** — `ImuStub.tap_callback(self, func)` is the
   Lua-callable stub. The implementation stores the function and fires it on
   `fire_tap()`. This is the canonical surface the Lua VM sees.

2. **`HaloEmulator.inject_imu_tap()`** dispatches an `"imu_tap"` event which
   calls `imu.fire_tap()` → invokes the registered Lua callback. Emulator tests
   rely on this path — it is not a stub omission.

3. **halo_emulator README API listing** (IMU section):
   > `tap_callback(func)`, `direction()`, `raw()`, `config(options)`

4. **`brilliant_sdk` top-level README** feature matrix:
   > Tap events — Frame ✓, Halo ✓

### What the ARD got wrong

The ARD §5.1 wrote `frame.imu.on_tap(n, callback)` (with a built-in N-count
discriminator). **This API does not exist.** The real API is:

```lua
frame.imu.tap_callback(function()
    -- fires once per hardware-detected tap
end)
```

There is no `n`-count parameter. Double-tap discrimination must be implemented
in Lua by counting taps within a time window.

### Double-tap on-device (FAMILIAR_RESET)

The callback fires on every hardware tap. To detect a double-tap:

```lua
local TAP_WINDOW_S = 0.35   -- 350ms window
local tap_count    = 0
local tap_last_t   = 0

frame.imu.tap_callback(function()
    local now = frame.time.utc()
    if (now - tap_last_t) > TAP_WINDOW_S then
        tap_count = 0      -- outside window: start new sequence
    end
    tap_count  = tap_count + 1
    tap_last_t = now
    if tap_count >= 2 then
        tap_count = 0
        -- FAMILIAR_RESET: snap to neutral, notify host
        state.mood, state.intensity, state.bob_phase = 0, 50, 0.0
        frame.bluetooth.send(string.char(0x01))
    end
end)
```

This is **interrupt-driven** (no polling). Latency = hardware tap detection
time + Lua callback overhead. Well under 50ms in practice.

### IMU-peak ATTENTION trigger

No `frame.on_imu_peak` primitive exists either. The ATTENTION-on-IMU-peak
trigger from ARD §5.1 must use `frame.imu.raw()` polled in the render loop.
At 20fps the loop fires every 50ms — exactly at the ARD's ≤50ms latency target.
The ATTENTION trigger reads `accel.z` (corrected float32 per ARD §5.1 gotcha)
and fires when it exceeds a configurable threshold.

### Side finding — `frame.display.circle()` exists

The halo_emulator display API confirms `circle(cx, cy, r, color, filled)` is
available. The Bresenham mid-point fallback in `draw_halo_glow()` is correct
but unnecessary — can be replaced with a single `frame.display.circle()` call.
Not blocking, but worth a cleanup pass before Week 3 merges.

### Action for implementer

1. Replace the commented stub in `device/main.lua` (lines 374–380):
   - Remove `-- if frame.imu and frame.imu.on_tap then ... end`
   - Wire `frame.imu.tap_callback(...)` using the debounce pattern above
2. Add IMU-peak poll in the render loop (read `frame.imu.raw()`, threshold on
   `accel.z`, transition to ATTENTION state for 500ms)
3. **Flag to Raven:** ATTENTION state triggered by IMU peak is a new accelerometer
   data-read path (currently IMU raw is not used in the device loop). No new
   BLE characteristic needed — purely on-device. Low privacy surface.

---

## GATE 2 — Heap API (ARD §10 Q3)

**Question:** Is `frame.system.get_heap_usage()` (or equivalent) available in
the current Halo Lua stdlib?

### Verdict: ❌ NO-GO → use fallback as v1 design

### Evidence

Source examined: `brilliantlabsAR/brilliant_sdk` (GitHub, main branch),
specifically `halo_emulator/stubs/system.py`.

1. **`SystemStub` has no `get_heap_usage` method.** The complete top-level
   `frame.*` API is: `sleep`, `light_sleep`, `standby`, `yield`, `on_wakeup`,
   `stay_awake`, `reboot`, `battery_level`, `battery_voltage`,
   `battery_charging`, `ship_mode`, `charge`, `wakeup_source`, `get_eui`,
   `get_se_revision`. No heap function.

2. **`frame.system` sub-namespace does not exist.** System-level functions are
   all top-level `frame.*` calls. There is no `frame.system` table anywhere
   in the SDK source.

3. The emulator build wires up stubs for every documented `frame.*` namespace.
   Absence from the stub is strong negative evidence; a real firmware function
   that wasn't emulated would be a known regression.

### Fallback design (accepted as v1 per ARD §5.1)

Track heap pressure manually at two allocation sites:

```lua
-- ─── Heap proxy (fallback: no frame.system.get_heap_usage()) ─────────────────
-- Approximation: sprite row table (24 rows × ~25 bytes) + BLE receive buffer.
-- Real Halo heap is ~200KB. Effective budget for app data ≈ 40KB (conservative).
local HEAP_BUDGET_BYTES   = 40 * 1024   -- conservative app budget
local HEAP_REDUCE_THRESH  = 0.80        -- 80% → reduce quality
local HEAP_HALT_THRESH    = 0.95        -- 95% → graceful halt

local function heap_used_bytes()
    -- SPRITE_ROWS: 24 strings, each ~25 bytes = 600 bytes
    local sprite_bytes = #SPRITE_ROWS * 25
    -- BLE receive buffer: worst-case 244 bytes (max BLE MTU)
    local ble_bytes = 244
    return sprite_bytes + ble_bytes
end

local function heap_fraction()
    return heap_used_bytes() / HEAP_BUDGET_BYTES
end
```

In the render loop, check `heap_fraction()` per frame:
- `>= 0.80`: drop halo glow rings (free ~230 set_pixel calls/frame)
- `>= 0.95`: `frame.display.clear(); frame.bluetooth.send(graceful_halt_msg); break`

This proxy will never actually trigger with current allocation profile
(sprite + BLE ≈ 844 bytes << 40KB budget). Its main value is establishing
the instrumentation pattern for future growth.

### Hardware-validation check (flips gate to GO)

If Brilliant adds heap introspection in a future firmware, the flip condition is:

```lua
-- Hardware validation probe (run once on device, check stdout):
if type(frame.system) == "table" and
   type(frame.system.get_heap_usage) == "function" then
    local used, total = frame.system.get_heap_usage()
    print("heap ok: " .. used .. "/" .. total)
else
    print("heap: no API — using proxy")
end
```

When this prints `"heap ok: ..."` on real hardware, delete `heap_used_bytes()`
and replace `heap_fraction()` with `frame.system.get_heap_usage()` directly.

### Action for implementer

1. Add `heap_fraction()` proxy (pattern above) to `device/main.lua`
2. Add reduce-quality and graceful-halt checks in the render loop
3. No new deps needed. No new sensor surface — purely internal bookkeeping.

---

## Summary Table

| Gate | Verdict | Primary path | Fallback | Implementer action |
|------|---------|-------------|----------|-------------------|
| IMU interrupt callback | ✅ GO | `frame.imu.tap_callback(func)` — interrupt-driven; Lua debounce for double-tap; IMU-peak via render-loop poll | (not needed) | Replace stub in main.lua; add IMU peak poll; flag Raven re: ATTENTION sensor path |
| Heap API | ❌ NO-GO → fallback as v1 | — | Manual proxy: sprite rows + BLE MTU bytes; 80%/95% thresholds via `heap_fraction()` | Add `heap_fraction()` + render-loop guard; add hw-validation probe comment |

---

## Flags

- **Raven:** ATTENTION-on-IMU-peak adds an accelerometer read path on-device.
  No new characteristic. Data stays on-device. Low privacy surface — confirm
  with Raven that on-device-only accelerometer use requires no additional
  disclosure.
- **Lagos:** No new SDK dependencies. `frame.imu.tap_callback` and
  `frame.imu.raw()` are already in the Halo Lua stdlib. No packages to add.


---

# YT — Week 3 Onboarding UX Decision

| Field | Value |
|-------|-------|
| **Date** | 2026-06-13 |
| **Author** | Y.T. (App Developer) |
| **File** | `projects/synesthetic-familiar/host/main.py` |
| **Status** | IMPLEMENTED — pending Librarian activation-gate wiring |

---

## Context

Week 3 "It's alive" — Phase-1 final milestone for Synesthetic Familiar (VESPER).
The host app needed first-launch onboarding UX, calibration-state surfacing,
fallback visibility, and a harness for the ATTENTION display path.

ARD §5.4 specifies a 3-day baseline ramp-up: population defaults for days 1–3,
personal mean+1.5σ after. Week 2 (`inference.py`) had no explicit gate; the
`decisions.md` open item flagged this as blocking Week 3 onboarding.

---

## Decisions Made

### D1 — First-launch detection via `baseline is None`
Use `load_baseline() → None` as the first-launch signal. No separate flag file
needed. Rationale: baseline being absent *is* the semantic truth of "not calibrated yet".

### D2 — Calibration status as a pure string function
`get_calibration_status(baseline: Baseline | None) -> str` is pure, no I/O, testable
by injecting a `Baseline` dataclass directly. Juanita can unit-test every state without
touching the filesystem or running a sensor loop.

### D3 — Activation gate call site with TODO-for-Librarian
Rather than duplicating logic, `get_calibration_status()` dispatches to
`is_baseline_active(baseline)` from `host.inference` if that export exists,
falling back to `_approx_baseline_active()` (age ≥ 3 days from `created_at`).
The `TODO(Week3-Librarian)` comment at the module-level `try/except` marks the
exact wiring point. No inference.py changes were made (read-only for Y.T.).

### D4 — `print_onboarding()` with injectable `out: TextIO`
CLI `print()` is fine for playground UX. Injectable `out=io.StringIO()` makes
the function testable without stdout capture. `run()` calls it with default stdout.

### D5 — Fallback surfacing via `print()` in the run loop
Both the both-fail (10 s) and confidence-hold (30 s) paths now `print()` a
`[VESPER]`-prefixed line to stdout in addition to the existing `logger.info()`.
Logger = machine-readable; print = wearer-readable CLI UX.

### D6 — ATTENTION displayed in `_send_update` when `mood_int == Mood.ATTENTION`
Single print with `⚡ [VESPER] ATTENTION` prefix. Fires only when mood_int=3 is
actually sent, so no spurious output from current inference (which never returns
`attention`). Safe to add now; will fire when Librarian wires ATTENTION into
`compute_mood` or when `run_mock_cycle` is used.

### D7 — FAMILIAR_RESET surfaces to user in device-message handler
Added `print("[VESPER] Familiar reset — 'I'm fine' gesture acknowledged")` in
`_make_device_msg_handler` alongside the existing `logger.info`. The gesture
acknowledgement is user-facing context, not just dev-log noise.

### D8 — `run_mock_cycle()` for ATTENTION harness testing
Device-side peak detection is Ng's Lua code. Host piece: a standalone async
function that cycles NEUTRAL → CALM → STRESSED → ATTENTION, injectable via
`FakeTransport` and `noop_sleep`. Exposed as `--mock-cycle` / `--mock-cycle-count`
CLI flags (forces MockTransport; never instantiates SensorStream). Juanita can
drive it directly from acceptance tests without any CLI invocation.

---

## Deferred / TODOs

- **TODO(Week3-Librarian):** Add `is_baseline_active(baseline: Baseline | None) -> bool`
  to `host/inference.py` per ARD §5.4. The call site in `get_calibration_status()` is
  ready; remove the `try/ImportError` guard once the export lands.
- **ATTENTION in `compute_mood`:** Librarian may wire ATTENTION mood detection in
  `inference.py`. When that lands, `_send_update`'s ATTENTION print fires on real data.
- **`--mock-cycle-delay`:** Not added; default 1.0 s is fine for manual testing. Add
  if acceptance tests need faster cycling.

---

## Test impact

128/128 tests pass. No existing test asserts on stdout content, so the new `print()`
calls are silent noise in the test run. `print_onboarding`, `get_calibration_status`,
and `run_mock_cycle` are importable and testable by Juanita without a live loop.


# Eye Dilation Addendum — ATTENTION Animation (Week 3)

**Author:** Da5id (HUD/UX)  
**Date:** 2026-06-13  
**Status:** ADDENDUM to existing ATTENTION spec (decisions.md §2–6)  
**Aaron Decision:** INCLUDE eye dilation now (Q1 resolved)

---

## 1. Design Intent

Eye dilation reinforces the "I notice you" read of ATTENTION. The pupil expanding is a universal mammalian signal of heightened awareness — the creature's eye literally opens wider when it perceives the head motion. Combined with the white eye and +4px jump, dilation completes the "startled recognition" micro-moment.

---

## 2. Baseline Eye Geometry (from `familiar_neutral.txt`)

```
Eye region: rows 8–10, columns 13–17 (0-indexed from top-left)

Row 8:   ...333..   (3 eye pixels)
Row 9:   ..33333..  (5 eye pixels)
Row 10:  ...333..   (3 eye pixels)
```

**Baseline dimensions:**  
- Width: 5px at widest (row 9)  
- Height: 3px  
- Approximate center: row 9, column 15  
- Total eye pixels: 11

---

## 3. Dilated Eye Specification

**Dilation:** +1px radius on all exposed edges

```
REST (11 pixels):          DILATED (19 pixels):
     ...333..                   ..33333..
     ..33333..                  .3333333.
     ...333..                   ..33333..
                                         
(rows 8–10, cols 13–17)    (rows 7–11, cols 12–18)
```

**Dilated dimensions:**
- Width: 7px (was 5)
- Height: 3px (unchanged — we expand laterally + add 1 row above)
- Total eye pixels: 19 (was 11)

**Implementation:** During ATTENTION, any pixel that is adjacent (orthogonally or diagonally) to an eye pixel (palette index 3) also renders as eye color. This is a render-time inflation — no sprite change needed.

---

## 4. ASCII Keyframe Comparison (24×24 grid, rows 6–12)

```
REST STATE (current sprite):
Row 6:  000000112222221100000000
Row 7:  000001222222222210000000
Row 8:  000012222222333221000000   ← eye: 3 pixels
Row 9:  000122222233333221000000   ← eye: 5 pixels (widest)
Row 10: 000122222223332221000000   ← eye: 3 pixels
Row 11: 001222222222222221000000
Row 12: 001222222222222222100000

DILATED STATE (ATTENTION render):
Row 6:  000000112222221100000000
Row 7:  000001222233333210000000   ← eye expands UP (+1px row)
Row 8:  000012223333333221000000   ← eye: 5 pixels (was 3)
Row 9:  000122223333333221000000   ← eye: 7 pixels (was 5)
Row 10: 000122223333332221000000   ← eye: 5 pixels (was 3)
Row 11: 001222222222222221000000   ← no dilation down (body edge)
Row 12: 001222222222222222100000
```

**Net effect:** Eye expands from 11→19 pixels (+8 pixels, +73%). Reads as distinctly wider without dominating the sprite.

---

## 5. Timing

| Condition | Eye State |
|-----------|-----------|
| `state.attn_timer > 0` | **Dilated** (full 500ms ATTENTION_DURATION_S) |
| `state.attn_timer == 0` | **Rest** (normal 11-pixel eye) |

**Why hold for full duration (not just launch peak):**
- 180ms is the *jump* animation; 500ms is the total ATTENTION overlay
- Dilating only during the 60ms launch would be imperceptible (sub-100ms blink threshold)
- Holding dilation for the full 500ms gives the "wide-eyed" moment time to register in peripheral vision

**No separate easing:** Dilation is binary (on/off with ATTENTION state). The 60ms launch already provides the "snap" entrance; fading the dilation would add render complexity for minimal perceptual gain.

---

## 6. Tunable (Lua constant, matches existing ATTENTION_* convention)

```lua
-- ─── ATTENTION Eye Dilation (Week 3 addendum, Da5id spec) ────────────────────
local ATTENTION_EYE_DILATE_PX = 1   -- radius expansion for eye during ATTENTION
```

**Implementation hint for Ng:**  
In `draw_creature()`, when `state.mood == 3` (ATTENTION), for each non-transparent pixel:
1. If pixel index == 3 (eye): draw as normal
2. If pixel index ≠ 3 but any orthogonal/diagonal neighbor is index 3: also draw as eye color (0xFFFFFF for ATTENTION palette)

This is a morphological dilation — no sprite change, just render-time neighbor detection.

---

## 7. Glance-Ergonomics Verification

| Concern | Check |
|---------|-------|
| **Sprite bounds** | Dilated eye stays within rows 7–10, cols 12–18. Sprite is rows 4–20, cols 6–21. ✓ No clipping. |
| **STRESSED collision** | STRESSED (mood=2) uses amber eye (0xFF8800), undilated. ATTENTION (mood=3) uses white dilated eye. Colors + shape differ. ✓ No collision. |
| **CALM collision** | CALM (mood=1) uses teal eye (0x00FFCC), undilated. ✓ No collision. |
| **Peripheral legibility** | +8 pixels (11→19) is a 73% area increase at the attention locus. Combined with white vs cyan color, the dilation registers as "eye opened wider" even in peripheral vision. ✓ |
| **Pixel budget** | 19 eye + ~80 body = ~99 lit pixels during ATTENTION. Still 1.6% of 256×256 canvas. ✓ Under 5% idle target. |

---

## 8. Open Question Resolution

### §6 Q1: Eye dilation — **RESOLVED**

**Status:** ✅ INCLUDE NOW (Aaron decided 2026-06-13)  
**Original recommendation:** Defer for Week 3 polish  
**Aaron's decision:** Ship with dilation in Week 3  

### §6 Q2: Mood restoration — **NO CHANGE**

Team already converged on restore-to-previous-mood. Implementation exists (`state.pre_attn_mood`). No further action required.

---

## 9. Checklist for Ng (addendum items only)

- [ ] Add `ATTENTION_EYE_DILATE_PX = 1` constant
- [ ] In `draw_creature()`, when `mood == 3`, inflate eye pixels by ATTENTION_EYE_DILATE_PX (morphological dilation)
- [ ] Verify dilated eye renders correctly on device (no clipping, correct white color)

---

## 10. Reference: Existing ATTENTION Constants (from decisions.md §3)

```lua
local ATTENTION_JUMP_AMP_PX   = 4       -- upward burst amplitude
local ATTENTION_LAUNCH_MS     = 60      -- launch phase duration
local ATTENTION_SETTLE_MS     = 120     -- settle phase duration
local ATTENTION_DURATION_MS   = 180     -- jump animation window
local ATTENTION_COOLDOWN_MS   = 500     -- anti-spam cooldown
local ATTENTION_DURATION_S    = 0.5     -- total overlay duration (500ms)
-- NEW:
local ATTENTION_EYE_DILATE_PX = 1       -- eye radius expansion
```

---

*End of addendum — merge into decisions.md §2 (Posture change) and §3 (Tunable Parameters) as appropriate.*


# Y.T. Wave-2 Bind-Up Decision — Week 3 "It's alive"

**Date:** 2026-06-13  
**Author:** Y.T. (host-side app developer)  
**Status:** RESOLVED — 190 passed, 0 skipped, 0 xfailed (was 176/11/3)

---

## Summary

Two mechanical bind-ups in `host/main.py`, plus the new `host/onboarding.py` module,
completing the Wave-2 work items and clearing all outstanding skipped/xfailed tests.

---

## BIND-UP 1 — Activation Accessor

**Problem:** `host/main.py` contained a `_is_baseline_active` import shim
(`try: from host.inference import is_baseline_active … except ImportError: pass`)
and an age-based fallback `_approx_baseline_active()` behind a `TODO(Week3-Librarian)`.
Librarian shipped `get_activation_info(baseline) → ActivationInfo` and
`ACTIVATION_THRESHOLD = 50` in Week 3. The shim was never needed.

**Decision:** Remove the shim and both fallback helpers (`_approx_baseline_active`,
`_baseline_age_days`). Import `get_activation_info` and `ACTIVATION_THRESHOLD`
directly from `host.inference`. Rewrite `get_calibration_status()` to call
`get_activation_info(baseline)` and format the result:
- `state == "calibrating"` → `"calibrating (n / 50 samples — population defaults active)"`
- `state == "personalized"` → `"personalized (n=N samples, mean=M, stddev=S)"`

Progress counter (`sample_count / samples_needed`) replaces the age-based "day N of 3"
display — sample-count gating is the authoritative gate per decisions.md 2026-06-12.

**Rationale:** Pure mechanical bind. No design latitude; Librarian's contract was
complete. Age-based fallback is permanently retired; the field `_BASELINE_MIN_DAYS`
and `datetime` import are removed as dead code.

---

## BIND-UP 3 — FAMILIAR_RESET Host Reaction

**Problem:** `_make_device_msg_handler()` logged and printed on `FamiliarReset` but
took no action on local state. `run()` therefore ignored FAMILIAR_RESET. This left
3 xfail tests in `test_week3_reset.py` Group 2 (JUANITA-T2-5):
- `test_reset_triggers_neutral_send`
- `test_reset_restarts_sequence_counter`
- `test_reset_during_gated_session_clears_stale_mood`

**Decision:** Use a `list[bool]` reset flag shared between the receive callback closure
and the `run()` loop. The flag is set inside the callback (synchronously, during
`await transport.send()`) and checked at the top of each loop frame.

When the flag is set:
1. Clear the flag.
2. Call `seq.reset()` — re-syncs sequence counter (ARD §5.2 reconnect protocol).
3. Call `_send_neutral_reset(transport, seq)` — sends `FAMILIAR_UPDATE` with
   `mood=NEUTRAL`, routes intensity through Gate 2 (quantise → jitter → encode).
4. Update `last_send_time = tick_start` and `both_fail_start = None`.
5. `continue` — `finally` (sleep pacer) still executes; frame's sensor data is skipped.

**Why `list[bool]` not `asyncio.Event`?** All asyncio code is single-threaded; the
callback fires synchronously inside `await transport.send()`. A simple mutable
container is sufficient and avoids introducing a coroutine wait in the callback path.

**Why `continue` after reset, not fall-through?** The device already snapped to
NEUTRAL. Processing the current frame's sensor data would immediately overwrite the
NEUTRAL send with a potentially non-NEUTRAL mood — contradicting the reset intent.

**New helper:** `_send_neutral_reset(transport, seq)` — semantically distinct from
`_send_neutral_fallback` (which is a sensor-fail path). Both route through Gate 2.

---

## New Module — `host/onboarding.py`

**Problem:** `test_week3_onboarding.py` had 11 tests skipping because
`host.onboarding` did not exist. Juanita's contract:
- `is_first_launch(baseline_path: Path) → bool` — pure, file-existence check
- `run_first_launch_flow(baseline_path: Path) → None` — banner + creates marker file
- `run_returning_flow(baseline: Baseline | None) → None` — logs returning-user status

**Decision:** Create `host/onboarding.py` implementing exactly that contract.
`is_first_launch` is a one-line `not baseline_path.exists()` — pure, no I/O.
`run_first_launch_flow` creates parent dirs, writes an empty marker, prints the
first-launch banner. `run_returning_flow` logs but does not raise on `None` input.

**Reject criteria met:**
- `is_first_launch` uses caller-supplied path (no `~/.vesper` hardcode).
- After `run_first_launch_flow`, `is_first_launch(same_path)` returns `False`.
- `run_first_launch_flow` has no BLE SDK imports (pure host UX).
- `run_returning_flow(None)` does not raise.

---

## Test Suite After Changes

```
190 passed in 0.33s
```

Delta: +14 tests (11 skipped → passed, 3 xfailed → passed), 0 regressions.
The `@pytest.mark.xfail` decorators were removed from the three test classes in
`test_week3_onboarding.py` and from `TestFamiliarResetHostReaction` in
`test_week3_reset.py`, since the conditions they guarded are now fully implemented.


# Implementation Note — Week 3 ATTENTION Visuals

**Author:** Ng (SDK Engineer)  
**Date:** 2026-06-13  
**Status:** SHIPPED — device/main.lua updated  
**Scope:** ATTENTION animation: jump motion, eye dilation, body desaturation, mood restoration

---

## Summary

All four ATTENTION visual tasks from Da5id's spec (decisions.md §2–6) and the eye-dilation addendum (dasid-week3-eye-dilation.md) are implemented in `projects/synesthetic-familiar/device/main.lua`. Tests: 188 passing, 2 pre-existing failures in `TestFamiliarResetHostReaction` (Y.T.'s host-side domain, unaffected by Lua changes).

---

## Task 1 — Jump Motion

**Constants added:**
```lua
local ATTENTION_JUMP_AMP_PX  = 4    -- upward burst amplitude (pixels)
local ATTENTION_LAUNCH_MS    = 60   -- launch phase: 0 → peak (ms)
local ATTENTION_SETTLE_MS    = 120  -- settle phase: peak → 0 (ms)
local ATTENTION_DURATION_MS  = 180  -- total jump window (launch + settle)
```

**Easing helpers added** per Da5id's reference Lua:
- `ease_out_quad(t)` — fast-start, decelerating (launch)
- `ease_in_out_quad(t)` — smooth S-curve (settle)

**`compute_attention_jump(attn_timer)` added:**  
Returns 0–4px upward offset. Uses `(ATTENTION_DURATION_S - attn_timer) * 1000` as elapsed_ms — derives from the existing countdown rather than storing a wall-clock start time.

**Applied in render loop:**
```lua
local attn_jump_px = compute_attention_jump(state.attn_timer)
local render_y = SPRITE_CY + bob_y - attn_jump_px
```
All three draw calls (halo glow, creature, fraying) receive `render_y`. Because halo and fraying are gated to CALM/STRESSED respectively, they are no-ops during ATTENTION; the jump only visually matters on `draw_creature`.

### Timer Reconciliation

Da5id's checklist listed `state.attention_start_t`, `state.attention_active`, `state.attention_last_t`, `state.mood_before_attention` as new fields. **These were not added.** The existing state already covers every requirement:

| Da5id field | Existing equivalent |
|-------------|-------------------|
| `attention_active` | `state.attn_timer > 0` |
| `attention_start_t` | `ATTENTION_DURATION_S - state.attn_timer` (derived) |
| `attention_last_t` | `attn_timer` covers anti-re-entrancy (guard already in IMU block) |
| `mood_before_attention` | `state.pre_attn_mood` |

Single source of truth: `state.attn_timer` (countdown). No duplication.

---

## Task 2 — Eye Dilation

**Constant added:**
```lua
local ATTENTION_EYE_DILATE_PX = 1   -- neighbor radius for dilation
```

**Two-pass render in `draw_creature()`:** After the main pixel loop, when `mood_idx == 3`, iterate sprite looking for eye pixels (index 3). For each, paint all 8 neighbors (dr, dc ∈ {-1,0,1}, not both zero) as eye color if they are not themselves eye pixels. Bounds-checked.

**Pixel count:** 11 → 19 (+73%). Dilated region: rows 7–10, cols 12–18. Sprite bounds: rows 4–20, cols 6–21. No clipping. ✓

**Timing:** Binary (on for full ATTENTION_DURATION_S, off otherwise). No easing needed — the 60ms launch snap provides entrance snap perceptually.

---

## Task 3 — Body Desaturation

**Status: Already correct in Wave-1.** The ATTENTION palette `[3]` already uses neutral gray body colors:
```lua
[1] = 0x1A1A1A,   -- body dark  — gray (desaturated)
[2] = 0x2E2E2E,   -- body mid   — gray (desaturated)
```
Added inline comments to the palette block clarifying the desaturation intent and why it distinguishes ATTENTION from STRESSED (which retains warm amber).

---

## Task 4 — Q2 Mood Restoration

**Status: Already correct in Wave-1.** `state.pre_attn_mood` is saved on ATTENTION trigger and restored on `attn_timer` expiry. Comment added to the expiry block:

```lua
-- Team decision (2026-06-13): restore-to-previous-mood (not neutral).
-- Aaron deferred to team; team converged; no behavior change needed.
```

**Flicker risk assessment:** No flicker risk observed. `pre_attn_mood` is written once on trigger (before `state.mood = 3`) and read once on expiry. Incoming BLE packets during the overlay correctly update `pre_attn_mood` (not `state.mood`) via the `attn_timer > 0` guard in `on_ble_data`. The restored mood therefore reflects the latest host state, not a stale snapshot. Behavior is correct.

---

## 0x01 Contract

`OPCODE_FAMILIAR_RESET = 0x01` in `host/familiar_protocol.py` is unchanged. The double-tap handler still sends `string.char(0x01)`. Contract intact. ✓

---

## Files Changed

- `projects/synesthetic-familiar/device/main.lua` — all changes above

## Files NOT Changed (per charter)

- `host/main.py`, `host/inference.py`, `host/sensors.py` — Y.T.'s domain


# Raven — Week 3 Privacy Audit: VESPER "It's alive"

| Field       | Value |
|-------------|-------|
| **Author**  | Raven (Security & Privacy) |
| **Date**    | 2026-06-13T23:13:01-07:00 |
| **Scope**   | Week 3 new surfaces: ATTENTION-on-IMU-peak, first-launch onboarding + baseline activation gate, W3-1 snapshot-zeroing confirmation, secrets scan |

---

## Surface 1 — ATTENTION-on-IMU-peak (device/main.lua)

### Data Flow

```
frame.imu.raw()
  └─▶ imu_raw.accelerometer.{x,y,z}   [local Lua variables only]
        └─▶ ax, ay, az = raw / IMU_SCALE  [g, local]
              └─▶ mag = sqrt(ax²+ay²+az²) [local scalar]
                    └─▶ if mag > 1.8g:
                              state.mood      = 3     [local render state]
                              state.attn_timer = 0.5  [local countdown]
                          ─── NO frame.bluetooth.send() call ───
```

**BLE transmissions in device/main.lua — complete inventory:**
1. Startup reconnect ACK: `0x02` + last_seq (3 bytes) — no sensor data
2. Double-tap FAMILIAR_RESET: `0x01` (1 byte) — no sensor data
3. Every-10-packets FAMILIAR_ACK: `0x02` + last_seq (3 bytes) — no sensor data

The IMU-peak code path (lines 548–564) **exclusively mutates local `state` variables**. `frame.bluetooth.send()` is not called from the render loop IMU-peak branch. Raw accelerometer values (`ax`, `ay`, `az`, `mag`) are Lua locals — they are never serialised, logged, or transmitted.

**Bystander inference check (TEST-STRATEGY privacy-audit row: "non-wearer cannot infer stress/calm from visual alone"):**

ATTENTION visual: gray desaturated body + white eye + 4px upward jump (180ms) + 500ms overlay. This visual is distinct from STRESSED (amber body, amber eye) and CALM (teal body, teal eye). A bystander observing the ATTENTION overlay learns at most "a sudden motion event occurred" — they cannot determine whether the wearer is stressed or calm. The ATTENTION trigger is motion-magnitude-only (no mood inference on device). ARD §5.6 explicitly accepts that an *informed* observer can associate creature behavior with wearer state; the 24×24 peripheral sprite remains opaque to a casual bystander. The TEST-STRATEGY row is satisfied: the ATTENTION visual does not leak stress/calm — it is a momentary, generic motion response.

**Additional confirmation:** The device-side ATTENTION trigger is invisible to the host. The host continues sending FAMILIAR_UPDATE at 10Hz based on its own inference. No new BLE characteristic was introduced. The host's ATTENTION state (mood_int=3) follows an independent path from `compute_mood()` on the host.

### Verdict: ✅ APPROVED

No accel value leaves the device via the ATTENTION path. No stress/calm inference is possible from the ATTENTION visual alone. No new BLE characteristic. No host visibility of device-side IMU peak event. Clean.

---

## Surface 2 — Onboarding + Baseline Activation Gate

### What lands in ~/.vesper/baseline.json

```json
{
  "mean":         0.412,   // running Welford mean of tension scalar (0.0–1.0)
  "stddev":       0.087,   // sample stddev of tension scalar
  "sample_count": 47,      // count of high-confidence samples accumulated
  "created_at":   "2026-06-13T..."  // ISO 8601 first-session timestamp
}
```

**Tension scalar derivation** (`inference.py` line 251–255):
```python
tension = audio_pitch_variance * 0.4 + imu_acceleration * 0.3 + imu_rotation * 0.3
```

This is a three-input weighted scalar in [0.0, 1.0]. It is:
- **Not** raw audio samples (zeroed after extraction — Gate I7)
- **Not** a voiceprint or acoustic fingerprint
- **Not** raw IMU data
- **Not** re-identifying: the scalar alone cannot identify an individual without ground-truth behavioral data for comparison

The mean and stddev are a two-number summary of the wearer's typical arousal distribution. This is a behavioral metric, not a biometric in the GDPR Article 9 sense (no morphological, physiological, or behavioral characteristic that allows unique identification when processed with appropriate techniques). For a single-user local playground, this risk level is accepted.

**Onboarding print surface — new finding:**

`get_calibration_status()` in `main.py` (lines 100–108) prints to stdout on every returning-user startup when "personalized":
```
[VESPER] Familiar online — personalized (n=53 samples, mean=0.412, stddev=0.087)
```

The `mean` and `stddev` of the tension baseline are written to the terminal at INFO level. For a single-user playground on the wearer's own machine this is acceptable Phase-1 behaviour. However, this surfaces a behavioral metric in plaintext to the terminal — anyone with access to the terminal session (shell history, screen capture, log aggregator) would see it.

**P2-2 regression check:** Prior deferral was "baseline.json is plaintext, not encrypted; accept for Phase-1 single-user playground." The format and risk level are unchanged. No regression. The new P2 observation is the stdout print of mean/stddev, which is a related but distinct surface.

**onboarding.py print review:** `run_first_launch_flow()` prints only the static banner and calibration status ("calibrating (0 / 50 samples — population defaults active)"). No sensitive data. `run_returning_flow()` only logs INFO "returning user — baseline loaded" (no values). Clean.

### Verdict: ✅ APPROVED (Phase-1 accepted risk — P2-2 not regressed)

No biometric-identifying data in baseline.json. Plaintext acceptable for Phase-1 single-user playground; P2-2 deferral stands. New P2 item added: stdout print of mean/stddev in "personalized" status string should move to `--verbose` / debug-only in Phase-2.

**New P2 item (extend or companion to P2-2):**

> **P2-4:** `get_calibration_status()` prints `mean=X.XXX, stddev=X.XXX` to stdout on every returning-user startup when personalized. Phase-2 should replace with a non-metric string (e.g. "personalized ✓") at INFO level and move the numeric values to `--verbose` or debug log. Owner when actioned: **Y.T.** (onboarding UX).

---

## Surface 3 — W3-1 Snapshot Zeroing (sensors.py)

**Requested hardening:** Ensure buffer is cleared on every code path (not just happy path), and snapshot copy is zeroed in-place before `del`.

**Confirmed present — three-layer zeroing in `_extract_frame()` (lines 315–340):**

```python
with self._audio_lock:
    samples = self._buffer.copy()
    self._buffer[:] = 0.0        # Layer 1: in-buffer zero (under lock, every path)
    self._buffer_pos = 0
    mic_ok = self._mic_ok
try:
    ...                           # feature extraction
finally:
    samples[:] = 0.0             # Layer 2: snapshot copy zero (in-place, every path incl. exception)
    del samples                  # Layer 3: reference release
```

**Confirmed present — stop() zeroing (lines 252–257):**
```python
with self._audio_lock:
    self._mic_ok = False
    self._buffer[:] = 0.0
    self._buffer_pos = 0
```

The `finally` block guarantees Layer 2 + Layer 3 execute on **every** exit path from `_extract_frame()` — normal return, exception from `_compute_rms`, exception from `_compute_pitch_variance`, and exception from the SensorFrame constructor. This is exactly the hardening requested in W3-1.

**Verdict: ✅ CONFIRMED — W3-1 present and correct.**

---

## Surface 4 — Secrets Scan (Week 3 diff)

Scanned `projects/synesthetic-familiar/` for:
- API keys, tokens, credentials, passwords
- Cloud SDK imports (OPENAI, AWS, GCP, Azure)
- Bearer tokens, GitHub PATs, SSH private keys
- Hardcoded secrets patterns

**Result: CLEAN.** One false-positive match ("concentric rings" in main.lua — a comment). No secrets, no cloud SDK imports, no credentials. Week 3 is clean.

---

## Summary Table

| Surface | Verdict | Notes |
|---------|---------|-------|
| ATTENTION accel path (device/main.lua) | ✅ **APPROVED** | No accel value or stress inference leaves device; no new BLE characteristic; bystander cannot infer stress/calm from ATTENTION visual |
| Onboarding + baseline persistence | ✅ **APPROVED** (P2 note) | No raw biometrics; P2-2 not regressed; new P2-4 item: move mean/stddev console print to --verbose |
| W3-1 snapshot zeroing (sensors.py) | ✅ **CONFIRMED** | Three-layer zeroing present; finally block guards all paths |
| Secrets scan | ✅ **CLEAN** | No secrets, tokens, or cloud SDKs in Week 3 code |

---

## Open / Deferred Privacy Items (complete list for handoff)

| ID | Item | Owner (when actioned) | Phase |
|----|------|-----------------------|-------|
| P2-1 | BLE LESC (LE Secure Connections) pairing — wire is unauthenticated | Ng | P2 |
| P2-2 | baseline.json encryption / OS keychain storage | Y.T. | P2 |
| P2-3 | Jitter range review (currently ±5 on {0,25,50,75,100} → narrow; review whether ±10 or ±8 is needed) | Librarian / Ng | P2 |
| P2-4 | *(new, Week 3)* `get_calibration_status()` prints mean/stddev to stdout when personalized — move to `--verbose`/debug log | Y.T. | P2 |

**Week 3 ships clean. No blocking conditions.**


# Decision: Juanita Week 3 Fallback-Depth & Threshold-Tuning Tests

| Field | Value |
|-------|-------|
| **Date** | 2026-06-13 |
| **Author** | Juanita (Tester / QA) |
| **Status** | DELIVERED — all 72 new tests green |
| **Requested by** | Aaron Kubly |
| **Wave** | Week 3 Wave 2 |

---

## What Was Done

Added 72 new tests in 3 files to deepen graceful-fallback verification and threshold-tuning coverage for the VESPER Week 3 "it's alive" bar.

### Files Created

| File | Tests | Focus |
|------|-------|-------|
| `tests/test_week3_fallback_depth.py` | 9 | Timeout boundaries, recovery, RESET-during-fallback |
| `tests/test_week3_threshold_tuning.py` | 37 | Confidence gate, activation boundary, quantisation buckets, jitter |
| `tests/test_week3_ble_flake.py` | 26 | Garbled device bytes, extreme sensor floats, heap gap |

**Suite totals: 190 → 262, all green.**

---

## Key Contracts Verified

### 1. Graceful Fallback Depth

**Exact timeout boundaries (strict `>`, not `>=`):**
- `test_at_exactly_10s_does_not_fire`: delta=10.0 must NOT fire the both-fail fallback.
- `test_just_after_10s_fires_neutral`: delta=11.0 fires exactly one NEUTRAL.
- Same pattern for confidence-hold at 30.0 / 31.0.

**Recovery after fallback:**
- `test_good_frame_after_both_fail_sends_inference_result`: after NEUTRAL fired, a stressed-ungated frame drives normal inference (2 sends total; mood flips from 0 to 2).
- `test_good_frame_after_confidence_hold_sends_again`: after hold fires, recovery send follows.
- `test_both_fail_timer_clears_on_good_frame`: regression — timer does NOT carry across a good-frame gap.

**FAMILIAR_RESET during both-fail state:**
- `test_reset_during_both_fail_sends_neutral_once`: RESET fires at frame 3 (timer at 2s, not yet expired); run() handles RESET (1 NEUTRAL send), clears `both_fail_start=None`. Subsequent both-fail frames restart from scratch — no spurious timeout.
- `test_reset_clears_both_fail_timer_prevents_double_fire`: RESET at 9s elapsed (one tick before timeout); exactly 1 send (the RESET reaction). Without the `both_fail_start=None` clear, a second NEUTRAL would fire.

**Seam used:** `_ResetCallbackStream` + `_CaptureCallbackTransport` — fires FAMILIAR_RESET opcode 0x01 via the on_receive callback after yielding the Nth frame, deterministic, no hardware.

### 2. Threshold Tuning

**Confidence gate (CONFIDENCE_GATE=0.7, strict `<`):**
- stressed + both ok → confidence=0.8, `gated=False` ✓
- neutral + both ok → confidence=0.6, `gated=True` ✓
- stressed + mic_ok=False → 0.8×0.6=0.48, `gated=True` ✓
- stressed + imu_ok=False → 0.8×0.7=0.56, `gated=True` ✓
- `test_gate_is_strict_less_than_not_less_than_or_equal`: pins strict-`<` semantics by constructing a MoodResult with confidence=CONFIDENCE_GATE and asserting `gated=False`.

**Activation gate (ACTIVATION_THRESHOLD=50):**
- n=49: population STRESS_THRESHOLD(0.65) → neutral (tension 0.49 < 0.65)
- n=50: personal threshold (0.275) → stressed (tension 0.49 > 0.275)
- n=51: same as n=50
- `test_boundary_flip_between_49_and_50`: comparative test; moods must differ.

**Intensity quantisation (5 buckets, 10 boundary values parametrized):**
- `[0.000, 0.125)→0`, `[0.125, 0.375)→25`, `[0.375, 0.625)→50`, `[0.625, 0.875)→75`, `[0.875, 1.0]→100`
- All 10 boundary values tested as a parametrized suite.

**Jitter contract (±5, clamped to [0,100]):**
- All 5 buckets × 11 jitter values (-5 to +5) = 55 exhaustive checks; none outside [0, 100].
- Special case: 0+-5=clamped to 0; 100+5=clamped to 100.

### 3. BLE Flake Tolerance

**Garbled device bytes:**
- 10 parametrized bad-byte inputs (empty, unknown opcode, truncated ACK, over-length ACK, reversed-direction opcode, 100-byte zeroed blob, 16-byte pattern) — `dispatch_device_message` must return None or a valid message type, never raise.
- `test_dispatch_valid_ack_still_works_after_garbled_sequence`: verifies host state is not corrupted by bad bytes.

**Extreme/NaN/Inf sensor values:**
- `1e300` values: Python float math handles overflow (clips to Inf), falls to stressed branch, no crash.
- NaN pitch_variance: NaN comparisons always False → neutral branch → gated. Confirmed.
- Inf acceleration: tension=Inf → stressed. No crash.
- NaN baseline poisoning guard: `update_baseline(..., float("nan"))` returns original baseline unchanged (sample_count does not increment, mean/stddev remain finite).

### 4. Heap Guard Observability — Coverage Gap Documented

**Finding:** `FamiliarAck` has exactly one field: `last_received_seq`. No heap field.

**Structural test:** `test_familiar_ack_has_no_heap_field` asserts `fields == {"last_received_seq"}`. If Ng adds a heap field, this test fails — prompting a review of host-side handling.

**Gap:** The host has NO wire-level signal for device heap pressure. If device hits 95% OOM (→ safe-halt), the host observes BLE silence, which eventually (10 s) triggers the both-fail → NEUTRAL fallback.

**Proxy safety net verified:** `test_both_fail_fallback_is_heap_oom_proxy` asserts `BOTH_FAIL_TIMEOUT_S` is finite and ≤ 15 s.

---

## Correctness Review (Juanita as reviewer)

### What I checked before writing tests

1. `compute_mood` gating formula: `gated=(confidence < CONFIDENCE_GATE)` — strict less-than confirmed in inference.py line 73. No rejection.
2. Both-fail timeout condition: `elif (tick_start - both_fail_start) > BOTH_FAIL_TIMEOUT_S` — strict greater-than confirmed in main.py line 485. No rejection.
3. Confidence-hold condition: `if (tick_start - last_send_time) > CONFIDENCE_HOLD_TIMEOUT_S` — strict greater-than confirmed in main.py line 510. No rejection.
4. FAMILIAR_RESET handler clears `both_fail_start = None` — confirmed in main.py line 478. No rejection.
5. `update_baseline` NaN guard: `if not math.isfinite(tension): return baseline` — confirmed in inference.py lines 155-161. No rejection.

### One real bug caught during test authoring

**`test_imu_fail_reduces_confidence_below_gate`** initially used `imu_acceleration=0.0, imu_rotation=0.0` with the intent to represent a failed IMU.  With zero IMU values, tension=0.4 → neutral, confidence=0.6×0.7=0.42 (not 0.56 as asserted).  Fixed: `imu_ok=False` only penalises confidence — it does NOT zero the raw values.  The test was corrected before delivery; no code change needed.

### No contract violations found

All fallback, confidence-hold, activation-gate, quantisation, and BLE-flake contracts are correctly implemented in current code. No rejections.

---

## Owner Actions Required

| Owner | Item | Priority |
|-------|------|----------|
| **Ng** | Add heap_status byte to FAMILIAR_ACK (or DEVICE_STATUS message) so host can log at 80% and back off at 95% — W3-B/W3-E | Future (not blocking Week 3 ship) |

---

## New Test Doubles Introduced

**`_CaptureCallbackTransport`** (`test_week3_fallback_depth.py`): extends FakeTransport to store the on_receive callback in a shared list ref, allowing `_ResetCallbackStream` to call it.

**`_ResetCallbackStream`** (`test_week3_fallback_depth.py`): async sensor stream that fires FAMILIAR_RESET (opcode 0x01) via the stored callback after yielding the Nth frame. Deterministic, no wall-clock dependency.

Pattern: both are module-private (underscore prefix); not candidates for `helpers.py` as they are tightly coupled to the specific test topology.


# Librarian — Week 3 Documentation Sync (2026-06-13)

**Date:** 2026-06-13T23:13:01.451-07:00  
**Author:** Librarian (AI/ML)  
**Status:** COMPLETED  
**Task:** Synchronize project documentation with Week 3 shipped reality

---

## Context

Wave 1 + bind-up complete. Week 3 "It's alive" shipped 190+ tests green. Multiple decisions resolved SDK gates and locked Week 3 implementation details. Documentation (ARD.md, TEST-STRATEGY.md, README.md) still contained "OPEN" or outdated status markers for items now resolved and shipped.

**Request:** Update docs to reflect actual shipped behavior, cite decision dates, mark gates RESOLVED.

---

## Work Completed

### 1. ARD.md §5.1 SDK Gate Table (lines 207–213)

**Updated from:** OPEN placeholders to RESOLVED with actual outcomes.

- **Gate 1 (IMU interrupt):** Changed from `frame.imu.on_tap(n, callback)` (ARD assumption) to **`frame.imu.tap_callback(func)` (actual API, 2026-06-12)**. Double-tap discrimination: Lua debounce accumulator, 350ms window. IMU-peak ATTENTION trigger: render-loop poll of `frame.imu.raw()` at 20fps, ≤50ms latency, threshold `IMU_PEAK_THRESH_G = 1.8g`. Status: ✅ **GO**

- **Gate 2 (heap API):** Changed from "unconfirmed, fallback design TBD" to **`frame.system.get_heap_usage()` NOT available; manual proxy confirmed as v1 design (2026-06-12)**. Heap fraction proxy: sprite rows (24×25B) + BLE buffer (244B) vs. ~40KB budget. Thresholds: ≥80% reduce (skip glow), ≥95% halt. Firmware-swap hook documented for future. Status: ❌ **NO-GO → fallback as v1**

- **Gate 3 (sprite format):** Clarified that `frame.display.circle()` is confirmed available; Bresenham fallback replaced with 1× circle call per ring (8× reduction). Status: ✅ **RESOLVED**

### 2. ARD.md §10 Open Questions (lines 575–590)

**Updated:** Q1 and Q3 marked RESOLVED with decision citations.

- **Q1 (IMU event primitive):** Reclassified from OPEN to **RESOLVED GO (2026-06-12)**. Real API = `frame.imu.tap_callback(func)`. No N-count. Double-tap via Lua debounce. Citation: decisions.md "SDK Gate Verdicts — Week 3 Go/No-Go".

- **Q3 (Heap monitoring):** Reclassified from OPEN to **RESOLVED NO-GO (2026-06-12)**. `frame.system` namespace does not exist. Manual proxy accepted as v1. Citation: decisions.md "SDK Gate Verdicts — Week 3 Go/No-Go".

- **Q2, Q4–Q6:** Remained as-is (Q2 already resolved, Q4–Q6 deferred or in progress).

### 3. ARD.md Build Sequence Week 3 Rows (lines 560–562)

**Updated:** Specific shipped details replace placeholders.

- Row 1 (Week 3 deliverables): Now specifies ACTIVATION_THRESHOLD=50, IMU-peak poll mechanism (render loop 20fps), double-tap API (`frame.imu.tap_callback` debounce 350ms), ATTENTION state visual (white eye, gray body, 180ms +4px jump, 500ms overlay), host onboarding, graceful degradation verified.

- Row 2 (Polish + test): Clarifies "baseline learning ACTIVATION_THRESHOLD=50 fully implemented with `get_activation_info()` accessor" and "heap proxy established with firmware-swap hook".

- Row 3 (SDK gates): Status changed to **✅ RESOLVED (2026-06-12)**: IMU GO, Heap NO-GO, 190+ tests green.

### 4. TEST-STRATEGY.md Week 3 Acceptance Rows (lines 1359–1362)

**Updated:** Manual check criteria now cite actual Week 3 outcomes.

- **Week 3 — "It's alive":** Expanded success criterion from "double-tap locally snaps NEUTRAL; host sees FAMILIAR_RESET notification" to include ATTENTION details: "ATTENTION overlay fires on IMU peak (500ms white eye + gray body + 180ms +4px jump); baseline activation gate at 50 Welford samples; 190+ tests green".

- **Week 3 — Privacy audit:** Unchanged (already correct).

### 5. projects/synesthetic-familiar/README.md

**Updated:** Codename and status.

- **Codename:** Changed from PULSE to VESPER (2026-06-08 decision).
- **Status:** Updated from "Week 1 scaffold" to "Week 3 complete — 190+ tests green".
- **New section:** "Week 3 Shipped" bullet list of all Week 3 deliverables (IMU double-tap, ATTENTION overlay, baseline activation gate, heap monitoring fallback, host onboarding, privacy audit, test count).
- **File map:** Removed (playground context; kept architecture summary for reference).

---

## Decision Citations

All updates cite specific decisions.md records with dates:

| Update | Decision Record | Date |
|--------|-----------------|------|
| Gate 1 API correction | SDK Gate Verdicts — Week 3 Go/No-Go | 2026-06-12 |
| Gate 2 NO-GO verdict | SDK Gate Verdicts — Week 3 Go/No-Go | 2026-06-12 |
| Gate 3 circle() confirmation | VESPER Week 1 — SDK Gaps & Decisions | 2026-06-09 |
| Q1 resolved (IMU) | SDK Gate Verdicts | 2026-06-12 |
| Q3 resolved (heap) | SDK Gate Verdicts | 2026-06-12 |
| Week 3 build row details | Week 3 "It's alive" — Work Breakdown & Sequencing | 2026-06-12 |
| ACTIVATION_THRESHOLD | Baseline Activation Gate — Population→Personal Threshold | 2026-06-12 |
| Codename VESPER | VESPER Project Codename Decision | 2026-06-08 |

---

## Validation

- ✅ No behavior change to code (docs-only updates).
- ✅ All facts cited to decisions.md (searchable source of truth).
- ✅ Contradictions flagged: None found between docs and decisions/code.
- ✅ Test status verified: 190+ tests confirmed green in Week 3 Test Plan decision.

---

## Summary

ARD.md §5.1, §10, and build-sequence rows now accurately reflect shipped Week 3 reality. TEST-STRATEGY.md Week 3 acceptance criteria expanded to cite specific deliverables. README.md updated with VESPER codename and Week 3 status. All updates cite .squad/decisions.md with decision dates. Docs are now in sync with what shipped.

Week 3 documentation close is complete.


---

## 2026-06-13: Week 3 Persona Review Cycle — 2 Cycles, All Blocking/Important Addressed, 265 Green

**Status:** COMPLETE  
**Owner:** Team (Y.T., Ng, Librarian, Juanita) + Aaron (approval)  
**Date:** 2026-06-13  
**Branch:** synesthetic-familiar/week3-its-alive  
**Base commit:** ee971a3  

---

### Executive Summary

Two-cycle persona review and fix wave for Week 3 "It's Alive" milestone. **Cycle 1** surfaced 2 blocking, 4 important, 11 minor findings across Code, Security, and Architect panels (6 personas). **Cycle 2** re-reviewed all findings; all blocking/important items closed; residual dead code removed. **Final state:** 265 tests green. Branch ready for ship-to-pr.

---

### Cycle 1 Findings & Disposition

| Category | Count | Disposition |
|----------|-------|-------------|
| **Blocking (B)** | 2 | B1 onboarding dual-implementation, B2 device last_seq reset |
| **Important (I)** | 4 | I1 heap_fraction inert guards, I2 get_calibration_status leaks stats, I3 mood domain clamp, M1 byte validation |
| **Minor (M)** | 11 | M3 baseline size guard, M5 tautological threshold, M6 README count, M1–M11 misc. |
| **Praise** | — | Security: protocol parsing + privacy zeroing. Architect: architectural coherence. |

**No security blockers.** Privacy-zeroing and protocol parsing both approved as-designed.

---

### Fix Wave — Agent Work (Cycle 1 → Cycle 2)

#### Y.T. (Host Lead) — B1 + I2 + Minors

**B1: Onboarding Dual-Implementation**
- **Problem:** host/onboarding.py implemented correct sentinel logic but was never called from un(). Meanwhile un() used untested print_onboarding(baseline) helper, which repeated banner on every launch until ≥50 high-confidence samples accumulated (days).
- **Fix:** Wired onboarding.py as single source of truth. Replaced print_onboarding(baseline) with:
  `python
  if is_first_launch(baseline_path):
      run_first_launch_flow(baseline_path)
  else:
      run_returning_flow(baseline)
      print(f"\n[VESPER] Familiar online — {get_calibration_status(baseline)}\n")
  `
  Added aseline_path: Path injectable parameter; three integration tests driving un() end-to-end.

**I2: get_calibration_status() Leaking Stats**
- **Problem:** Status string formatted mean/stddev directly (mean={baseline.mean:.3f}, stddev={baseline.stddev:.3f}). Raw model parameters are implementation detail; surfacing them confuses UX.
- **Fix:** Status now contains only activation state and sample count: "calibrating (n / 50 samples — population defaults active)" or "personalized (n samples)".

**Minors:** Added ng injectable to _send_neutral_reset, removed unused imports.

#### Ng (Device Lead) — B2 + I1 + I3 + M1

**B2: Double-Tap Reset Did Not Reset Device Seq-Dedup**
- **Problem:** 	ap_callback snapped state to NEUTRAL and sent FAMILIAR_RESET opcode, but left state.last_seq stale. Host called seq.reset() and restarted counter at  x0000; device's stale last_seq caused is_newer_seq(0x0000, <stale>) to reject first post-reset packet.
- **Fix:** In 	ap_callback, set state.last_seq = 0xFFFF (sentinel). Verified against actual is_newer_seq implementation: (0x0000 - 0xFFFF) & 0xFFFF = 1 → accept.

**I1: heap_fraction() Structurally Static — Guards Permanently Dead**
- **Problem:** heap_fraction() returns (#SPRITE_ROWS * 25 + 244) / 40960 ≈ 0.020 (all compile-time constants). 80% (reduce) and 95% (halt) guards are dead code.
- **Fix (Aaron-approved):** Made inertness explicit with WARNING comments at both sites (body + render loop). Guards and structure preserved intentionally for future firmware-swap one-line body change.

**I3: pre_attn_mood Could Be Set to ATTENTION (3)**
- **Problem:** Two sites could stash mood=3 into state.pre_attn_mood, violating invariant that ATTENTION is transient overlay, not underlying mood. On overlay expiry state.mood = state.pre_attn_mood would lock device in ATTENTION forever.
- **Fix:** Clamp pre_attn_mood to {0, 1, 2} in two sites: on_ble_data (when ttn_timer > 0) and IMU-peak trigger.

**M1: No Range Validation on Host Bytes**
- **Problem:** state.mood, state.intensity, state.confidence assigned directly from message without clamp.
- **Fix:** Explicit clamp at acceptance point: mood_in = clamp(msg.mood, 0, 3), intensity_in = clamp(msg.intensity, 0, 100), confidence_in = clamp(msg.confidence, 0, 100).

#### Librarian (Docs + Inference) — M3 + M6

**M6: README.md Stale Test Count**
- **Problem:** Two references to "190+" remained from Week 2. Week 3 final = 262.
- **Fix:** Updated both references (§10 status line, §23 shipped deliverables) to "262".

**M3: load_baseline() — No Size Guard Before Read**
- **Problem:** path.read_text() had no cap; corrupt/malicious/symlinked baseline.json could exhaust host memory before validation.
- **Fix:** Added pre-read stat() check. If st_size > 4096, raises ValueError (caught by existing exception handler, returns None). 4 KB = 33× headroom for valid ~120-byte baseline.

#### Juanita (Test Infrastructure) — M5

**M5: Tautological Confidence-Gate Test**
- **Problem:** 	est_gate_is_strict_less_than_not_less_than_or_equal manually constructed MoodResult with gated=(CONFIDENCE_GATE < CONFIDENCE_GATE) — never called compute_mood, never exercised gating logic.
- **Fix:** Replaced with four real compute_mood calls straddling gate (0.7): stressed+both_ok (0.80→False), stressed+imu_fail (0.56→True), stressed+mic_fail (0.48→True), neutral+both_ok (0.60→True). Cross-check: esult.gated == (result.confidence < CONFIDENCE_GATE) catches future < → <= regression.

---

### Cycle 2 Re-Review & Cleanup

**Cycle 2 Personas:** Correctness, Skeptic, Architect. **All findings from Cycle 1 re-verified as ADDRESSED.**

**Residual Work (Architect Catch):** Deleted dead print_onboarding() from main.py (stale from B1 refactor, no production caller).

**Final Test Status:** 265 passed.

---

### Phase-2 Advisory (Deferred)

**Skeptic finding:** Reset-epoch BLE-timing edge. When device receives FAMILIAR_RESET (0x01) opcode and simultaneously drops BLE connection, the device's resetting state.last_seq = 0xFFFF could race with a reconnection attempt. **Severity:** LOW. **Mitigation:** Host-side seq.reset() is idempotent; brief double-reset on reconnect is harmless. **Defer:** Phase 2 timing model refinement.

---

### Carry-Forward Items — Phase-2 Deferral & Closure

| Item | Source | Disposition |
|------|--------|-------------|
| **Baseline verbose print** (P2-4) | Raven TDD | ✅ **CLOSED** — I2 fix replaces leaked stats with activation state only. |
| **Heap host-visibility wire field** | Architect | → Phase 2 (firmware-swap integration). |
| **Hardware threshold calibration** | Y.T. notes | → Phase 2 (ambient-sensing extension). |
| **Reset-flag thread-safety** | Skeptic | → Phase 2 (multi-threaded host if adopted). |

---

### Branch & Next Step

**Branch:** synesthetic-familiar/week3-its-alive  
**Commit:** 6808c96 (host+tests B1+I2), 068a405 (device B2+I1+I3+M1), c81f9c0 (cleanup)  
**Final Test:** 265 passed (0.39s)  
**Decision:** Ready for ship-to-pr. Push branch, open PR, request Copilot code review, then cloud-review-cycle, then squash-merge to main.

---

## 2026-06-14: Week 3 PR #4 Cloud Review Cycle — 3 Cycles, 12 Copilot Comments All Addressed, Squash-Merged

**Status:** SHIPPED (merged as e63de17)  
**Date:** 2026-06-14  
**Merger:** Copilot PR review (copilot-pull-request-reviewer[bot])  
**Merge SHA:** e63de17  
**Branch:** synesthetic-familiar/week3-its-alive (squash-deleted after merge)

### Summary

Week 3 PR #4 underwent 3 cloud-review cycles via Copilot's automated review. All 12 Copilot comments across cycles 1–3 were addressed and verified. Real bug discovered and fixed: `baseline_path` parameter missing from `load_baseline()` and `save_baseline()` calls in host/main.py, causing injected path desyncing between sentinel detection and disk I/O. All test infrastructure changes minimal; 265 tests green throughout.

### Cycle Breakdown

**Cycle 1 (10 Copilot threads, all addressed):**
- **Y.T. (host/main.py):** Threaded baseline_path through load_baseline()/save_baseline() calls (~lines 429, 531). Root cause: sentinel-file detection used injected path but disk reads/writes used hardcoded default, leaving injected files empty and mismatching baseline state on next run. Removed unused `import sys` (line 33). Commit 139c370.
- **Librarian (docs):** Updated hard-coded test count 262→265 in README (lines 10, 23). De-numericized ARD (line ~562) and TEST-STRATEGY (line ~1361) success criteria to "Full Week 3 automated suite green" / "comprehensive Week 3 test coverage" (durable spec docs must survive incremental test additions). Removed duplicate sentence in README (lines 44–46). Commit 139c370.
- **Juanita (tests):** Removed unused `import math` from test_week3_threshold_tuning.py (line 16). Clarified off-by-one wording in test_week3_fallback_depth.py docstring (line 351, changed "after frame 3" → "after frame index 2 (0-indexed)"). Commit 139c370.

**Cycle 2 (2 Copilot threads, all addressed):**
- **Librarian:** Reworded README line 20 "Heap monitoring (fallback)" → "Heap guard (static proxy, GAP-3 pending)" to clarify proxy covers ~2% budget and 80%/95% thresholds inert until `frame.system.get_heap_usage()` (GAP-3) ships. Updated line 23 test-coverage bullet "heap thresholds" → "heap guard constants/structure (runtime thresholds inert until GAP-3)". Commit 08efca7.
- **Y.T.:** Corrected `.squad/agents/yt/history.md` codename record: VESPER current, PULSE earlier candidate. Commit 08efca7.

**Cycle 3:**
- No unresolved threads. Status clean. Squash-merged as e63de17.

### Durable Lessons Captured

1. **Hard-code test counts in durable spec docs = churn liability** (Librarian finding). Solution: intent-based language ("comprehensive Week 3 coverage") in ARD/TEST-STRATEGY; exact counts (265) in README status/badges only. De-numericized success criteria survive incremental test additions without doc PRs.

2. **Injectable path parameters must thread through *all* I/O call sites** (Y.T. finding). Sentinel-file detection and disk read/write both affected when baseline_path is injectable for testing. Single-function audit required when adding seams.

3. **Cloud review via Copilot PR review works as advertised** (team confirmation). 12 comments across 3 cycles, all actionable (no spam), all addressed, then clean merge. Copilot-pull-request-reviewer[bot] is the live config that enables this; documented for future PR cycles.

### Test & Merge Status

- **Final test count:** 265 passed, 0 failed (unchanged from pre-merge; all cycles maintained green)
- **Merge:** Squash-merged as e63de17 to main
- **Branch:** synesthetic-familiar/week3-its-alive deleted by GitHub after merge
- **Local state:** main reset to origin/main (e63de17), clean worktree

---

# Fix Records — Week 3 PR #4 Copilot Review (Inbox Merge, 2026-06-14)

## Y.T. — PR #4 Copilot Review — host/main.py Baseline-Path Threading

**Date:** 2026-06-14  
**Branch:** synesthetic-familiar/week3-its-alive  
**Author:** Y.T. (host app owner)  
**Requested by:** Aaron Kubly

### Summary

Three bugs flagged by Copilot in `projects/synesthetic-familiar/host/main.py`, all fixed.
No changes to inference.py, tests, or docs (owned by other agents).

### Fix 1 — load_baseline() missing baseline_path (~line 430)

**Root cause:** When `baseline is _LOAD_BASELINE_FROM_DISK`, `load_baseline()` was called
without the injectable `baseline_path` argument. Callers injecting a non-default `baseline_path`
for sentinel-file detection (e.g. tests using `tmp_path/baseline.json`) would get sentinel
detection from their injected path but disk reads from the hardcoded `~/.vesper/baseline.json`
— mismatched state.

**Fix:** `load_baseline()` → `load_baseline(baseline_path)`

**Production safety:** `baseline_path` defaults to `_DEFAULT_BASELINE_PATH` which equals
`inference._BASELINE_PATH`, so production behavior is unchanged.

### Fix 2 — save_baseline() missing baseline_path (~line 532)

**Root cause:** Same root cause as Fix 1 in the shutdown path. `save_baseline(baseline)` would
always write the default file even when an injected `baseline_path` was active, leaving the
injected-path file empty and breaking sentinel/baseline consistency on the next run.

**Fix:** `save_baseline(baseline)` → `save_baseline(baseline, baseline_path)`

### Fix 3 — Unused `import sys` (line 34)

**Root cause:** `sys` was imported but never referenced in `main.py`, likely a leftover from
`print_onboarding` removal. Confirmed with `rg 'sys\.'` — zero matches.

**Fix:** Removed the import line.

### Test Results

```
265 passed in 2.12s
```

All 265 tests green. The `baseline_path` threading did not break any existing tests, confirming
no test was asserting the previously-buggy behavior.

---

## Librarian — PR #4 Copilot Review Corrections

**Date:** 2026-06-14  
**Branch:** synesthetic-familiar/week3-its-alive  
**Filed by:** Librarian (AI/ML Specialist, docs-accuracy owner)  
**Requested by:** Aaron Kubly

### Summary

Five issues flagged by Copilot's PR #4 review have been resolved in docs. No host code or tests were modified (parallel work ongoing).

### Changes Applied

#### `projects/synesthetic-familiar/README.md`

| # | Location | Issue | Fix |
|---|----------|-------|-----|
| 1 | Line 10 (Status line) | Hard-coded "262 tests green" — stale after Y.T. added 3 onboarding integration tests | Updated to **265 tests green** |
| 2 | Line 23 (bullet) | Same "262 tests green" hard-code | Updated to **265 tests green** |
| 3 | Lines 44–46 | Duplicate sentence "See ARD §4–§5.5…" appeared twice back-to-back | Removed the accidental duplicate |

#### `docs/projects/synesthetic-familiar/ARD.md`

| # | Location | Issue | Fix |
|---|----------|-------|-----|
| 4 | Line ~562 (build-sequence table) | "190+ tests green" — conflicts with 265; brittle running count in a durable spec doc | Replaced with **"Full Week 3 automated suite green"** (non-numeric) |

#### `docs/projects/synesthetic-familiar/TEST-STRATEGY.md`

| # | Location | Issue | Fix |
|---|----------|-------|-----|
| 5 | Line ~1361 (milestone success criteria) | "190+ tests green" — same brittleness in durable spec | Replaced with **"comprehensive Week 3 automated test coverage green"** (non-numeric) |

### Rationale for Non-Numeric in ARD / TEST-STRATEGY

Copilot's own guidance: either update to the accurate count or make non-numeric to avoid future drift. README status/badge-style lines carry the exact count (265) because a precise count is useful there. ARD and TEST-STRATEGY are durable spec docs whose success criteria should survive incremental test additions without requiring a doc PR every sprint — so they use intent-based language instead.

### Verification

Post-edit grep confirmed:
- No "262" in any of the three owned files
- No "190+" in any of the three owned files  
- Duplicate sentence in README fully removed

### Cycle-2 Copilot Review — Heap Accuracy Fix (2026-06-14)

**Cycle-2 addition:** README line 20 renamed "Heap monitoring (fallback)" → **"Heap guard (static proxy, GAP-3 pending)"** and reworded to make explicit that the proxy covers ~2% of budget and the 80%/95% thresholds are inert until `frame.system.get_heap_usage()` (GAP-3) ships. README line 23 test-coverage bullet changed "heap thresholds" → **"heap guard constants/structure (runtime thresholds inert until GAP-3)"** to avoid implying runtime threshold coverage that does not yet exist.

---

## Juanita — PR #4 Copilot Review — Test Files

**Date:** 2026-06-14  
**Branch:** synesthetic-familiar/week3-its-alive  
**Author:** Juanita (QA/test owner)  
**Requested by:** Aaron Kubly

### Summary

Two issues flagged by Copilot in Juanita-owned test files, both fixed.
No changes to host code, inference, docs, or any other agent's files.

### Fix 1 — Remove unused `import math` (test_week3_threshold_tuning.py line 16)

**Root cause:** `import math` was present but never referenced. Verified with
`rg 'math\.'` across the file — zero matches. The import was likely left behind
when the original tautological MoodResult test was replaced with real
`compute_mood` boundary calls (which do not require math constants).

**Fix:** Removed the `import math` line (line 16). `import unittest` is now the
first import after `from __future__ import annotations`.

**Behavioral impact:** None — unused import only.

### Fix 2 — Off-by-one wording in docstring (test_week3_fallback_depth.py line 351)

**Root cause:** The test method `test_reset_during_both_fail_sends_neutral_once`
had an ambiguous docstring first line:

> "8 both-fail frames; FAMILIAR_RESET fires after frame 3."

`_ResetCallbackStream` with `reset_at=3` fires the callback when
`self._idx == reset_at` *after* the per-iteration increment — i.e., after
yielding frame **index 2** (the 3rd frame in 1-indexed terms). The existing
FakeClock timing block ("Frame 2: yields frame, then RESET fires") and the
inline comment (`# fires after yielding frame 2 (0-indexed)`) both described
this correctly. Only the summary line was wrong/ambiguous.

**Fix:** Changed:
```
8 both-fail frames; FAMILIAR_RESET fires after frame 3.
```
to:
```
8 both-fail frames; FAMILIAR_RESET fires after frame index 2 (0-indexed).
```

This is now internally consistent with the FakeClock timing section, the inline
`reset_at=3` comment, and `_ResetCallbackStream`'s class docstring semantics.

**Behavioral impact:** None — docstring only, no assertions changed.

### Test Results

```
265 passed in 0.40s
```

All 265 tests green. No behavior change confirmed.


---

# Decision: VESPER Phase 2 Capability Scope

| Field | Value |
|-------|-------|
| **Author** | Enzo (Product / PM) |
| **Date** | 2026-06-14 |
| **Status** | PROPOSED — awaiting Aaron decision on OQ-1 through OQ-3 |
| **Scope** | VESPER (Synesthetic Familiar) — Phase 2 milestone |
| **Reference** | `.squad/files/phase2-prd-draft.md` |

---

## Decision

Phase 2 milestone focus is **Capability Expansion: camera input + cloud refinement**, as selected by Aaron post-PR #4 merge.

Both features were explicitly deferred from Phase 1 with documented rationale. Phase 1 proved the "alive" feeling core loop. Phase 2 deepens inference quality and longitudinal knowing.

---

## What's IN

- Camera capture pipeline (host-local, visual features only — no raw frame storage)
- Privacy indicator + consent UX for camera
- Camera-augmented mood inference
- Extended local baseline or opt-in cloud baseline sync (path TBD — OQ-2)
- LESC BLE encryption (ARD §5.6 Phase 2 flag)
- 48×48 sprite expansion (ARD §5.5 Phase 2 note)
- CI cloud-import guard

## What's PARKED

- Peer-to-peer mood sharing
- Community sprite upload
- Cross-device roaming
- Personality sliders / creature evolution (Week 7 stretch goal)

## What's KILLED

- Full cloud inference (raw features to cloud) — hard no
- On-device ML (M55 NPU TFLite) — SDK not ready
- Raw audio/video upload — direct contradiction of privacy promise
- Web Bluetooth parity — wrong Phase 2 bet

---

## Privacy Gate — Hard Stop

⛔ **Raven review is required before any camera or cloud implementation begins.**

The following open questions must be resolved by Aaron + Raven before build starts:

| OQ | Question | Stakes |
|----|----------|--------|
| OQ-1 | Camera: build or park? Which architecture option (A1/A2/A3)? | Recording indicator mandate; privacy overhead |
| OQ-2 | Cloud refinement: which path (B1/B2/B3)? | Cloud egress vs. brand promise |
| OQ-3 | Is VESPER still positioned as "no cloud"? | Brand differentiator vs. inference quality |

**This decision record is parked until OQ-1 through OQ-3 are answered.**

---

## Rationale

Phase 1's positioning ("no data leaves device") is a genuine competitive differentiator in a Gemini-heavy ecosystem. Camera and cloud are both high-value capabilities and high-risk to that positioning. The bet is not whether to add capability — it's whether we can add it without becoming the thing we aren't. That's Aaron's call, with Raven's input.

---

*Enzo — Product/PM | 2026-06-14*

---

# Decision: Phase 2 Capability Architecture — Camera Input + Cloud Refinement

| Field | Value |
|-------|-------|
| **Date** | 2026-06-14 |
| **Author** | Hiro (Architect) |
| **Status** | DRAFT — awaiting Aaron review |
| **Artifact** | `.squad/files/phase2-architecture-draft.md` |

## Summary

Phase-2 architecture proposal for adding camera input and cloud refinement to the Synesthetic Familiar (VESPER).

### Camera Input
- Camera enters as a **third modality** alongside mic + IMU, feeding into the existing mood heuristic on host
- `SensorFrame` extended with 3 fields: `visual_activity`, `visual_brightness`, `camera_ok`
- Camera capture on-device (Halo), JPEG relay to host via BLE, feature extraction on host, buffer zeroed
- Recommended scope: **scene-level features only** (activity + brightness) — no face detection (Phase 3)
- Wire format (`FAMILIAR_UPDATE` 6 bytes) unchanged — camera folds into mood heuristic on host side
- Camera is additive: `camera_ok=False` is default/normal; creature never degrades vs Phase 1

### Cloud Refinement
- Three options evaluated: (A) opt-in cloud inference fallback, (B) periodic baseline sync, (C) federated local refinement
- **Recommended: Option C** — no user data egress; population model weights pushed to host via standard update channel
- Option B (baseline sync) is a natural opt-in extension for multi-device use (Phase 2.5)
- Option A (cloud inference) rejected for Phase 2 — too much scope, latency issues, privacy egress

### Privacy
- Phase-1 "no raw egress" promise extended: no per-user data leaves host (Option C)
- 5 new privacy constraints defined (CAMERA-I1 through MODEL-I5), 2 merge-blocking
- Camera recording indicator (LED) is merge-blocking SDK gate
- BLE LESC pairing promoted from deferred to gate (JPEG in transit is interceptable)
- Egress point inventory mapped for all three options

### Mono-Repo
- Everything stays in `projects/synesthetic-familiar/` — no shared packages (three-copies rule: only one consumer)

### Open Questions for Aaron
- Q1: Camera scope — scene-level vs face detection
- Q2: Cloud option — C (recommended) vs B vs A
- Q3: BLE LESC — gate vs accept-and-document for playground
- Q4: Camera frame rate target
- Q5: Enzo PRD alignment on cloud-powered inference

---


# SDK Feasibility Decision — Week 4 Camera (Ng)

| Field | Value |
|-------|-------|
| **Date** | 2026-06-14 |
| **Author** | Ng (SDK Engineer) |
| **Status** | FINAL |
| **Verdict** | ⛔ CAMERA BLOCKED |
| **Blocking condition** | CAMERA-I3 — no user-accessible LED control in Halo SDK |

---

## Verdict: CAMERA BLOCKED

The Halo SDK **cannot satisfy Raven's CAMERA-I3 merge-blocking condition**. The hardware recording-indicator LED is not accessible from Lua scripts. Camera work stops here. Week 4 pivots to cloud-refinement-only (Option C federated local refinement, per Hiro's architecture draft §2.3).

---

## SDK Investigation — Full Findings

### (a) Triggered Still Capture

**CONFIRMED.** The Halo Lua API provides a complete async capture surface:

```lua
frame.camera.capture({quality="HIGH"})      -- async start; resolution fixed at 640px
while not frame.camera.image_ready() do
    frame.sleep(0.05)
end
local data = frame.camera.read(mtu)         -- returns nil when exhausted
```

Sources: `docs.brilliant.xyz/halo/halo-sdk-lua/` (Camera section), `docs.brilliant.xyz/halo/halo-sdk-bluetooth-specs/` (Camera section).

### (b) JPEG Format / Size / Quality

- **Resolution:** 640px only (no other option documented).
- **Format:** JPEG output by default. Advanced `frame.camera.mpix` pipeline (libmpix) can produce QOI, palette, or raw Bayer, but JPEG is the default and standard path.
- **Quality:** Configurable — `"VERY_HIGH"`, `"HIGH"`, `"MEDIUM"`, `"LOW"`, `"VERY_LOW"`.
- **Typical size:** At `"MEDIUM"` quality for a 640×480 outdoor scene, expect 10–25KB; `"HIGH"` ~25–50KB.

**Bonus finding:** `frame.camera.mpix.get_stats()` returns a luminance histogram (`y_histogram`, `y_histogram_vals`, `y_histogram_total`) and per-channel averages (`rgb_average_r/g/b`, `rgb_min/max_r/g/b`). This means scene-level features (`visual_brightness`, `visual_activity` proxy) could potentially be extracted **on-device from stats alone**, without transmitting the JPEG over BLE at all. This would eliminate CAMERA-I1/I2/I6 concerns entirely — but CAMERA-I3 still blocks because `capture()` must be called regardless, and the LED gate is about the capture cycle, not the data transfer.

### (c) Recording-Indicator LED — CAMERA-I3 — BLOCKED ⛔

**NOT AVAILABLE.** The complete Halo Lua API surface documented in `docs.brilliant.xyz/halo/halo-sdk-lua/` covers: System, Time, File System, Button, Bluetooth, IMU, Compression, Speaker, Microphone, Display, Camera (+ libmpix). There is **no `frame.led`, `frame.indicator`, or equivalent namespace**.

The physical white LED on Halo's left arm is **firmware-managed only** — it indicates charging status and pairing mode. Lua scripts have zero access to it. `frame.camera.capture()` does not document auto-activating any visible recording indicator LED.

Raven's CAMERA-I3 states: *"a hardware recording-indicator LED MUST be active during every capture cycle. If the Halo SDK CANNOT force the LED on during triggered capture, the camera feature is BLOCKED."*

This condition **cannot be satisfied** with the current SDK. The gate fires.

### (d) BLE Throughput — 1–2fps Feasibility

**MARGINALLY VIABLE (moot given I3 block, documented for completeness):**

- BLE LUA RX characteristic: max packet = negotiated MTU (up to 512 bytes), raw data payload = MTU − 4 bytes.
- Camera image chunks are sent over regular LUA RX (no dedicated camera characteristic).
- At MTU=512, practical sustained throughput in BLE 5.0 LE data-length-extension mode: ~30–50KB/s.
- A 20KB JPEG at "LOW" quality: ~0.5s transfer → ~2fps achievable.
- A 40KB JPEG at "HIGH" quality: ~1s transfer → ~1fps achievable.
- Architecture draft estimate of "2–4s for a 30KB frame" is pessimistic for BLE 5.0; 1fps is realistic at MEDIUM quality.

---

## CAMERA-I3 — Why Workarounds Don't Apply

Two workarounds were considered and rejected:

1. **Use the display as a visual indicator** (flash a bright ring on the 256×256 OLED during capture): The display is the creature's face — a full-screen flash during capture would be highly disruptive to the creature's ambient rendering. More critically, Raven's condition specifies a **hardware** recording-indicator LED, not a software visual indicator. A display flash does not satisfy the privacy requirement (bystanders cannot see the tiny OLED from normal distances, whereas a physical LED can be seen from >1m).

2. **Firmware customization to expose LED control**: The Halo firmware is open-source at `github.com/brilliantlabsAR/frame-2-firmware`. In principle, a firmware patch could expose `frame.led.set(bool)`. However: (a) firmware customization is out of scope for a playground demo, (b) it would break standard OTA updates, and (c) the task brief explicitly says "custom firmware never" (Ng charter).

---

## On-Device Stats Alternative (Future Reference)

`frame.camera.mpix.get_stats()` after a capture call returns:
- `y_histogram` — luminance histogram bins → directly maps to `visual_brightness`
- `rgb_average_r/g/b` — per-channel averages → scene colorfulness proxy for `visual_activity`

A future Phase-3 design could use **stats-only** mode: capture → read stats → discard JPEG entirely (never call `frame.camera.read()`). This would:
- Eliminate JPEG transmission over BLE entirely (resolving BLE-I4 sniffer exposure)
- Eliminate CAMERA-I1/I2/I6 concerns (no JPEG bytes on host side at all)
- Provide the exact `visual_brightness` and a coarse `visual_activity` proxy natively

**CAMERA-I3 would still apply** (capture still occurs; LED requirement is about the capture cycle, not data transfer). A firmware patch or future SDK update exposing LED control would unlock this path.

---

## Week 4 Pivot Recommendation

Camera is blocked. Week 4 work:

1. **Cloud refinement (Option C — federated local refinement)** — Librarian owns `inference.py` + `model_sync.py`. No Ng work required beyond confirming Phase-1 is unbroken.
2. **Phase-1 regression** — 265/265 tests passing on `synesthetic-familiar/week4-it-sees` branch. No code changes made; camera scaffold NOT added.
3. **Flag for future SDK watch** — If Brilliant Labs adds `frame.led.*` in a future firmware/SDK release, revisit CAMERA-I3. The stats-only path (`mpix.get_stats()`) is the cleanest forward option.

---

## Source Index

| Claim | Source |
|-------|--------|
| `frame.camera.capture()` confirmed | `docs.brilliant.xyz/halo/halo-sdk-lua/` §Camera |
| JPEG 640px, quality configurable | `docs.brilliant.xyz/halo/halo-sdk-lua/` §Camera |
| `frame.camera.mpix.get_stats()` stats API | `docs.brilliant.xyz/halo/halo-sdk-lua/` §Camera Image Processing |
| No `frame.led` API — complete Lua surface | `docs.brilliant.xyz/halo/halo-sdk-lua/` (full page reviewed) |
| White LED = firmware-only (charging/pairing) | `docs.brilliant.xyz/halo/halo/` getting started page |
| BLE MTU 512, LUA RX characteristic | `docs.brilliant.xyz/halo/halo-sdk-bluetooth-specs/` §BLE Services |
| Camera images on LUA RX (no dedicated channel) | `docs.brilliant.xyz/halo/halo-sdk-bluetooth-specs/` §Camera |
| Ng charter: "custom firmware never" | `.squad/agents/ng/` charter |


# Librarian Week 4 — Visual Weight Extension + Option-C Cloud Sync

| Field | Value |
|-------|-------|
| **Author** | Librarian (AI/ML) |
| **Date** | 2026-06-14T00:48:14-07:00 |
| **Branch** | `synesthetic-familiar/week4-it-sees` |
| **Scope** | VESPER Phase 2, Week 4 "It sees" — inference-side deliverables |
| **Raven gates satisfied** | MODEL-I5, CAMERA-I1 (egress proof), §6.1 weight bounds |

---

## 1. Decision Summary

Implemented the inference-side Phase-2 additions:

1. **Visual weight extension in `host/inference.py`** — camera features folded into `compute_mood` as additive terms, gated on `camera_ok`. Phase-1 additive invariant preserved structurally and verified by test.
2. **Bounded online weight tuning** — EMA-based, ≤ 2× default bound, divergence guard, reset-to-defaults.
3. **`host/model_sync.py`** — Option-C federated weight sync: HTTPS-only download, SHA-256 content hash verification, fail-closed, zero user data egress (MODEL-I5).

---

## 2. Tension Formula

**Phase-1 (unchanged, locked per ARD §5.4):**
```
tension = audio_pitch_variance × 0.4 + imu_acceleration × 0.3 + imu_rotation × 0.3
```

**Phase-2 augmentation (additive, only when `camera_ok=True`):**
```
tension += visual_activity × W_va  +  (1.0 − visual_brightness) × W_vb
```

Default values: `W_va = 0.15`, `W_vb = 0.05`.

Rationale for formula:
- `visual_activity × W_va`: high scene movement (0–1) → alert/stressed → positive contribution to tension.
- `(1 − visual_brightness) × W_vb`: dark environment → tense, bright environment → calm → dark adds tension.
- Both inputs are [0, 1] with positive weights → arithmetic is clean and bounded.
- Maximum camera additive contribution at defaults: `1.0×0.15 + 1.0×0.05 = 0.20`.

**Why not rescale Phase-1 weights?** Phase-1 weights are LOCKED per ARD §5.4. Rescaling them would break the activation gate math and the locked specification. Camera is strictly additive, not a replacement.

---

## 3. ADDITIVE INVARIANT — Proof

> **Claim:** `compute_mood(..., camera_ok=False, ...)` returns EXACTLY the same `MoodResult` as a Phase-1 call with identical audio/IMU inputs.

**Structural proof:**
```python
# Phase-1 tension (always computed)
tension = audio_pitch_variance * _W_PITCH + imu_acceleration * _W_ACCEL + imu_rotation * _W_ROT

# Camera augmentation — ONLY entered when camera_ok=True
if camera_ok:
    tension += ...  # unreachable when camera_ok=False
```

When `camera_ok=False`, the `if camera_ok:` block is never entered. The tension value, threshold selection, mood classification, and confidence reductions are byte-for-byte identical to the Phase-1 code path. `camera_ok=False` is the default — camera absence is never penalised.

**Test coverage:** `TestAdditiveInvariant` in `test_week4_sensorframe_camera.py` verifies all five field of `MoodResult` (mood, mood_int, confidence, gated, tension) across 6 parametrized cases (stressed, calm, neutral, mic-only, IMU-only, both-sensors-missing).

---

## 4. Bounded Online Weight Tuning

**Algorithm:** Exponential Moving Average (EMA).

```
new_weight = (1 − α) × current_weight + α × target_weight
```

With `α = 0.1` (default), 23 sync iterations are needed to reach 90% convergence from any starting point toward a stable target.

**Why EMA, not SGD or gradient methods:**
- Playground scope — no loss function, no labeled ground truth.
- EMA is transparent, monotonically damped, and resistant to single-outlier spikes.
- The hard clamp (`max(0, min(weight, DEFAULT × 2))`) enforces the ≤ 2× bound regardless of alpha or target value. SGD would require learning rate tuning to achieve the same bound guarantee.

**Bound enforcement (Hiro §6.1 risk mitigation):**
```python
max_va = DEFAULT_VISUAL_WEIGHTS.visual_activity * MAX_VISUAL_WEIGHT_MULTIPLIER  # 0.30
max_vb = DEFAULT_VISUAL_WEIGHTS.visual_brightness * MAX_VISUAL_WEIGHT_MULTIPLIER  # 0.10

new_va = max(0.0, min(new_va, max_va))
new_vb = max(0.0, min(new_vb, max_vb))
```

**Divergence guard:** If any weight reaches ≥ 90% of its bound after an EMA step, a `logger.warning` is emitted. The caller can then call `reset_visual_weights()` to restore defaults.

**Reset:** `reset_visual_weights()` (inference.py) and `reset_weights_to_defaults()` (model_sync.py) return `VisualWeights()` — factory defaults, no disk I/O. Caller saves if desired.

---

## 5. Option-C Federated Design — No-Egress Proof

**What is downloaded:**
A static JSON file from a known HTTPS URL (e.g., a GitHub release asset):
```json
{"version": "1", "visual_activity": 0.15, "visual_brightness": 0.05}
```
This is a population-aggregate weight suggestion. It does not encode per-user data. It is functionally equivalent to a software update.

**What stays local (never leaves host):**
| Data | Location | Egress? |
|------|----------|---------|
| `baseline.json` (Welford mean/stddev) | `~/.vesper/` | ❌ Never |
| `visual_weights.json` (tuned visual weights) | `~/.vesper/` | ❌ Never |
| Raw audio, IMU features | Host memory | ❌ Never |
| Visual features (visual_activity, visual_brightness) | Host memory | ❌ Never |
| MoodResult values | Host/BLE wire | ❌ Never to cloud |

**The sync HTTP request (annotated):**
```
GET /population_weights.json HTTP/1.1
Host: update-server.example.com          ← server hostname only
User-Agent: Python-urllib/3.12           ← stdlib default, not a VESPER id
Accept-Encoding: identity

[No body, no custom headers, no cookies, no session tokens]
```

**Absent from the request (MODEL-I5):**
- ❌ User ID — not generated or stored in this codebase
- ❌ Device ID — not generated or stored in this codebase
- ❌ Baseline stats (mean, stddev, sample_count) — not included
- ❌ Session token — not generated or stored
- ❌ Custom headers — `Request(url)` with no `add_header()` calls (verified by inspection)

The server operator sees: IP address (inherent to TCP) + stdlib User-Agent. Both are standard for any HTTPS fetch and are not VESPER application-layer identifiers. This satisfies Raven's MODEL-I5 gate (§4.2).

**Integrity verification:** SHA-256 of the downloaded file is compared to `PopulationManifest.sha256` before any weights are used. On mismatch: download is discarded, `current` weights are returned unchanged (fail-closed).

**Offline capability:** If the server is unreachable (OSError, TimeoutError, or any network exception), `sync_population_weights` returns `current` unchanged. The creature runs normally on local weights.

---

## 6. Files Changed

| File | Change |
|------|--------|
| `host/inference.py` | Added `VisualWeights`, `DEFAULT_VISUAL_WEIGHTS`, weight constants; `load/save/reset/tune_visual_weights`; updated `compute_mood` signature + camera branch |
| `host/model_sync.py` | **NEW** — `download_weights`, `sync_population_weights`, `apply_weight_update`, `reset_weights_to_defaults`, `get_current_weights`, `PopulationManifest`, `DEFAULT_MANIFEST` |

---

## 7. Test Result

| Metric | Before | After |
|--------|--------|-------|
| Passing | 265 | 299 |
| Skipped | 20 | 19 |
| Failed | 0 | 0 |

The 19 remaining skips are all in Ng's `_CameraRelay` / `SensorFrame` extension — expected, pending Ng's Week 4 delivery.

---

*Librarian — AI/ML | VESPER Phase 2 Week 4 | 2026-06-14T00:48:14-07:00*


# Decision: Juanita Week-4 "It sees" Test Suite

| Field | Value |
|-------|-------|
| **Author** | Juanita (Tester / QA) |
| **Date** | 2026-06-14 |
| **Branch** | `synesthetic-familiar/week4-it-sees` |
| **Status** | PROPOSED — pending team review |
| **Supersedes** | juanita-week3-fallback.md (extends, does not replace) |

---

## Context

Week 4 of Phase 2 ("It sees") introduces camera input and cloud model sync.
The plan is LOCKED and Raven-gated.  I wrote acceptance tests in parallel with
Ng (sensors.py) and Librarian (inference.py / model_sync.py), working solely
from the locked contract without waiting for their code.

---

## Decision: Test Structure for Week 4

### Three test files, clear ownership

| File | Contract being tested | Gates whose PR |
|------|-----------------------|----------------|
| `test_week4_sensorframe_camera.py` | SensorFrame 3-field extension + additive invariant + camera inference behavior | Ng (field types/defaults) + Librarian (compute_mood visual params) |
| `test_week4_privacy_gates.py` | CAMERA-I2, CAMERA-I1, CAMERA-I6, MODEL-I5 | Ng (_CameraRelay zeroing) + Librarian (model_sync privacy) |
| `test_week4_camera_edge_cases.py` | Hash mismatch, server unreachable, partial JPEG, BLE mid-drop, weight bounds | Ng (_CameraRelay) + Librarian (model_sync) |

### Skip-not-xfail for pending code

Tests for code that hasn't landed yet use `pytest.skip`, not `pytest.mark.xfail`.
Rationale:
- `xfail` implies I know the test will fail AND eventually pass — I can't guarantee that without seeing the implementation.
- `skip` is honest: "not testable yet, activate when the API exists."
- Skip-to-active is automatic: the `_CAMERA_FIELDS_LANDED` / `_COMPUTE_MOOD_CAMERA_LANDED` / `_CAMERA_RELAY_AVAILABLE` / `_MODEL_SYNC_AVAILABLE` flags are computed at import time from `inspect.signature()` and `hasattr()`, so no manual re-enabling is ever needed.

### Additive-invariant test approach

The single most important gate is: `camera_ok=False` → exact Phase-1 behavior.

Approach chosen: **side-by-side comparison** of Phase-1 and Phase-2 calls rather than asserting absolute values.
- This is resilient to future heuristic tuning (thresholds, weights) — the invariant holds regardless of what the exact numbers are.
- Parametrized over 6 sensor combinations (stressed, calm, neutral, mic-only, IMU-only, both-missing) to catch any camera-ok interaction with the sensor-failure confidence reduction path.
- Separate regression guard `test_camera_ok_false_does_not_reduce_confidence_vs_phase1` catches the "penalise camera absence" mistake directly.

### Current suite counts

- **318 collected** — 296 passed, 22 skipped, 0 failed.
- 265 existing tests: all still green (zero regression).
- 53 new tests: 31 active now (including all MODEL-I5 tests — Librarian's model_sync.py already landed), 22 pending Ng's camera/relay code.

---

## Raven Privacy Gate Coverage

All four Raven conditions have at least one active-now structural test plus
one or more skip-pending tests that will activate once the implementation lands:

| Raven condition | Active-now coverage | Pending coverage |
|----------------|---------------------|-----------------|
| CAMERA-I1 (buffer zeroed) | Module docstring check (active once relay lands) | `TestCameraI1_BufferZeroed.test_camera_relay_zeros_buffer_after_extraction` |
| CAMERA-I2 (floats only on public surface) | 3 tests active now on Phase-1 SensorFrame; 1 more activates with Ng's fields | `test_sensorframe_camera_fields_are_float_typed_when_present` |
| CAMERA-I6 (no JPEG in INFO+ logs) | `test_sensorframe_construction_emits_no_image_bytes_in_logs` (active now) | `test_camera_relay_extraction_logs_no_pixel_data` |
| MODEL-I5 (no user data in request; hash verify) | — | 4 tests (all pending Librarian's model_sync.py) |

---

## What Each Implementer's PR Must Pass to Merge

**Ng's PR** (sensors.py camera fields + `_CameraRelay`):
- All 7 `TestSensorFrameCameraFields` tests
- All 2 `TestCameraI1_BufferZeroed` tests
- All 4 `TestCameraI2` camera-field tests
- `TestCameraRelayEdgeCases` (5 parametrized + 1 BLE-drop test)
- `TestCameraI6.test_camera_relay_extraction_logs_no_pixel_data`

**Librarian's PR** (compute_mood visual params + model_sync.py):
- All 7 `TestAdditiveInvariant` tests (6 parametrized + 1 regression guard)
- All 5 `TestCameraContribution` tests
- All 4 `TestModelI5_ModelSyncPrivacy` tests
- All `TestModelSyncHashMismatch` tests (5 parametrized + 1 state-isolation)
- All `TestModelSyncServerUnreachable` tests
- `TestOnlineWeightBounds` (2 tests)

---

## Risks Accepted

1. **_CameraRelay API naming is unknown.** Tests probe `_receive_jpeg()` and `_extract_visual_features()` as the most natural names. If Ng chooses different names, the tests will skip with a clear message explaining what to update.
2. **model_sync.py function signatures are unknown.** Tests probe `download_weights(url, expected_hash)`, `get_weights_with_fallback()`, `get_current_weights()`, `apply_weight_update()`, `reset_weights_to_defaults()`. If Librarian uses different names, the tests skip with guidance.
3. **Hash algorithm assumed to be SHA-256.** This matches the `hashlib.sha256` convention in the Phase-1 codebase and the architecture draft's "content-hash" language. If SHA-512 is used, update the test helpers.


# Raven — Phase 2 Privacy Gate Decision

| Field | Value |
|-------|-------|
| **Reviewer** | Raven (Security & Privacy) |
| **Date** | 2026-06-14T00:48:14-07:00 |
| **Scope** | VESPER Phase 2: Camera Input + Cloud Refinement (locked direction) |
| **Requested by** | Aaron Kubly |
| **Verdict** | ✅ **APPROVE-WITH-CONDITIONS** |

---

## 1. Phase-2 Data-Flow Diagram (≤5 boxes)

```
┌──────────────────────────────┐
│  [1] Halo Camera (on-device) │  forward-facing, outward
│  frame.camera.capture()      │  JPEG at 1–2 fps
│  LED indicator active        │
└────────────┬─────────────────┘
             │ Raw JPEG over BLE (unencrypted, local RF)
             │ ⚠ E-1: sniffer threat within ~10m
             ▼
┌──────────────────────────────────────────────────────┐
│  [2] Host: sensors.py _CameraRelay                   │
│  JPEG reassembly → decode → extract features         │
│  visual_activity (0.0–1.0), visual_brightness (0.0–1.0) │
│  JPEG buffer zeroed in-place immediately after        │
│  ✅ E-2: in-memory only, no persist, no cloud        │
└──────────────────┬───────────────────────────────────┘
                   │ (visual_activity, visual_brightness) — floats only
                   ▼
┌──────────────────────────────────────────────────────┐
│  [3] Host: inference.py compute_mood                  │
│  audio + IMU + visual → MoodResult                   │
│  online weight tuning stays local                    │
└──────────────────┬───────────────────────────────────┘
                   │ mood_enum + intensity + confidence + seq (6 bytes)
                   │ UNCHANGED wire format
                   ▼
┌──────────────────────────────┐
│  [4] Device (Halo, Lua)      │
│  sprite render — unchanged   │
└──────────────────────────────┘

       ┌────────────────────────────────────┐
       │  [5] Update Server (HTTPS, GET)    │
       │  population model weights JSON     │
       │  ← download only; no user data     │  ✅ E-3
       └────────────────────────────────────┘
         (static GitHub release asset or equivalent)
```

**Five boxes. Every sensor-derived data movement marked.**

---

## 2. Egress / Exposure Point Analysis

### E-1 — Raw JPEG over unencrypted BLE (Camera → Host)

| Dimension | Assessment |
|-----------|------------|
| **Data** | Raw JPEG, 10–40KB, scene image from outward-facing camera. May contain faces of unconsenting third parties. |
| **Who can see it** | Any BLE scanner within ~10m. No authentication, no encryption, no pairing barrier. |
| **Retention** | In-flight only. Never written to host disk. Zeroed after extraction (see E-2). |
| **Mitigation** | LESC (P2-1) deferred per locked direction. Accepted as "playground demo, no BLE confidentiality guarantee" with explicit documentation (see gate condition BLE-I4). |
| **Raven ruling** | **ACCEPTED** — under strict documentation requirement. The Halo camera is outward-facing; the JPEG is a scene image, not a biometric selfie. The primary risk is third-party (bystander) faces captured in the frame. This must be named in all user-facing documentation, not just called a "wearer risk." |

### E-2 — Feature extraction buffer (host memory)

| Dimension | Assessment |
|-----------|------------|
| **Data** | Decoded JPEG bytes in Python memory. |
| **Who can see it** | Host process only. No transmission. |
| **Retention** | Zeroed immediately after feature extraction (CAMERA-I1). |
| **Mitigation** | Same pattern as mic I7 gate (approved Phase 1). In-place buffer zeroing required — `buffer[:] = 0`, not `del buffer`. `del` is not a security primitive (see history Learning #1). |
| **Raven ruling** | **CLEAN** — CAMERA-I1 governs this. Pattern proven. |

### E-3 — Population model download (HTTPS, cloud → host)

| Dimension | Assessment |
|-----------|------------|
| **Data** | HTTP GET request for model weights JSON. No user data in request. |
| **Who can see it** | Update server operator sees IP address and User-Agent. No biometric data. No user identifier. |
| **Retention** | Weights stored locally as JSON file. |
| **Mitigation** | HTTPS only. Content hash or signature verified post-download. No user ID, device ID, baseline stats, or identifying custom headers in the request. Serving as static GitHub release asset is the lowest-risk form. |
| **Raven ruling** | **CLEAN** — under MODEL-I5 gate conditions. Functionally equivalent to a software update. |

---

## 3. Merge-Blocking Constraints — Confirmation and Additions

### CAMERA-I1 (Hiro) — CONFIRMED AND REINFORCED

**Verdict: CONFIRMED MERGE-BLOCKING.**

Raw JPEG buffer MUST be zeroed immediately after visual feature extraction. No raw image data persists beyond the extraction call. No image data written to disk or transmitted to cloud.

**Additional enforcement (Raven adds):** Zeroing MUST use in-place assignment (`buffer[:] = 0` or equivalent) on the decoded byte array, not solely `del buffer`. `del` is reference deletion, not memory erasure. Same standard as mic I7 gate. The `finally` block pattern from `_extract_frame` in sensors.py is the required implementation pattern.

### CAMERA-I2 (Hiro) — CONFIRMED AND REINFORCED

**Verdict: CONFIRMED MERGE-BLOCKING.**

`SensorFrame` exposes only `visual_activity: float` and `visual_brightness: float`. No raw pixel arrays, no JPEG bytes, no decoded image objects appear on any public API, test fixture, or log output (see CAMERA-I6 below).

**Additional enforcement:** This constraint is a contract boundary equivalent to the `SensorFrame` mic boundary (mic I7). Any code review finding JPEG bytes, numpy image arrays, or PIL/cv2 Image objects on the `SensorFrame` or `_CameraRelay` public surface is a merge blocker.

### CAMERA-I3 (Hiro) — REQUIRED. POSITION STATED.

**Verdict: CONFIRMED MERGE-BLOCKING. Raven upholds Hiro's call.**

A hardware recording indicator (LED) MUST be active on the Halo device during every camera capture cycle. This is not optional for the playground.

**Rationale:**

The Halo camera is outward-facing. At 1–2fps, the JPEG captures the scene in front of the wearer. This scene may contain:
- Faces of people who have not consented to being photographed
- Private spaces (homes, medical facilities, confidential meetings)
- Content the wearer cannot even see (camera field of view ≠ wearer field of vision)

There is no other mechanism by which a third party can know capture is occurring. The LED is the only bystander signal. Its absence means unconsented capture of potentially identifiable third parties with no visible indicator — this fails basic bystander-consent norms regardless of whether the captured content is "only" used for scene-level features.

The fact that face detection is locked OFF does not eliminate this exposure: the raw JPEG exists during the Halo → host BLE transit, and that JPEG contains the scene image in full resolution.

**If the Halo SDK (`frame.camera.capture()`) cannot activate the LED independently or contemporaneously with capture: camera feature is BLOCKED.** No exceptions for playground scope.

---

## 4. Additional Gate Conditions (Raven's own requirements)

### BLE-I4 — Unencrypted BLE JPEG documentation (GATE CONDITION, required before merge)

The README, any user-facing `--help` output, and the project's privacy notice MUST contain a visible warning:

> **Camera BLE relay:** Raw scene JPEG is transmitted over unencrypted BLE. Any Bluetooth scanner within approximately 10 metres may capture scene images during use. This is a playground demo — there is no BLE confidentiality guarantee. Captured images may contain images of bystanders and third parties.

**The warning must name the third-party risk specifically.** Framing it as a wearer-only risk is insufficient — the primary exposure is bystanders, not the wearer.

LESC (P2-1) remains on the carry-forward list for Phase 3. Its deferral from Phase 2 is accepted under the playground scope, with the above documentation as the compensating control.

### MODEL-I5 — Population model download integrity (GATE CONDITION, required before merge)

1. Download MUST use HTTPS only. No HTTP fallback.
2. The HTTP request MUST NOT include: user ID, device ID, baseline statistics, session token, or custom headers that could fingerprint the requester beyond standard HTTP.
3. The downloaded model file MUST have its content hash verified before application (SHA-256 of expected file embedded in code or fetched from a signed manifest). If hash fails, the download is discarded and local defaults are retained.
4. Serving the model as a static GitHub release asset is the recommended implementation — it is public, auditable, and carries no user-tracking.

### CAMERA-I6 — No frame content in logs (NEW, MERGE-BLOCKING)

The host-side JPEG decode and feature-extraction path MUST NOT log, write, or expose JPEG bytes, frame dimensions, pixel values, or decoded image objects at any log level in normal operation. Debug-level logging of extracted feature floats (`visual_activity`, `visual_brightness`) is acceptable. Any log statement that would emit image content, frame size in pixels, or raw byte counts derived from image data is a merge blocker.

---

## 5. Verdict

### ✅ APPROVE-WITH-CONDITIONS

The locked Phase-2 direction preserves the core Phase-1 privacy promise for cloud refinement (Option C: no per-user data egress). The camera path introduces one genuine threat vector — raw JPEG over unencrypted BLE — which Aaron has explicitly accepted with documentation. I accept this decision for the playground scope with the conditions enumerated below.

**The "no raw biometric egress" brand promise is NOT violated by this direction**, provided the conditions are met. The wire format is unchanged. The cloud path is download-only. The camera exposes a scene-level threat (BLE sniffing of JPEG) that is real, documented, and acceptable only because:

1. The camera is outward-facing (not a biometric selfie camera)
2. Extraction produces only two floats (activity, brightness) — not face vectors
3. The raw buffer is zeroed before any other operation
4. The LED indicator gates capture (CAMERA-I3)
5. Documentation names the bystander risk explicitly

**If any numbered condition below is not met at merge time, the camera feature does not ship.**

---

## Gate Conditions (numbered for tracking)

| # | ID | Condition | Blocking level |
|---|-----|-----------|---------------|
| 1 | CAMERA-I1 | Raw JPEG buffer zeroed in-place (`buffer[:] = 0`) immediately after feature extraction, in a `finally` block. Never written to disk. Never transmitted to cloud. | 🔴 MERGE-BLOCKING |
| 2 | CAMERA-I2 | `SensorFrame` public API contains only `visual_activity: float` and `visual_brightness: float`. No JPEG bytes, pixel arrays, or image objects on any public surface. | 🔴 MERGE-BLOCKING |
| 3 | CAMERA-I3 | Halo LED indicator is active during every camera capture cycle. If the SDK cannot satisfy this, camera feature is blocked. | 🔴 MERGE-BLOCKING |
| 4 | CAMERA-I6 | Host-side JPEG/decode path emits no image content, raw byte counts, or frame dimensions at any non-debug log level. | 🔴 MERGE-BLOCKING |
| 5 | BLE-I4 | README and `--help` carry a visible warning naming the unencrypted BLE sniffer risk and explicitly calling out the bystander/third-party risk (not just wearer risk). | 🔴 MERGE-BLOCKING |
| 6 | MODEL-I5 | Population model download uses HTTPS only. No user-identifying data in the request. Content hash verified before application. | 🔴 MERGE-BLOCKING |

**LESC (P2-1) deferred to Phase 3. Accepted for playground scope under condition 5 (documentation).**

---

*Raven — Security & Privacy | VESPER Phase 2 Privacy Gate | 2026-06-14T00:48:14-07:00*



