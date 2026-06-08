# Project Context

- **Owner:** Aaron Kubly
- **Project:** halo — mono-repo playground for authoring apps on Halo smart glasses using the Brilliant SDK
- **Target device:** Brilliant Halo (BLE peripheral, Lua 5.3 VM on-device, camera/mic/speaker/display)
- **SDK surfaces:** Python (Mac/Linux/Windows), Flutter (iOS/Android), Web Bluetooth (Chromium)
- **SDK repo:** https://github.com/brilliantlabsAR/brilliant_sdk
- **Docs root:** https://docs.brilliant.xyz/halo/
- **Created:** 2026-06-01

## Role: NG (SDK Quality & Developer Experience)

**Focus:** SDK reliability, API completeness, developer friction points, cross-platform consistency.

**Previous Sessions:**
- Turn 1 (2026-06-01): SDK lineage audit (Monocle → Frame → Halo). Documented 8 breaking changes, deprecated APIs, capability gaps.
- Turn 2 (2026-06-01): Migration patterns & compatibility. Frame vs. Halo hardware differences. Web Bluetooth Chromium-only constraint.
- Turn 3 (2026-06-02): Community-discovered SDK rough edges inventory. Six architectural gaps, workaround patterns, recommendations for upstream SDK fixes. See `.squad/decisions/decisions.md for full decision entry.

**Archived (2026-06-02):** Full learnings appended to `.squad/agents/ng/history-archive.md. Current history truncated to recent work only.

---

## Codename Brainstorm — 2026-06-08
- Pitched SDK-quality-lens codename candidates for the Synesthetic Familiar. Team converged on **PULSE** (4 agents). Official codename now VESPER (Aaron final selection). See orchestration-log.

## Session 2026-06-08: VESPER BLE Wire-Format Lock — Endianness/Seq/Opcode/ACK Spec
- Locked: LE endianness (ATT native, M55 native), signed-16 delta dedup (handles wraparound), opcode space (0x00–7F Device→Host, 0x80–FF Host→Device), FAMILIAR_ACK auto every 10 packets, FAMILIAR_RESET 0x01 Device→Host notification. Routed Juanita for test update.

## Current Session (2026-06-02): GitHub Landscape — Community SDK Wrappers & Libraries

**Task:** Search GitHub for community SDK wrappers, BLE drivers, and Lua libraries. Assess production-readiness and recommend adoption/avoidance.

**Summary:** Executed systematic gh searches across repo names, code patterns, and Brilliant Labs official org. Found 9 noteworthy projects.

**Key Findings:**
- Pre-Official Community Work: uma-shankar-gupta/brilliant_ble (Dart, obsolete), brilliantsole/Brilliant-Labs-Frame-Web-SDK (JS, superseded)
- High-Quality Refs: CitizenOneX/frame_ble (Flutter), CitizenOneX/frame_ble_python (Python), CitizenOneX/frame_examples_python (essential migration template)
- Real-World Usage: anonimousname1234/SARBINS (wayfinding), milesprovus/Monocle-Teleprompter (Google API pattern)
- False Positives: caic-xyz (unrelated), floren/monocle (legacy), bitfeed (unrelated)
- Lua Libraries: Generic JSON parsers; not Halo-specific

**Verdict:** USE CitizenOneX examples (migration ref). MONITOR official SDK adoption. AVOID community web/Flutter forks. ARCHIVE Monocle projects.

**Output:** `.squad/agents/ng/github-sdk-community-2026-06-02.md — Annotated catalog.

**Next Steps:** Confirm official SDK standard, flag CitizenOneX in migration guide, monitor Halo community post-launch.

---

## Ideation 2026-06-02

Raw blue-sky ideas for SDK tooling, debugging, community workflows. See `.squad/agents/ng/ideation-2026-06-02.md (no decisions promoted).

---

## Ideation Pass 2 2026-06-02

