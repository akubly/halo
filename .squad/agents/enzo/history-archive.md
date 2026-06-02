# Archive: Enzo Learnings (Pre-2026-06-02)

Compressed factual learnings from initial research. Raw ideation garden not promoted to decisions.

## Halo Product Position
- 0.2" micro-OLED (256x256px), camera, stereo bone-conduction audio, 14hr battery
- Host-centric (Python/Flutter/Web apps drive logic; Halo is BLE peripheral)
- Natural use-cases: real-time HUD info, voice-first interactions, AR/spatial overlays, memory/logging, always-on accessories
- **"Passive advisory agent" model:** Noa succeeds because it augments what user is already doing, not demanding active attention

## Brilliant Lineage Evolution
**Monocle (2022–2023):** FPGA-heavy, 70mAh battery, MicroPython on-device. Failed: RTL learning curve too steep, hourly recharging, no voice.
**Frame (2024–2025):** Lua transition, Noa first-party app, 210mAh battery + dock. Worked: simpler scripting, proven AI advisor pattern. Failed: still limited battery, single mic, FPGA hidden.
**Halo (2026+):** Accessibility play, no FPGA, NPU for quantized models, dual mics + bone conduction, 14hr battery, Zephyr OS, host-centric. Removed: FPGA complexity, touch buttons, charging case.

**Arc:** "Hacker autonomy (Monocle) → Noa companion (Frame) → App ecosystem (Halo)" = intentional de-specialization (researcher with custom HDL → Noa user → Any Python/Flutter dev ships in days).

## Community Signal
**Strong patterns:** Heads-up telemetry, AI/LLM integration, vision + object detection, utility scripts, WebRTC streaming.
**Unmet needs:** Audio as primary I/O (no TTS/voice synthesis), gesture/IMU beyond tap, memory/logging apps, web-first AR.
**Friction:** 2–3 year old projects (Monocle dominated), ~20–30 public projects total (small relative to SDKs), high abandonment, FPGA work is dead.

**Implication:** Audio is genuinely untouched gap. Python projects dominate; showcase Python first. Persistence/memory missing. Gesture underutilized. Community capable but friction + unclear "what to build" guidance blocks adoption.

## Ideation Garden (Not Promoted)
8 blue-sky use-cases collected (2026-06-02): Social Reflex, Energy Cartography, Skill Atomizer, etc. Raw seeds for Phase 2+ prioritization; not commitments.
