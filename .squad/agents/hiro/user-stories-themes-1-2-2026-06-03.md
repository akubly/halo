# User Stories — Themes 1 & 2 | 2026-06-03
## Architectural Lens: Consent-Aware Memory & The Synesthetic Familiar

---

## THEME 1: CONSENT-AWARE MEMORY (The Useful One)

### [HIRO-T1-1] As a future maintainer, I want the on-device consent ledger to be a first-class data structure, so that privacy constraints are architecture, not middleware.

**Persona:** Future Maintainer (inheriting code in 6 months)

**Acceptance Criteria:**
1. Consent metadata is embedded in the **message wire protocol**, not bolted on at the SDK layer. Every recording event carries `[timestamp, subject_hash, consent_status, expiry_epoch]` as part of the canonical BLE frame.
2. The mono-repo enforces this via linting: any camera/mic capture without a paired consent record fails build-time validation.
3. Consent ledger is queryable by expiry: running `list_expired_consent(cutoff_epoch)` returns all footage that requires redaction within the next 24 hours.
4. Redaction jobs are *scheduled*, not ad-hoc—on-device scheduler runs auto-blur at fixed intervals, and logs are verifiable (audit trail of what was redacted and why).
5. Future device migrations (Frame→Halo→Halo2) can decode the ledger without losing provenance—wire format is **versioned and self-describing**.

**Architectural Note:**
Consent is not a toggle; it's a **durability boundary**. The system architecture splits into three data zones: ephemeral (rolling buffer, unencrypted), consented-persistent (encrypted, revocable), and consent-expired (auto-redacted). Each zone has distinct BLE layer handling, storage encryption keys, and export rules. This changes the SDK from "command dispatcher" to "consent enforcer."

---

### [HIRO-T1-2] As an on-call engineer responding to "footage was leaked," I want cryptographic notarization of consent at capture time, so that every exported clip is self-proving and tamper-evident.

**Persona:** On-Call Engineer (debugging privacy incidents)

**Acceptance Criteria:**
1. Every footage export carries a **signed consent manifest**: `(clip_hash, consenting_subjects, consent_timestamps, redaction_operations_applied, signer_device_id)` cryptographically signed by the recording Halo.
2. The manifest is **human-readable in plaintext** (not just a blob). An auditor can read: "Alice's face detected, 3 possible IDs matched consent DB, Alice_ID approved at 14:32 UTC, 1 frame redacted per John_ID revocation at 14:33 UTC."
3. If consent status changes *mid-recording* (John revokes while recording is active), the manifest shows exactly which frames are affected and why.
4. Manifest travels with exported footage; if footage is ever disputed, the manifest can be verified against John's device (zero-knowledge proof: "this signature came from that Halo").
5. **Failure case:** Consent manifest is **malformed or missing** when export is attempted → export is **blocked**. System refuses to create "unsigned footage."

**Architectural Note:**
This elevates consent from application logic to **protocol infrastructure**. The BLE layer gains a cryptographic signing step; every payload leaving the device proves consent state. This is similar to how OpenTelemetry carries trace context—consent context is now a **first-class citizen in the message envelope**.

---

### [HIRO-T1-3] As a forker building multi-wearer collaboration, I want consent negotiation to be **peer-to-peer and bystander-verifiable**, so that I don't need a central consent service.

**Persona:** Forker (extending Halo into workplace/clinical use)

**Acceptance Criteria:**
1. When two Halos come into Bluetooth range, they auto-exchange **consent stance advertisements**: device A broadcasts `(stance: recording|observation|private, retention_window: 1h|1d|7d, consent_salt: hash)` *without TLS* (fast, local-only, no auth).
2. Each Halo **signs an encounter proof** with both devices' public keys: `sign(Alice_ID || Bob_ID || timestamp || Alice_stance || Bob_stance)`. This proof is embedded in any footage containing both wearers.
3. A third party (lawyer, regulator, bystander) can verify the proof by querying either device: "Is this encounter notarized?" → both devices confirm the signature independently.
4. If Bob *revokes* his consent after the encounter, his device adds a **revocation entry** to the ledger *without reaching out to Alice*. Alice's next export sees the revocation and auto-redacts Bob from that moment forward.
5. Revocation is *non-repudiable*: Bob's device signs every revocation with a timestamp. If Bob later claims he never revoked, Alice can show the signed proof.

