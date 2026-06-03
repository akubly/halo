# User Stories: SDK Developer Experience — Themes 1 & 2
**Date:** 2026-06-03  
**Author:** Ng (SDK Engineer)  
**Scope:** Developer-experience stories for Consent-Aware Memory and The Synesthetic Familiar themes  
**Personas:** Playground demo developer, test harness author, Lua-on-device developer

---

## THEME 1: CONSENT-AWARE MEMORY

### [NG-T1-1] As a playground demo developer, I want a single-call API to attach consent metadata to frame buffers, so that I can mark recording sessions without manually managing bystander identity lists.

- **Acceptance criteria:**
  - `frame.camera.attach_consent_context(consenting_ids: List[str])` method exists and is callable from Python/Flutter/JS
  - Consent context persists with every frame event emitted by `on_frame` callbacks
  - Consent metadata is serializable + accessible in `frame.on_tracking_event` callbacks (so host app can check consent before processing)
  - Documentation includes example: "Record a bird-watching session; tag co-watcher IDs as consenting"
  - Passing empty list defaults to "no explicit consent; safe for ephemeral buffer only"

- **SDK note:**
  - Brilliant SDK needs a `ConsentContext` struct (device_id, timestamp, granted_ids: Set, revoked_ids: Set) attached to `CameraFrame` message wire format.
  - Lua hook: `frame.on_frame` callback receives frame + consent_context as arguments; host app sees consent lineage inline.

---

### [NG-T1-2] As a test harness author, I want a Lua-accessible consent revocation simulator so that I can write integration tests that verify redaction happens correctly when a bystander revokes mid-recording.

- **Acceptance criteria:**
  - Lua stdlib function: `frame.consent.simulate_revocation(revoked_id: str, frame_index: int)` 
  - When called during recording, auto-redacts all frames from `frame_index` onward that contain the revoked ID's biometric signature
  - Harness can assert: "frame N-1 contains Bob's face; frame N is blurred" (redaction applied)
  - Works in emulator mode (test-harness Lua environment without real hardware)
  - No dependency on external face-detection service; uses on-device model signatures

- **SDK note:**
  - Python test harness needs `brilliant_sdk.consent.SimulationMode` context manager.
  - Lua needs a built-in `frame.consent.*` namespace with redaction stubs (no actual face processing; just mark regions as "revoked").
  - BLE message format must include "revocation event" opcode so host SDK can handle consent cascade without round-tripping.

---

### [NG-T1-3] As a Lua-on-device developer, I want to emit `consent_needed` events from the on-device event loop when a new face appears, so that the host app can request consent asynchronously without blocking frame processing.

- **Acceptance criteria:**
  - `frame.on_consent_needed(callback)` hook fires when camera detects a new (previously-unseen) face biometric
  - Callback receives: (face_embedding_hash, timestamp, confidence_score)
  - Event is non-blocking; frame capture continues while host app handles consent request
  - Multiple simultaneous `consent_needed` events queue without dropping
  - Face embeddings are hashed (not raw images); bystander can later verify hash via zero-knowledge proof (optional for Phase 1)

- **SDK note:**
  - Lua runtime needs lightweight face-detection offload (TensorFlow Lite model, M55 NPU-eligible).
  - BLE message type: `CONSENT_NEEDED_EVENT` with (embedding_hash, ts, conf_score). No raw image data crosses BLE.
  - SDK must handle queue backpressure: if `consent_needed` events arrive faster than host processes, Lua callback receives "queue_saturation: 0.80" warning and can throttle capture rate.

---

### [NG-T1-4] As a playground demo developer, I want to query a local consent ledger on the Halo device to see which bystanders have granted/revoked consent across the past N hours, so that my app can decide whether to upload footage to cloud storage.

- **Acceptance criteria:**
  - Python/Flutter API: `frame.consent.query_ledger(lookback_hours: int) -> ConsentLedger`
  - `ConsentLedger` includes: (person_id, first_seen_ts, last_consent_state, state_changes: List[(ts, state)])
  - Query completes in <100ms (ledger is on-device, no BLE round-trip)
  - Example: "In past 6 hours, Alice consented 3x, revoked 1x; current state = consented"
  - UI can display: "Safe to upload: footage of Alice (consented), Bob (no consent detected, auto-blur enforced)"
  - Ledger is encrypted on-device; host app reads via SDK, not raw filesystem access

