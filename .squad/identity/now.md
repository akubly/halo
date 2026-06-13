---
updated_at: 2026-06-13T07:23:00Z
focus_area: VESPER Week 3 "It's alive" — WAVE 1 COMPLETE (SDK gates resolved, gates live, baseline activation gate landed, test harness ready)
active_issues: []
status: Week 3 Wave 1 COMPLETE — Gates, baseline activation, onboarding harness, acceptance tests (176 passing), ATTENTION spec all shipped
---

# What We're Focused On

**Synesthetic Familiar (VESPER)** — Theme-2 project at `projects/synesthetic-familiar/`.

**WEEK 3 "It's alive" — WAVE 1 MERGED** — 2026-06-13 orchestration complete.

**Status:**

### Completed (Wave 1 — 2026-06-13)
- ✅ **SDK Gate 1 (IMU Interrupt):** GO — `frame.imu.tap_callback()` confirmed (ARD API name incorrect; corrected)
- ✅ **SDK Gate 2 (Heap API):** NO-GO → Manual proxy fallback (sprite rows + BLE MTU bytes, 80%/95% thresholds)
- ✅ **Baseline Activation Gate:** ACTIVATION_THRESHOLD=50 Welford samples (Librarian) — population defaults for <50, personal mean+1.5σ for >=50
- ✅ **Onboarding UX Harness:** First-launch detection, calibration status, fallback surfacing, ATTENTION/FAMILIAR_RESET display (Y.T.)
- ✅ **Acceptance Test Suite:** 48 tests (14 FAMILIAR_RESET protocol, 34 baseline activation, 13 onboarding) — 176 total passing, 3 xfailed (Ng contract), 11 skipped (Y.T. pending)
- ✅ **ATTENTION Animation Spec:** 180ms jump (60ms launch + 120ms settle, +4px), white eye + desaturated body, 500ms cooldown (Da5id)
- ✅ **Device Implementation (Ng):** Double-tap FAMILIAR_RESET (opcode 0x01), ATTENTION-on-IMU-peak (1.8g threshold, 500ms overlay), heap_fraction() proxy, glow simplification
- ✅ **Test Results:** 128/128 baseline maintained (no regressions)

### Locked Decisions (Week 3 Wave 1)
- ACTIVATION_THRESHOLD = 50 (sample-count gate, not calendar days)
- ATTENTION is device-side IMU-triggered overlay (not host-side mood state)
- Double-tap FAMILIAR_RESET snaps device to NEUTRAL locally (device-originated notification)
- Heap fallback as v1 design (manual proxy, hardware-swap hook documented)

### Next Step: Week 3 Wave 2 (Post-Gate)
- Ng: Post-gate device implementation (double-tap, ATTENTION rendering, heap thresholds live)
- Da5id: Calibration pass (IMU peak threshold tuning on hardware)
- Raven: Privacy audit on ATTENTION state (on-device accelerometer use)
- Juanita: Fallback verification (hardware edge cases)
- Librarian: Documentation (ARD §10 updates, TEST-STRATEGY updates)

