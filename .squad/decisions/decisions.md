# Decisions Log

## 2026-06-02: GitHub Landscape Scan Validates Phase-1 Roadmap — No Changes Needed
**Status:** Proposed  
**Owner:** Enzo (Product/PM)  
**Date:** 2026-06-02  
**For:** Aaron (final approval)

Scanned GitHub for Halo ecosystem signal to validate Phase-1 roadmap (Workout Coach → Bird Watcher → Time Tracker) against existing community projects. **Result:** Phase-1 is strategically sound. No roadmap changes needed.

**Key Findings:**
- ~50 active projects (mostly Frame-era, 2023–2025)
- 0 Halo community projects (device too new; AnkiLens is first, 1 star, emerging)
- Critical gaps: audio output (0 projects), gesture/IMU (1 dead project), persistence (0 projects), web BLE (1 project)
- Each Phase-1 project fills a real gap with no direct conflicts

**Verdict:** Keep Phase-1 as drafted. No changes needed.

**Rationale:**
- ✅ Fills genuine gaps (audio, persistence, web BLE)
- ✅ No conflicts with existing projects
- ✅ Leverages Halo's unique hardware
- ✅ Demonstrates "what to build" guidance for community
- ✅ Likely to accelerate adoption (community will fork + extend)

**Appendix:** See `.squad/agents/enzo/github-halo-landscape-2026-06-02.md` for full registry, category breakdown, and standout repos.

---

## 2026-06-02: "Only Gemini Ships" — VALIDATED by 2026-06-02 GitHub Landscape Scan
**Status:** RESEARCH COMPLETE — No decision action required (prior recommendation stands)  
**Owner:** Librarian (AI/ML)  
**Date:** 2026-06-02  
**Confidence:** VERY HIGH

**Quantitative Validation (13 public repos with identifiable AI model choice):**
| Model | Count | % | Status |
|-------|-------|---|----|
| Gemini (Google) | 12 | 92% | DOMINANT |
| Whisper (OpenAI) | 0 | 0% | In docs, not production code |
| Claude / GPT-4o | 0 | 0% | Mentioned in comparison docs only |
| Local (Llama, Mistral, Qwen) | 0 | 0% | 0 AR glasses projects |

**Findings:** Brilliant's `frame_realtime_gemini_voicevision` (80 stars, official) is the canonical pattern. All AI projects use Gemini or Google Cloud services. No Claude integrations, no Whisper in actual Frame code, no GPT-4o projects.

**Why Alternatives Haven't Shipped:**
- Gemini Live API is only major LLM offering true multimodal streaming (voice + vision simultaneously)
- Claude/GPT-4o both request-reply only (not streaming) — higher latency perception
- Community defaults to reference implementation (network effects)

**For Halo Playground:**
1. Default to Gemini Live (multimodal streaming) for primary demo apps
2. Do not attempt Claude/GPT-4o as primary LLM until streaming APIs are published
3. Document Whisper as future option for privacy-first STT (not production yet)
4. Monitor edge-vlm-assistant + LiveKit patterns for non-glasses applicability

**Research Deliverables:** `.squad/agents/librarian/github-ai-on-halo-2026-06-02.md` — Full annotated project list

---

## 2026-06-02: Use CitizenOneX Frame Examples as Migration Reference Template
**Status:** Proposed  
**Owner:** Ng (SDK Engineer)  
**Date:** 2026-06-02  
**Related:** Frame→Halo Migration Gotchas (2026-06-01 decision log)