- **SDK note:**
  - Lua: Brilliant SDK needs `frame.storage.get_consent_ledger()` returning a JSON table with ledger entries.
  - SDK must maintain consent ledger as immutable append-log (for audit trail). Query is read-only; no deletion API.
  - Python SDK can wrap this as a filtered query object: `.query_ledger(hours=6).filter_by_state("consented").people()`.

---

### [NG-T1-5] ⚠️ **SDK Doesn't Expose This Yet:** As a playground demo developer, I want the SDK to auto-blur regions of video where a bystander has revoked consent BEFORE I receive the frame in my host app, so that I never accidentally process or store a non-consented face.

- **Acceptance criteria:**
  - `frame.camera.enable_consent_aware_blur(auto_blur: bool)` method exists
  - When enabled, every frame emitted by `on_frame` has revoked-ID regions pre-blurred (24×24 pixel blocks over faces)
  - Host app receives already-blurred frames; no need to re-run face detection
  - Performance: blur pass < 30ms on M55 (does not add noticeable latency)
  - Blur strength is configurable: `blur_strength: 1..4` (pixelation amount)
  - Option to log blur regions: `log_blur_events: bool` for audit trail

- **SDK note:**
  - **Current limitation:** `brilliant-msg` format does not support inline "pre-processed frame with metadata overlay" primitives. 
  - **Required API surface:** New BLE opcode `FRAME_WITH_BLUR_MASK` carrying (frame_buffer, blur_regions: [(x, y, w, h)]).
  - **Lua layer:** On-device blur requires lightweight inference (face bounding box) + pixelation kernel. M55 NPU can handle this; Lua VM needs a `frame.blur.apply_to_faces()` function.
  - **Missing:** No Lua standard library for image manipulation (pixelation, masking). Brilliant SDK must provide `libhalo-blur.lua` or equivalent.

---

## THEME 2: THE SYNESTHETIC FAMILIAR

### [NG-T2-1] As a playground demo developer, I want to drive the familiar's animation state from host-app sensor data (stress level, heart rate proxy, motion intensity), so that I can render the creature's visual mood in sync with the wearer's perceived state.

- **Acceptance criteria:**
  - Python/Flutter host app computes stress metric (0–100 scale: IMU variance + audio spectral centroid)
  - Call `frame.familiar.set_state(mood: str, intensity: float)` where mood ∈ {calm, alert, stressed, excited}
  - Mood change triggers animation callback in Lua: `frame.on_familiar_mood_change(callback)`
  - Familiar sprite responds: idle breathing at low intensity; agitated fraying at high intensity
  - Latency <200ms from host update to visible change on display
  - Multiple rapid mood changes queue without dropping; familiar smoothly interpolates between states

- **SDK note:**
  - SDK needs `FamiliarState` enum (calm, alert, stressed, excited) + intensity float.
  - BLE message: `FAMILIAR_UPDATE` with (state_id, intensity, animation_frame_hint). 
  - Lua runtime needs sprite blending/animation library to morph between mood states.
  - **Gap:** `brilliant-ble` doesn't have a "sprite animation sequencing" primitive. Lua layer needs `frame.sprite.animate(sprite_table, keyframes: List, duration_ms)`.

---

### [NG-T2-2] As a Lua-on-device developer, I want to emit familiar state events from the device's on-device sensor loop (IMU, audio), so that the familiar can respond in real-time to local motion without waiting for host-app latency.

- **Acceptance criteria:**
  - Lua hook: `frame.on_imu_peak(callback)` fires when IMU magnitude exceeds threshold (motion spike)
  - Callback can trigger familiar animation directly: `frame.familiar.pulse_on_motion(intensity)` 
  - No host-app round-trip needed; latency <50ms from motion to familiar response
  - Audio baseline (bone conduction speaker feedback) can also trigger: `frame.on_audio_transient(callback)`
  - Familiar maintains coherent state across on-device events + host updates (no visual glitches from conflicting commands)

