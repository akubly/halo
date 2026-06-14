# Raven (Security & Privacy) — Summarized History

**Project:** halo — Halo smart glasses playground  
**Role:** Threat modeling, sensor-data hygiene, consent flows  
**Created:** 2026-06-01

## Milestones Completed

### Phase 1: Threat Surface Inventory & Privacy Ideation (2026-06-01 to 06-02)
- Identified 4 critical gaps in Halo hardware spec (no consent indicator, cloud opacity, unguarded pairing, no retention policy)
- Pitched 8 privacy-as-feature ideas + 4 mash-ups + 3 amendments
- **Key insight:** Privacy constraints unlock architecture differentiation; Halo's bystander redaction = lawsuit moat

### Phase 2: Theme 2 User Stories & RAVEN-T2-1 Constraints (2026-06-03)
- Authored 3 user stories for Synesthetic Familiar privacy guardrails
- Key design decision: Intensity quantised to {0,25,50,75,100}, 5-10% jitter at host **before** encode, bob frequency snapped to tiers

### Phase 3: Week 1 Privacy Pass (2026-06-09)
- Audit of mock pipeline (all stubs, zero real sensors)
- Data flow safe; secrets clean
- RAVEN-T2-1 locked for Week 2: intensity quantised, jitter applied host-side, CI test `test_familiar_update_carries_no_raw_biometric_values` required

### Phase 4: Week 2 Privacy Audit (2026-06-10T23:17:50-07:00)
- Complete audit of real-sensor pipeline (sensors.py, main.py, inference.py, familiar_protocol.py). 101 tests passing.
- **Both merge-blocking gates: APPROVED**
  - **Gate I7 (Mic buffer):** Rolling buffer 1s, zeroed post-snapshot, SensorFrame public API safe (no ndarray), raw audio never logged/written/transmitted
  - **Gate 1 (No raw biometrics on wire):** `encode_familiar_update` signature clean, main.py passes only quantised+jittered values
- Cloud egress CLEAN (zero cloud SDKs)
- Quantise + jitter PASS (5-level bucketing, ±5 host-side before encode)
- Non-blocking follow-ups: W3-1 (harden snapshot zeroing), P2-1 (LESC), P2-2 (baseline plaintext), P2-3 (jitter range review)

## Key Learnings

1. `del samples` is not a security primitive; in-place buffer zero is actual protection
2. Confidence byte escapes quantisation but acceptable Phase 1
3. Jitter placement is defence layer; host-side quantisation prevents rate leakage
4. Phase 1 accepted risks have Phase 2 remediations (BLE unauth + baseline plaintext + narrow jitter)

## Critical Gaps (Hardware Spec)

1. No consent indicator (visual/audible) for camera or mic — violates bystander-consent laws
2. Cloud data-flow opacity (Noa agent's handling undocumented)
3. Pairing mode not time-limited — 8s button hold can trigger accidentally
4. No documented data retention policy

### Phase 5: Week 3 Privacy Audit (2026-06-13T23:13:01-07:00)

- Audited 4 surfaces: ATTENTION-on-IMU-peak, onboarding/baseline activation gate, W3-1 snapshot zeroing, secrets scan.
- **All gates: APPROVED / CONFIRMED / CLEAN. Week 3 ships.**
  - **ATTENTION accel path:** Render-loop poll of `frame.imu.raw()` is purely on-device. `ax/ay/az/mag` are Lua locals; no BLE send in the IMU-peak branch. No new characteristic. Bystander cannot infer stress/calm from ATTENTION visual (gray+white+jump ≠ stress/calm signal). ✅ APPROVED
  - **Onboarding/baseline.json:** `mean`/`stddev` of tension scalar — derived behavioral metric, not biometric-identifying. P2-2 deferral (plaintext) not regressed. New P2-4 item: `get_calibration_status()` prints `mean=X.XXX, stddev=X.XXX` to stdout when personalized — move to `--verbose`/debug in Phase-2. Owner: Y.T. ✅ APPROVED (Phase-1 accepted risk)
  - **W3-1 snapshot zeroing:** Three-layer zeroing confirmed in `_extract_frame()` `finally` block: (1) `self._buffer[:]=0.0` under lock, (2) `samples[:]=0.0` in finally, (3) `del samples`. Also zeroed in `stop()`. ✅ CONFIRMED
  - **Secrets scan:** No API keys, tokens, cloud SDKs, or credentials in Week 3 code. ✅ CLEAN
- Audit verdict filed: `.squad/decisions/inbox/raven-week3-audit.md`
- New deferred item added: **P2-4** (stdout mean/stddev print, owner Y.T.)

## Full Session History

Archived in `.squad/agents/raven/history-archive-detailed.md` (detailed threat inventory, ideation passes, story mappings, Week 1 & 2 audit narratives).



📌 Team update (2026-06-14T05:36:23Z): Da5id eye dilation INCLUDED (§6 Q1); host bind-up + onboarding complete (Y.T.); ATTENTION visuals shipped (Ng); 262 tests green (Juanita); docs synced (Librarian) — all surfaces APPROVED, ship ready — decided by Da5id, Y.T., Ng, Juanita, Librarian

📌 Team update (2026-06-14T07:59:43Z): Phase-2 plan drafted (camera + cloud refinement) — pending Aaron approval. Decisions: Enzo (capability scope), Hiro (architecture). No code written. Affected: implementation lead (Ng), privacy review (Raven), docs (Librarian), testing (Juanita), infrastructure (Da5id).