**Architectural Note:**
This eliminates the need for a **central consent broker**. The architecture becomes **gossip-based**: consent state propagates via device-to-device BLE exchanges (no server). Each device maintains its own ledger and signs locally. Verification is zero-knowledge (no device reveals its full dataset; only answers yes/no to specific queries). This is a fundamental shift from "consent service" to "consent protocol"—every playground app inherits this for free.

---

### [HIRO-T1-4] As a wearer, I want the memory ledger to auto-redact after consent expires, so that I *cannot accidentally export footage with stale consent*.

**Persona:** Wearer (end-user relying on consent expiry to do the right thing)

**Acceptance Criteria:**
1. Consent entries have **explicit expiry epochs** (e.g., "Alice consented until 2026-06-04 14:30 UTC"). Once that time passes, Alice's face is legally "no longer consented" to be in persistent storage.
2. On-device auto-redaction runs at midnight (or configurable interval) and **scans all persistent footage**, applying redaction to footage older than 24 hours where consent has expired.
3. Redaction is **logged and auditable**: a file `.consent_audit.log` shows "2026-06-04 23:00:15 — Redacted 47 frames containing John_ID; consent expired at 2026-06-03 14:30 UTC."
4. Export function **rejects any footage with expired-but-unredacted frames**. Error: "Cannot export: 12 frames require redaction due to expired consent. Run redaction job and retry."
5. **Failure case:** System clock is tampered/wrong. Behavior: system refuses to redact/export if internal clock differs by >30 minutes from a trusted external time source (NTP, phone time). Sends alert: "Clock skew detected; consent redaction disabled until sync."

**Architectural Note:**
This introduces **time as a data durability boundary**. The architecture must track "time until consent is valid" as a first-class property, parallel to storage encryption. The on-device scheduler becomes a **consent enforcer**, not just a background task. This requires careful clock-synchronization logic and a "time guard" that prevents footage export if the device time is unreliable.

---

### [HIRO-T1-5] As a on-call engineer, I want consent message failures to be **detected and surfaced as observable events**, so that silent consent-check bypasses are impossible.

**Persona:** On-Call Engineer (monitoring for privacy violations)

**Acceptance Criteria:**
1. Every consent check (before footage capture, before stitching, before export) is **logged to a consent-events trace** with fields: `(timestamp, subject_id, consent_decision, latency_ms, error_if_any)`.
2. If consent check **times out** (>500ms) or returns an error, the operation **blocks** (fail-secure); the error is logged with severity `WARN` or `ERROR`.
3. A dashboard/CLI tool queries the trace: `halo-consent-audit --device-id=X --since='1h' --filter=ERRORS` → shows all failures in the past hour.
4. If the same consent-check error repeats more than 3 times in 5 minutes (e.g., consent ledger corruption), the device **raises a severe alert** and disables recording until the error is acknowledged.
5. Tracing is **always-on**, not sampled. Consent decisions are too critical to lose.

**Architectural Note:**
Consent observability is a **cross-cutting concern** that ties into the distributed tracing layer (similar to OpenTelemetry). Every SDK (Python, Flutter, Web Bluetooth) must emit the same consent-event schema. This creates a **consent audit trail** that enables forensic analysis if privacy is ever disputed. The mono-repo gains an `observability/consent-schema/` directory that standardizes these events across all SDKs.

---

## THEME 2: THE SYNESTHETIC FAMILIAR (The Fun One)

### [HIRO-T2-1] As a future maintainer, I want the familiar's state machine and rendering pipeline to be **decoupled**, so that I can swap visual renders without rewriting mood logic.

**Persona:** Future Maintainer (someone adds a new familiar variant in year 2)

**Acceptance Criteria:**
1. The familiar's **mood state** (calm, alert, stressed, growing) is a deterministic pure function: `mood_state(elapsed_time, audio_baseline, movement_intensity, wearer_gaze_duration) → MoodEnum`.
2. The familiar's **visual render** is *completely separate*: a Lua sprite renderer accepts `MoodEnum` and emits display commands to the HUD layer. Mood logic doesn't know about pixels.
3. Two renderers are shipped with the mono-repo: "Ethereal Pet" (original) and "Glitch Companion" (corrupted, per Da5id/Librarian mashup). Both consume the same mood state.
4. Adding a third renderer (e.g., "Bioluminescent Blob") requires only writing a new `render_mood_to_sprites()` function; no changes to mood calculation.
5. **Test:** Mood state is verified via unit tests; renderers are verified via screenshot tests against reference images.