- **SDK note:**
  - Lua needs IMU event threshold configuration: `frame.imu.set_peak_threshold(magnitude: float, debounce_ms: int)`.
  - Familiar state machine must be serializable: on-device Lua and host app must share familiar state (or familiar acts as a "read-only display" of host state + occasional on-device overrides).
  - **Missing:** No "IMU event primitive" in Brilliant SDK. Current pattern requires polling; we need interrupt-style `on_peak` callback.

---

### [NG-T2-3] As a playground demo developer, I want to customize the familiar's sprite palette by uploading a Lua-based sprite generator function, so that each demo can define its own creature visual language (particles, fractals, glyphs).

- **Acceptance criteria:**
  - Upload Lua function: `function create_familiar_sprite(mood, intensity) return sprite_table end`
  - Function receives mood + intensity; returns `sprite_table` with animation frames
  - SDK validates sprite table structure (width, height, pixel data format) before accepting
  - Multiple sprite uploads per session allowed; familiar can switch between palettes
  - Example: Bloom-theme familiar (petals) vs. Glitch-theme familiar (RGB corruption)
  - Upload completes in <5s (Lua compile + validation), doesn't block main event loop

- **SDK note:**
  - Brilliant SDK needs Lua function signature validation: `validate_sprite_generator(func) -> bool`.
  - Sprite format: define canonical pixel-buffer structure (256×256 max, 16-bit RGB565 or 8-bit indexed).
  - **Gap:** No "user-defined sprite upload" pipeline in current SDK. Requires new BLE opcode `UPLOAD_SPRITE_FUNCTION` + Lua runtime sandbox for user-provided code.
  - Security: User-provided Lua must run in sandboxed context; validate no access to raw BLE/camera without explicit SDK permission.

---

### [NG-T2-4] As a test harness author, I want to assert that the familiar's animation frame progression matches expected keyframes under specific stress conditions, so that I can validate the synesthetic mapping (stress → visual artifact) is working correctly.

- **Acceptance criteria:**
  - Test harness method: `frame.familiar.capture_animation_sequence(duration_ms, stress_profile: List[(ts, stress_level)]) -> AnimationFrameSequence`
  - Harness injects stress levels over time (e.g., [(0, 10), (500, 50), (1000, 80)] — ramp stress from 10 to 80 over 1s)
  - Captures familiar sprite frames at 30fps; returns list of (frame_idx, sprite_state, timestamp)
  - Assert: "frame 10 is calm; frame 20 is alert; frame 30 is stressed" (visual progression matches stress curve)
  - Harness compares against golden frame sequence; fuzzy match tolerance for rendering variations
  - Works in emulator + simulator; no real device needed

- **SDK note:**
  - Python test harness needs `HaloSimulator.familiar` object with animation capture.
  - SDK emulator must render familiar sprites identically to real device (deterministic frame generation).
  - **Gap:** No "frame capture + assertion" API for familiar. Needs sprite state inspection: `frame.familiar.get_current_frame() -> bytes` + metadata.

---

### [NG-T2-5] ⚠️ **SDK Doesn't Expose This Yet:** As a Lua-on-device developer, I want to receive multi-modal sensor context (camera scene semantics, audio emotion, IMU gesture) in a single fused event, so that the familiar's mood can reflect cross-modal patterns (e.g., "calm audio + agitated motion = curious exploration mode").

- **Acceptance criteria:**
  - Lua hook: `frame.on_sensor_fusion_event(callback)` fires ~10Hz with fused context
  - Callback receives table: `{ camera_semantics: {object_labels}, audio_emotion: {valence, arousal}, imu_gesture: {type, confidence}, ts: uint64 }`
  - No host round-trip; all inference happens on-device (M55 NPU lightweight models)
  - Familiar can map multi-modal patterns to mood: calm audio + upward head nod = `excited`; tense audio + slouch = `stressed`
  - Latency <500ms from sensor to familiar state (acceptable for continuous ambient display)
  - Familiar state reflects cross-modal synthesis, not just single dominant sensor

