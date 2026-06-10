# Project Context

- **Owner:** Aaron Kubly
- **Project:** halo — mono-repo playground for authoring apps on Halo smart glasses using the Brilliant SDK
- **Stack:** TBD per package; SDK languages are Python, Flutter (Dart), Web Bluetooth (JS/TS). Lua 5.3 runs on-device.
- **Created:** 2026-06-01

## Learnings Summary

### Halo Architecture Foundations (2026-06-01)
- **Host-app model**: Glasses are peripherals; host drives logic. 3 canonical SDKs (Python, Flutter, Web Bluetooth), Lua on-device. Mono-repo can stay flat; SDK-per-workspace only if 3+ packages share tooling.
- **Lineage**: Monocle (closed) → Frame (Python+Flutter) → Halo (web+lua event loop rewrite). SDK API surface survives; on-device semantics churn. Brilliant prioritizes velocity over backward compat.

### Team Ideation & Themes (2026-06-02 to 2026-06-03)
- **Theme 1**: Consent-Aware Memory (privacy as protocol infrastructure)
- **Theme 2**: The Synesthetic Familiar (familiar as state machine, mood/render decoupling)
- **Key insight**: Constraints-as-architecture (privacy, display budget, battery shape mono-repo structure, BLE protocol, SDK contracts).
- **Cross-cutting concern**: Device Autonomy Tiers (local, hybrid, collective).
- **Strongest mash-up**: Self-Describing Privacy Mesh (distributed protocols + cryptographic consent + edge enforcement).

---

## Theme-2 ARD — 2026-06-07

Authored the Architecture Requirements Document for **The Synesthetic Familiar** — the first official Halo playground project. Document lives at `docs/projects/synesthetic-familiar/ARD.md`.

### Architectural Decisions Made (Locked)

1. **Host-peripheral model confirmed**: Mood inference runs on host (Python), render on device (Lua). M55 NPU is for gate-keeping, not inference.

2. **Autonomy tier: Hybrid Host-Primary**: Host captures sensors + computes mood; device interpolates + renders; device has local fallback on BLE drop.

3. **Mood/render decoupling**: Mood is a pure function `(sensors) → { mood_enum, intensity, confidence }`; render is pure Lua sprite animation. Two separate concerns, two separate modules.

4. **Confidence gating**: If mood confidence < 0.7, hold current state. "Silence is safer than hallucination" (LIBRARIAN-T2-5-ERROR).

5. **Privacy by abstraction**: Creature uses breathing/color/orbit — no labeled emotions visible to bystanders. 5-10% visual jitter prevents statistical inference.

6. **BLE message format**: `FAMILIAR_UPDATE` opcode with mood_enum (4 states), intensity (0-100), confidence (0-100). 6 bytes total.

7. **Display budget respected**: 24×24 sprite at ~1.5% lit pixels idle; 3% max during calm glow. Well under 30% limit.

8. **Graceful degradation hierarchy**: mic+IMU → mic-only → IMU-only → hold-last-state → neutral. Device never freezes.

### Key Open Questions for Aaron (SUBMITTED 2026-06-07)

1. **Host platform**: Python (recommended) vs. Web Bluetooth vs. Flutter?
2. **Sensors for v1**: Mic+IMU (recommended) vs. Mic-only vs. +Camera?
3. **Model location**: Local heuristic (recommended) vs. Cloud API?
4. **Creature form**: Abstract-with-eyes (recommended) vs. Full face vs. Particles?
5. **Evolution scope**: None in Phase 1 (recommended)?

### Phase 1 Scope

IN: Idle behavior, stress/calm states, first-launch UX, attention moments, quick-reset gesture, graceful degradation, privacy-by-design.

OUT: Peer mood sharing, cross-device roaming, evolution over time, custom sprites, sensor fusion ML, personality sliders.

### Next Steps

- Aaron approves/modifies open decisions
- Week 1: "It moves" (sprite renders, BLE works)
- Week 2: "It reacts" (mood inference live)
- Week 3: "It's alive" (polish, UX, ship)

---

## Theme-2 ARD APPROVED — 2026-06-07

Aaron has approved all 3 open decisions. ARD finalized with locked constraints.

### Decisions Approved ✅

**Decision 1: Sensors for v1** ✅ **MIC + IMU**
- Camera deferred to Phase 2 (eliminates recording-indicator overhead for v1)
- Mic captures on host phone; IMU relayed from device
- Sufficient signal for stress/calm detection without camera privacy complexity

**Decision 2: Mood Model** ✅ **LOCAL HEURISTIC (HOST PYTHON)**
- No cloud calls in v1 (latency unacceptable for ambient display)
- Local heuristic on host: pitch_variance (0.4) + acceleration (0.3) + rotation (0.3)
- Cloud refinement deferred to Phase 2 for insights
- Privacy: embodied signals stay on host+device

