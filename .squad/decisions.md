# Halo Decisions Log

## 2026-06-01

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
