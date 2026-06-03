# User Stories: Themes 1–2 — Edge Cases & Failure Modes
**Date:** 2026-06-03  
**Author:** Juanita (Tester)  
**Scope:** Negative-path user stories for Consent-Aware Memory & The Synesthetic Familiar  

---

## Theme 1: Consent-Aware Memory

### [JUANITA-T1-1] Wearer When Memory Consent Request Times Out
**As a** wearer reviewing an evening's stitched memory,  
**when** a bystander (Jordan) hasn't responded to the consent request after 24 hours,  
**I want** the system to gracefully redact Jordan from the narrative and display the edit history,  
**so that** I don't accidentally store footage of an non-consenting person, and I can see who was redacted and retry consent later.

**Acceptance Criteria:**
- Memory stitching completes by 11 PM even if 1–5 consent requests are pending
- Pending consent faces are auto-blurred with a redaction count ("3 faces pending consent")
- Wearer receives a notification with faces pending + retry-consent shortcuts
- The auto-redacted memory can be synced to cloud (redactions are permanent until consent arrives)
- If consent arrives later (within 7 days), the system logs the change but does NOT re-expose raw footage retroactively

**Test Note:** Emulator: simulate 30-minute consent request window (shorter than real 24h for testing speed), inject missing ACKs, verify auto-redaction + logging. Real device: pair with second Halo, power it off mid-consent-negotiation, verify timeout handling.

---

### [JUANITA-T1-2] Bystander When Consent Revocation Arrives Mid-Recording
**As a** bystander (Sarah) who initially consented to recording,  
**when** I revoke consent halfway through the wearer's 12-hour memory ledger recording,  
**I want** all footage containing my face from revocation-time onward to be redacted immediately on the wearer's device,  
**so that** my consent withdrawal is enforced in real-time, not as a post-hoc cleanup step.

**Acceptance Criteria:**
- Revocation signal reaches wearer's Halo via BLE within 5 seconds (test assumes <10m range)
- Wearer's device redacts Sarah's face in *all* rolling-buffer footage starting from revocation timestamp
- A redaction log entry is created: "Sarah revoked consent at 14:32:10; redacted 47 frames"
- Future stitching does NOT include any footage of Sarah (even if she later re-consents)
- If BLE connection drops during revocation broadcast, the wearer's device re-tries for up to 2 minutes before timing out

**Test Note:** Emulator: test redaction pipeline under various BLE signal strengths (drop every Nth frame during revocation transmission). Real device: two Halos in range, one wearer, one revocation-sender; kill BLE mid-revocation and measure retry behavior.

---

### [JUANITA-T1-3] Wearer When Storage Fills During Memory Stitching
**As a** wearer on a long trip with heavy sensor recording (camera every 10s),  
**when** device storage fills to 95% capacity while Noa is mid-stitching the evening narrative,  
**I want** the system to halt stitching, notify me, and preserve the last coherent narrative checkpoint,  
**so that** I don't end up with a corrupted memory ledger or unexpected data loss.

