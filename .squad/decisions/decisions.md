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
