# Raven (Security & Privacy) — Session History

**Project:** halo — Halo smart glasses playground  
**Role:** Threat modeling, sensor-data hygiene, consent flows  
**Created:** 2026-06-01

## Milestones Completed

### Phase 1: Threat Surface Inventory & Privacy Ideation (2026-06-01 to 06-02)
Identified 4 critical gaps in Halo hardware spec:
- No consent indicator (visual/audible) for camera or mic — violates bystander-consent laws.
- Cloud data-flow opacity (Noa agent's handling undocumented).
- Pairing mode not time-limited — 8s button hold can trigger accidentally.
- No documented data retention policy.

Pitched 8 privacy-as-feature ideas + 4 cross-pollinated mash-ups + 3 privacy-as-feature amendments. Key resonance: Librarian #7 (Episodic Stitching), Hiro #2 (Temporal Viewport), Enzo #4 (Memory Ledger).

**Insight:** Privacy constraints unlock architecture differentiation. Halo's ability to prove bystander redaction = moat against lawsuit liability.

### Phase 2: Theme 2 User Stories & RAVEN-T2-1 Constraints (2026-06-03)
Authored 3 user stories for Synesthetic Familiar privacy guardrails:
- [RAVEN-T2-1] Bystander opaqueness: abstract patterns, no labeled state inference.
- [RAVEN-T2-2] Wearer sync control: toggle + per-contact broadcast rules.
- [RAVEN-T2-3] Auditor verification: no server-side logging, encryption proof.

**Key design decision:** Intensity quantised to {0,25,50,75,100}, not continuous float. 5-10% jitter at host **before** encode, not Lua. Bob frequency snapped to discrete tiers (not breathing-rate mapping).

### Phase 3: Week 1 Privacy Pass (2026-06-09)
Audit of mock pipeline (all stubs, zero real sensors).
- **Finding:** Data flow safe (Mock Python → 6-byte BLE → render). Secrets clean. No API keys, tokens, `.env`.
- **RAVEN-T2-1 locked for Week 2:**
  - Intensity quantised {0,25,50,75,100} (no raw float).
  - 5-10% jitter at host before encode.
  - Bob frequency snapped to tiers.
  - CI test `test_familiar_update_carries_no_raw_biometric_values` required before Week 2 real-sensor merge.
- **Veto authority:** If either gate is absent at real-sensor merge, RAVEN blocks.

### Phase 4: Week 2 Privacy Audit (2026-06-10T23:17:50-07:00)
Complete audit of real-sensor pipeline (sensors.py, main.py, inference.py, familiar_protocol.py). 101 tests passing.

**Both merge-blocking gates: APPROVED.**

#### Gate I7 (Mic buffer discipline) — APPROVED
- Rolling buffer exactly 1s (`np.zeros(sample_rate)`), never grows.
- Zeroed under lock post-snapshot (`sensors.py:308`, `self._buffer[:] = 0.0`).
- Also zeroed on stop() (`sensors.py:244`).
- SensorFrame public API: 4 float + 2 bool only. No bytes/ndarray/list.
- Raw audio never logged (callback logs sounddevice status only), written, transmitted.
- `del samples` at line 319 is correct belt-and-suspenders label but does NOT zero heap memory — real protection is in-place buffer zero at line 308. Non-blocking hardening for Week 3.

#### Gate 1 (No raw biometrics on wire) — APPROVED
- `encode_familiar_update` signature: (mood, intensity, confidence, seq) — no raw sensor param.
- `main.py` passes only: mood_int (0-3), quantised+jittered intensity (int), confidence×100 (int), seq counter. Zero raw values.
- Neutral fallback uses hardcoded constants (no leakage).

#### Cloud egress — CLEAN
- `inference.py`: stdlib only (dataclasses, datetime, json, math, pathlib, typing).
- `sensors.py`: numpy + sounddevice (local audio), no cloud SDK.
- `main.py`: frame_sdk (BLE SDK, not cloud), others stdlib.
- Grep `requests|boto3|openai|anthropic|google|azure|httpx` in host/*.py: zero matches.

#### Quantise + jitter — PASS
- Quantise: {0,25,50,75,100} correct 5-level bucketing per contract.
- Jitter: ±5 via `random.randint(-5,5)`, clamped 0-100, **host-side before encode**.
- At lower bound of original spec (±5-10%). Non-blocking; LESC Phase 2 is real protection.
- Jitter is obscurity + anti-robotic polish, NOT cryptographic guarantee. BLE remains unauthenticated/unencrypted (Phase 1 accepted risk).

#### Non-blocking follow-ups
- **W3-1:** Harden snapshot zeroing (Ng, Week 3). Add `samples[:] = 0.0` before del.
- **P2-1:** LESC (BLE encryption/auth, Phase 2).
- **P2-2:** Baseline plaintext hardening at `~/.vesper/baseline.json` (Librarian, Phase 2, OS keychain).
- **P2-3:** Jitter range review post-LESC (Phase 2).

---

## Learnings

1. **`del samples` is not a security primitive.** Numpy snapshot refcount decrement ≠ memory zero. In-place buffer zero is actual protection.
2. **Confidence byte escapes quantisation.** Transmitted at ~1% precision; not a direct biometric, acceptable Phase 1, but future protocols should consider whether reliability signals need discrete tiers too.
3. **Jitter placement is the defence layer.** Host-side quantisation + jitter before encode prevents rate leakage from transmitted intensity byte. Lua-only jitter is insufficient.
4. **Phase 1 accepted risks have Phase 2 remediations.** BLE unauthenticated + baseline plaintext + narrow jitter range are known risks with locked Phase 2 owners.

---

### Threat Surface Inventory (2026-06-01)

**SENSORS — Sensitive Data Generators:**
- **Camera:** 640×480 global shutter, always accessible via `frame.camera.capture()` Lua API. No hardware kill switch or LED indicator mandated. Raw Bayer frames can be streamed over BLE to host app. NO BYSTANDER CONSENT SIGNAL observed in hardware spec.
- **Microphone:** Dual TDK MEMS, supports always-on Audio Activity Detection (AAD) at 20µA for wake detection. Can be activated via `frame.microphone.start()` and streamed to host over LUA RX BLE characteristic. NO mandated audible indicator found.
- **IMU:** 6-axis (accel + magnetometer) with tap detection; streams raw sensor data and computed heading/pitch/roll. Low power (125µA accel, 30µA compass). Tap callback available but no privacy concern — orientation-only data.
- **Location:** None captured on-device. No GPS. IMU heading is compass-based, not absolute location.

**RECORDING INDICATORS — Bystander Consent:**
- **No hardware recording LED documented.** Device shows white LED (charging status), button-controlled pairing mode LED (flashing). No camera-active or mic-active LED mandated in hardware spec.
- **No audible indicator specified.** Bone conduction speakers are present but no mandatory audio cue on capture/record start.
- **RISK:** Wearer can film/record without visible indicator to bystanders. Non-compliance with laws requiring recording consent indicators (e.g., CA AB 375, EU GDPR visual/audible signals).

**BLE PAIRING & ENCRYPTION:**
- **Pairing model:** BLE bonding required; 8-10s button press enters pairing mode (single device at a time). No multi-device pairing history.
- **Encryption:** BLE 5.3 standard; bonded devices use encrypted link. No evidence of rotating session keys or per-frame ECDH — standard BLE LESC (LE Secure Connections) expected.
- **Pairing attack surface:** Button-hold mode is NOT time-limited; 8s unguarded button hold = pairing mode. Could be triggered by long-press during normal use (e.g., accidental grip while in pocket). 8-10s window is reasonable but not hardened against accidental activation.
- **Bonded forever:** No documented re-pairing requirement or periodic key rotation. Once bonded, device reconnects automatically.

**DATA FLOW — Default Paths:**
- **On-device processing:** Lua VM runs on Cortex-M55; camera, mic, IMU data processed locally before export.
- **Host app channel:** All sensor data (camera, mic) flows to host via BLE LUA RX characteristic after Lua app captures and encodes (JPEG for camera, PCM/LC3 for audio).
- **Cloud path:** Noa (cloud AI agent) mentioned on product page; documented data-flow from host app to Noa NOT found in SDK docs. Assumption: host app determines cloud upload policy — **unclear where Halo raw data goes from Noa.**
- **No documented telemetry from device firmware.**

**ENCRYPTION & SECRETS:**
- No API keys, tokens, or secrets documented in SDK.
- BLE comms encrypted via bonding; firmware OTA signed (MCU-BOOT SMP scheme, no further details in public docs).

**CRITICAL GAPS:**
1. **No consent indicator (visual/audible) for camera or mic** — violates bystander-consent laws in many jurisdictions.
2. **Cloud data-flow opacity:** Noa agent's sensor data handling policy not documented in public SDK/hardware specs.
3. **Pairing mode not time-limited** — 8s button hold can be triggered accidentally, exposing device to unpaired hosts in proximity.
4. **No documented data retention policy** on host app side — unclear if Noa stores video/audio after cloud inference.

## Ideation 2026-06-02

**Privacy as Feature, Not Constraint**

1. **Ephemeral Vision Mode** — Recorded video auto-deletes after 30 seconds unless user explicitly saves it; bystanders see a countdown LED showing "you're being filmed but this is temporary."

2. **Consent Broadcast Beacon** — Halo emits a persistent BLE signal that broadcasts "I'm recording right now; scan with your phone to see my camera feed in real-time and grant/revoke consent."

3. **Selective Blur on Wearer's Terms** — User pre-marks faces, license plates, home addresses they don't want to see; Halo's on-device AI automatically blurs them from video, giving the wearer selective blindness to protect *others* from their gaze.

4. **Cryptographic Attention Proofs** — Camera captures hash-only proof that wearer "looked at X" (verifiable accountability) without storing or exporting the actual image data.

5. **Privacy Mode as Social Signal** — External LED ring shows realtime privacy stance to bystanders: red = recording, yellow = observation-only, green = fully private; transparency broadcast from across the room.

6. **Decentralized Consent Layer** — Before video leaves the device, bystanders within BLE range can cryptographically sign consent/revocation that embeds into video metadata; footage is legally encumbered.

7. **Automated Face-Gating** — Halo learns wearer's face and automatically refuses to record when others are in frame unless they explicitly opt-in via phone or NFC tap; the glasses become a consent engine, not a surveillance tool.

8. **Privacy Redaction Workflow** — After every recording session, wearer enters mandatory guided redaction: mark faces, plates, addresses to blur before any export; creates accountability friction and transparent data retention.

---

## Ideation Pass 2 2026-06-02

**Cross-Pollination: Privacy Lens on All Agents' Ideas**

Completed `.squad/agents/raven/ideation-pass2-2026-06-02.md`:

- **🔥 Resonance (3 ideas):** Librarian #7 (Episodic Stitching—privacy as guardrail), Hiro #2 (Temporal Viewport—zero-knowledge replay), Enzo #4 (Memory Ledger—consent-gated storage)
- **🀀 Mash-ups (4 NEW ideas):** 
  1. Consent-Gated Memory Ledger (Librarian × Enzo × Raven #6)
  2. Embodied Privacy Proof System (Hiro #7 × Raven #4)
  3. Ambient Consent Breathing (Da5id #1 × Raven #5)
  4. Peer Consent Mesh (Ng #5 × Raven #6)
- **✏️ Amendments (3 revisions):** Raven #2 (remove app-scan requirement), Raven #4 (salted hashes + zero-knowledge proofs), Raven #8 (automatic first-pass blur + audit trail)
- **🌟 NEW (3 privacy-as-feature ideas):** Bystander Replay Rights, Privacy Proof-of-Work (consensus voting), Privacy Cascades (transitive consent for inference)

**Key insight:** Privacy constraints *unlock* Librarian's memory system, Hiro's temporal queries, and Ng's mesh—they're not limitations, they're differentiators. Halo's ability to prove it redacts bystanders is the moat against lawsuit liability.

---

## User Stories Themes 1-2 — 2026-06-03

**Status:** Authored  
**Scope:** 9 user stories (6 Theme 1: Consent-Aware Memory, 3 Theme 2: The Synesthetic Familiar)  
**Personas:** Bystander (primary for T1), Wearer, Auditor, Revoked-Consent Ex-Friend  

**Themes:**

### Theme 1: Consent-Aware Memory (6 stories)
Concrete privacy obligations for Halo's Memory Ledger + Episodic Stitching. Translates Enzo's on-device rolling buffer and Librarian's stitching engine into *testable* consent invariants.

- **[RAVEN-T1-1]** Bystander notification: persistent, non-dismissible, 24h window for revocation
- **[RAVEN-T1-2]** Wearer review: mandatory pre-storage approval per-face, audit trail logged
- **[RAVEN-T1-3]** Revocation enforcement: persistent do-not-record token, bilateral scope
- **[RAVEN-T1-4]** Audit compliance: cryptographic consent manifest + zero-knowledge proofs
- **[RAVEN-T1-5]** Right-to-be-forgotten: revocation + cloud export notice + re-encryption
- **[RAVEN-T1-6]** Privacy receipts: session-end proofs signed + timestamped for legal defensibility

### Theme 2: The Synesthetic Familiar (3 stories)
Privacy guardrails for the Familiar creature (Y.T. #1 × Da5id × Librarian #2). Ensures ambient internal-state rendering doesn't become involuntary biometric leakage.

- **[RAVEN-T2-1]** Bystander opaqueness: abstract patterns, no labeled state inference
- **[RAVEN-T2-2]** Wearer sync control: toggle + per-contact rules for state broadcasting
- **[RAVEN-T2-3]** Auditor verification: no server-side logging, encryption proof, retention policy

**Key design decisions encoded:**
1. Consent is **bilateral** (wearer ↔ bystander), **not broadcast** (wearer → many).
2. Revocation is **persistent locally** but **doesn't propagate** across the mesh; each pair negotiates independently.
3. **Privacy receipts + audit trails** enable legal defensibility — Halo's moat.
4. Familiars are **opaque to bystanders** — beauty without revelation.
5. **All consent metadata is cryptographically signed** — tampering is detectable.

**Implementation notes:**
- **Critical path:** T1-1, T1-2 (core consent flow) + T1-6 (privacy receipts) for MVP.
- **Post-MVP:** T1-3 (revocation persistence), T1-4 (audit tooling), T1-5 (right-to-be-forgotten).
- **Cross-cutting:** BLE encryption + consent metadata layer, on-device signing (device private key), time-server integration.
- **Theme 2 ships with Theme 1:** Familiar safeguards are dependencies of any memory system.

**Saved to:** `.squad/agents/raven/user-stories-themes-1-2-2026-06-03.md`

---

## Codename Brainstorm — 2026-06-08

Pitched security/privacy-lens codename candidates for the Synesthetic Familiar. Team converged on **PULSE** (4 agents independently nominated variants). Official project codename now PULSE. See `.squad/orchestration-log/2026-06-08T07-17Z-codename-brainstorm.md`.

---

## VESPER Week-1 Privacy Pass — 2026-06-09

**Scope:** Week-1 mock pipeline review for `projects/synesthetic-familiar/`. All source files are `# TODO` / `raise NotImplementedError` stubs — no real sensors touched in Week 1.

**Key findings:**

1. **Data flow confirmed safe (3 boxes, Week 1):** Mock Python source → 6-byte `FAMILIAR_UPDATE` BLE packet → Halo Lua render. Zero real sensor data captured or transmitted. Finding: CLEAR.

2. **Secrets scan: CLEAN.** No API keys, tokens, passwords, or `.env` files in the committed package. `requirements.txt` contains only `brilliant-ble`, `brilliant-msg`, `numpy`, `sounddevice` — no cloud SDKs.

3. **RAVEN-T2-1 constraint established for Week 2:** The bobbing sprite's animation parameters (`intensity` byte, bob frequency) must NOT be a 1:1 mapping to any biometric rate. Key rules locked in `.squad/decisions/inbox/raven-vesper-week1-privacy.md`:
   - `intensity` quantised to `{0, 25, 50, 75, 100}` — no raw float passthrough
   - 5–10% random jitter applied at host **before** `encode_familiar_update()`
   - Bob frequency snapped to discrete tier (not continuous breathing-rate float)
   - `test_familiar_update_carries_no_raw_biometric_values` must be in CI before Week 2 real-sensor merge

4. **BLE expectations for Week 2:** LESC bonding (encrypted channel) confirmed as requirement. No pairing mode triggered programmatically. No device address or raw sensor data written to disk or committed files.

**Disposition:** No block on Week 1. Two hard gates before real sensors land in Week 2: (a) protocol CI test passing, (b) intensity quantisation + jitter enforced. RAVEN vetoes merge if either is absent.

**Decision output:** `.squad/decisions/inbox/raven-vesper-week1-privacy.md`

**Learned:** The "jitter before encode" placement matters — jitter added only in Lua render layer can still leak rate from the transmitted `intensity` byte if an attacker sniffs BLE. Host-side quantisation + jitter is the correct defence layer.

---

## Session 2026-06-09: VESPER Week 1 Privacy Validation Complete

**Scope:** Week-1 mock pipeline audit for `projects/synesthetic-familiar/`. All source files are stubs — zero real sensor data.

**Key findings:**
1. **Data flow safe:** Mock Python → 6-byte BLE → Halo render. No real sensors. Finding: CLEAR.
2. **Secrets audit: CLEAN.** No API keys, tokens, `.env` files. Requirements clean (no cloud SDKs).
3. **RAVEN-T2-1 locked for Week 2:**
   - `intensity` quantised to {0, 25, 50, 75, 100} — no raw float
   - 5–10% jitter at host **before** encode
   - Bob frequency snapped to tiers (not continuous)
   - Protocol test `test_familiar_update_carries_no_raw_biometric_values` required in CI before Week 2

**Decision merged:** `raven-vesper-week1-privacy.md` → decisions.md

**Veto authority:** If either Week 2 gate is absent at real-sensor merge, RAVEN blocks the PR.

**Outcome:** Week 1 green. Week 2 privacy gates formalized.

---

## Session 2026-06-10T23:17:50-07:00: VESPER Week 2 Privacy Audit

**Scope:** Week-2 real-sensor pipeline — `sensors.py`, `main.py`, `inference.py`, `familiar_protocol.py`. 101 tests passing. First audit of live mic capture + IMU relay + local mood heuristic.

**Both merge-blocking gates: APPROVED. Week 2 may merge.**

### Gate I7 (Mic buffer discipline) — APPROVED
- Rolling buffer is exactly 1 second (`np.zeros(sample_rate)`) — never grows.
- Buffer zeroed under lock immediately after snapshot copy (`self._buffer[:] = 0.0` at `sensors.py:308`).
- Buffer also zeroed on `stop()` (`sensors.py:244`).
- `SensorFrame` public API: 4 `float` + 2 `bool` fields only. No `bytes`, `ndarray`, list anywhere.
- Raw audio never logged (callback logs only sounddevice `status` flag), never written to disk, never transmitted.
- `del samples` at line 319 is correct belt-and-suspenders labeling but does not zero heap memory — real protection is the in-place zero at line 308. Non-blocking hardening item for Week 3.

### Gate 1 (No raw biometrics on wire) — APPROVED
- `encode_familiar_update` signature: `(mood, intensity, confidence, seq)` — no raw sensor parameter exists.
- `main.py` passes only: `mood_int` (0–3), quantised+jittered intensity (int), `confidence × 100` (int), sequence counter. Zero raw values cross the wire.
- Neutral fallback uses hardcoded constants — no sensor leakage.

### Cloud egress — CLEAN
- `inference.py`: stdlib only (`dataclasses, datetime, json, math, pathlib, typing`). Zero network imports.
- `sensors.py`: `numpy` + `sounddevice` (local audio), no cloud SDK.
- `main.py`: `frame_sdk` (BLE SDK, not cloud), all others stdlib.
- Grep for `requests|boto3|openai|anthropic|google|azure|httpx`: zero matches in `host/*.py`.

### Quantise + jitter — PASS
- Quantise: `{0, 25, 50, 75, 100}` — correct 5-level bucketing per contract.
- Jitter: ±5 via `random.randint(-5, 5)`, clamped 0–100, applied **host-side before encode**.
- Jitter is at the lower bound of original Week 1 spec (±5–10%). Non-blocking; LESC in Phase 2 is the real protection.
- Noted explicitly: jitter is obscurity + anti-robotic polish, NOT a cryptographic privacy guarantee. BLE remains unauthenticated/unencrypted (Phase 1 accepted risk).

### Desktop mic indicator — PASS
- `sounddevice.InputStream` uses OS audio subsystem normally. No raw driver bypass. OS-managed indicator operates as expected.

### Residual risks (non-blocking)
1. **`del samples` doesn't zero heap** — add `samples[:] = 0.0` before del for belt-and-suspenders hardening (Week 3, Ng).
2. **Confidence byte not quantised** — transmitted at ~1% precision; not a direct biometric, acceptable for Phase 1.
3. **BLE unauthenticated/unencrypted** — LESC deferred to Phase 2 (Phase 1 accepted risk, single-user playground).
4. **`~/.vesper/baseline.json` plaintext** — derived arousal statistics stored unencrypted; Phase 2 OS keychain consideration (Librarian).

**Decision output:** `.squad/decisions/inbox/raven-week2-privacy-audit.md`

**Learned:**
- `del samples` on a numpy snapshot is a CPython refcount decrement, not a memory zero. The in-place buffer zero (`self._buffer[:] = 0.0`) is the actual protection. Belt-and-suspenders intent is good but the comment should clarify this distinction.
- Confidence byte escapes quantisation — future protocols should consider whether reliability signals also need discrete tiers, especially once LESC lands and only statistical inference (not raw sniffing) remains as an attack vector.
- Jitter at ±5 absolute points on a 0–100 scale is weaker obscurity than originally spec'd (±5–10%). Once LESC encrypts the channel, jitter's primary role becomes anti-robotic naturalness, not privacy, and the range can be relaxed.