**Acceptance Criteria:**
- Storage monitoring detects >90% capacity and signals stitching to enter "safe-finish" mode
- Current narrative-in-progress is checkpointed (partial stitching saved with metadata: "stitching halted at 18:45:30")
- Notification explains: "Memory storage 95% full. Last complete narrative: through 18:30. Older footage (pre-12h) can be auto-deleted."
- Wearer can opt-in to auto-delete oldest buffer chunks (hour-by-hour granularity) to continue stitching
- If deletion happens, redaction history is preserved (which bystanders' consents were tied to deleted footage)

**Test Note:** Emulator: artificially constrain storage to 512MB, generate heavy camera stream (1 frame/second), inject storage-full condition mid-stitching, verify checkpoint + recovery. Real device: fill storage via large Lua app upload, trigger stitching under constraint.

---

### [JUANITA-T1-4] Privacy Incident: Wearer When Consent Ledger Syncs to Cloud Without Completing Redactions
**As a** wearer preparing to back up my memory ledger to cloud storage,  
**when** the export process begins before all consent requests have been resolved (some faces still pending),  
**I want** the system to BLOCK the export and show me a list of unresolved consent faces,  
**so that** I never accidentally upload footage of non-consenting bystanders to a cloud service.

**Acceptance Criteria:**
- Export pre-flight check: scan entire memory ledger for "pending consent" markers
- If ANY pending faces exist, export is rejected with a clear list: "Export blocked. 5 faces pending consent. Resolve or redact?"
- Wearer can: (a) wait for consent, (b) force-redact pending faces, or (c) delay export
- If wearer force-redacts, the action is logged: "Forced redaction of 5 faces at 20:15:32 (pending consent truncated)"
- Export proceeds ONLY after all faces are either consented or redacted; metadata includes redaction audit trail

**Test Note:** Unit test: memory export function rejects with pending faces (mock data + test DB). Integration test: real device + emulated cloud backend; trigger export with unresolved consent state; verify rejection + UI clarity. THIS IS A CRITICAL FAILURE MODE.

---

### [JUANITA-T1-5] Comedy of Errors: Wearer When BLE Loop Creates Cascading Consent Requests
**As a** wearer at a crowded meetup with 8 other Halo wearers,  
**when** each wearer's device detects the others and automatically broadcasts "send me consent for mutual recording," creating a cascade of cross-device consent negotiations,  
**I want** the system to detect this cascade and enter "batch consent mode"—aggregating requests instead of bombing my display,  
**so that** I don't end up with 50 simultaneous consent notifications paralyzing my interaction.

**Acceptance Criteria:**
- When >5 simultaneous consent requests arrive within 10 seconds, system coalesces them into a single "Group Consent Batch" notification
- Batch UI shows: "8 wearers detected. 5 requesting consent to record. Approve all / Review individually / Deny all"
- If approved, all 5 receive consent confirmation within 2 seconds
- If any network lag occurs during batch approval, individual confirmations are ACK'd separately (no cascading failures)
- System logs batch event: "Batch consent: 5 approved, 2 auto-denied (signal loss), 1 timeout"

**Test Note:** Emulator: spawn 8 virtual Halo devices, trigger simultaneous consent broadcasts, measure batch coalescing latency and UI responsiveness. Chaos test: drop every 3rd BLE packet during batch negotiation; verify individual ACK retries work (no cascade collapse).

---

## Theme 2: The Synesthetic Familiar

### [JUANITA-T2-1] Wearer When Familiar Animation Runs Faster Than Display Refresh
**As a** wearer wearing Halo during an intense workout (high motion, IMU data streaming at 100 Hz),  
**when** the synesthetic familiar is attempting to render emotional state updates (stress→calm transition) but Halo's display can only refresh at 25 fps,  
**I want** the familiar animation to gracefully degrade (skip frames, not stutter or freeze),  
**so that** my emotional companion feels smooth even under load, not like a broken robot.

**Acceptance Criteria:**
- Display refresh rate is capped at 25 fps (per decisions.md); familiar's animation loop respects this
- If emotion-state changes faster than 25 fps (e.g., user's stress spikes in <40ms), the familiar skips intermediate frames rather than buffering
- Familiar motion grammar remains legible even with dropped frames (e.g., a calm→stressed transition should read as "shift to anxious" even if 50% of in-between frames are skipped)
- Lua callback queue for familiar updates is bounded at 10 pending animations; older updates are discarded with a logging event
- User sees zero flicker or stutter; the animation degrades gracefully to a lower frame-rate motion, not a glitchy pause

**Test Note:** Emulator: IMU injection at 100 Hz (sleep 10ms between samples); render emotion-state updates as fast as possible; measure actual FPS vs. intended; verify no dropped frame artifacts. Real device: high-motion workout; measure familiar animation smoothness with frame-counter telemetry.

---

### [JUANITA-T2-2] Familiar When Cloud Model Inference Fails or Latency Explodes
**As a** wearer in an area with poor connectivity (rural location, tunnels, airplane mode activated mid-flight),  
**when** the synesthetic familiar is supposed to infer emotional state via cloud LLM (e.g., Gemini Live processing audio tone),  
**I want** the familiar to enter "offline mode" and render cached emotional inferences (from recent history or a default baseline),  
**so that** my companion doesn't freeze or disappear the moment connectivity drops.

**Acceptance Criteria:**
- If cloud inference request times out (>3 seconds) or returns 5xx error, familiar switches to offline-inference mode
- Offline mode uses a simple local heuristic: IMU motion → stress estimate (high acceleration = higher stress), mic energy → engagement level
- Familiar animation continues using local estimates; motion grammar remains consistent (same synesthetic metaphors)
- Once connectivity resumes, device re-syncs with cloud; if cloud inference differs from local estimate, the transition is smooth (familiar *shifts* emotion state over 2–3 seconds, not abruptly)
- Telemetry logs: "Cloud inference timeout × 3; entered offline mode. Resumed sync after 45 seconds."

**Test Note:** Emulator: mock cloud API to return 503 on-demand; trigger familiar update; verify offline fallback + logging. Real device: enable airplane mode mid-session; measure familiar behavior continuity. Integration test: test cloud-to-local sync transition under realistic latency (add 500ms+ delay).

---

### [JUANITA-T2-3] Wearer When Familiar Sprite Consumes All Available Lua Heap Memory
**As a** wearer running a long meditation session with the familiar rendering complex animated stress-reduction patterns,  
**when** the familiar's memory usage gradually crescendos due to animation state accumulation (history buffer never trimmed),  
**I want** the system to detect heap usage at >80% and gracefully reduce familiar complexity (fewer animation frames, lower resolution),  
**so that** the device doesn't OOM-crash mid-session.

**Acceptance Criteria:**
- Lua heap usage is monitored; at 80% threshold, familiar enters "low-power animation mode"
- Low-power mode: reduce animation frame count by 50%, use fewer color gradients, simplify sprite palette
- Wearer receives a subtle notification: "Familiar entering calm mode (low power)"
- At 95% heap, familiar freezes in a safe state (idle pose) and logs the event; app is halted gracefully (not crashed)
- After app exit, heap is freed; next session familiar is fresh (no persistent corruption)

**Test Note:** Emulator: use Lua profiling to measure heap growth over time; set artificial heap limit (e.g., 256KB), run long session, trigger stress patterns continuously; measure reduction points + verify safe state. Real device: same test with actual Halo's available heap.

---

### [JUANITA-T2-4] Bystander When Familiar Inadvertently Broadcasts Wearer's Emotional State
**As a** bystander standing near a wearer with the synesthetic familiar active,  
**when** the familiar's visual representation (color, motion grammar, animation intensity) is *visible to me* through the wearer's display or external LED indicators,  
**I want** the system to ensure the familiar does NOT inadvertently reveal sensitive emotional data (e.g., rapid color shifts that scream "anxiety attack") to nearby people,  
**so that** the wearer's private emotional state remains theirs alone.

**Acceptance Criteria:**
- Synesthetic familiar rendering uses only peripheral-vision animations (orbit, pulse) that are difficult for bystanders to interpret from a distance
- If the wearer has marked their familiar as "private" (in settings), all external LED indicators are disabled or show only a neutral heartbeat (no color/mood encoding)
- Emotional state inferences (from cloud or local) are NEVER written to shared logs or exposed via Bluetooth broadcast
- Display brightness during familiar animation is capped at 50% indoors, 70% outdoors—preventing bystander-readable emotional patterns
- Privacy audit: check that familiar telemetry logs NEVER include raw emotion scores sent off-device

**Test Note:** Unit test: verify no telemetry exfiltration of emotion data. Integration test: two Halos in range; one displaying familiar; second wearer's packet sniffer confirms no emotion metadata in BLE advertisements. Real device: visual inspection of wearer's display from bystander's vantage point (difficult to read specific emotions).

---

### [JUANITA-T2-5] Comedy of Errors: Familiar's Emotional Inference Wildly Misinterprets Wearer Intent
**As a** wearer who just finished a tense phone call (elevated tone, rapid speech) but is now actually calm,  
**when** the synesthetic familiar's emotion model lags behind reality and keeps rendering "stressed" animations for 2 minutes after I've relaxed,  
**I want** the system to provide a quick-reset gesture (e.g., double-tap) so I can tell my familiar "I'm actually fine now",  
**so that** I don't spend two minutes watching my companion freak out while I'm sitting peacefully.

**Acceptance Criteria:**
- Quick-reset gesture (double-tap + hold) immediately sets familiar to "calm baseline" state
- The gesture override is logged locally: "Manual reset: user corrected emotion state from 'stressed' to 'calm' at 14:32"
- Over time, if resets happen frequently after specific triggers (e.g., always after phone calls), the system should *learn* to not transition to stressed-mode after phone call audio
- Familiar responds to reset within 500ms (animation smoothly transitions to calm pose)
- Reset does NOT send data to cloud; learning loop is on-device only (privacy-preserving feedback)

**Test Note:** Emulator: simulate phone-call audio (high energy), trigger stress inference; apply double-tap reset; verify animation transition + logging. Real device: user testing with actual phone calls; measure reset responsiveness and verify inference learning over repeated scenarios (5+ phone-call cycles).

---

## Summary: Failure Modes Identified

| Story | Failure Mode | Severity | Why It Matters |
|-------|--------------|----------|-----------------|
| T1-1  | Auto-redaction on consent timeout | MEDIUM | Bystander privacy at risk if stitching completes without explicit redaction |
| T1-2  | Revocation enforcement during live recording | CRITICAL | Real-time privacy is the selling point of consent-aware memory |
| T1-3  | Storage exhaustion during stitching | HIGH | Data loss + corrupted memory narrative |
| T1-4  | Cloud export without consent completion | **CRITICAL PRIVACY INCIDENT** | Uploading non-consented footage is a GDPR/legal liability |
| T1-5  | Consent request cascade in crowded environments | MEDIUM | UX paralysis + consent fatigue |
| T2-1  | Display refresh lag with fast emotion updates | LOW | Familiar feels janky, not a data loss issue |
| T2-2  | Model inference failure during offline mode | MEDIUM | Familiar disappears, breaks the companion illusion |
| T2-3  | Lua heap exhaustion during long sessions | HIGH | App crash mid-meditation, loss of session state |
| T2-4  | Emotional state leakage to bystanders | CRITICAL | Privacy violation + social awkwardness |
| T2-5  | Emotion inference lag creates false negative signal | LOW | UX annoyance, not a correctness issue |

---

**Next Steps:**
1. **T1-4 (Cloud Export Privacy)** — Priority 0. Implement pre-flight consent check before any export. Add integration tests with real device + emulated cloud backend.
2. **T1-2 (Revocation Enforcement)** — Priority 1. Test real BLE revocation flow; measure redaction latency. Ensure <5 second enforcement SLA.
3. **T2-4 (Emotional State Leakage)** — Priority 1. Audit all telemetry paths; verify no emotion data in BLE advertisements. Visual privacy inspection with bystander + device side-by-side.
4. **T1-3, T2-3 (Resource Exhaustion)** — Priority 2. Heap + storage monitoring tests under sustained load.
5. **T2-1, T2-5 (UX Degradation)** — Priority 3. Refinement after core privacy + correctness tests pass.

