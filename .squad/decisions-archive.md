# Halo Decisions — Archive

> Archived by Scribe on 2026-06-11 (7-day Tier-2 gate: decisions.md exceeded 50 KB).
> Entries from before 2026-06-04 moved here. Active decisions remain in .squad/decisions.md.
> Week 4 archival (2026-06-14): Entries from 2026-06-07 (older than 7 days) appended below.

---


### Dark-First Display Budget
**Author:** Da5id (Designer)  
**Status:** Proposed

Halo's display is a 0.2" OLEDoS micro-display with 256×256 pixels in a round viewport. Display constraints drive design decisions:

1. **OLED power draw** — lit pixels consume power; black pixels consume none.
2. **300 mAh total battery** — 14-hour target means ~21 mW average system draw.
3. **No double-buffer** — every draw call is immediate; full-screen redraws cause visible repaints.

**Constraints (Team-Wide):**
- All app screens MUST use 0x000000 (true black) as the default background
- Limit lit pixel area to ~30% of 256×256 canvas
- Avoid sustained 100% brightness; default to 50–70% indoors
- Minimize full-screen clears; prefer incremental updates
- Baseline refresh at 25–30 fps

**Acceptance pending:** Hiro (Architect), YT (Engineer)

---

### Playground Roadmap — Initial Candidates
**Author:** Enzo  
**Status:** Draft (awaiting Aaron approval)

Five candidate playground demos to establish patterns and build community momentum. Recommends Phase 1 (2–3 weeks):
1. **Bird Watcher** (1–2 days) — vision + memory
2. **Workout Coach** (3–5 days) — audio + real-time guidance
3. **Time Tracker** (2–3 days) — HUD overlay + always-on

Phase 2 (2–4 weeks) adds Scene Documenter and Translator.

**Next Steps:** Aaron confirms Phase 1 set, then decompose into GitHub issues.

---

### Mono-Repo Structure Decision
**Owner:** Hiro (Architect)  
**Status:** Pending ratification

**Decision:** Structure the mono-repo as a flat workspace with one directory per SDK (sdk-python/, sdk-flutter/, sdk-webbluetooth/, examples/, infra/).

**Rationale:**
1. No shared logic between SDKs
2. Language ecosystems don't mix
3. Each SDK example uses its own language & idioms
4. Team autonomy — developers can clone sdk-{lang}/ and work independently

Do not extract shared utilities into sdk-shared/ now; revisit when 3+ SDKs have repeated patterns.

---

### Testing Posture Recommendation for Halo SDKs
**Author:** Juanita (Tester)  
**Status:** Ready for Squad review

Testing strategy varies by SDK due to BLE and hardware constraints:
- **Python:** Emulator-first, pytest, ~90% unit/integration coverage
- **Flutter:** Real-device hardware tests, ~70% unit/widget coverage
- **Web Bluetooth:** Browser+device hybrid, Jest/Playwright, ~60%

**Recommendation:** Adopt Python as testing reference implementation using emulator-first test harness as "gold standard" for correctness.

**Edge cases to test:** BLE disconnect mid-call, MTU negotiation, pairing timeout, low battery, Lua callback exceptions, message queue overflow, firmware version mismatch.

---

### LICENSE Recommendation for Halo Playground Repo
**Author:** Lagos  
**Status:** Draft — awaiting Aaron's decision

Brilliant SDK is published under BSD-3-Clause (permissive, copyleft-free, no patent restrictions).

**Recommendation:** Adopt MIT for halo playground repository.
- MIT is most permissive and widely recognized
- Fully compatible with BSD-3-Clause dependencies
- Simplifies attribution with single sentence
- Signals low governance burden

**Attribution language proposed** for README + NOTICE file.

---

### Initial AI Model Tier for Halo Playground
**Owner:** Librarian (AI/ML)  
**Status:** Proposed

Halo is a wearable with extreme power/memory constraints (Alif B1 processor, 14-hour battery). Cannot run local LLMs; latency budget 1–3s acceptable.

