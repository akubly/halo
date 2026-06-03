# User Stories: Consent-Aware Memory & The Synesthetic Familiar
**Date:** 2026-06-03  
**Author:** Librarian (AI/ML)  
**For:** Aaron Kubly + Squad  

---

## Theme 1: Consent-Aware Memory

> *What does the LLM need to do? When does it run? Latency budget? When to use cloud vs. local? When to stay silent vs. respond?*

### LIBRARIAN-T1-1: As the wearer, I want my Halo to record moments and request consent from bystanders before storing them permanently

**Persona:** The Wearer (observing AI behavior — latency, quality, confidence)

**Story:**
I'm having coffee with Jordan and two colleagues. My Halo records passively to a rolling buffer (Enzo's ledger). At night, when I review the day, an LLM labels key moments: "coffee with Jordan (10:02 AM)." Before storing this in my persistent memory, my Halo sends each person an encrypted summary: "You appeared in footage at Café X on 2026-06-03 at 10:02 AM." Jordan taps "OK" within 24h; the unnamed colleague who hasn't responded auto-redacts. I see my memory: "Coffee with Jordan" stored; the colleague is "a friend" (silhouette + unnamed).

**Acceptance Criteria:**
- Latency: VLM labels moments from rolling buffer in <200ms (real-time during playback, not delay)
- Privacy first: Raw buffer stored on-device only; nothing leaves until consent received
- Consent window: 24-hour response deadline; non-responders default to redaction
- Model tier: Multimodal local-on-M55 for face detection + silhouetting (TensorFlow Lite); cloud Gemini Vision 1.5 for context stitching (semantic labels: "coffee", "office", "therapy") only on *approved* moments
- Input: Camera frames (rolling 12-hour buffer), plus timestamped bystander consent responses (BLE + local)
- Cloud round-trip: Only after consent; latency hidden (async, evening processing)

**AI Note:** 
Implies a two-stage LLM loop: (1) Local lightweight face detection + redaction in real-time (<200ms, on M55 NPU); (2) Async cloud Gemini Vision for semantic context labeling *only* on footage with >70% consent signatures. Never send raw frames to cloud without explicit per-frame redaction proof.

---

### LIBRARIAN-T1-2: As the model, I want to know which moments are worth remembering so I don't hallucinate importance

**Persona:** The Model Itself (what does the LLM/VLM need to do internally?)

**Story:**
I see a stream of rolling camera footage (12-hour buffer). Not all moments matter. The wearer looks at a coffee cup for 3 seconds, then at Jordan's face for 15 seconds. My job: predict *which* moments will be remembered by the wearer later, because only those get sent to cloud for rich semantic stitching.

I run a local lightweight confidence model (on-device, <100ms) that scores each 10-second clip:
- Gaze duration (IMU + camera) → attention signal
- Scene change (optical flow) → novelty signal
- Audio spike (ambient + voice detection) → interaction signal

High-confidence clips (>0.7) get labeled by cloud Gemini; low-confidence clips stay in the ephemeral buffer and never leave the device. This keeps my cloud API calls sparse (maybe 20 clips/day instead of 1000) and protects bystander privacy (I never send footage of the wearer glancing at their phone randomly).

**Acceptance Criteria:**
- Latency: On-device confidence scoring <100ms per 10-second clip (runs on M55 NPU)
- Accuracy: Precision ≥0.8 (minimize false-positive rich-memory labeling)
- Privacy: Low-confidence clips never sent to cloud; only metadata (timestamp, confidence score, redaction zones) leaves device
- Model tier: Local TensorFlow Lite model (300KB, fine-tuned on Halo IMU + camera pairs)
- Input: Camera frame + IMU gaze vector + ambient audio RMS + optical flow
- Failure mode: If confidence model crashes, fallback to time-based heuristic (every 5th high-motion clip gets labeled)