- **SDK note:**
  - **Current limitation:** Brilliant SDK provides camera frames + audio stream + IMU data as *separate* async streams. No fusion primitive.
  - **Required API surface:** New BLE message type `SENSOR_FUSION_CONTEXT` carrying (camera_semantics_hash, audio_emotion_vector, imu_gesture_id, confidence, ts).
  - **Inference on-device:** Requires TensorFlow Lite models for (a) camera scene understanding, (b) audio emotion classification, (c) IMU gesture recognition. Current Lua layer does not expose these models.
  - **Missing:** No `frame.ml.infer_scene()`, `frame.ml.infer_emotion()`, `frame.ml.classify_gesture()` in Brilliant SDK. Lua layer needs lightweight model wrappers optimized for M55 NPU.
  - **Workaround (Phase 1):** Fuse on host app; send fused state to device. Requires real-time BLE throughput; may not scale to 10Hz without latency.

---

## Cross-Theme Summary

| Story ID | Persona | Theme | SDK Gap | Priority |
|----------|---------|-------|---------|----------|
| NG-T1-1 | Demo Dev | Consent | BLE opcode + Lua hook | HIGH |
| NG-T1-2 | Test Author | Consent | Consent simulation in test harness | HIGH |
| NG-T1-3 | Lua Dev | Consent | Face detection event primitive | HIGH |
| NG-T1-4 | Demo Dev | Consent | Ledger query API | MED |
| NG-T1-5 ⚠️ | Demo Dev | Consent | Pre-blur frame pipeline + image manipulation lib | LOW (Phase 2) |
| NG-T2-1 | Demo Dev | Familiar | Familiar state enum + animation primitive | HIGH |
| NG-T2-2 | Lua Dev | Familiar | IMU event interrupt + familiar state sync | HIGH |
| NG-T2-3 | Demo Dev | Familiar | Sprite upload sandbox + validation | MED |
| NG-T2-4 | Test Author | Familiar | Animation frame capture + assertion | MED |
| NG-T2-5 ⚠️ | Lua Dev | Familiar | Sensor fusion context + on-device ML models | LOW (Phase 2) |

---

## SDK Readiness Assessment

### **Theme 1: Consent-Aware Memory**
- **Viability:** High. Core API needs: consent context metadata (BLE), Lua event hooks, ledger query.
- **Blockers:** None hard; primarily new BLE opcodes + Lua stdlib extensions. Can be shipped incrementally.
- **Recommendation:** Stories NG-T1-1, NG-T1-2, NG-T1-3, NG-T1-4 are Phase 1 (doable in 2–3 weeks). NG-T1-5 (pre-blur) deferred to Phase 2.

### **Theme 2: The Synesthetic Familiar**
- **Viability:** Medium. Sprite rendering pipeline is straightforward; sensor fusion is ambitious.
- **Blockers:** IMU interrupt primitives not yet in SDK. Sensor fusion requires on-device ML (needs M55 NPU TensorFlow Lite integration).
- **Recommendation:** Stories NG-T2-1, NG-T2-2, NG-T2-3, NG-T2-4 are Phase 1 (doable with host-side fusion; familiar respons to mood updates). NG-T2-5 (true on-device multi-modal fusion) deferred to Phase 2 (requires ML infrastructure).

### **Highest-Risk Stories (Requiring New Infrastructure)**
1. NG-T1-5 — Pre-blur requires image processing library in Lua (no precedent in Brilliant SDK).
2. NG-T2-5 — Sensor fusion + on-device ML requires significant M55 integration work.

### **Preferred Build Sequence**
1. **Phase 1a (1 week):** NG-T1-1, NG-T2-1 (consent context + familiar state primitives)
2. **Phase 1b (2 weeks):** NG-T1-2, NG-T1-3, NG-T2-2 (test harness + event hooks)
3. **Phase 1c (1 week):** NG-T1-4, NG-T2-3, NG-T2-4 (ledger + sprite upload + testing)
4. **Phase 2 (4+ weeks):** NG-T1-5, NG-T2-5 (image processing, on-device ML)

---

## Favorite Story

**[NG-T1-3]** — *As a Lua-on-device developer, I want to emit `consent_needed` events from the on-device event loop when a new face appears...*

**Why:** This story is the inflection point between "SDK feature" and "architectural pattern." It's small enough to ship in Week 1, but it forces us to design the consent pipeline as a *system*, not a checklist. The non-blocking event model means the familiar can keep breathing while consent requests flow asynchronously—that's the rhythm of wearable computing done right. And it's the story that makes privacy *tangible to developers*: you see your code deciding whether to record, and you feel the responsibility. That's good SDK design.
