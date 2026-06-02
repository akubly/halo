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