Cross-pollinated ideation: resonance with Hiro's microservices topology + Librarian's world model. Four mash-ups synthesized:
1. **Gyro-Paced Radial Time** (Ng #1 × Da5id #6) — IMU-responsive clock, first kinetic display control
2. **Micro-Haptic Feedback** (Ng #3 × Y.T. #7) — Silent flicker-based haptics via gesture recognition
3. **Episodic Lua Recorder** (Ng #2 × Librarian #7) — On-device tracking + host LLM stitching
4. **Privacy-Aware Refresh** (Ng #7 × Raven #7) — Face-gating drives display power budget

Three NEW cross-pollinated SDK patterns: sensor-fusion context primitive, event-priority backpressure queue, peer-to-peer Lua library CDN.

See `.squad/agents/ng/ideation-pass2-2026-06-02.md`.

---

## User Stories Themes 1-2 — 2026-06-03

**Task:** Author SDK developer-experience user stories through Ng's lens for Aaron's two chosen themes:
1. **Theme 1 — Consent-Aware Memory** (most-cited convergence; privacy + usability)
2. **Theme 2 — The Synesthetic Familiar** (fun + peripheral design + ambient mood)

**Target Personas:**
- Playground demo developer (forking + modifying existing Halo demos)
- Test harness author (Juanita's spiritual successor; integration + chaos testing)
- Lua-on-device developer (event loop authoring; sensor fusion loops)

**Scope:** Surface hidden-but-required SDK primitives. Call out where `brilliant-ble` / `brilliant-msg` falls short. Map stories to BLE opcode gaps, Lua stdlib gaps, and infrastructure work.

**Output:** `.squad/agents/ng/user-stories-themes-1-2-2026-06-03.md`

**Key Findings:**
- **Theme 1 (Consent-Aware Memory):** 5 stories authored. Viability HIGH; no hard blockers. Phase 1 includes consent context metadata (BLE), Lua event hooks, ledger query. Phase 2: pre-blur pipeline (requires image manipulation lib not yet in Brilliant SDK).
- **Theme 2 (The Synesthetic Familiar):** 5 stories authored. Viability MEDIUM. Sprite rendering is straightforward; sensor fusion is ambitious. Phase 1: familiar state + mood animation + sprite upload. Phase 2: true on-device multi-modal fusion (requires M55 NPU TensorFlow Lite integration).

**Stories Authored:** 10 total (5 per theme). Each story includes acceptance criteria + SDK notes revealing required API surface.

**"SDK Doesn't Expose This Yet" Stories:**
- NG-T1-5 (Pre-blur frame pipeline): Requires image processing library in Lua. New BLE opcode `FRAME_WITH_BLUR_MASK` + blur kernel not yet available.
- NG-T2-5 (Sensor fusion context): Requires on-device ML models (scene understanding, emotion classification, gesture recognition) on M55 NPU. No `frame.ml.*` namespace yet.

**Recommended Build Sequence:**
- Phase 1a (1 wk): NG-T1-1, NG-T2-1 (consent context + familiar state)
- Phase 1b (2 wk): NG-T1-2, NG-T1-3, NG-T2-2 (test harness + event hooks)
- Phase 1c (1 wk): NG-T1-4, NG-T2-3, NG-T2-4 (ledger + sprite + testing)
- Phase 2 (4+ wk): NG-T1-5, NG-T2-5 (pre-blur, on-device ML)

**Favorite Story:** NG-T1-3 (consent-needed events) — It's the inflection point between "SDK feature" and "architectural pattern." Small enough to ship Week 1; forces entire consent pipeline design. Non-blocking events mean familiar keeps breathing while consent flows asynchronously. That's wearable computing done right.

**Next Steps:** Aaron prioritization → GitHub issue decomposition → implementation assignment (likely split: SDK changes → upstream Brilliant, playground integration → Ng + demo authors).

---

## Learnings

### 2026-06-08: VESPER BLE Wire-Format Finalization (§5.2)

**Endianness:** Chose **little-endian** for all multi-byte fields. Rationale: BLE ATT layer is LE; ARM Cortex-M55 on Halo is LE; Python `struct '<'` and Lua `string.pack('<I2', ...)` both handle it natively. No guessing required — it's the hardware-native choice.

**Sequence wraparound rule:** uint16 seq wraps 0xFFFF → 0x0000. Device applies a **signed 16-bit delta** comparison: `delta = (received_seq - last_accepted_seq) mod 65536`. If delta is 1–32767 (positive half of int16 space) → accept. If delta is 0 → duplicate, drop. If delta is 32768–65535 (negative half) → stale/out-of-order, drop. This is wraparound-safe for any realistic packet rate. On reconnect: host resets seq to 0x0000, device resets last_accepted_seq to 0xFFFF so delta=1 on first packet.

**Opcode scheme:** Split at 0x80. Range `0x80–0xFF` = Host→Device commands; range `0x00–0x7F` = Device→Host notifications/ACKs. Current assignments: `0x80` = FAMILIAR_UPDATE (H→D), `0x01` = FAMILIAR_RESET (D→H, no payload), `0x02` = FAMILIAR_ACK (D→H, uint16 LE last_received_seq).

**ACK cadence:** Device auto-sends FAMILIAR_ACK every 10 accepted FAMILIAR_UPDATE packets (~1 ACK/sec at 10Hz). No host-initiated request opcode needed — keeps protocol unidirectional for the common case. Also sends unsolicited ACK on BLE reconnect.

**Wire format summary:**
- FAMILIAR_UPDATE: 6 bytes (opcode, mood, intensity, confidence, seq LE)
- FAMILIAR_ACK: 3 bytes (opcode, seq LE)
- FAMILIAR_RESET: 1 byte (opcode only)