**Decision 3: Creature Form** ✅ **ABSTRACT-WITH-EYES**
- Geometric shape (no face, no mouth) with single bright eye
- Eyes convey agency and attention direction without revealing state to bystanders
- 24×24 sprite remains abstract enough to satisfy privacy (RAVEN-T2-1) while feeling "alive"
- Full-face and particle-system alternatives rejected

### Consequences Propagated

- **Section 4**: Removed camera optionality; confirmed host=Python, device=Lua; local-only mood inference documented
- **Section 5.3**: Locked Python desktop + Mic+IMU (no camera)
- **Section 5.4**: Local heuristic approach documented concretely; no cloud fallback discussion
- **Section 5.5**: Abstract-with-eyes form locked; eye-based render spec documented
- **Section 5.6**: Privacy section simplified (no camera privacy concerns); mic indicator on phone-side confirmed
- **Section 7**: Open decisions replaced with resolved decisions + alternatives-considered notes
- **Section 8**: Risks/mitigations tightened (removed cloud failure; mic-noise handling added)
- **Section 9**: Milestones tightened with exact technical scope (no if-then-decide language)

### Ready to Build

**Immediate next step:** Week 1 — "It moves" (Lua sprite on device + Python mock FAMILIAR_UPDATE)
- Device: `main.lua` sprite animation loop (24×24 geometric form with eye)
- Host: Python entry point + BLE connection harness
- Success: Aaron sees creature bobbing on Halo, no jitter

---

## Codename Brainstorm — 2026-06-08

Pitched architecture-lens codename candidates for the Synesthetic Familiar. Team converged on **PULSE** (4 agents independently nominated variants). Official project codename now PULSE. See `.squad/orchestration-log/2026-06-08T07-17Z-codename-brainstorm.md`.

---

## VESPER ARD Architecture Clarifications — 2026-06-08

Post-test-strategy advisory review surfaced three ARD ambiguities. Resolved all three. Edits landed in `docs/projects/synesthetic-familiar/ARD.md`.

### Learnings

1. **Heap ownership is device-local.** The ARD already implied it (Lua monitors heap, reduces complexity at 80%, halts at 95%) but never made it explicit. Test Strategy drifted into a host/device heap-warning protocol the ARD never specified. Fix: add a single explicit statement in §5.1 and §5.2 — "Heap management is device-local; not reflected in any host-bound message." FAMILIAR_ACK stays seq-only. No new protocol surface needed. Lesson: when the ARD implies something strongly but doesn't state it, the Test Strategy will invent its own interpretation. State it.

2. **Quick-reset is device-owned.** §3 labeled JUANITA-T2-5 as "Lua input" (on-device) while §5.2 listed `FAMILIAR_RESET` as Host→Device — a direct contradiction. Decision: double-tap detected on-device (Lua IMU/tap), device snaps to NEUTRAL immediately with no host round-trip. FAMILIAR_RESET flipped to Device→Host notification. Rationale: the wearer is correcting a bad inference in real-time; waiting for a host round-trip adds 100-300ms latency and fails if BLE is degraded. Device owns the reset; host can observe via notification. Ng inherits this direction for byte-level spec.

3. **Confidence gating authority is the host alone.** §4 and §5.4 both said confidence gating lives on the host, but left ambiguity about whether device-side gating was also expected. Test Strategy added redundant device-side gating as "required" behavior. Fix: make explicit in §4 autonomy table and §5.4 bullets — host is the single authority; device-side gating is optional defense-in-depth only. Lesson: "authority" must be named explicitly when a concern could reasonably live in two places.

### 2026-06-08 — Tech Design Decision for VESPER

4. **An ARD that specifies byte-level wire formats, file-level decomposition, and constructor signatures IS the technical design.** Aaron asked whether a separate tech design doc was needed before Week 1. Assessed the ARD (§4–§5.5) and Test Strategy (§2–§3) and found they already cover: wire format at byte level, component decomposition at file level, interface contracts with injection signatures, state machine transitions, render specs with pixel budgets, and ports-and-adapters seams. A standalone tech design would re-litigate locked decisions. Recommended: skip it, use per-package READMEs that emerge from implementation. Decision filed to `.squad/decisions/inbox/hiro-vesper-techdesign.md`.

5. **Document from confusion, not speculation.** The anti-anchoring alternative (write a tech design anyway) would be correct if the ARD were requirements-only or if multiple independent implementers needed coordination. For a single-dev 2–3 week playground project with an implementation-grade ARD, front-loading a tech design is premature documentation. The signal to write one mid-sprint: if the implementer keeps re-reading the ARD to answer "how should X talk to Y" and can't find the answer.

---

## VESPER Scaffold — 2026-06-09

Created the Week 1 code scaffold for the Synesthetic Familiar at `projects/synesthetic-familiar/`.

### Package Location Decision

