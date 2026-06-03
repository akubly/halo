# Librarian Pass 2 — AI/ML Ideation Synthesis
**Date:** 2026-06-02  
**Librarian (AI/ML):** Cross-pollination analysis of 8 squad agents  
**Scope:** Identify resonant ideas, novel AI mashups, amendments, and new directions shaped by other agents' constraints + opportunities

---

## 🔥 Resonance — 3 Ideas That BEG for AI Patterns

### 1. **Raven #5: Privacy Mode as Social Signal**
> "External LED ring shows realtime privacy stance to bystanders: red = recording, yellow = observation-only, green = fully private."

**Why this resonates for AI:** The privacy stance is *itself* a temporal classification task. An LLM loop can infer intended privacy mode from context (user is in meeting → yellow; camera-to-face → red; blank scene → green) and surface predictions *before* user must manually toggle. This reframes privacy from *binary toggle* to *contextual inference*—the glasses learn your privacy preferences and proactively broadcast them. Pair with Claude or Gemini multi-turn reasoning to build a "privacy intent model" that gets smarter each session.

### 2. **Da5id #7: Pulse Poker (Monocular Asymmetry as Gameplay)**
> "A party game where only YOU see a secret color pulse in your peripheral vision; others watch your micro-expressions to catch when you 'see it'."

**Why this resonates for AI:** Micro-expression detection is a classic CV task, but monocular glasses uniquely *hide* the wearer's eyes from others while revealing their own gaze/attention. An on-device lightweight pose model (running on M55 NPU) can detect micro-saccades + facial muscle micro-movements, feed them to a small transformer predicting "pulse moment" with 90% precision. This makes the game *real*—others aren't guessing; they're reading your micro-tells. Invert the asymmetry: Halo becomes a social-mirror AI that surfaces your hidden reactions.

### 3. **Hiro #4: Gaze-Driven Distributed Tracing**
> "Your eye gaze becomes an OpenTelemetry tracing context; every service in your personal network receives your attention vector."

**Why this resonates for AI:** Gaze is a rich signal for LLM context windows. If your glasses know you're looking at object X for 3 seconds, that's *user intent ground truth*. Pair with multimodal LLM (Gemini Live camera stream): gaze coordinates + what you're looking at → LLM reasons about your likely goal. E.g., you gaze at a broken bike lock for 5 seconds; LLM proactively offers "unlock tutorials" before you ask. This flips the reasoning model: instead of reactive QA, gaze-driven predictive reasoning. Attention becomes the primary API surface for intent.

---

## 🔀 Mash-ups — 4 NEW AI Patterns

### **MASH-UP #1: Raven #7 × Librarian #1 = "Consent-Aware Embodied Memory"**
> Raven: "Automated Face-Gating — Halo learns wearer's face and automatically refuses to record when others are in frame unless they explicitly opt-in."  
> Librarian #1: "Persistent Embodied Memory Agents — Halo maintains a continuous neural profile of you."

