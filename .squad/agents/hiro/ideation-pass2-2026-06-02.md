# Hiro Ideation — Pass 2, Cross-Pollination | 2026-06-02

Round-1 ideas + eight agents' ideation inputs → architectural synthesis. Lens: **What patterns emerge? What system boundaries shift?**

---

## 🔥 Resonance

Three ideas that hit hardest for system & architecture thinking:

1. **Librarian #1 (Persistent Embodied Memory Agents)** — Shifts the mono-repo from "host SDK dispatch layer" to "agent persistence + context sharing layer"; glasses become stateful entities with history, not stateless command executors. Changes how we think about data flow between host and device.

2. **Raven #6 (Decentralized Consent Layer)** — Privacy as a **first-class architectural constraint**, not a bolt-on compliance layer. Implies cryptographic metadata in every message; changes how BLE protocol abstraction must be designed to carry consent proof.

3. **Yt #2 (Real-Time Computer Vision Object Tracking Loop)** — Closes the sensor-to-display loop entirely on-device without host dependency. Reveals that our host-peripheral model assumption (host drives logic) may be **wrong for latency-critical tasks**; architecture must support peer autonomy, not just host command.

---

## 🔀 Mash-ups

Four new ideas combining round-1 insights with others' work:

### **A. Hiro #3 × Librarian #1 × Raven #6 = "Self-Describing Privacy Mesh"**

