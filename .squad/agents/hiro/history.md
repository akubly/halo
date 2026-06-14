# Hiro (Architect) — Summarized History

**Project:** halo — Halo smart glasses playground  
**Role:** Architecture + integration contracts  
**Created:** 2026-06-01

## Milestones Completed

### Phase 1: ARD & Theme 2 VESPER (Locked 2026-06-07)
- Host-peripheral model (Python host, Lua device); mood inference on host; M55 NPU gates
- Hybrid host-primary autonomy; confidence gating on host; device BLE-drop fallback
- Mood/render decoupling; abstract breathing/color creature; bystander opaque
- Privacy: 5-10% jitter + quantised intensity; raw audio/IMU never leave host

### Phase 2: ARD Persona Review (2026-06-09)
- Applied 15 findings from Design+Security panels
- Heap ownership device-local; quick-reset device-owned (no round-trip); confidence gating host-only
- 30s confidence-hold timeout + 10s both-sensors-fail fallback resolved gating/liveness tension
- Baseline persistence locked to `~/.vesper/baseline.json`

### Phase 3: Week 1 Scaffold (2026-06-09)
- Created `projects/synesthetic-familiar/` with file layout, ownership table, stubs
- Package location: `projects/synesthetic-familiar/` (mirrors `docs/projects/synesthetic-familiar/`)

### Phase 4: Week 2 Integration Contract (Locked 2026-06-10)
- Locked contract binding Ng, Librarian, Da5id, Juanita, Raven
- SensorFrame: 6 fields (4 float, 2 bool); no raw bytes; mic_ok/imu_ok flags
- compute_mood with mic_ok, imu_ok, baseline kwargs; returns MoodResult with gated flag
- Gating authority: main.py (not inference.py)
- Confidence-hold timeout (I2, 30s) + both-sensors-fail (10s) both in main.py
- Intensity quantise {0,25,50,75,100} + jitter ±5 before encode (Gate 2)
- Two hard merge-blocking gates: Gate I7 (mic buffer ≤1s, no raw bytes), Gate 1 (no raw biometrics on wire)

### Phase 5: Week 2 Completion (2026-06-10)
- Ng shipped sensors.py + main.py (59 passed, 5 xfailed)
- Librarian shipped inference.py (5 xfailed, importable)
- Da5id proposed visual enhancements
- Juanita delivered 47 new tests (101 total, all green)
- Raven approved both privacy gates

## Key Learnings

1. Contract-first prevents drift; Week 1 surfaced import-contract misalignment
2. Explicit > Implied; when ARD implies something, explicitly state it
3. Authority must be named; ambiguous ownership invites multiple interpretations
4. Tension resolution, not removal; confidence gate + stuck-creature timeout coexist
5. Storage tier locks tests; baseline persistence must be named explicitly
6. Topology must name the real adapter (desktop Python, not phone)
7. ATTENTION is an overlay, not a peer state
8. "Open but non-blocking" is debt language; gate blocking items explicitly
9. Confidence gating + liveness in tension; 30s timeout resolves it
10. Jitter is polish, not privacy; obscurity + abstraction are real protection
11. Week 3 pattern: SDK gates are the critical path — design the plan so ALL non-gate work starts immediately in parallel; treat gate outcomes as a fork, not a blocker, by pre-designing both paths

### Phase 6: Week 3 Breakdown & Sequencing (2026-06-12)
- Decomposed Week 3 "It's alive" into 15-item work breakdown
- Identified critical path: SDK gates (Ng) → device features → verification
- Sequenced 4-wave fan-out: gates+non-gate work parallel, device features post-gates, integration, polish
- Plan approved by Aaron; full fan-out executed 2026-06-13

## Learnings

12. **Camera is additive, never degrading** — design new modalities so their absence is the default state, not an error. `camera_ok=False` means Phase-1 behavior exactly. This prevents regressions when hardware/SDK gaps appear.
13. **Privacy gates scale with data sensitivity, not feature count** — scene-level visual features (brightness, activity) are LOW privacy risk; face detection is HIGH. The architecture decision isn't "camera yes/no" but "what do you extract from the frame?"
14. **Cloud options form a spectrum of egress** — Option C (receive population model, send nothing) preserves Phase-1 promise; Option A (send derived features) breaks it. Map the egress points first, then choose the option.
15. **Three-copies rule held for Phase 2** — camera capture, cloud client, online learning: all single-consumer. No shared packages needed. Resist extraction pressure until a second project needs the same capability.

### Phase 7: Phase-2 Capability Architecture (2026-06-14)
- Drafted Phase-2 architecture for camera input + cloud refinement
- Camera enters as third modality in SensorFrame; scene-level features only (no face detection)
- Recommended Option C (federated local refinement, no user data egress) for cloud
- Defined 5 new privacy constraints (CAMERA-I1 through MODEL-I5), 2 merge-blocking
- BLE LESC promoted from deferred to gate (JPEG over unencrypted BLE is interceptable)
- Everything stays in `projects/synesthetic-familiar/` — no shared packages
- Artifacts: `.squad/files/phase2-architecture-draft.md`, `.squad/decisions/inbox/hiro-phase2-capability-arch.md`
- 5 open questions flagged for Aaron; Enzo PRD alignment flagged as scope dependency

## Full Session History

Archived in `.squad/agents/hiro/history-detailed-2026-06-12.md` (detailed ARD decisions, persona review applications, scaffold creation, integration contract, PRD review passes).