**Architectural Note:**
This is a **clean architectural boundary** between domain logic (what is the wearer feeling?) and presentation (how do we show it?). The familiar's core lives in the host SDK (Python/Flutter), calculating mood from sensor inputs. Rendering is pure Lua on-device, receiving mood updates via BLE. This separation enables community contribution: artists can fork the renderer while the maintainers keep the mood model stable.

---

### [HIRO-T2-2] As an on-call engineer, I want the familiar to degrade gracefully when sensors are unavailable, so that it's resilient to BLE glitches or audio capture failures.

**Persona:** On-Call Engineer (debugging why familiar "froze")

**Acceptance Criteria:**
1. The mood calculation has **explicit fallback modes**: if audio input is unavailable, use IMU-only; if IMU is unavailable, use gaze only; if all sensors fail, familiar enters "idle" state (slow breathing, neutral color).
2. Each fallback is **logged with a severity level**: WARN (1 sensor down), ERROR (2+ sensors down). Dashboard shows which sensors are healthy.
3. When a sensor recovers after a dropout, mood state **smoothly interpolates** back to full-sensor fidelity over 5 seconds (not a sudden jump).
4. **Failure case 1:** BLE connection to host drops mid-session. Familiar on-device defaults to local-only mood inference (using IMU accelerometer only) and continues rendering. When host reconnects, sync catches up.
5. **Failure case 2:** Audio stream stalls (host app crashes). Familiar detects no mood updates for >10 seconds and enters "dormant" state (very slow pulse, desaturated color). Doesn't go black; signals "something's wrong without alarming the wearer."

**Architectural Note:**
The familiar's **data dependencies** must be explicit in the architecture. The host calculates mood from a vector of sensor inputs; the on-device renderer has a graceful degradation hierarchy. When a sensor fails, the system doesn't try to hide it—it **degrades to a lower-fidelity but still-meaningful state**. This is a core reliability pattern: always show *something* rather than failing silent.

---

### [HIRO-T2-3] As a wearer wearing multiple Halos or switching between devices, I want my familiar to **maintain continuity of mood and growth**, so that the familiar doesn't "reset" when I change glasses.

**Persona:** Wearer (someone who owns or borrows multiple Halos)

**Acceptance Criteria:**
1. Familiar mood state is stored in a **device-agnostic profile** encrypted with the wearer's key and synced to their phone or cloud backup (opt-in).
2. When the wearer switches to a different Halo, the new device fetches the profile and **initializes the familiar's mood to match** where it left off (within 5 seconds).
3. Growth/evolution data persists: if the familiar evolved from "egg" to "butterfly" over 30 days on Halo A, it remains a butterfly when the wearer switches to Halo B.
4. The familiar's **personality quirks** (reaction speed, favorite colors) are profile properties, not device-specific. The familiar "remembers you" across devices.
5. **Privacy:** Familiar profile is encrypted end-to-end; the host OS can sync it, but cannot read its contents (device proves ownership via a key the wearer controls).

**Architectural Note:**
This introduces a **sync layer** to the host SDK: familiar state becomes a *roaming profile*. The architecture gains complexity (encryption, device attestation, sync conflict resolution), but the payoff is a familiar that's **portable and persistent**. This is similar to how Brilliant's Noa profiles are designed—the relationship travels with the user, not the device.

---

### [HIRO-T2-4] As a forker building social familiars (group pets), I want the familiar's mood to be a **shared computation across 2+ wearers**, so that we can build multiplayer experiences without polling.

**Persona:** Forker (extending Halo for social use)

