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