**Options:**
- **Option A (Recommended):** Hosted Multimodal API (Claude Vision, GPT-4o) — fastest iteration, Noa proof validates pattern, weeks to first working app
- **Option B:** Hybrid (Local STT + Cloud LLM) — better privacy, ~1.5s latency, months effort
- **Option C:** Local-First Small Models — full control, high effort, months to years

**Recommendation:** Choose Option A immediately. Action items: establish baseline Halo ↔ host communication, pick Claude or GPT-4o, implement conversation history, measure real latency.

---

### Web Bluetooth Platform Limitation (Chromium-Only)
**Author:** NG  
**Status:** Open for team consensus

Web Bluetooth SDK is **only available in Chromium-based browsers** (Chrome, Edge, Opera) on desktop and Android. Not supported in Firefox, Safari, or non-Chromium browsers.

**Implications:**
1. Demo devices must use Chromium
2. No automatic fallback
3. CI/CD tests must use Chromium (Puppeteer, Playwright)
4. Cross-browser apps need feature flags or explicit browser checks

**Questions for consensus:** Document supported browsers matrix? Warn Web Bluetooth examples about Chromium requirement? Fallback strategy for non-Chromium requests?

---

### Recording Consent Indicators — Requirement for Any Sensor Capture
**Author:** Raven (Security & Privacy)  
**Status:** Open — Requires team decision  
**Severity:** High (Legal + Privacy)

Halo hardware provides no mandated visual/audible recording indicator for camera or microphone. Jurisdictional requirements (California AB 375, GDPR, UK PECR) mandate bystander-visible signal when recording.

**Proposed Mitigation (Option A - Recommended):**
- Mandate white LED blink or pulsing tone whenever camera/mic capture is called
- Implement in host app (not firmware change)
- LED/tone must persist until stream ends

**Decision Gate:** All Halo apps using sensors → must show indicator. Implementation checklist: Noa app LED+tone, SDK docs, reference app template, telemetry logging.

---

### Host-App Scaffolding Pattern
**Owner:** Y.T.  
**Status:** Proposed

Standardize shared playground scaffold across Python, Flutter, and Web platforms. All platforms follow identical startup flow: connect → reset → upload libraries → upload main app → start event loop.

**Proposal:**
- Boot template for each platform
- Example Lua app with click handler + message parsing
- Device-aware UX helpers (Halo vs Frame detection, circular display layout)

**Decision:** APPROVED for implementation in next playground project. Start with Python scaffold, validate with first demo, port template to Flutter and Web.

**Risks:** Templates become stale; mitigation is CI validation. Developers may copy-paste without understanding; mitigation is heavy comments + SDK docs reference.

---

### Sparse Radial HUD Principle
**Author:** Da5id (Designer)  
**Status:** Proposed

After tracing Brilliant Labs' hardware evolution (Monocle → Frame → Halo), a consistent UX philosophy emerges. All Halo UI designs MUST follow these constraints:

1. **Center-out composition** — Place primary content at center; secondary content at edges. Circular mask clips corners.
2. **Maximum 3 visual elements per screen** — Icons > text. Numbers > sentences.
3. **Glance budget: <1 second** — Content appears in upper peripheral vision; design for recognition.
4. **Incremental updates only** — No double-buffer means no safe full-screen transitions. Update only the region that changed.
5. **Input triad: button cycles, tap confirms, voice queries** — Mirror Brilliant's trajectory: diversify inputs, simplify display.

Brilliant's hardware trajectory is a product thesis: **smart glasses are ambient displays, not wrist computers**.

**Acceptance:** Pending Hiro (Architect) + YT (Engineer) review.

---

### Playground Roadmap Amendment — Lineage-Informed Re-prioritization
**Status:** AMENDMENT (to initial draft)  
**Author:** Enzo  
**Date:** 2026-06-01