**Chose `projects/synesthetic-familiar/`** (not repo-root flat). Rationale: mirrors `docs/projects/synesthetic-familiar/` so code and docs share a namespace; keeps repo root clean (tooling/config only); ARD §5.3 tree is a relative path, not an absolute placement directive. Decision record: `.squad/decisions/inbox/hiro-vesper-package-layout.md`.

### Scaffold Files Created

- `host/main.py` — entry point stub (Ng owns mock-send harness)
- `host/sensors.py` — `SensorFrame` dataclass + `SensorStream` async iterator signatures
- `host/inference.py` — `MoodResult` dataclass + `compute_mood()` signature + threshold constants
- `host/familiar_protocol.py` — thin stub, docstring + TODO only (Ng owns)
- `host/requirements.txt` — loosely-pinned deps: `brilliant-ble`, `brilliant-msg`, `numpy>=1.24`, `sounddevice>=0.4`
- `device/main.lua` — thin stub, docstring + TODO only (Ng owns)
- `device/sprites/.gitkeep` — empty dir placeholder (Da5id owns assets)
- `tests/test_inference.py` — five stub test cases matching ARD §5.4 scenarios
- `tests/test_protocol.py` — thin stub, docstring + TODO only (Juanita owns)
- `README.md` — project summary, Week 1 goal, file map, ownership table

### Ownership Summary

Ng: `familiar_protocol.py`, `main.py` (harness), `device/main.lua`  
Da5id: `device/sprites/*`  
Juanita: `tests/test_protocol.py`  
Shared: `sensors.py`, `inference.py`, `tests/test_inference.py` (stubs ready for Week 2 fill-in)

---

## Session 2026-06-09: VESPER Week 1 Kickoff Coordinator Role

**Role:** Coordinated 5-agent parallel execution (Ng, Da5id, Juanita, Raven, self).

**Key coordination moment — Integration Reconciliation:**
- Detected contract drift: Juanita's tests expected `Mood` IntEnum + `seq_is_newer` export; Ng initially used int constants
- Brokered alignment: Ng examined test expectations and added both exports without changing tests
- **Result:** Mood enum + seq_is_newer function are now **canonical** and locked per test contract

**Orchestration logs written:**
- 5 agent logs (one per agent) + session log capture key moments
- All decisions from inbox merged into decisions.md (no duplicates)
- Decisions archive gate passed (no entries >30 days old)

**Outcome:** Week 1 "It moves" software foundation complete. 54 tests passing. Hardware validation pending.

---

## Session 2026-06-09: VESPER ARD Persona-Review Remediation

Applied 15 accepted findings (B1, B2, I1, I2, I4, I5, I6, I7, I9, I12, M1–M5) to ARD.md.

### Learnings

1. **Topology must name the real adapter, not the conceptual one.** "Phone mic" survived in the ARD even after the topology was decided as "desktop Python host." Every topology statement in §4, §5.3, and §5.6 must match the real adapter. When topology changes, grep every section.

2. **ATTENTION is an overlay, not a peer state.** A state that must return to the prior state is semantically an overlay/interrupt, not a reachable peer. Modeling it as a peer causes incorrect reset behavior. Ask: "does this state know where it came from?" — if yes, it's an overlay.

3. **"Open but not blocking" is a debt statement, not a risk management strategy.** Three SDK gaps were critical-path but labeled non-blocking. Reclassifying them as go/no-go gates with fallback designs turns vague risk into actionable gates. Rule: if a gap missing would block a milestone, it's a gate.

4. **Confidence gating and liveness are in tension.** The confidence gate (< 0.7 → suppress) is correct for accuracy, but without a timeout it creates a stuck-creature failure mode. The ~30s confidence-hold timeout resolves the tension without weakening the gate. Both invariants coexist.

5. **Jitter is not privacy.** Visual jitter provides anti-robotic animation polish; it does not protect against an informed observer. Conflating the two weakens the honest privacy posture. Real protection = obscurity + abstraction.

6. **Storage strategy must be locked before tests can be written.** Baseline persistence was "Phase 1 can use host filesystem" but was never locked. Juanita's test was blocked. Rule: if a test references a storage layer, the ARD must name it explicitly.

---

## Learnings

2026-06-09: PR #1 review pass — 7 doc-consistency fixes across ARD.md and decisions.md: `struct.pack('<HH', ...)` → `'<H'` for single uint16; NEUTRAL reachability has two distinct paths (sensor fallback vs confidence-hold timeout which sends last-computed mood, not necessarily NEUTRAL); raw audio/IMU never leaves host (not BLE pipe); full FAMILIAR_UPDATE wire format in privacy section; Week-1 jitter criterion now forbids frame stutter, not intentional anti-robotic jitter; `familiar_protocol` is BLE encode/decode only, not mic/inference; confidence-hold timer resets on successfully sent frames only, not suppressed/gated ones.