Embodied protocol-buffer mesh (Hiro #3) where each Halo advertises capabilities *with embedded consent metadata* (Raven #6) and persistent context traces (Librarian #1). Instead of two wearers negotiating schemas, they negotiate **trust graphs + consent proofs**. The gRPC service endpoint becomes a privacy-aware agent that refuses to exchange certain schema types unless consent prerequisites are met. Enables multi-wearer collaboration without central broker, while making privacy posture verifiable and locally enforceable.

**Why this matters:** Mono-repo no longer separates "SDK implementation" from "consent framework." Both live in the mesh protocol layer. Host SDKs don't need consent logic; the device layer handles it.

### **B. Hiro #4 × Yt #2 = "Gaze as Local Attention Vector"**

Gaze-driven distributed tracing (Hiro #4) meets real-time object tracking (Yt #2). Instead of server-side tracing context, **eye-gaze becomes on-device attention geometry**. Your gaze targeting a tracked object automatically pins that object's trace telemetry to your display. Multi-wearer rooms: all gazes overlay on a shared spatial trace layer (without revealing who looked where). Edges stay local; only trace metadata syncs.

**Why this matters:** Decouples "where I'm looking" (private, stays on-device) from "what I'm debugging" (shareable, encrypted). Architecture needs a "spatial trace projection" layer between distributed tracing and display rendering.

### **C. Hiro #1 × Enzo #5 + Da5id #3 = "Social Capability Constellation with Presence Heartbeat"**

Distributed compute mesh (Hiro #1) meets presence heartbeat (Enzo #5) and compass-rose navigation (Da5id #3). Instead of wearers discovering peers via gRPC service ads, they discover via **real-time presence constellation**: every wearer's available capability (video processing, transcription, ML inference) pulses as a mote in a shared compass-rose HUD. Tapping a mote claims/releases that capability from your personal network. Constellation rotates as team moves or capabilities come online.

**Why this matters:** Caps the abstractions layer at constellation visualization. No need for a separate orchestrator; topology *is* the UI. Host doesn't need a capability-tracking microservice; each device tracks its own motes.

### **D. Hiro #6 × Librarian #5 = "Embodied Personas as Consensus Agents"**

Consensual overlay reality (Hiro #6) meets multiplayer AR embodied personas (Librarian #5). Instead of each wearer seeing *different* overlays based on trust graph, overlays are rendered by **competing mini-agents** (collaborator, critic, devil's advocate) that each inhabit shared AR space. Wearers see the same *agents*, but each agent's output is weighted by that wearer's trust settings. Enables multi-perspective collaboration without fragmentation.

**Why this matters:** Privacy model shifts from "different views of same data" to "same agents, different weights." Changes how we distribute agent state vs. data state across the mesh.

---

## ✏️ Amendments

Revisions to round-1 ideas now that I've seen the others:

### **Hiro #1 (Distributed compute mesh)** — Needs urgency gate
The mesh is valuable only if **consensus or decision-making pressure** exists. Round-1 assumed collective ML inference; cross-pollination reveals deeper use case: **embodied decision support across wearers**. Librarian #5 (embodied personas) + Enzo #5 (presence) suggests the mesh should orchestrate *minds* (agents), not just CPUs. Refine to: "Multiple Halo wearers form a distributed reasoning mesh where mini-agents (each wearer's advisors) negotiate attention/agreement before surfacing decisions to the group."

### **Hiro #2 (Temporal viewport)** — Retention window is underspecified
Raven's ephemeral mode (Raven #1) and cryptographic proofs (Raven #4) suggest temporal viewport needs **consent expiry**. Frames older than consent windows should auto-blur faces. This isn't a feature; it's a **architectural guardrail**. Refine: "Shared sensor database with auto-decaying consent metadata; query windows must verify bystander consent is still valid or render de-identified."

### **Hiro #3 (Protocol-buffer mesh)** — Schema negotiation is friction
Yt's ideas (real-time tracking, haptic feedback, gesture recognition) reveal that most high-bandwidth loops (vision, IMU) don't need gRPC schema negotiation; they need **frame-rate-matched streaming**. gRPC is overkill. Refine: "Halo pairs auto-negotiate streaming transports (high-frequency binary for sensors, low-frequency gRPC for commands)." Reduces complexity; separates concerns.

### **Hiro #6 (Consensual overlay reality)** — Privacy model is incomplete
Raven #3 (selective blur on wearer's terms) + Librarian #4 (world model) suggests overlays should include **local occlusion reasoning**. If I blur faces, my overlay should also suppress agent inferences that would leak identity (e.g., "this person looks stressed" still doxxes). Refine: "Each wearer's overlay rendering engine must validate that agent outputs don't violate their local privacy policy before display."

---

## 🌟 NEW (cross-pollinated)

Three ideas only visible through cross-pollination:

### **1. "Mono-Repo as Consent Artefact"**

Raven's privacy-as-feature lens + Lagos's community-mirror lens reveals: the mono-repo structure itself should be a **privacy compliance teaching tool**. Every example app in the playground includes embedded consent workflows (phone-see recording, bystander scan, metadata signing). Developers don't add consent later; it's baked into the host-app scaffold (YT #Host-App Scaffolding). Community building (Lagos) = learning by doing consent correctly.

**Implication:** YT's scaffold template gains a new section: "Consent Initialization" (required, no skip). Mono-repo structure validates this at build time (linting).

### **2. "Spatial Execution Debugger + Privacy Audit Trail"**

Hiro #8 (live architecture debugger as light trails) meets Raven #4 (cryptographic attention proofs). Instead of developers debugging latency blind, they see **light trails annotated with consent provenance**. When a message carries bystander consent metadata, the trail glows green; when consent has expired, red; when consent was revoked mid-flight, blinking. Developers immediately see privacy violations as visual anomalies. Turns privacy debugging from compliance checklist into spatial visualization.

**Implication:** Mono-repo needs a "debugger protocol" that extends OpenTelemetry to carry cryptographic proofs. New workspace: `infra/halo-privacy-debugger/`.

### **3. "Device Autonomy Tiers"**

Yt #2 (real-time tracking on-device) + Librarian #1 (embodied memory agents) reveals that our flat host-peripheral model is **actually hierarchical**. Some tasks (gaze tracking, heartbeat sync) are purely device-local. Others (object inference, scene understanding) are host-or-device (swappable). Still others (social consensus, embodied reasoning) span multiple hosts. Architecture needs **explicit autonomy tiers** (local, hybrid, collective) with graceful degradation when network fails. Glossary entry: "Autonomy Tier" (planning to add to `.squad/decisions.md`).

**Implication:** Mono-repo structure adds a *third dimension*: `sdk-python/` `sdk-flutter/` × `sdk-webbluetooth/` × `autonomy-layer/` (new cross-cutting concern). Tier assignment becomes a decision gate for every new playground project.

---

## Summary

**Strongest mash-up:** **A. Self-Describing Privacy Mesh** — Unifies Hiro's distributed system thinking (embodied protocol buffers) with Raven's privacy-first constraints (consent metadata) and Librarian's agent persistence. Shifts the entire architecture from "how do glasses talk?" to "how do glasses *decide what to say while respecting each other's privacy*?" This is the Venn diagram where architecture, privacy, and multi-wearer reasoning all converge.

