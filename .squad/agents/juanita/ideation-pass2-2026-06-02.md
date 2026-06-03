# Chaos-Engineering Pass 2: Adversarial Testing as Demo (2026-06-02)

> After reading the team's round-1 ideation, here's where the chaos gets *interesting*. My job: find the ideas that will break delightfully, mashup new failure modes, and propose how even the best ideas crater under stress.

---

## 🔥 Resonance: Three Ideas That WILL Break Spectacularly

### 1. **Librarian #6 × Halo Hardware = Hallucination Cascade**  
**Citation:** Librarian #6 "Hallucination-as-Generative-Content"

This idea surfaces uncertainty as glitchy overlays. **Here's how it fails:** On Halo's 256×256 circular display with 50% pixel-burn budget, rendering "morphing UI states" and "probabilistic object outlines" creates one of three catastrophes:

1. **Battery drain spiral** — Real-time probabilistic rendering (multiple alpha-blended candidates per frame) is expensive. Low-power mode kicks in → display dims → overlays become invisible → app looks broken, not artistic.
2. **Lua callback storm** — Each morphing state change triggers re-rendering; if the LLM's uncertainty updates faster than 25 fps (real possibility with streaming responses), Lua callback queue overflows → button input gets dropped → user can't interact with the "fallback certainty" option.
3. **Perceptual trust collapse** — Users see glitchy overlays and assume the *device* is broken, not the AI's confidence. They'll hard-reset, losing context. The "artistic uncertainty" becomes "app is trash."

**Why this is good chaos:** It reveals the hidden assumption that wearable users will *tolerate ambiguity*. They won't—they expect precision. The rendering pipeline has hard constraints that LLM design ideation skips entirely.

---

### 2. **Y.T. #1 + Raven #2 = Consent-Broadcast Deadlock**  
**Citation:** Y.T. "Pet Digital Familiar" + Raven "Consent Broadcast Beacon"

Y.T.'s idea: idle companion sprite in the corner. Raven's idea: always-on BLE broadcast showing "I'm recording." **The collision:**

1. **BLE radio duty cycle** — The beacon needs to broadcast every ~100ms to be scannable. The sprite animation needs display updates every 40ms (25 fps). Both fight for the radio on a device with one BLE antenna and one power budget.
2. **User confusion layer** — The beacon *looks* like it's always active, but if display power-save mode kicks in (Halo's default per decisions.md), the beacon *actually stops broadcasting* (radio shuts down). Bystanders think they can scan; the device is dark. Trust broken.
3. **Legal liability edge case** — Raven's idea assumes the beacon *proves* consent. But if it silently drops and resumes without user notice, you've created legal ambiguity: "I thought they were still recording, but the beacon was stale." Logs show device was in power-save.

**Why this is good chaos:** Highlights that privacy-as-feature and always-on ambient signals are fundamentally in tension on a power-constrained wearable. You must choose.

---

### 3. **Enzo #3 + Ng #1 = Latency Spiral in "Skill Atomizer"**  
**Citation:** Enzo "Skill Atomizer" (real-time step-by-step guidance) + Ng "Spatial Audio Beamforming via IMU"

Enzo's idea: predict user's next move and prompt before they get stuck. Ng's idea: spatial audio that follows head gaze. **The failure mode:**

1. **Inference latency cascade** — Predicting "user's next move" requires on-device Lua reasoning or cloud round-trip. Cloud round-trip is 500ms+ (network + LLM). By the time the guidance arrives, the user has already moved (or gotten stuck for 3 seconds watching the spinner).
2. **Spatial audio sync** — If the audio guidance is spatialized to follow gaze, the latency creates *disorientation*: you hear "turn left" but the audio lags your head movement by 500ms, so the spatial cue points *backward* relative to where you're looking. Your brain gets confused.
3. **User gets frustrated** — The promise is "before you get stuck." Deliver it 500ms late and the app feels like it's *gaslighting* you: "you should have known this" whispers the AI, while you're still confused.

**Why this is good chaos:** Reveals that "anticipatory UI" is only valuable if latency is sub-100ms. Anything slower reads as *intrusive*, not helpful.

