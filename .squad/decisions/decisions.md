# Decisions Log

## 2026-06-01: Playground Roadmap Amendment — Lineage + Community Validation
**Status:** AMENDMENT (to initial draft)  
**Owner:** Enzo  
**Date:** 2026-06-01  

After reviewing Brilliant's arc (Monocle → Frame → Halo) and community projects, Phase 1 re-prioritization is validated. Halo is deliberately de-specializing (from FPGA-centric → audio-first). Community review shows audio projects are completely absent (0% of 20–30 projects), validating **audio-first prioritization**.

**Revised Phase 1 launch sequence (start 2026-06-08, target 2026-06-22):**
1. **Workout Coach** (3–5 days) — Audio + real-time guidance (fills genuine whitespace)
2. **Bird Watcher** (1–2 days) — Vision + lightweight ML (confirms camera + ML approachable)
3. **Time Tracker** (2–3 days) — HUD + web Bluetooth (proves multi-platform reach)

**Implication:** All three Phase 1 projects remain 1–5 days. Lead with audio (Halo's differentiator). Phase 2 (Scene Documenter + Translator) launch ~2 weeks after Phase 1.

**Awaiting:** Aaron's approval to proceed with Phase 1 sprint starting 2026-06-08.

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