**Acceptance Criteria:**
1. Multiple Halos in Bluetooth range can **opt-in to a shared mood space**: each device uploads its sensor data (audio intensity, movement, gaze) to a shared computation layer (can be a phone or central Halo).
2. The shared layer computes a **collective mood**: `collective_mood(alice_audio, bob_audio, alice_immu, bob_imu, ...)` → a single emergent state that reflects the group.
3. Each wearer's Halo displays a shared familiar that responds to the *collective* mood, not individual mood. If Alice is calm but Bob is stressed, the familiar is a "hybrid state" (two faces, blended colors).
4. The shared computation is **cryptographically signed** by all participants. If any wearer disputes the collective mood, they can audit the calculation (zero-knowledge proof: "These inputs produced this output").
5. **Failure case:** One wearer's BLE connection drops. The remaining wearers' collective mood is **recalculated without that wearer** and all devices immediately re-sync. Familiar smoothly transitions to reflect the new group state.

**Architectural Note:**
This is a **distributed mood computation** pattern. The architecture gains a new concern: consensus and synchronization across multiple wearers. Each device must be able to verify the computation without trusting a central authority. This is similar to blockchain consensus but with much tighter latency budgets (consensus in <500ms, not minutes). The mono-repo gains a `distributed-mood/` workspace documenting the protocol.

---

### [HIRO-T2-5] As a on-call engineer, I want familiar rendering to include **performance metrics in debug mode**, so that I can diagnose HUD latency caused by the familiar.

**Persona:** On-Call Engineer (debugging "familiar is janky")

**Acceptance Criteria:**
1. In debug mode, the familiar's Lua renderer logs: `(timestamp, sprite_count, pixel_area, frame_time_ms, battery_cost_estimate_mW)` for every frame.
2. If any single frame exceeds **50ms** (violating the 20 fps baseline for low-power display), the frame is logged with `WARN` and marked in telemetry.
3. A CLI tool aggregates this: `halo-perf --app=familiar --since='1h' --metric=frame_time` → shows frame-time histogram and identifies worst-case renders.
4. The familiar's visual complexity (number of sprites, animation cycles per frame) has **hard limits** baked into the renderer: attempting to render >32 sprites or >256 pixels lit throws an error.
5. **Test:** Synthetic stress test: render familiar at maximum complexity, verify frame times stay <50ms and battery draw <5mW.

**Architectural Note:**
Performance observability is a **HUD-wide concern**, and the familiar must respect Da5id's display budget constraints (no more than 30% pixels lit, <21mW average draw). The renderer exposes a **metrics interface** that the host SDK can query, enabling dashboards and alerting. This prevents future contributors from accidentally making the familiar so complex it drains the battery.

---

## Cross-Theme Observations

### Architectural Patterns Emerged

1. **Consent as Protocol Infrastructure (Theme 1)** — Consent moves from "application middleware" to a **wire-protocol layer concern**. Every message carries consent context; every export is self-proving.

2. **Familiar as Modular State Machine (Theme 2)** — The familiar decouples mood computation (host-side, deterministic) from rendering (device-side, Lua). This enables both **scalability** (new renderers added without core logic changes) and **testability** (unit-test mood separately from visuals).

3. **Failure Modes Are Architecture** — Both themes surface **graceful degradation** as a design requirement. Consent: when a sensor fails, redaction continues; Familiar: when BLE drops, mood inference continues locally. This is not error-handling; it's **architectural resilience**.

4. **Cross-Device Continuity** — Theme 1 (consent history traveling with footage) and Theme 2 (familiar roaming profile) both require **portable state**. The mono-repo gains a sync layer and encryption infrastructure shared by both themes.

5. **Observability as First-Class** — Both themes demand rich telemetry (consent audit trail, performance metrics). The architecture must support **always-on structured logging** without sacrificing device resources.

---

## Summary

**Consent-Aware Memory (Theme 1)** establishes privacy as a **first-class architectural constraint**: cryptographic notarization, peer-to-peer verification, time-based durability boundaries. The system architecture gains three distinct data zones and a consent protocol layer embedded in BLE.

**The Synesthetic Familiar (Theme 2)** demonstrates how the host-peripheral model scales to **embodied, stateful experiences**: mood computation separates from rendering, sensors gracefully degrade, state roams across devices. The architecture gains a distributed mood layer and modular rendering pipeline.

Together, they reveal the halo mono-repo's foundational pattern: **constraints (consent, display budget, battery) become architecture, not middleware.** Future playground projects inherit both the privacy guarantees and the resilience patterns automatically.

---

*Authored by Hiro (Architect), 2026-06-03.*