---

## 🀀 Mash-Ups: Four NEW Chaos Demos

### **Juanita #2 × Hiro #4** — "Gaze Tracking Denial of Service"
**Mashup:** Hiro #4 ("Gaze-driven distributed tracing") assumes you can render OpenTelemetry traces in your visual field as your gaze moves. Juanita #2 ("BLE Stutter-Fest" — drop every 3rd packet) meets Hiro's idea.

**The chaos test:**  
- Eye gaze is sampled at ~30 Hz (fast IMU inference).
- OpenTelemetry spans arrive over lossy BLE (every 3rd dropped).
- Render a live trace tree to the display that re-flows every time a span arrives or vanishes.
- **Expected failure:** Trace tree flickering is worse than the visual distraction of the glitchy rendering. User can't read any latency data because the display is repainting faster than the eye can track. The "gaze context propagation" becomes visual noise.
- **Chaos reveals:** Rendering real-time telemetry on a micro-display is only viable with *predictable* update rates. Lossy transports break the entire paradigm.

---

### **Juanita #4 × Librarian #2** — "Synesthetic Saturation Attack"
**Mashup:** Librarian #2 ("Peripheral Sense Augmentation via Synesthetic AI") proposes rendering "emotional resonance as color gradients" and "tactile pressure as bone conduction." Juanita #4 ("Button Mash Chaos" — 100 clicks/sec) collides with this.

