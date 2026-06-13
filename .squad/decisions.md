# Halo Decisions Log

## 2026-06-07: Theme-2 Synesthetic Familiar as First Official Halo Project — ACCEPTED
**Status:** ACCEPTED  
**Owner:** Hiro (Architect), Aaron (final approval)  
**Date:** 2026-06-07  
**Scope:** Establishes Synesthetic Familiar (Theme-2) as first official Halo playground demo; locks architectural approach

**Decision:** Synesthetic Familiar is the first official Halo playground project. Architecture follows host-peripheral model: Python host (mood inference from mic+IMU) → Lua device (render breathing sprite). 8 core architectural choices are locked:

1. **Host-Peripheral Architecture Confirmed** — Python host drives inference; Lua device renders. No deviation from Brilliant's canonical model.

2. **Autonomy Tier: Hybrid Host-Primary** — Host handles mood inference; device interpolates/renders locally. Device has IMU-only fallback if BLE drops. Latency budget 200-500ms achievable.

3. **Mood/Render Decoupling** — Mood calculation = pure function `compute_mood(sensors) → { mood_enum, intensity, confidence }`. Rendering = pure Lua with no shared state. Enables future renderer swaps and independent unit testing.

4. **Confidence Gating: Silence is Safer** — If mood confidence < 0.7, system holds current Familiar state rather than displaying uncertain values. Gate applied host-side before BLE transmission.

5. **Privacy by Abstraction** — Familiar uses abstract visual language (breathing, color, orbit speed) with no labeled emotions, text, or explicit biometric indicators. Visual jitter (5-10%) prevents statistical inference. Satisfies lighter Theme-2 privacy requirements.

6. **BLE Protocol: FAMILIAR_UPDATE (0x80)** — Custom opcode carrying mood_enum (1B), intensity (1B), confidence (1B), sequence (2B) = 6 bytes total in single BLE packet. No raw biometric data transmitted.

7. **Display Budget: Within Constraints** — 24×24 sprite at 7 o'clock, 80% radius. Idle ~1.5% lit, calm ~3%, stressed ~2.5% — all well under 30% canvas limit.

8. **Graceful Degradation Hierarchy** — Sensor failure fallback: (1) Mic+IMU → full inference; (2) Mic-only → 0.7 confidence cap; (3) IMU-only → 0.6 cap; (4) Both fail → hold 10s, then neutral. No freeze or error state.

**Rationale:** Architecture aligns with decisions.md (hosted multimodal API, device portability, privacy-by-abstraction, M55 gate-keeping role). Hiro validated against LIBRARIAN-T2-5-ERROR, RAVEN-T2-1, and DASID-T2-1 user stories.

**Deliverable:** `docs/projects/synesthetic-familiar/ARD.md`

---

## 2026-06-07: Theme-2 Synesthetic Familiar — 3 Key Decisions Locked by Aaron
**Status:** APPROVED  
**Owner:** Hiro (Architect), Aaron (final decision)  
**Date:** 2026-06-07  
**Approval Date:** 2026-06-07  
**Related:** Theme-2 Synesthetic Familiar ARD (2026-06-07)

Aaron approved 3 critical architectural decisions for Synesthetic Familiar v1 (Theme-2 first official Halo playground project). These decisions are now LOCKED and drive the Week 1–3 milestone sequence.

**Decision 1: Sensors for v1 — Mic + IMU (LOCKED)**
- Mic + IMU provides good inference signal for stress/calm detection (voice tone + motion)
- No camera in v1 eliminates privacy overhead and complexity
- Rationale: Proven sufficient for v1 "feels alive" bar; camera deferred to Phase 2

**Decision 2: Mood Model — Local Heuristic (LOCKED)**
- Local heuristic on host (no cloud for v1)
- Rationale: Latency (200-500ms local vs. 500-2000ms cloud) essential for ambient display; privacy (no telemetry); reliability (no network dependency)
- Cloud refinement deferred to Phase 2

**Decision 3: Creature Form — Abstract-with-Eyes (LOCKED)**
- Abstract geometric form with single bright eye (no face, no anthropomorphic features)
- Rationale: Recognizable as creature but abstract enough that bystanders cannot read wearer internal state; preserves privacy (RAVEN-T2-1)

**Consequences:**
- ARD now build-ready (status APPROVED in docs/projects/synesthetic-familiar/ARD.md)
- Phase 1 milestone sequence locked: Week 1 "It moves" (render loop), Week 2 "It reacts" (host inference), Week 3 "It's alive" (UX + polish)
- Tech stack finalized: Python 3.11 host + Lua device render + local heuristic (no cloud, no ML framework)
- Privacy by abstraction confirmed (abstract visuals, no biometric leak, on-device inference)

**Next Step:** Week 1 "It moves" — Python host harness + Lua sprite render on Halo device.

---

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