After reviewing Brilliant's arc (Monocle → Frame → Halo), the Phase 1 project order should shift to align with Halo's hardware bets and strategic direction. **Audio is the new frontier** — Halo's stereo mics + bone-conduction speakers represent the first real audio I/O investment.

**Revised Phase 1 Priority (Reordered):**

1. **Workout Coach** (3–5 days) — NOW FIRST. Real-time form feedback via audio + IMU. Proves audio is the differentiator. Demonstrates host-peripheral model (Flutter app handles audio synthesis). Non-intrusive/advisory—exactly what Halo hardware is built for.

2. **Bird Watcher** (1–2 days) — SECOND. Point Halo at birds; recognize species + log sighting. Validates Camera pipeline works; easy to compose with other sensors. Demonstrates host-driven inference.

3. **Time Tracker** (2–3 days) — THIRD. Tap to toggle time tracking; display elapsed time on HUD. Web Bluetooth validates ecosystem breadth (not just Python/Flutter). Proves always-on low-power display works.

**Rationale:** The lineage reveals that Brilliant is deliberately **simplifying the developer path** at each generation. Our playground should reflect this strategy: lead with audio (our only new hardware feature), showcase host-peripheral model, recruit multi-platform devs.

**Revised launch:** Workout Coach → Bird Watcher → Time Tracker (starting 2026-06-08, target 2026-06-22). Awaiting Aaron's approval on re-prioritization.

---

### Future-Device Portability vs. Halo-Focused Design
**Decision Date:** 2026-06-01  
**Owner:** Hiro (Architect)  
**Status:** PENDING RATIFICATION  

**Decision:** Design this mono-repo for Halo, not future devices. Accept that Lua on-device APIs will change with hardware generations. Brilliant has shown willingness to break Lua contracts for clarity and velocity.

**Rationale:**
1. Premature abstraction is costly; Frame→Halo Lua breakage invalidates abstractions anyway.
2. Host SDK APIs are stable. We don't need a "device abstraction layer" at the Python/Flutter level; SDK structure is portable.
3. Mono-repo structure doesn't block future devices. If/when Halo 2 arrives, add `sdk-python-halo2/` or new major version branches.
4. Language ecosystem constraints dominate; future hardware won't change that.

**Commitment:** SDK directory names are device-agnostic (`sdk-python`, `sdk-flutter`, `sdk-webbluetooth`). Example apps are clearly labeled per device. No abstraction layer for "device-agnostic Lua event loop." Future device support is a *new major version*, not a new branch.

**For Aaron:** Does this align with Brilliant's roadmap? Are there device families planned where a shared host-SDK abstraction would be valuable?

---

### Model Tier for Halo (Post-Evolution Analysis)
**Date:** 2026-06-01  
**Owner:** Librarian (AI/ML)  
**Status:** Proposed (Amends prior hosted-multimodal recommendation)  

**Prior decision:** Start with **hosted multimodal API** (Claude 3.5 Sonnet or GPT-4o). After tracing Brilliant's 3-generation trajectory, this recommendation is *strengthened*, not changed.

**Why evolution validates the approach:** Monocle (64MHz) → Frame (still 64MHz, 256KB RAM) → Halo (M55 + NPU). Yet each generation chose cloud LLM. Monocle + Frame had no local LLM capacity. Halo added NPU, but Brilliant still keeps cloud LLM—NPU is for efficiency (wake-word, activity detection), not replacement.

**Confidence table:**
| Option | Monocle | Frame | Halo Signal | Confidence |
|--------|---------|-------|-----------|-----------|
| **Hosted Multimodal API** | ✅ Day 1 | ✅ Norm | ✅ Current design | **VERY HIGH** |
| **Hybrid (Local STT + Cloud LLM)** | ❌ N/A | ✅ Noa uses Whisper | ✅ Still in use | **HIGH** |
| **Local-First Small Models** | ❌ N/A | ❌ Nobody did it | ⚠️ NPU hints maybe | **LOW** |

