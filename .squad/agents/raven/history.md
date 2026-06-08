# Project Context

- **Owner:** Aaron Kubly
- **Project:** halo — mono-repo playground for authoring apps on Halo smart glasses
- **My layer:** Threat models, sensor-data hygiene, consent flows, secrets
- **Sensitive surfaces:** camera, microphone, BLE pairing, any third-party API call carrying sensor data
- **Created:** 2026-06-01

## Learnings

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