**New AI Pattern:** Instead of just face-gating on *presence*, build a **consent-augmented memory agent**. Halo learns:
- Who you *want* recorded with (trusted circle: family, close friends) vs. who needs opt-in
- Consent patterns over time (e.g., "colleagues always opt-in to morning standups, never afternoons")
- Emotional tone (friend is stressed → record sparingly; friend is excited → auto-record moments they'll cherish)

**The Demo:** During a group photo, Halo *requests* consent on behalf of your friends ("Sarah says OK, John says maybe, Maya said no last month"). Halo builds a temporal consent model that gets smarter—future recordings become "smart recordings" where opt-in is predicted, not asked. Memory becomes consent-aware and relationship-aware.

---

### **MASH-UP #2: Da5id #1 × Enzo #2 = "Biometric Breathing Coach via Peripheral Motion"**
> Da5id: "Breathing Halo — A ring at the canvas edge that expands/contracts to pace your breath, visible only in peripheral vision."  
> Enzo #2: "Energy Cartography — build a spatial heat-map of your home showing energy-drain zones via bone-conduction feedback."

**New AI Pattern:** **Ambient Biometric Inference Loop**. Combine:
- On-device audio (bone conduction speaker + microphone) to infer breathing rhythm (low-frequency)
- Breathing ring rendering (Da5id's peripheral motion)
- Contextual model: when you enter energy-drain zones (boring meeting room, fluorescent corridor), LLM predicts stress/fatigue from past patterns
- Multimodal LLM (Gemini) generates *personalized* breathing exercises that match your stress type + location

**The Demo:** You walk into your office's fluorescent hallway (energy drain). Halo detects elevated heart rate (via bone conduction audio baseline) + recognizes the location. Breathing ring pulses with a customized 4-7-8 breath pattern you prefer. Noa whispers via bone conduction: "You're stressed; this corridor usually drains you. 60-second breathing. Ready?" Breathing ring visually guides you. After 30 days, the LLM predicts stress *before* biometric spikes and pre-emptively offers coaching.

---

### **MASH-UP #3: Ng #1 × Librarian #5 = "Spatial Audio Beamforming as Context Channel"**
> Ng: "Spatial Audio Beamforming via IMU + Speaker — create a spatial sound 'bubble' that follows gaze direction."  
> Librarian #5: "Multiplayer AR Embodied Personas — Multiple LLM agents inhabit shared AR spaces as glyphs/holograms."

**New AI Pattern:** **Directional Attention for Multi-Agent Reasoning**. In a shared Halo space (2+ wearers):
- Your gaze direction (IMU head tracking) determines which "agent voice" you hear from bone conduction (beamformed to your attention direction)
- Each agent (collaborator, advisor, adversary LLM persona) inhabits a specific spatial location
- Gaze-switching = agent-switching; the LLM context window shifts based on who you're "looking at"

**The Demo:** You and a friend are co-designing a furniture layout in AR. Both wear Halo. You look at a lamp (left side)—a "designer persona" whispers suggestions in your left ear. You turn to look at your friend—their voice (or collaborative LLM) comes through clearly, localized to their head position. Turn to the wall—a "physics advisor" LLM explains load capacity from that direction. Spatial audio + gaze + multi-agent LLM = immersive collaborative reasoning without crowded UI.

---

### **MASH-UP #4: Juanita #7 × Raven #1 = "Chaos-Tested Privacy Guarantees"**
> Juanita: "Camera Starvation — Request photo capture every 10ms to test queue backpressure, buffer overrun."  
> Raven: "Ephemeral Vision Mode — recorded video auto-deletes after 30 seconds unless user explicitly saves."

**New AI Pattern:** **Adversarial Privacy-Robustness Testing Loop**. Instead of chaos tests *destroying* the device, use chaos to *verify* privacy invariants:
- Stress-test ephemeral deletion under load: Does 100 concurrent video captures all delete on the 30-second timer? Or does buffer pressure cause leaks?
- Use LLM to *generate* adversarial scenarios: "In this financial firm, an attacker tries to exfiltrate camera feed by triggering buffer overflow. Can the on-device AI detect the attack pattern and refuse recording?"
- Each chaos test becomes a privacy audit: privacy guarantees must hold even under stress.

**The Demo:** Continuous privacy chaos simulator logs: "Day 1: 500 stress tests, 100% deletions on-time. Day 5: Camera buffer pressure causes 2 frames to persist past 30-second timeout—alert and patch." Privacy becomes *measurable* and *verifiable* via adversarial LLM-driven testing.

---

## ✏️ Amendments

### **Librarian #1: Persistent Embodied Memory — Add Privacy Tiers**
**Prior idea:** "Halo maintains a continuous neural profile of you (visual history, voice patterns, emotional tone)."

**Amendment:** Memory should have explicit privacy tiers:
- **Tier 1 (Public):** Patterns you're willing to share (e.g., "I prefer mornings") → can surface to other wearers or LLM services
- **Tier 2 (Private):** Patterns only you see (e.g., "I get anxious around specific people") → on-device only, never exported
- **Tier 3 (Ephemeral):** Temporary session state → auto-purges after 24 hours

Raven's consent-gating ideas make this *mandatory*. The LLM loop should respect memory privacy tiers automatically.

---

### **Librarian #5: Embodied Personas — Add Conflict Resolution**
**Prior idea:** "Multiple LLM agents inhabit shared AR spaces... competing/cooperating for user attention."

**Amendment:** When multiple personas give *conflicting* advice:
- **Conflict mode:** Both voices are rendered spatially, and the LLM explicitly surfaces the disagreement ("Advisor A says 'be cautious'; Advisor B says 'take the risk'")
- **Async reasoning:** Instead of real-time competition, wearers can "defer" a decision: "Show me both scenarios in detail tonight." LLM writes a comparison document for async review.
- **Consensus vote:** For group decisions (2+ wearers), personas can be voted on. The winning persona becomes the group's reasoning model for the next phase.

This reframes multi-agent LLM from entertainment to *decision amplification*.

---

### **Librarian #2: Peripheral Sense Augmentation — Swap to Bone Conduction**
**Prior idea:** "Render abstract concepts as felt/visual metaphors — 'emotional resonance' as color gradients on HUD."

**Amendment:** Bone conduction is *already* available (stereo speakers). Replace visual "tactile pressure intensity" with **haptic simulation via audio**:
- Low-frequency bone conduction patterns (50–100 Hz) perceived as "pressure" or "touch"
- Can modulate without additional hardware
- Pairs naturally with Enzo's "bone-conduction whisper coaching"

This is more feasible and doesn't overconstrain the visual HUD (which Da5id already has packed tight).

---

## 🌟 NEW — Ideas Shaped by Raven, Hiro, Da5id Constraints

### **1. Privacy-First Local Inference as Competitive Advantage**
**Shaped by:** Raven (privacy) + Librarian ideation (model choice)

**Proposal:** Don't just document "on-device privacy." *Demo* it.

Build a **Privacy-First Noa Clone** (Workout Coach or Bird Watcher) that:
- Runs *all* vision inference locally on M55 NPU (bounding boxes, pose detection, bird species ID)
- *Never* sends raw images to Gemini—only send structured outputs (bounding boxes + confidence + IMU context)
- Passes Raven's consent gates: no image data leaves the device unless explicitly approved

**Why this matters:** Brilliant's Noa sends full camera frames to Gemini Live. Our first demo could be *more privacy-conscious* while still using multimodal AI. This becomes a differentiator in the community: "Halo apps can be AI-powered AND privacy-first."

**Action:** Pair with Raven to define privacy invariants. Use local TensorFlow Lite models (Coral-optimized) for on-device vision. Keep cloud LLM calls narrowly scoped (e.g., "Is this bird rare?" given bounding box + species name, not image).

---

### **2. Mesh-Aware Reasoning — Hiro's Architecture Meets AI Context**
**Shaped by:** Hiro (P2P mesh, distributed tracing) + Librarian (context stitching)

**Proposal:** Build **multi-device context coherence** into the LLM loop.

When 2+ Halos are in Bluetooth range (Hiro's mesh layer):
- Combine sensor feeds (2 perspectives, 2 microphones) into unified context window for Gemini
- Gaze coordinates from both wearers inform shared reasoning ("You both looked at that plant for 5 seconds—is it the same species?")
- Distributed tracing (gaze + attention flows) becomes the "context breadcrumb" for LLM reasoning

**Why this matters:** Multiplayer AR is Hiro's moonshot. AI can amplify it by *reasoning across two perspectives* instead of treating each wearer as isolated. This unlocks collaborative AI demos that wouldn't work on single-device apps.

**Action:** When building the first multiplayer demo (Ng's ideas + Hiro's mesh), ensure LLM prompt includes "I see this from device A at bearing 45°; device B sees it at bearing 220°. Infer 3D position."

---

### **3. HUD-Aware LLM Output Formatting — Da5id's Constraints as Prompt Anchors**
**Shaped by:** Da5id (round, monocular, glance-budget, max 3 elements) + Librarian (multimodal prompting)

**Proposal:** Add **HUD constraints to the LLM system prompt** for every AI app.

Don't let Gemini return wall-of-text responses that don't fit on a circular, low-power display. Instead:
- System prompt includes: "Output MUST be ≤3 visual elements (icons, numbers, brief labels). Max 10 words. Use these HUD patterns: [Breathing Halo, Orbital Notifications, Depth Rings, Radial Time]."
- When LLM returns a response, *post-process* with a formatter that maps text → HUD patterns
- Examples: "Low battery warning" → Bloom Alert (urgent flower); "Next turn in 50m" → Orbital Notification (moon drifting left)

**Why this matters:** Most AR demos fail because the output is designed for phones/web, not glasses. By baking HUD constraints into the *LLM prompt itself*, we ensure AI responses are glasses-native from the start.

**Action:** Create a `.squad/agents/librarian/hud-constraints-system-prompt.md` with Gemini prompt templates for each Da5id HUD pattern. Use this as the foundation for all playground demos.

---

### **4. Ephemeral-by-Default Recording + AI Summarization — Raven + Librarian Synthesis**
**Shaped by:** Raven (ephemeral mode, face-gating) + Librarian #7 (episodic context stitching)

**Proposal:** Flip the recording model.

- **Wearer POV:** Halo records *everything* to a rolling 30-second buffer (on-device, no cloud). At the 30-second mark, auto-deletes unless wearer taps "save."
- **Bystander POV:** LED countdown shows "recording but ephemeral" (Raven's consent beacon).
- **AI Synthesis:** When wearer *does* save a clip, Gemini Vision processes it *that evening* (offline window, lower latency cost):
  - Extracts key moments (faces blurred per Raven #3 rules)
  - Generates 1-sentence summary + tags
  - Stitches multiple day's clips into weekly narrative

**Why this matters:** Combines privacy (ephemeral) + community (shared summaries) + AI (async synthesis). Solves the "memory ledger" problem (Enzo #4) but privacy-first.

**Action:** Design a "Noa Review Coach" demo that records form corrections during workouts, summarizes them nightly, and streams corrected form back to the wearer over the next 7 days. Privacy-first + multimodal AI + always-on utility.

---

### **5. Generative Chaos Testing for Edge Cases — Juanita's Testing + Librarian's Adversarial Reasoning**
**Shaped by:** Juanita (chaos engineering) + Librarian (LLM agent loops)

**Proposal:** Use Claude or Gemini to *generate* chaos test scenarios.

Instead of hand-coding 8 chaos tests, feed Claude a description of Halo's architecture + constraints:
- "Halo has a 300mAh battery, 256KB Lua VM, BLE 5.3, and a 256×256 OLED display. Propose 10 scenarios that stress each subsystem to failure and validate recovery."
- Claude generates test plans (in English + pseudocode)
- Juanita translates to Lua/Python; runs weekly
- LLM also *predicts* failure modes: "If button callback queue fills, Lua VM might deadlock. Suggest: add timeout + graceful queue flush."

**Why this matters:** Chaos testing is expensive (human intuition + manual coding). LLM can synthesize edge cases faster and broader than hand-crafted tests.

**Action:** Create a `.squad/agents/librarian/chaos-prompt.md` that documents Halo's subsystems. Feed it to Claude (long context window) monthly to refresh the chaos test suite.

---

## Summary Memo

**Cross-squad synthesis yields:** The most AI-resonant ideas are those that flip traditional asymmetries:
- Privacy → *transparent signal* (Raven #5 + AI)
- Solo recording → *multi-device context* (Hiro + AI)
- Reactive QA → *gaze-driven prediction* (Hiro #4 + AI)
- Manual testing → *adversarial LLM test generation* (Juanita + AI)

**Highest-signal mashup:** **Raven #7 × Librarian #1** (Consent-Aware Memory) — this reframes the entire recording model and creates a privacy+AI narrative that differentiates Halo from Brilliant's Noa (which doesn't do consent-aware memory).

**Next steps:** Aaron's approval on mash-up priorities, then decompose "Privacy-First Noa Clone" + "HUD-Aware LLM Formatting" into GitHub issues for Phase 1 playground projects.