**Implication:** Copy Frame's Noa pattern exactly (immediately). Add Halo-specific on-device optimizations later if needed (wake-word, activity gating). Never attempt local LLM inference; both Monocle & Frame generations skipped this for a reason.

**Recommendation unchanged:** Hosted multimodal API first. Confidence increased by 3-generation validation.

---

### Frame → Halo Migration — Silent Failure Gotchas
**Date:** 2026-06-01
**Status:** Open for team consensus
**Impact:** Cross-team (devs copying Frame examples, QA verifying port correctness)

**5 Silent Failure Gotchas (code compiles/runs but produces no output or crashes only at runtime):**

1. **Halo Display Power-Save Default** — Ported Frame app displays nothing on Halo; no errors. Root cause: Halo display starts in `power_save(true)` mode; Frame starts enabled. Fix: Call `frame.display.power_save(false)` at startup.

2. **TxSprite Wire Format Mismatch** — Images render with garbage/corruption. Root cause: Old host-side `brilliant-msg` mixed with new `data.lua`; compressed flag at wrong offset. Fix: Update ALL on-device Lua libraries via `upload_stdlua_libs()`.

3. **Removed `data.parsers` Table** — App starts, Lua REPL works, but event loop crashes when first message arrives. Root cause: Frame-era `frame_app.lua` tries `data.parsers[MSG_CODE] = ...`; table doesn't exist. Why not caught: Parser registration is lazy; only fails when messages arrive.

4. **IMU Data Type Change** — IMU values are correct magnitude but garbage precision; physics simulations drift. Root cause: Unpacking 6 × `int16` as calibrated `float32`; bytes misinterpreted. Why silent: No exception; values are plausible but wrong (1000x actual).

5. **TxTextSpriteBlock API Change** — App runs fine until user triggers text display; crash at that point. Root cause: Code calls old constructor `TxTextSpriteBlock(text="Hello", ...)`; new API requires `.create_text_sprites()`. Why not immediate: Text rendering is often user-triggered.

**Team-Wide Implications:** Frame SDK examples are NOT directly port-to-Halo. Copy-paste will silently fail. QA needs specific checklists. Lua library version tracking is critical. Integration tests must include message receipt.

**Recommendation:** Create ported-app checklist, add lint rules, pin device firmware version, provide Frame→Halo migration script, document wire format compatibility matrix.

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

## 2026-06-03

### Aaron's Ideation Curation — User Preferences Ranked
**Author:** Aaron Kubly (via Copilot directive)  
**Date:** 2026-06-03  
**Status:** CANONICAL DIRECTION (team baseline)  
**Scope:** Design focus for all subsequent sprints

**Summary:**  
Aaron's curated selection from two rounds of ideation across 9 agents establishes team priorities. Three themes ranked by strategic value:

**Theme Ranking (by Aaron):**
1. 🥇 **Consent-Aware Memory** — useful. Privacy-forward recording device with mandatory per-person consent gates. Most-cited convergence across Hiro, Enzo, Librarian, Raven, Lagos.
2. 🥈 **The Synesthetic Familiar** — fun. Joyful peripheral-aware creatures (Y.T. pet × Librarian synesthetic rendering × Da5id haptic feedback).
3. 🥉 **Radial / Kinetic Interaction Language** — neat. Da5id's round-display vocabulary for time, notifications, breath pacing.

**Aaron's 11 Selected Individual Ideas:**
- Enzo #3 (Skill Atomizer) — Real-time task decomposition
- Enzo #4 (Memory Ledger) — 12-hour on-device buffer
- Ng #4 (Live Camera Peek) — 64×64 corner context window
- Y.T. #1 (Pet Familiar) — Reactive creature in corner vision
- Y.T. #2 (Skeleton Mirror) — Cartoonish pose feedback
- Y.T. #4 (Fortune Teller) — Absurdist oracle from pixel chaos
- Da5id #1 (Breathing Halo) — Ring paces breathing
- Da5id #2 (Orbital Notifications) — Messages orbit rim
- Librarian #2 (Synesthetic AI) — Abstract concepts as metaphors
- Librarian #4 (Local World Model) — On-device 1–3s prediction
- Raven #4 (Cryptographic Proofs) — Hash-only attention proof, no image storage

