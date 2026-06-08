# Project Context

- **Owner:** Aaron Kubly
- **Project:** halo — mono-repo playground for authoring apps on Halo smart glasses
- **My layer:** Tests, test infra, edge cases, correctness review
- **Testing reality:** BLE is flaky by nature; hardware-in-the-loop tests are slow — mock when possible, real device when necessary
- **Created:** 2026-06-01

## Learnings

### Emulator & Simulator Coverage (2026-06-01)
- **Official emulator:** `halo-emulator` (Python SDK only) — experimental, but feature-complete
- Covers: Lua 5.3 runtime, display rendering (256×256), button events, IMU injection, battery state, audio/data I/O
- **Cannot** test: Real BLE flake, actual camera JPEG output (mock only), firmware upgrade flow, device pairing mode
- **Python = emulator-first:** pytest-ready test harness, mock Bluetooth, framebuffer inspection
- **Flutter = real-device only:** No emulator; uses real BLE stack (`brilliant_ble` 4.0+). Can run `flutter test` on business logic, but Halo integration tests require hardware.
- **Web Bluetooth = real-device only:** Chromium-only (Chrome/Edge/Opera), requires actual BLE device and browser security context

### Testing Stack per SDK Flavor (2026-06-01)
- **Python:** pytest + halo-emulator + brilliant-msg (msg codes 0x0B, 0x20, etc.)
- **Flutter:** flutter test (unit/widget) + device tests via adb; no Halo-specific emulator
- **Web Bluetooth:** Jest/Vitest (browser test via Puppeteer/Playwright) + real device for integration
- **Lua-only apps:** halo-emulator can load Lua directly; REPL interactive mode for manual testing

### BLE & Hardware Edge Cases Worth Pre-Listing (2026-06-01)
1. **BLE disconnect mid-operation:** No automatic reconnect; caller must detect broken connection and re-init. Test: inject BLE error mid-photo capture.
2. **Pairing mode transience:** Button hold to enter pairing mode (10s LED flash). Timeout behavior not documented. Test: simulate missed pairing window, verify error handling.
3. **Firmware update window:** Must stay in BLE range, close proximity. Partial update leaves Halo in unknown state. Test: can't emulate; hardware-only. Flag for manual testing.
4. **Bluetooth MTU negotiation:** Python/Flutter auto-negotiate MTU 517; web depends on browser. Lua payload must fit in a single MTU frame. Test: fuzz with oversized strings, verify "payload too large" errors.
5. **Button click glitch:** BLE packet loss can drop double-click. Single/double/long are mutually exclusive but detection is frame-dependent. Test: rapid button event injection, verify no race conditions in Lua callback.

## Session 2026-06-08: VESPER Test Strategy Rev 2 — All 11 Findings Closed
- Revised TEST-STRATEGY.md: B1/B2/B3 blocking (heap device-only, wire format LE/dedup, false-positive bug fixed), I4–I10 important (methodology framing, acceptance test decoupling, ownership clarity, privacy/jitter, Lua authority, quick-reset spec, story mapping), M11 minor (Appendix A split resolved/open). Review-driven remediation complete; test suite buildable.
6. **IMU tap flake:** Tap detection threshold varies with orientation and motion. False positives in noisy environments. Test: emulator can inject taps; real device needs shaking rig. Pre-enumerate tap directions (6 axis IMU: accel + compass).
7. **Audio codec mismatch:** Halo supports LC3 or PCM; Frame legacy support for CCITT u-law. Codec negotiation happens on first `send_audio()`. Test: verify LC3 default, reject unsupported codecs.
8. **Battery/charging flag:** `set_battery_level()` + `set_battery_charging()` in emulator; real device updates on charger detect. Power-save mode auto-enables at ~10%. Test: verify low-battery UI transitions.
9. **Display palette limits:** Halo uses 4-bit indexed color (16 colors); Frame uses named colors. Palette data is sent as part of sprite headers. Test: oversized palettes, verify clipping or error.
10. **Lua execution timeout:** Blocking Lua loop starves message queue. No documented timeout; system defaults to ~5s. Test: inject long-running Lua, verify watchdog behavior or timeout.