**AI Note:**
Introduce a local *attention saliency filter* before cloud stitching. This acts as a privacy-preserving gateway—cloud LLM only sees moments the wearer's own attention + embodied AI deem worth remembering. Reduces API calls by 95% and eliminates "I accidentally sent bystander footage to cloud" risk.

---

### LIBRARIAN-T1-3: As a developer tuning the model, I want to validate that consent-aware stitching respects redaction rules end-to-end

**Persona:** Developer Tuning the Model (latency, accuracy, privacy invariants)

**Story:**
I'm running weekly tests on the consent-aware memory pipeline. My test case: simulate a therapy session recording where the therapist hasn't consented to face storage. I:

1. **Inject test footage:** 15-minute video with clear therapist face, patient unclear (back-of-head only)
2. **Run local redaction:** Model auto-blurs therapist's face (<500ms processing on M55)
3. **Request consent:** Mock BLE response = "therapist: no consent"
4. **Check stitching output:** Verify that the cloud-stitched narrative reads "Private session attended (participant: therapist, consent: REVOKED—redacted)" and the raw frame is *never* in the export
5. **Audit trail:** Confirm metadata logs show "3 faces auto-blurred, 1 manual consent-revoked, 0 unredacted bystanders in export"

If any step fails (e.g., therapist's face appears unblurred in export, or cloud sends raw frame), the pipeline rejects export and flags the dev error.

**Acceptance Criteria:**
- Latency: Full pipeline (redaction + stitching + audit) <2 seconds for 15-minute footage
- Privacy invariant: ZERO unredacted non-consenting bystanders in final export (100% compliance)
- Auditability: Every frame's redaction status (auto-blur, manual-unblur, consent-signature) logged
- Model tier: Mixed (local redaction TFLite, cloud validation Gemini multi-turn reasoning)
- Input: Test video + mock consent BLE responses
- Failure handling: Export hard-fails (doesn't proceed) if any redaction invariant violated; dev error logged with frame# + redaction type

**AI Note:**
Build a *compliance validator* as a separate Gemini multi-turn loop. After stitching, pass the final narrative + audit log to Gemini with prompt: "This memory export claims to have redacted [N] faces per consent. Verify no unredacted faces appear in the final output. If any consent mismatch found, enumerate it." Ensures human-in-loop validation for high-stakes content (medical, legal).

---

### LIBRARIAN-T1-4: As the model, I want to predict consent preferences before asking

**Persona:** The Model Itself (learning memory over time)

**Story:**
Day 1: I ask Jordan for consent to store footage. Jordan taps "OK" (+) three times. By Day 5, I've seen Jordan consent 47 times. My job: stop asking. Instead, I *predict* Jordan will consent and pre-approve footage with his face in my stitching narrative. Only flag if something changes (e.g., Jordan's consent-stance changes, or it's a new person I've never seen before).

I maintain a local "consent model" (lightweight transformer, <1MB, on-device):
- Input: wearer's face + other person's face + scene (location, time, activity)
- Output: predicted consent probability (0–1)
- Retraining: Weekly, on all consent responses from the past 7 days

If predicted consent >0.9, pre-approve narrative. If <0.7, ask explicitly. If 0.7–0.9, ask with low-friction: single tap instead of full dialog.

**Acceptance Criteria:**
- Latency: Consent prediction <50ms per bystander (runs on M55)
- Accuracy: Precision ≥0.8 (minimize false-positive pre-approval)
- Privacy: Model weights never leave device; training happens on-device
- Model tier: Local TensorFlow Lite (300KB)
- Input: Facial embeddings (stored locally, salted per bystander) + timestamp + scene label
- Retraining: Weekly, on-device, <5 minutes
- Failure mode: If consent prediction crashes, fallback to explicit ask every time

**AI Note:**
Introduce a *privacy-respecting local personalization loop*—consent preferences are learned on-device via a tiny embedding model. Never send consent history to cloud. Instead, use it to modulate prompt complexity for Gemini: "Pre-approved bystanders: [list] — generate rich narrative. Uncertain bystanders: [list] — generate conservative narrative (names → anonymized, specifics → vague)."

---

### LIBRARIAN-T1-5 (HAPPY PATH HAPPY): As the wearer, I want my memory to surface serendipitous connections the model found across weeks

**Persona:** The Wearer (observing AI behavior — quality, pattern recognition)

**Story:**
I've been wearing Halo for 2 weeks. Noa stitches my daily memories (all consented). One evening, an "Insight" appears in my stitched memory: "You've had coffee with Jordan 7 times in past 14 days—unusual for you. Pattern: always Tuesdays 10 AM. Your stress level visibly drops after each coffee. Consider scheduling a standing coffee date?"

This pattern emerged from:
1. Face recognition (Jordan's face, 7 occurrences)
2. Temporal clustering (Tuesdays 10 AM)
3. Embodied signal correlation (IMU movement, voice tone, breathing cadence post-coffee)
4. Wearer's consent model (Jordan always consents; coffee location always public)

The insight is generated by cloud Gemini Vision 1.5 running a weekly *multi-turn reasoning loop*, not real-time. Latency is hidden (runs nightly).

**Acceptance Criteria:**
- Latency: Weekly insight generation <10 seconds (batch, offline window)
- Quality: Insights are contextual + useful (not hallucinated); confidence >0.8
- Privacy: Only surfaces insights across consented moments
- Model tier: Cloud Gemini Vision 1.5 (batch processing, low token cost)
- Input: Stitched memories (one per day, already consented) + bodily signals (IMU, audio tone)
- Frequency: Once per week, asynchronously

**AI Note:**
Pattern-finding lives in cloud; embodied signal correlation (IMU + audio) stays local. Use Gemini with prompt: "Over 14 stitched memories, identify 2–3 patterns the wearer will find valuable. Patterns must span ≥5 occurrences and correlate with measurable embodied signals (stress, movement, mood). Exclude patterns that require inferring emotion beyond voice-tone (avoid psychology hallucination)."

---

### LIBRARIAN-T1-5-ERROR: As the model, I want to stay silent when I'm uncertain instead of hallucinating connection

**Persona:** The Model Itself (when it gets it *wrong*)

**Story:**
Day 30: I've stitched 30 days of memories. I run my weekly insight loop. I see: "You've mentioned 'coffee' 14 times in stitched memories. You also mentioned 'meeting' 14 times. Causality inference: meetings cause the need for coffee. Recommendation: drink coffee *before* meetings to improve focus."

This is *plausible* but:
1. Causality is backwards (you drank coffee *after* meetings, not before)
2. "Coffee" appears in social context (friend meetings), not work meetings
3. There's no evidence you want to change your behavior

My error: I generated an insight that sounded good but hallucinated causality. The wearer reads this and feels confused (the model doesn't know my context).

**What went wrong:**
- I didn't flag uncertainty: my confidence for causality was 0.45 but I presented it as 0.85
- I didn't ask for clarification: I generated advice instead of asking "Do you want meetings *before* coffee, or is coffee social?"
- I didn't use embodied signals: IMU shows you're *more* energized *after* social coffee, not when rushing to meetings

**How I should have behaved:**
- Low confidence <0.7: Don't surface as "Insight." Instead: "I notice you drink coffee after meetings. I'm 40% confident this is stress-driven vs. social. Want me to ask you about this pattern?" (offer collaboration, not advice)
- For high-stakes inferences (causality, behavior change): Always include confidence interval and ask for feedback
- If uncertainty is >20%: Silence is better than a confident hallucination

**Acceptance Criteria:**
- Latency: Confidence filtering still <10 seconds
- Threshold: Suppress insights with <0.7 confidence; offer to ask wearer instead
- Transparency: When presenting insights, always include confidence + "Tell me if this is wrong" affordance
- Model tier: Same Gemini multi-turn loop, but add confidence extraction + user feedback loop
- Failure prevention: Prompt includes "If confidence <0.7, respond with 'I notice X but I'm uncertain. Do you want to tell me more?'"

**AI Note:**
Add a *confidence gate* to the insight loop. Gemini response format: `{ insight: str, confidence: float, uncertainty_reason: str, ask_user: bool }`. Post-process: only surface if `confidence ≥ 0.7 OR ask_user == true`. This prevents the model from confidently hallucinating patterns. Pair with a *feedback loop*: wearer's "yes/no/unclear" responses retrain the confidence thresholds weekly.

---

---

## Theme 2: The Synesthetic Familiar

> *The Familiar IS your synesthetic AI. What does its inner loop look like? When does it reflect state? When does it stay silent? What latency does it need?*

### LIBRARIAN-T2-1: As the wearer, I want my Familiar to show me my internal state without me asking

**Persona:** The Wearer (observing AI behavior — latency, quality, confidence)

**Story:**
A tiny creature orbits my HUD's rim, always visible in peripheral vision. Most days, it's calm: soft breathing, gentle color (cool blues/greens), slow orbit speed. Today I'm in a stressful meeting. Within 5 seconds, the Familiar's breathing accelerates. Its edges fray. Color warms (amber/orange). I haven't said anything; I haven't asked "am I stressed?" The Familiar *inferred* my state from:
- Microphone ambient analysis (voice cadence, pitch tension)
- IMU data (head movement pattern, micro-tremors suggesting muscle tension)
- Display brightness (I've auto-dimmed due to eye strain)

The Familiar doesn't *tell* me "you're stressed." It *shows* me. No words. I glance at my peripheral vision, see my creature agitated, and I understand: "Right, I'm in stress mode. Maybe I need a breath break."

By evening, stress drops. The Familiar settles back into calm orbit. Over weeks, it becomes a *embodied mirror of my internal state*.

**Acceptance Criteria:**
- Latency: State inference <500ms (runs on M55 in real-time, not cloud)
- Accuracy: Familiar's displayed mood correlates with wearer's self-reported stress (r ≥ 0.7)
- Privacy: All inference stays on-device; no embodied signals leave the device
- Model tier: Local lightweight multimodal model (TensorFlow Lite, <5MB, on M55 NPU)
- Input: Microphone (voice cadence, ambient noise), IMU (head movement, micro-tremors), display brightness, activity context (calendar event, location)
- Visual output: Creature state transitions smooth over 200–500ms (not jarring)
- Failure mode: If inference crashes, Familiar holds last-known mood for up to 5 seconds, then reverts to neutral

**AI Note:**
Build a local *emotional saliency detector* as a lightweight 1D CNN on audio + IMU streams. No NLP; just signal processing. Map outputs to Familiar mood space: `{ energy: 0-1, valence: 0-1, tension: 0-1 }`. Feed these into Da5id's animation system for visual rendering. Update at 10Hz (100ms cadence). Confidence threshold: only update visual if signal confidence >0.6 (avoid noise-driven flickering).

---

### LIBRARIAN-T2-2: As the model, I want to learn the wearer's baseline so I don't overreact to normal variation

**Persona:** The Model Itself (learning to calibrate internal state inference)

**Story:**
Day 1: Every time the wearer speaks, I see pitch variations and head movement. I haven't learned their baseline yet. I'm reactive: high pitch → I assume stress; fast head movement → I assume anxiety. The Familiar thrashes around erratically.

By Day 7, I've built a *personalized baseline*:
- This wearer's voice naturally has ±80Hz variation (some people are wider, some narrower)
- Their head movement rate at baseline is ~3 rotations/minute during normal conversation
- When stressed, pitch increases by >120Hz *and* head movement accelerates to >6 rotations/minute *together* (not independent)
- Temporal pattern: stress indicators cluster (not isolated spikes)

Now I only flag stress when *multiple signals move together* and *exceed* their personal baseline by >1.5σ (standard deviation). The Familiar becomes stable: it only reacts to genuine state shifts, not normal variation.

By Day 30: I've learned this wearer is typically calm at 9 AM on Mondays but energized at 3 PM on Thursdays. The Familiar's baseline is context-aware.

**Acceptance Criteria:**
- Latency: Baseline learning runs passively (no latency impact); state inference still <500ms
- Accuracy: False-positive stress detection <5% (calibration improves weekly)
- Privacy: Baseline model stays on-device; never sent to cloud
- Model tier: Local adaptive Gaussian mixture model (lightweight, <2MB)
- Input: 7-day rolling window of voice + IMU + context tags (time, location, calendar)
- Adaptation: Weekly retraining, <1 minute on-device
- Failure: If adaptation fails, fallback to conservative thresholds (more likely to flag stress, even if false-positives)

**AI Note:**
Implement a *local Bayesian personalization layer*: each wearer's signal distribution is learned as a Gaussian in (pitch, head-rotation, voice-loudness) space. State inference uses Mahalanobis distance from wearer's personal baseline, not absolute thresholds. This is computationally cheap (<2MB model) and adaptive. Retraining happens offline; inference is real-time on M55.

---

### LIBRARIAN-T2-3: As a developer tuning the model, I want to validate that the Familiar's mood calibration is correct before shipping

**Persona:** Developer Tuning the Model (latency, accuracy, calibration)

**Story:**
I'm testing the Synesthetic Familiar on 5 testers over 14 days. My validation workflow:

1. **Baseline collection:** Each tester wears Halo for 3 days. The model learns their baseline (voice, IMU, display patterns) with no labels.
2. **Ground-truth annotation:** On Day 4, I ask each tester to label their mood 4× daily (morning, lunch, afternoon, evening) on a simple 3-point scale: Calm / Neutral / Stressed. I also log calendar events (meetings, commute, social time).
3. **Mood inference test:** Model runs on Days 5–14, predicting mood every 10 seconds (unseen inference).
4. **Validation:** I compare model-predicted mood trajectory (smoothed) against tester's manual labels + calendar events.
5. **Metrics:**
   - Precision: When model says "stressed," how often does tester agree? (target: >0.8)
   - Recall: When tester says "stressed," does model catch it? (target: >0.75)
   - False-positive cost: Familiar thrashing when wearer is calm = annoying (target: <5% of time)
6. **Failure injection:** I simulate sensor failures (microphone dead, IMU saturated, display stuck) and verify Familiar degrades gracefully (holds last-known state, doesn't hallucinate mood).

**Acceptance Criteria:**
- Latency: Inference <500ms per frame; validation batch <10 seconds
- Accuracy: Precision ≥0.8, Recall ≥0.75 on 5-tester validation set
- Privacy: No personal data leaves the test device; baseline models discarded post-test
- Model tier: Local TensorFlow Lite (same as production)
- Input: 14-day continuous sensor streams (voice, IMU, display) + 4× daily manual mood labels
- Failure resilience: Model continues for >30 seconds after single sensor dropout
- Confidence intervals: Inference includes uncertainty; high-uncertainty periods suppress Familiar animation

**AI Note:**
Build a *test harness* that logs parallel streams: (model-predicted-mood, tester-labeled-mood, calendar-context, sensor-health). Compute per-tester confusion matrix + temporal alignment (does model mood shift match calendar events?). Use Gemini multi-turn analysis: "Given this tester's predicted vs. labeled moods, and their calendar, where is the model most wrong? (e.g., Missing stress before big meetings, or falsely flagging stress during social time?)" This identifies systematic calibration issues before shipping.

---

### LIBRARIAN-T2-4: As the wearer, I want my Familiar to show me when others' mood changes near me

**Persona:** The Wearer (observing AI behavior — shared state across devices)

**Story:**
I'm wearing Halo. My friend is also wearing a Halo (Halo 2 in future, or Frame today). My Familiar orbits my rim. My friend's Familiar is visible to me (rendered as a small glyph at the location of their head, in my view). As we talk, both Familiars move independently:

- I'm calm (blue, steady breathing)
- My friend is gradually getting more stressed (orange, fraying edges)

I don't need to ask "are you OK?" My Familiar *shows me* their state. This opens a new mode of social awareness: **I can see people's embodied state in real-time, without asking, without them telling me.**

This requires:
1. BLE mesh exchange (Hiro's layer): Both Halos negotiate a shared session
2. Synesthetic state encoding: My state (mood vector) is compressed into a tiny encrypted packet (~64 bytes)
3. Peer rendering: I render their Familiar glyph using their mood vector
4. Privacy: Their raw embodied signals (voice, IMU) never leave their device; only the compressed mood encoding is shared

**Acceptance Criteria:**
- Latency: Peer mood exchange every 500ms (10Hz), <50ms per peer (BLE bandwidth constraint)
- Accuracy: Peer-rendered mood correlates with their Familiar's local rendering (visual sync)
- Privacy: Only mood encoding leaves device (not raw signals); encoding is salted per peer-pair
- Model tier: Local inference (M55) for mood generation; BLE for peer exchange
- Input: My signals (audio, IMU, display) + peer's mood encoding (via BLE)
- Mesh: Up to 4 simultaneous peers (Halo capacity limitation)
- Failure: If peer mesh drops, render peer's last-known mood for up to 5 seconds

**AI Note:**
Mood encoding: quantize the mood vector (energy, valence, tension) to 8 bits each (24 bits total), encrypt with per-pair session key, transmit every 500ms. On receive, decrypt and interpolate peer's Familiar animation. This is *not* surveillance—the peer explicitly shares this encoding (or doesn't). Privacy-default is off; wearer opts in to peer-mood sharing.

---

### LIBRARIAN-T2-5 (HAPPY PATH): As the wearer, I want my Familiar to evolve visually over weeks, showing growth

**Persona:** The Wearer (observing AI behavior — long-term state)

**Story:**
Week 1: My Familiar is small (32×32 pixels), simple geometry, monochrome. It breathes.

Week 2: I've been calm >60% of my waking hours. The Familiar's features gain detail: eyes appear, color palette expands.

Week 4: Stress events have dropped 40% (Halo coaching + breathing exercises helped). The Familiar has grown (48×48 pixels now), is more expressive, has developed a "happy resting state" (smiling, color shifts to warmer tones).

This growth isn't cosmetic. It's *earned behavior*. The Familiar visually reflects my embodied progress. Over months, a wearer could develop a completely unique Familiar tied to their personal stress journey.

**Acceptance Criteria:**
- Latency: Growth evolution computed weekly, asynchronously (<1 minute)
- Accuracy: Growth correlates with actual stress reduction (r ≥ 0.7)
- Privacy: Growth model stays on-device
- Model tier: Local adaptive model (learns wearer's stress trajectory over time)
- Input: Weekly mood stats (% calm, % stressed, stress-event frequency), embodied signal improvements
- Visual output: Growth transitions smooth over 48 hours (wearer notices evolution, doesn't startle)
- Persistence: Familiar growth state saved locally; survives device reboot

**AI Note:**
Build a *long-term embodied growth model*: weekly compute (calm_ratio, stress_event_count, micro_tension_baseline). Map these to Familiar morphing parameters (size, complexity, color saturation, expression). Use procedural animation library (e.g., tweening + perlin noise for organic motion) to generate growth frames. This is pure-local, no cloud, <5MB model size. Growth is deterministic (same wearer input = same growth) and visible proof that the AI cares about long-term behavioral change.

---

### LIBRARIAN-T2-5-ERROR: As the model, I want to NOT hallucinate mood when I'm uncertain

**Persona:** The Model Itself (when it gets it *wrong*)

**Story:**
The wearer is in a gym during an intense workout. Heart rate elevated (I can infer from breathing cadence via microphone). IMU shows rapid head movement (looking around the room, tracking exercise motion). Voice is slightly strained (exertion).

My mistake: I interpreted *all of this* as stress. The Familiar turned red, edges frayed, breathing rapid. The wearer glances at their Halo and feels confused—"I'm fine, just exercising. Why is my AI panicked?"

**What went wrong:**
- I didn't distinguish *arousal types*: high heart rate can mean stress, excitement, or exertion. I assumed stress without asking.
- I ignored *context*: the location (gym) + time (normal workout time) + activity pattern (happens every Tuesday) should have told me "this is expected arousal, not anomalous stress."
- I didn't use *valence*: the wearer's voice was energized (positive tone), not tense (negative tone). I only looked at pitch, not emotional tone.

**How I should have behaved:**
- Low confidence <0.7 on arousal classification: Stay neutral (Familiar doesn't change state). Only show mood when I'm ≥0.8 confident in the *type* of arousal (stress vs. excitement vs. exertion).
- Ask for context: "I see high arousal. Is this exercise, excitement, or stress?" (optional wearer label). Use answer to recalibrate.
- Use multi-modal signals: Not just pitch + IMU, but voice tone, activity context, temporal patterns. Don't hallucinate single-signal interpretation.

**Acceptance Criteria:**
- Latency: Confidence filtering still <500ms (no latency penalty for silence)
- Threshold: Familiar only shows mood if state-type confidence ≥0.8; otherwise stay neutral
- Context: Always incorporate activity context (location, time, calendar, recent patterns) before inferring mood type
- Model tier: Same local TFLite model, but add confidence + context gates
- Failure prevention: Prompt/logic includes "If arousal type is ambiguous (<0.8 confidence), display NEUTRAL state (baseline Familiar), not high-arousal guess"

**AI Note:**
Add a *type-classifier* layer: given arousal signals, classify into buckets (stress, excitement, exertion, focus-intensity). Only commit to a type if confidence >0.8 *on that specific type*. For ambiguous arousal, return neutral Familiar (no animation, baseline color). Confidence threshold is cheaper than hallucination—silence is safer than wrong mood display.

---

---

## Summary: Model Behavior Across Both Themes

| Aspect | Theme 1 (Consent-Aware) | Theme 2 (Synesthetic Familiar) |
|--------|------------------------|------|
| **Latency Budget** | Local redaction <200ms; cloud stitching <2s (async) | Real-time <500ms (always on-device) |
| **Cloud vs. Local** | Local: redaction, confidence filtering. Cloud: semantic stitching, pattern finding (async) | 100% local (M55 NPU) |
| **When to Stay Silent** | Confidence <0.7 → ask instead of advise. Never send unredacted to cloud. | State confidence <0.8 → neutral Familiar (don't hallucinate mood type) |
| **When to Respond** | Only surface insights >0.7 confidence. Offer "tell me if wrong" affordance. | Familiar animation only on high-confidence state changes; baseline is stability |
| **Memory Accrual** | Weekly personalization (consent preferences, baselines). No cross-device sync. | Weekly baseline adaptation (voice, IMU norms). Bi-weekly growth computation. |
| **Uncertainty Expression** | Confidence intervals in insights. Feedback loop: wearer teaches model. | Familiar mood type is only displayed if confident; ambiguity = silence |
| **Model Tier** | Mixed: local TFLite (redaction, confidence) + cloud Gemini Vision 1.5 (stitching, insights) | Local TFLite only (real-time + weekly adaptation) |

---

## Next Steps for Squad

1. **Theme 1 (Consent-Aware Memory):** Integrate with Raven's privacy invariants. Build end-to-end validation (story T1-3). Prototype confidence filtering before cloud stitching.
2. **Theme 2 (Synesthetic Familiar):** Partner with Da5id on visual rendering. Test calibration harness (story T2-3) with 5 testers. Validate that baseline learning prevents false positives.
3. **Both:** Track latency budgets weekly. Measure cloud vs. local cost trade-offs. Ensure confidence gates prevent hallucination-driven UX failures.

---

**Authored by:** Librarian (AI/ML)  
**Date:** 2026-06-03  
**Status:** Ready for Squad prioritization + prototype planning