**Notable Omissions:**
- Zero ideas from Hiro (architecture/mesh), Lagos (community/meta), Juanita (chaos demos)
- "Community as protocol" theme deliberately deprioritized
- Enzo #1 (Social Reflex) omitted—Juanita had invalidated it in pass-2

**Strategic Signal:**
Bias toward fun-leaning, HUD-design-rich, on-device-AI-with-privacy projects. Deprioritize multi-device meshes, community ceremonies, chaos demos. Every spawned agent should calibrate to these preferences before proposing further work.

---

### Decision: Theme 1 (Consent-Aware Memory) as Phase-1 North Star
**Author:** Enzo (Product/PM)  
**Date:** 2026-06-03  
**Status:** PROPOSED (awaiting Aaron approval)  
**Scope:** Roadmap prioritization + architectural commitment

**Summary:**  
Aaron's curation converges on three themes. Enzo recommends **locking Theme 1 (Consent-Aware Memory) as the flagship North Star for Phase-1**, even though it's architecturally ambitious. This shapes every Phase-1 playground to feed a *personal memory ledger* prioritizing privacy by default.

**Context:**  
Theme 1 requires cross-layer infrastructure:
- **SDK layer:** Raven's consent metadata in every message
- **Data model:** Librarian's episodic stitching + versioning
- **Hardware:** On-device LLM for prompt inference + privacy checks

Easier to build privacy-first from day 1 than retrofit later.

**Three Options Evaluated:**

**Option A: Pick Theme 1, Prototype End-to-End** ✅ **RECOMMENDED**
- Effort: High (weeks 1–12)
- Risk: Architectural blocker in Lua VM or battery budget
- Upside: Differentiates from Brilliant Noa; privacy becomes feature, not compliance checkbox

**Option B: Sketch All Three in Parallel**
- Effort: Very High (3 independent workstreams)
- Risk: Context diffusion; integration hell at week 6
- Upside: Risk hedging; data on resonance

**Option C: Spike the Riskiest Assumption First**
- Effort: Low (5-day spike)
- Risk: Delays roadmap
- Upside: De-risks Theme 1 before full commitment

**Recommendation: Option A**

**Rationale:**
1. **Coherence:** Aaron's 11 picks aren't random; they cluster around privacy-first local reasoning.
2. **Differentiation:** "Halo respects your privacy by design" is a competitive moat vs. Brilliant's streaming pattern.
3. **Architectural soundness:** Privacy infrastructure must be foundational, not bolted-on.
4. **Phase-1 Coherence:** Every playground demo becomes a data collection instrument feeding Theme 1 infrastructure.

**Phase-1 Implementation Path:**
1. **Week 1–2:** Ship Pet Familiar + Skeleton Mirror (joy narrative)
2. **Week 3–6:** Build Memory Ledger infrastructure + consent layer (Theme 1 foundation)
3. **Week 7–10:** Workout Coach + Bird Watcher (with memory hooks enabled)
4. **Week 11–12:** Time Tracker redesigned as radial time (Theme 3 validation)

**Known Risks:**
| Risk | Mitigation |
|------|-----------|
| Battery overhead of consent negotiation | Spike in week 0 (Option C hybrid) |
| Lua VM memory limits for episodic stitching | Prototype with simple test script |
| Bystander notification latency | Design UI + UX flow before coding |
| Privacy law uncertainty | Loop Raven + legal team into design reviews |

**Decision Gate:**  
Aaron must confirm:
1. Is Theme 1 (Consent-Aware Memory) the North Star? Y/N
2. Should Phase-1 reorder to joy-first (Pet + Skeleton before Workout Coach)? Y/N
3. Approve budget for Raven + Librarian to spike memory architecture (weeks 1–2)? Y/N

---


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

---



---

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