### Failure Modes & Test Enumerations (2026-06-01)
- **Connection failures:** No device found, pairing rejected, MTU too small, auth denied
- **Partial frame drops:** Audio stream gap, sprite mid-upload timeout, camera JPEG truncation
- **Permission denied:** Microphone/camera not granted on host OS; BLE access denied on mobile
- **Lua errors:** Syntax errors in uploaded scripts, missing libraries, callback exceptions
- **Message queue overflow:** Host sends faster than Halo can consume; ACK flow control must work
- **Firmware mismatch:** SDK version >= firmware version required; downgrade not supported

## Ideation 2026-06-02

Chaos-engineering ideas: deliberately broken, perverse, adversarial stress tests. One sentence per idea.

1. **The Inversion Mirror** — Display renders everything inverted/backwards at 60Hz to stress framebuffer throughput, palette swap timing, and reveal frame-sync lag.
2. **BLE Stutter-Fest** — Deliberately drop every 3rd Bluetooth packet and test reassembly logic, ACK flow control corruption, and partial message state recovery.
3. **Audio Feedback Loop** — Capture microphone and immediately re-render as speaker output at increasing volume to test audio codec saturation, digital distortion, and feedback loops.
4. **Button Mash Chaos** — Inject 100 button clicks/sec for 10 seconds to stress-test Lua callback queue, debounce race conditions, and button state machine collapse.
5. **Lua Bomb** — Upload 100KB Lua script (way oversized) to test VM memory limits, parser timeout, graceful OOM error recovery, and VM restart behavior.
6. **Pairing Purgatory** — Force pairing mode, then disconnect/reconnect 50 times rapidly to stress-test pairing state machine, phantom bonds, MTU renegotiation, and BLE stack resilience.
7. **Camera Starvation** — Request photo capture every 10ms (way faster than hardware can deliver) to test queue backpressure, timeout handling, camera buffer overrun, and image truncation.
8. **Display Hallucination** — Send conflicting sprite palettes (16-color, then 256-color, then corrupted header) to test palette validation, rendering fallback, and visual corruption detection.

## Ideation Pass 2 2026-06-02

**Status:** Complete. Cross-pollinated all 8 agents' round-1 ideas.

**Key findings:**

- **🔥 Resonance (3 high-risk ideas):** Librarian #6 (hallucination rendering) breaks under power budget. Raven #2 + Y.T. #1 create BLE/display deadlock. Enzo #3 + Ng #1 reveal latency spiral in real-time guidance.
- **🀀 Mash-ups (4 new chaos tests):** Gaze-tracking-via-lossy-BLE, synesthetic-saturation, skeleton-mirror-memory-bomb, depth-rings-under-camera-starvation.
- **✏️ Amendments (3):** Expanded BLE #2 with ACK timeout testing, enhanced Audio #3 with clipping detection, extended Pairing #6 with phantom-bond recovery.
- **🌟 NEW (8 untested failure modes):** Frame-rate purgatory, palette poisoning, microphone echo tunnel, MTU negotiation thriller, Lua callback reentrancy, IMU saturation drift, display power-save ghost, BLE name collision nightmare.
- **Special charge:** Enzo's "Social Reflex" fails spectacularly due to latency (>2s too slow), privacy violation (wiretaps bystanders), and social friction (pauses interrupt natural speech).