**The chaos test:**
- Feed 1000 rapid input events (button mashes + head shakes) to the synesthetic engine.
- Each event triggers LLM reasoning: "What emotion does this user action signal?"
- Each emotion maps to a color gradient + bone-conduction frequency.
- **Expected failure:** 
  - Bone-conduction speaker clips / distorts (audio codec saturation from Juanita #3).
  - Color gradients strobe faster than human perception (triggers seizure risk for vulnerable users).
  - Lua callback queue overflows; some emotions are skipped, creating dead zones in the emotional feedback loop.
- **Chaos reveals:** Synesthetic feedback is high-latency by nature (inference time). High-frequency input invalidates the entire premise.

---

### **Juanita #5 × Y.T. #2** — "Skeleton Mirror Memory Bomb"
**Mashup:** Y.T. #2 ("Skeleton Pose Mirror") uses pose detection and overlay rendering. Juanita #5 ("Lua Bomb" — upload 100KB script). Stack them.

**The chaos test:**
- Upload a Lua script that:
  1. Calls pose-detection inference every frame.
  2. Records every pose to a rolling buffer (memory sink).
  3. Renders 10 skeleton overlays simultaneously (one per recorded frame).
  4. Attempts to save the entire pose sequence to device storage.
- Run this for 60 seconds.
- **Expected failure:**
  - Lua VM OOM after ~5 seconds (pose buffer fills available heap).
  - Skeleton rendering slows from 25 fps to 5 fps (garbage collection thrashing).
  - Device becomes unresponsive; only recovery is hard-reset.
  - User data (pose recordings) are in an inconsistent state mid-save.
- **Chaos reveals:** The pose mirror idea assumes you can do real-time pose detection indefinitely. You can't—memory is finite, and Lua has no generational GC.

---

### **Juanita #7 × Da5id #4** — "Depth Ring Paradox under Camera Starvation"
**Mashup:** Da5id #4 ("Depth Rings" — concentric circles pulsing inward/outward to signal proximity) assumes continuous camera input. Juanita #7 ("Camera Starvation" — request photos every 10ms) reveals the collision.

**The chaos test:**
- App requests a photo every 10ms (100 req/sec).
- Camera can only deliver ~2 frames/sec in practice (hardware limitation).
- Depth-ring rendering assumes the latest depth data is fresh.
- **Expected failure:**
  - Queue backpressure: 98 of the 100 requests timeout. Lua code has to handle -EBUSY.
  - Depth data becomes stale; rings pulse inward when object is actually approaching (lag compensation fails).
  - User relies on depth cue to navigate; inverted cues cause collisions or disorientation.
  - Device crashes trying to buffer 100 pending photo requests in Lua.
- **Chaos reveals:** Ambient HUD concepts (like depth signaling) fail if the sensor data pipeline is oversubscribed. Real-time guarantees are impossible on Halo without explicit flow control.

---

## ✏️ Amendments

### Amendment to Juanita #2 "BLE Stutter-Fest"
Drop every 3rd packet → **expand to also test ACK timeout behavior**. If the host sends a packet and Halo's ACK is lost (dropped), does the host retransmit? If so, how many times before it gives up? Current proposal doesn't characterize retry budgets.

**New test:** Deliberately corrupt ACK packets (flip the checksum), measure retransmit behavior, verify eventual connection recovery.

---

### Amendment to Juanita #3 "Audio Feedback Loop"
Current idea: immediate re-render as speaker. **Add:** measure digital clipping + distortion, test that error recovery gracefully mutes the loop instead of oscillating.

**Why:** Audio saturation is silent until it isn't. User may not realize feedback is active until battery drains catastrophically. Test should verify that Halo *logs* the saturation event and notifies the host.

---

### Amendment to Juanita #6 "Pairing Purgatory"
Current idea: 50 rapid disconnect/reconnect cycles. **Expand to test:** phantom bonds — state where Halo *thinks* it's bonded to the host, but the host can't see it in the BLE central roster. This can happen if pairing succeeds but bonding info isn't flushed to persistent storage before a crash.

**New test:** Inject a power-loss signal mid-bond and verify graceful recovery.

---

## 🌟 NEW Ideas

### 1. **The Frame-Rate Purgatory**
Display refresh rate negotiation fails silently on Halo. The device defaults to 25 fps, but if the host (Python SDK) sends sprite updates at 60 fps expecting Halo to handle backpressure, Halo buffers ~35 frames before the queue overflows. **The chaos test:** Send 10 seconds of display updates at 120 fps; measure when the oldest frames finally get dropped; verify that the user sees *temporal tearing* (skipped frames appear as sudden motion jumps). This reveals whether display rendering is predictable enough for multi-touch or animation.

---

### 2. **The Palette Poisoning**
Halo allows palette changes per sprite, but there's no atomic transition. If you change the palette while a sprite is mid-render, the display shows *stale color indices* (old sprite, new palette) = visual corruption. **The chaos test:** Rapidly cycle sprite palettes (16-color → 4-color → corrupted header → 16-color) 100 times/sec; measure visual corruption, verify that Lua has error recovery (e.g., "palette mismatch, skipping sprite"), verify that the display doesn't lock up. This exposes whether Halo's rendering pipeline has any transactional guarantees.

---

### 3. **The Microphone Echo Tunnel**
Bone-conduction mic + speaker creates a 3cm feedback loop. **The chaos test:** Capture from mic, encode as LC3 (variable bitrate), stream to speaker, re-capture. Run for 60 seconds. Measure: codec bitrate explosion (echo detection failure), frequency-domain saturation, thermal spike on audio DSP. This tests whether Halo's audio stack is hardened against edge cases that Brilliant probably never stressed.

---

### 4. **The BLE MTU Negotiation Thriller**
BLE MTU can be 23–517 bytes, but SDKs negotiate it at connect time. **The chaos test:** Connect, negotiate MTU 517, then send a message that would fit in 517 but *not* in 100. Halo rejects it with "message too large for MTU." But what if the Lua app has already called `send_sprite()` with the payload? Is it dropped silently? Does the app crash? Does the connection reset? Chaos test reveals robustness of error handling when MTU becomes a constraint mid-session.

---

### 5. **The Lua Callback Reentrancy Maze**
Lua callbacks are synchronous. What if a button-press callback triggers message-receive callback? Does Lua queue them, or does reentrancy crash the VM? **The chaos test:** Rapidly inject BLE messages while mashing the button. Measure: Do callbacks interleave (breaking assumptions)? Does the VM deadlock? Does the app crash? This is a nightmare scenario for real-time apps that assume serial execution.

---

### 6. **The IMU Saturation Drift**
IMU data (6-axis: accel + compass) is sent as int16. What if accelerometer reaches max value (32767) due to physical shaking? Does the fusion algorithm saturate? Does calibration break? **The chaos test:** Physically shake Halo vigorously while recording IMU, then run pose inference on the saturated data. Does the skeleton pose mirror become nonsensical? Does the device overheat (excessive computation)? This tests real-world robustness when sensors hit their limits.

---

### 7. **The Display Power-Save Ghost**
Halo's display defaults to power-save mode (per decisions.md). But if Lua tries to render something *while power-save is active*, what happens? Does the render complete invisibly (user sees nothing)? Does the device automatically wake the display? **The chaos test:** Set power-save, immediately call display methods. Measure: hidden renders, latency to wake, UI consistency. This is a silent failure waiting to happen in production.

---

### 8. **The BLE Name Collision Nightmare**
Multiple Halos can advertise the same BLE name. Host SDK connects to "Halo-001", but if a second Halo with the same name appears mid-session, does the connection switch? Does the SDK notice? **The chaos test:** Two Halos in range, same advertised name. Connect to one, then power off that one and turn on the other (simulating MAC spoofing). Does the host notice? Or does it silently continue sending commands to /dev/null? This tests whether SDKs have identity assertions.

---

## ⚠️ Special Charge: The Beloved Idea That Fails Spectacularly

**Target:** Enzo #1 **"Social Reflex"** (the conversational co-pilot that detects when you're about to speak, records context, and suggests phrasing via Noa feedback).

### **The Failure Mode: The Latency-Privacy Death Spiral**

This idea is *beautiful* but it crashes under three constraints:

1. **Latency Nightmare**  
   Recording "the exact moment" you're about to speak requires:
   - Audio wake-word detection (on-device, ~500ms latency)
   - Context capture (camera inference + audio transcription of *others* speaking)
   - LLM reasoning ("is this user about to speak?" + "suggest rephrasing")
   - The entire pipeline must complete in **<2 seconds** or the moment passes.
   
   Enzo assumes Noa feedback is fast. It's not. If you're already 1 second into your statement by the time Noa suggests an alternative, you've already made your social move. The tool is useless.

2. **Privacy Catastrophe**  
   To record "context," Halo must:
   - Capture audio from *everyone in the room* (not just you).
   - Send to cloud for speech-to-text (Whisper or similar).
   - Process through an LLM that *memorizes* what others said.
   
   Raven's security team will reject this immediately. You've built a *wiretap*, not a social tool. Bystanders have no idea you're recording them for Noa to analyze. This violates GDPR, California AB 375, UK PECR. **Dead on arrival.**

3. **The Awkward Pause**  
   Even if latency magically drops to <500ms, the UX is broken. You're about to speak, Halo vibrates (haptic feedback via flicker from Ng #3?), you see Noa's suggestion pop up on the edge of your vision. **You've now paused mid-breath.** The social context shifts. You're no longer responding naturally; you're thinking about Noa's suggestion. The tool has introduced the very social friction it aimed to prevent.

### **Why This Critique Matters**

Enzo's idea assumes Halo is a *passive observer of your social intent*. But Halo is always-on and *visible to others*. The moment it activates, you've signaled something—hesitation, uncertainty, reliance on AI. In high-stakes social moments (confrontation, negotiation, vulnerability), that signal *changes the conversation*. The tool becomes a *liability*, not a benefit.

**Chaos engineering lesson:** Not all ambient AI is feasible on a wearable. Some ideas sound magical until you add latency, privacy law, and social dynamics. Then they crater.

---

## Next Steps (Not for Juanita)

1. **Pick 2-3 chaos tests** to prototype this sprint
2. **Prioritize by coverage:** Ideas 1-3 above (resonance) hit high-risk assumptions
3. **Real device vs. emulator:** 
   - New ideas 1-3 (frame rate, palette, microphone) → emulator first, then real device
   - New ideas 4-8 (MTU, reentrancy, IMU, power-save, BLE collision) → real device only
4. **Document failure modes** for each test; use as reference for SDK error handling

---

**Date:** 2026-06-02  
**Status:** Ideation — ready for squad discussion  
**Chaos energy:** High. Ready to break things.
