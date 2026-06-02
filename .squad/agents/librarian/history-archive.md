# Archive: Librarian Learnings (Pre-2026-06-02)

Compressed factual research on AI/ML patterns for Halo. "Proved" vs. "Speculative" distinction maintained throughout.

## Sensor Pipeline → Reference Architecture (Halo)
**Hardware Inputs:** Camera (ultra low-power), 2x mics + audio activity detection, 6-axis IMU + tap detection, Bluetooth 5.3 only.
**Processing:** Alif B1 NPU (wake-word, activity detection only); main LLM logic on host (cloud-dependent, cannot run Llama/Mistral locally).
**Output:** MicroOLED display, 2x bone-conduction speakers, 14hr battery (all-day, always-on gate-keeping critical).

**Patterns Brilliant Demonstrates:** (1) Multimodal as core (Noa = vision+audio always), (2) Cloud-first LLM logic (hardware too constrained), (3) Stateful conversations (memory/personalization), (4) Tap/gesture as interrupt, (5) Always-on audio gate (dual mics + activity detection), (6) Battery trumps features (1W avg max).

## Brilliant AI Evolution (Monocle → Frame → Halo)
**Monocle (2023):** Nordic M4F CPU, FPGA, ChatGPT integration, cloud LLM only. Noa added later.
**Frame (2024):** Nordic M4F CPU, FPGA, Noa v2 (multimodal vision+audio, GPT-4 backend), host-side lightweight models (Whisper STT on host). 720p camera, dual mics, 210mAh battery.
**Halo (2026):** Alif B1 NPU, no FPGA, Noa v3 (same multimodal, optimized for wearable display+always-on context), on-device gates/filters (activity detection, wake-word). Ultra low-power camera, 2x mics + activity detection, 6-axis IMU, 14hr battery.

**Key progression:** CPU power constant (power-gated), compute strategy FPGA-graphics-only → FPGA+host-ML → NPU-gates-only, camera quality Unspecified → 720p → ultra-low-power-AI-first, sensors 3-axis → 3-axis+dual-mic → 6-axis+dual-mic+activity, battery session-based → always-day.

**libmpix role:** Image preprocessing before inference; now explicit on Halo.

## Community AI Projects (Proved vs. Speculative)
**Proved (Production on Frame):** 
- `frame_realtime_gemini_voicevision` (80 stars, official) — Real-time multimodal (camera POV + audio) streaming to Google Gemini Live; voice customization; canonical pattern.
- Community QR scanners, teleprompter, fitness — UI-centric, stateless; none attempted local LLM.

**Failed to materialize:**
- Local LLM (Llama, Mistral) — 0 projects found; Frame's nRF52840 (256 KB RAM) insufficient for even 7B quantized; community tried, hit wall, abandoned.
- RAG-on-glasses — 0 projects.
- Wake-word detection — 0 Frame projects (speculative for Halo; NPU enables it).
- Multimodal agent loops — 0 projects.

**Model ranking (community adoption):** Gemini Live (dominant, Brilliant's official demo), Whisper secondary (STT on host side), GPT/Claude supported but not observed, Llama/Mistral zero on AR glasses.

## GitHub Empirical Validation: "Only Gemini Ships"
**Sample:** 13 public GitHub repos with identifiable AI model choice on Brilliant hardware.
**Distribution:** Gemini 92% (12/13); Whisper 0% (docs only), Claude/GPT-4o 0%, Local LLM 0% on AR glasses (1 MacBook Air non-wearable).
**Root cause:** Gemini Live API only major LLM with true multimodal streaming (voice+vision simultaneously); Claude/GPT-4o request-reply only (higher latency perceived).
**Community inertia:** Reference implementation (`frame_realtime_gemini_voicevision` 80★) sticky; developers fork rather than rewrite.

**For Halo Playground:** Copy Frame's Gemini Live reference (immediately). Evaluate embeddings fork for post-MVP RAG experiment. Avoid local LLM attempts (will fail power/memory). Document STT choice (Whisper privacy vs. Google cost).

**Confidence:** Increased from HIGH to VERY HIGH via empirical GitHub data.

## Patterns Actually Proved vs. Speculative
**Proved:** Realtime multimodal cloud API (Gemini Live) production-ready; host-side STT+cloud LLM standard; BLE peripheral model; stateless image frames; display for text+UI feedback.
**Speculative:** On-device wake-word (Halo's audio activity detection, unproven end-to-end); local LLM inference (theoretical, not viable); RAG-on-glasses (no projects); image-to-action chains.

## Ideation Garden (Not Promoted)
8 blue-sky ideas collected (2026-06-02) spanning embodied memory, synesthetic AI, action-chaining, local world models, multiplayer personas, hallucination-as-content, episodic stitching, agentic loops. Raw seeds; not commitments.