When creating Halo playground documentation and Frame→Halo migration guides, reference and link to `CitizenOneX/frame_examples_python` (https://github.com/CitizenOneX/frame_examples_python) as the authoritative Frame example suite.

**Rationale:**
1. **Eliminates guesswork.** Developers can compare Frame vs. Halo side-by-side and understand exactly what changed (imports, Lua API, device type branching).
2. **Surfaces silent failure gotchas.** The "5 Silent Failure Gotchas" documented in Ng's 2026-06-01 decision log are precisely the things Frame examples don't do (e.g., `power_save(false)` call on Halo).
3. **Community contribution path.** Future developers migrating apps can PR new before/after pairs to the halo playground repo.

**Acceptance Criteria:**
- [ ] Halo playground repo examples/ directory created
- [ ] At least 3 examples with corresponding CitizenOneX Frame reference links
- [ ] README explains before/after mapping
- [ ] 5 Silent Failure Gotchas are all fixed in Halo version
- [ ] PR review confirms examples work on real Halo + Frame devices

---

## 2026-06-02: Official Scaffolds to Adopt
**Status:** APPROVED  
**Owner:** Y.T.  
**Date:** 2026-06-02

Three reference implementations stand out as ready-to-adopt:

1. **Python:** `halo_emulator/examples/repl_hello.py` — Cleanest emulator integration pattern; async-first; can swap `--emulator` for testing without hardware
2. **Flutter:** `simple_brilliant_app/template/simple_frame_app/` — Official scaffolding package (pub.dev); device detection + lifecycle handled by mixins; copy-paste ready
3. **Web:** `bl-monocle-reactjs-pwa` (Architectural Pattern) — localStorage + BLE lifecycle; PWA pattern; only real Web scaffold in community

**Action: Scaffolds to Create (Phase 1)**
- `playground/templates/python/` (main.py based on repl_hello.py, stripped to 40 lines; requirements.txt; README)
- `playground/templates/flutter/` (README + skeleton main.dart + pubspec.yaml reference)
- `playground/templates/web/` (index.html; app.js; README with live-serve instructions)

**Benefits:** No reinvention, first-time friendly, device portability (works on Halo and Frame), test coverage via emulator, monorepo precedent.

**Timeline:** Week 1: templates; Week 2: one demo per platform; Week 3: test; Week 4: publish.

---

## 2026-06-01: Community Validation Strengthens Hosted Multimodal API Recommendation
**Status:** Proposed (Final recommendation)  
**Owner:** Librarian  
**Date:** 2026-06-01  
**Evidence:** Community projects audit (Frame ecosystem)

**Recommendation:** Start with hosted multimodal API (Gemini, Claude, or GPT-4o). Community evidence is decisive:

**What succeeded:** 
- `frame_realtime_gemini_voicevision` (Brilliant first-party) — Gemini Live API backend, real-time multimodal (camera + audio) streaming, Flutter host app, maintained and demonstrated in multiple videos. **This is THE canonical pattern.**
- Community QR scanners, fitness trackers — UI-centric, stateless. None attempted local inference.

**What failed to materialize:**
- Local LLM (Llama, Mistral) — **Zero projects found.** Frame's nRF52840 (256 KB RAM) insufficient for even 7B quantized models. Community tried, hit wall, abandoned.
- RAG-on-glasses — Zero projects.
- Wake-word detection — Zero Frame projects.
- Multimodal agent loops — Zero projects.

**Model ranking (community adoption):**
1. Gemini Live API (dominant) — Brilliant's official demo default
2. Whisper (secondary) — Used for STT on host side
3. GPT/ChatGPT (supported but not observed)
4. Claude (theoretically supported, no projects)
5. Llama/Mistral (zero proven projects)

**For Halo Playground (Week 1–2):** Copy Frame's proven pattern: Halo camera/mic → Python host → Gemini Live API → Halo display + TTS. Leverage Halo's NPU (Alif B1) for on-device gate-keeping (wake-word, activity detection). Do NOT attempt local LLM. Frame community tried and failed; hardware barrier confirmed.

---

## 2026-06-01: Community-Discovered SDK Rough Edges & Workarounds
**Status:** Open for team consensus  
**Owner:** NG  
**Date:** 2026-06-01  
**Impact:** Developers (workaround patterns), SDK maintainers (feature requests)

Community (Monocle, some Frame) has surfaced **fundamental SDK limitations** that developers work around systematically. Not bugs — architectural gaps.

**Community-validated workarounds:**

1. **BLE-Direct as Fallback:** Developers bypass official SDKs, implement raw BLE. Example: `brilliant-monocle-driver-python` uses manual UART over BLE with Ctrl-A/Ctrl-D framing. For Halo: if `brilliant-msg` limits, developers will go BLE-direct (LUA TX/RX characteristics).

2. **Large File Upload Chunking:** Monocle filesystem limitation (128-char filenames) spawned community chunk loader. SDK doesn't abstract away limitations. For Halo: Lua scripts beyond MTU/filesystem require similar chunking.

3. **Custom Graphics Pipelines:** `vgrs` library implements vector graphics + rasterization; standard `text()` / `bitmap()` too limited. For Halo: simple sprites may be insufficient for rich applications.

4. **Multi-Language SDK Redundancy:** Community built Node.js, Go, unofficial Flutter bindings predating official SDKs. Reduces vendor lock-in. For Halo: unsupported use cases will spawn community BLE wrappers.

5. **MTU Fragmentation Pain:** Every community library implements own packet reassembly; official SDKs don't fully hide MTU. MTU handling still error-prone despite `brilliant-msg` layer.

6. **Undocumented Hardware Behavior:** Touch event callbacks (Monocle) not in official docs; community reverse-engineered via trial-and-error. Button event behavior, display power-save, IMU axis mapping all require documentation updates post-SDK release.

**Recommendations:**
1. Document BLE-direct fallback path ("when to use BLE-direct" guide)
2. Provide file upload streaming in SDK (`upload_lua_file_chunked()` method)
3. Create vector graphics optional layer or bless community library
4. Expand official SDK bindings (prioritize Rust or C# if requested)
5. Publish undocumented hardware facts (audit Halo Lua API docs)

---

## 2026-06-01: Reference Implementations to Adopt
**Status:** PROPOSED  
**Owner:** Y.T.  
**Date:** 2026-06-01  

Community projects show two gaps: (1) no standardized scaffold, (2) scattered patterns. Brilliant's official tools address some gaps but not scaffolding.

**Reference implementations to study & adapt:**

1. **fixermark/brilliant-monocle-driver-python:** Clean async context manager, handles UART MTU overflow, provides touch event callbacks. Adopt: callback-based event handler pattern, context manager lifecycle management, Bleak connection retry + MTU negotiation.

2. **bl-monocle-reactjs-pwa:** localStorage code snippet persistence, real-time code editor + test/flash workflow, responsive mobile design. Adopt: localStorage for persisting Lua snippets, code editor + test/validate workflow.

3. **monocle-node-cli:** REPL-style device interaction. Prove we can build Python CLI REPL for Halo (useful for playground testing + debugging).

**Proposed scaffold incorporation:**
- **Python:** Base on fixermark's asyncio pattern + `halo-emulator` for offline testing
- **Web:** localStorage pattern + CircularTextLayout + device detection
- **Flutter:** Official `simple_brilliant_app` package + async photo capture example

Implementation: Create `playground/templates/{python,web,flutter}/` with scaffolds. Reference the three community implementations in each README. Test with minimal "hello world" playground.

---

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

**Test addition:** Busted `test_calm_sustain_timing_exhaustive` added to cover edge cases (59.9s, 60.0s, 60.1s transitions).

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
