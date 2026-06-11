---
updated_at: 2026-06-11T00:00:00Z
focus_area: VESPER Week 2 "It reacts" — MERGED (101 tests, both privacy gates approved)
active_issues: []
status: Week 2 COMPLETE — Real sensors live, local inference (no cloud), privacy gates APPROVED
---

# What We're Focused On

**Synesthetic Familiar (VESPER)** — Theme-2 project at `projects/synesthetic-familiar/`.

**WEEK 2 "It reacts" MERGED** — 2026-06-10 merge wave complete.

**Status:**
- ✅ 101 tests green (was 54 at start of Week 2)
- ✅ Gate I7 (Mic buffer ≤1s, no raw bytes on SensorFrame public API) — **APPROVED**
- ✅ Gate 1 (No raw biometrics on wire, encode_familiar_update signature gated) — **APPROVED**
- ✅ Real mic + IMU sensors operational (sounddevice + numpy)
- ✅ Local mood heuristic (no cloud): tension = pitch_variance×0.4 + acceleration×0.3 + rotation×0.3
- ✅ Confidence gating (< 0.7 → suppress); 30s confidence-hold timeout; 10s both-fail → NEUTRAL
- ✅ Intensity quantised to {0,25,50,75,100}, jittered ±5 before encode (Gate 2)
- ✅ Visual enhancements (CALM halo glow + STRESSED edge fraying) within budget
- ✅ Privacy audit: zero cloud egress, Welford baseline at ~/.vesper/baseline.json

**Locked Decisions:** SensorFrame API (6 fields, no raw bytes), compute_mood signature with confidence gating, main loop state management, BLE wire format, test import paths.

**Next Step: Week 3 "It's alive"**
- Onboarding flow (baseline learning ramp-up)
- Attention moments (burst animation)
- Quick-reset mechanism
- Graceful fallback (confidence hold, both-fail neutral)
- Hardware validation (Halo IMU relay confirmation, OLED visual quality)