**Highest-confidence chaos test:** Gaze-tracking-via-lossy-BLE (Juanita #2 × Hiro #4). Tests whether real-time telemetry rendering is viable with lossy transports.

**Next actions:** Pick 2-3 for prototyping; prioritize real-device tests for MTU/reentrancy/BLE collision; use emulator for frame-rate/palette/power-save validation.

---

## User Stories Themes 1–2 — 2026-06-03

**Status:** Complete. Authored 10 negative-path user stories (5 per theme) from tester's chaos lens.

**Theme 1: Consent-Aware Memory (5 stories)**
- T1-1: Consent request timeout → auto-redaction + notification
- T1-2: Real-time revocation enforcement during recording
- T1-3: Storage exhaustion during stitching → checkpoint + safe recovery
- **T1-4 (CRITICAL):** Cloud export without completed consent checks → GDPR/privacy liability
- T1-5: Consent cascade in crowded environments → batch coalescing UX

**Theme 2: The Synesthetic Familiar (5 stories)**
- T2-1: Display refresh lag during fast emotion updates → graceful frame-skipping
- T2-2: Cloud model inference failure → offline fallback mode
- T2-3: Lua heap exhaustion during long sessions → degraded animation mode
- **T2-4 (CRITICAL):** Emotional state leakage to bystanders → privacy audit + visual inspection
- T2-5: Emotion inference lag → user quick-reset gesture + learning feedback

**Key findings:**
- **Highest-risk failure:** T1-4 (cloud export without consent completion) is a privacy incident waiting to happen. Pre-flight consent check is mandatory.
- **Second highest-risk:** T2-4 (emotional state visible to bystanders) violates social privacy expectations. Requires audit of all telemetry + external LED usage.
- **Best chaos insight:** T2-5 (emotion inference lag) is a comedy of errors (not a correctness bug), but reveals how sensor inference can break wearer's trust in companion when it disagrees with reality.

**Test priorities (ordered):**
1. T1-4 (Cloud export consent gating) — Priority 0
2. T1-2 (Revocation enforcement latency) — Priority 1
3. T2-4 (Emotional state privacy audit) — Priority 1
4. T1-3, T2-3 (Resource exhaustion) — Priority 2
5. T1-5, T2-1, T2-2, T2-5 (UX refinement) — Priority 3

**Deliverable:** `.squad/agents/juanita/user-stories-themes-1-2-2026-06-03.md` — full story format with acceptance criteria + test notes.

**Favorite story:** **T1-2 (Revocation Enforcement)** — It's the heartbeat of the entire consent-aware memory theme. If revocation doesn't work in real-time, the whole privacy narrative collapses. Testing it reveals whether the BLE/redaction pipeline can operate under latency pressure.

**Worst failure mode:** **T1-4 (Cloud Export Without Consent)** — This is the one that could turn a beautiful demo into a privacy incident. If a wearer accidentally exports non-consented footage to the cloud, Raven's entire privacy-as-feature thesis craters. It's also legal liability (GDPR, CCPA). Must be gate-checked before ANY cloud export feature ships.

---

## Synesthetic Familiar Test Strategy — 2026-06-08

**Status:** Complete. Authored full test strategy document for The Synesthetic Familiar
(docs/projects/synesthetic-familiar/TEST-STRATEGY.md). Testing decision filed to
.squad/decisions/inbox/juanita-test-strategy.md.

**Methodology chosen:** London-school (mockist, outside-in) TDD with Red→Green→Refactor discipline.

**Key seams identified:**

| Seam | Port Name | Real Adapter | Test Double |
|------|-----------|-------------|-------------|
| BLE transport | `TransportPort` | `BrilliantBLETransport` | `FakeTransport` |
| Sensor source (mic+IMU) | `SensorSourcePort` | `SounddeviceMicSource` + HaloIMURelay | `FakeSensorSource` |
| Clock / time | `ClockPort` | `time.monotonic` | `FakeClock` |
| Device display | None (not owned) | Halo OLED via Lua | halo-emulator framebuffer |

**Test pyramid:**
- Tier 1 (Unit): inference.py, familiar_protocol.py, extracted state_machine.lua
- Tier 2 (Acceptance): outside-in whole-app tests with FakeTransport + FakeSensorSource
- Tier 3 (Integration): real Python SDK against halo-emulator
- Tier 4 (Manual): real Halo per milestone (Weeks 1, 2, 3)

**Outside-in walkthroughs documented:**
1. NG-T2-1 (drive animation from host sensor data) — acceptance → unit chain
2. LIBRARIAN-T2-5-ERROR (confidence gating / silence > wrong) — acceptance → unit chain
3. JUANITA-T2-2 (offline fallback, sensor degradation) — acceptance → unit chain

**ARD gaps found (5 test blockers):**
1. `frame.system.get_heap_usage()` unconfirmed — blocks JUANITA-T2-3 heap tests
2. `FAMILIAR_ACK` trigger condition unspecified — blocks sequence-dedup tests
3. `frame.on_imu_peak()` is polling-only — blocks NG-T2-2 interrupt-style tests
4. Baseline persistence medium unspecified — blocks LIBRARIAN-T2-2 persistence tests
5. `FAMILIAR_RESET` opcode value (0x81?) unspecified — blocks JUANITA-T2-5 tests

**Design implication discovered:** DI is mandatory — FamiliarApp must accept
TransportPort, SensorSourcePort, and ClockPort as constructor parameters. Any
class that instantiates its own BLE or calls `time.monotonic()` directly is
untestable at acceptance tier. This is an architectural requirement, not a test nicety.

**Tooling stack confirmed:** pytest + pytest-mock + hypothesis (host); busted (Lua);
halo-emulator (integration); test markers: unit / acceptance / integration / device.

**Coverage targets:** 95% inference.py, 100% familiar_protocol.py, 85% sensors.py, 80% main.py.

---

## Learnings

### London-School Honest Framing (2026-06-08)
- Claiming "everything is mockist" is dishonest. Pure-function tests (`inference.py`,
  `familiar_protocol.py`) are DELIBERATELY classicist — value transformation with no
  collaborators to mock. Only acceptance tests are London-school / mockist.
- The Tell-Don't-Ask example in §1 must NOT say "inference tells protocol to encode" —
  orchestration lives in `FamiliarApp`. `inference_fn` returns a result; `FamiliarApp`
  decides what to do with it.

### inference_fn Seam (2026-06-08)
- Acceptance tests must inject `inference_fn` into `FamiliarApp` so orchestration is
  tested independently of heuristic tuning. Hardcoding sensor values in acceptance tests
  couples them to `compute_mood` internals — that's a unit test concern, not an acceptance
  test concern.
- Constructor: `FamiliarApp(transport, sensor_source, clock, inference_fn=compute_mood)`.

### Wire-Format Alignment (2026-06-08)
- ALL multi-byte fields are LITTLE-ENDIAN (`struct '<H'`, Lua `string.pack '<I2'`).
  Any test using `'>H'` (big-endian) is wrong.
- Seq dedup: signed-16 delta window. `(received - last) mod 65536` as signed int.
  delta=0 drop, 1-32767 accept, 32768-65535 drop. Naive `>` breaks at 0xFFFF→0x0000.
- `FAMILIAR_RESET`: Device→Host ONLY. Opcode `0x01`. 1 byte, no payload.
  No host-originated reset exists.
- `FAMILIAR_ACK`: Auto every 10 accepted packets. Seq-only (no heap field).

### busted is Authoritative for Lua (2026-06-08)
- `busted` runs real Lua and is the ground truth for `state_machine.lua`.
- Python `LuaStateMachineSim` is only an oracle — it validates Python-to-Python,
  NOT Python-to-production-Lua. For correctness, cross-validate via real Lua
  interpreter binding (e.g., `lupa`) or compare against busted results.

### Heap Ownership is Device-Only (2026-06-08)
- Heap management is entirely Lua-side. No heap state appears on the wire.
  `FAMILIAR_ACK` is seq-only. Any test asserting host-side heap behavior is wrong.

### Quick-Reset is Device-Originated (2026-06-08)
- Double-tap is detected by Lua IMU input, device snaps to NEUTRAL locally
  (no host round-trip), then notifies host via `FAMILIAR_RESET` opcode `0x01`.
  Host never sends a reset command. Any test that constructs a host-to-device
  reset message is wrong.
