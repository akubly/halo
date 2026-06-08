# Project Context

- **Owner:** Aaron Kubly
- **Project:** halo — mono-repo playground for authoring apps on Halo smart glasses using the Brilliant SDK
- **Stack:** TBD per package; SDK languages are Python, Flutter (Dart), Web Bluetooth (JS/TS). Lua 5.3 runs on-device.
- **Created:** 2026-06-01

## Learnings

### 2026-06-01 — Product & Architecture Overview
- **Halo is a host-app model** (not a traditional OS with app launcher). Glasses are *peripheral*, host (mobile/desktop) *drives logic*. Implication: each SDK is independent client lib; no cross-SDK coordination needed at build time. [https://docs.brilliant.xyz/halo/halo-sdk/]
- **3 canonical SDK targets**: Python (Mac/Linux/Windows), Flutter (iOS/Android), Web Bluetooth (Chromium on desktop/Android). Lua 5.3 on-device for event loops & custom processing. [https://docs.brilliant.xyz/halo/halo-sdk/]
- **Halo hardware**: Cortex-M55 + NPU, 14h battery, Bluetooth 5.3. Tight memory/power constraints. On-device AI inference possible, but host does heavy lifting. [https://brilliant.xyz/]
- **Shared concerns across SDKs**: BLE protocol abstraction (Bluetooth LE Specs), Lua VM wire protocol, example/reference apps. **Distinct concerns**: language-specific testing, build, package management. Suggests SDK-per-workspace structure with optional shared tooling workspace.
- **No "shared logic" cross-SDK**: Unlike a traditional app platform, there's no server-side SDK or shared compute that all SDKs depend on. Each SDK is independent. Mono-repo can remain flat; only extract shared infra if 3+ packages need it. [https://docs.brilliant.xyz/halo/halo-sdk/]

### 2026-06-01 — Lineage: Monocle → Frame → Halo
- **Monocle** (gen 1, monocular): Python only, programmed via AR Studio (VSCode extension). Firmware updates via AR Studio. Closed ecosystem.
- **Frame** (gen 2, binocular): Python + Flutter SDKs introduced. Still tightly coupled host model. **Lua event loop architecture fundamentally changed** Frame→Halo (old keyed-table parser model → new ordered-queue model). Migration required rewriting all on-device event loops. [https://docs.brilliant.xyz/frame/frame/, https://raw.githubusercontent.com/brilliantlabsAR/brilliant_sdk/main/python/MIGRATION.md]
- **Web Bluetooth SDK added** (gen 2.5 → Halo): Targets browsers & web platforms. No Frame Web SDK existed.
- **Package names renamed**: `frame-ble`/`frame-msg` → `brilliant-ble`/`brilliant-msg`. Signals Brilliant's intent to support *future devices* under a unified SDK brand. [Migration guides]
- **SDK API surface survived 2 gens**: BLE communication pattern, Lua integration, camera/mic/display control remain stable. The churn is in **on-device event loop semantics**, not host SDK contracts.
- **Brilliant is willing to break Lua APIs.** Frame→Halo forced rewrite of `frame_app.lua` across all users. This suggests SDKs should *not* over-invest in backward compat abstractions; velocity & clarity matter more. [https://raw.githubusercontent.com/brilliantlabsAR/brilliant_sdk/main/python/MIGRATION.md]

## Ideation 2026-06-02

1. **Glasses as distributed compute mesh** — Multiple Halo wearers auto-discover and form a P2P cluster; each pair contributes CPU cycles for collective ML inference tasks (vision, language, reasoning) with the network coordinating work distribution and result synthesis.

2. **Wearable temporal viewport** — Halo queries a shared local-first database of recorded sensor feeds (camera, audio, IMU) from nearby wearers and devices; you see any scene at any past moment within your network's retention window, navigable by time scrubbing gestures.

3. **Embodied protocol-buffer mesh** — Each Halo is a first-class gRPC service endpoint advertising capabilities; two wearers' glasses auto-negotiate message schemas, service discovery, and bi-directional streaming without a central broker—the mesh is self-describing.

4. **Gaze-driven distributed tracing** — Your eye gaze becomes an OpenTelemetry tracing context; every service in your personal network receives your attention vector; you see latency and throughput *in your visual field* as the traces propagate through your infrastructure.

5. **Glasses as edge orchestrator** — Halo becomes the command center for heterogeneous edge devices (phones, laptops, IoT sensors, local servers); you gesture to claim/release capabilities or re-balance workloads; topology and state are displayed as a zoomable spatial layer.

6. **Consensual overlay reality** — Multiple Halo wearers in the same physical space each see *different* overlays on identical scenes, computed from their trust graph, interests, and social role; overlays are encrypted and merged at the edge, never centralized.

7. **Embodied microservices topology** — Every Halo wearer running an app is a microservice node on a graph; nodes dynamically claim/release capabilities (e.g., "I can process video now," "I can transcribe audio"); the topology is rendered as a 3D constellation visible to all wearers.

8. **Live architecture debugger for edge** — Halo becomes a spatial debugger for distributed systems: walk through a room and *see* message flow between services as light trails, latency as visual thickness, bottlenecks as red hotspots; topology rotates to follow your head position.

## User Stories Themes 1–2 — 2026-06-03

Authored user stories for Aaron's two top-ranked themes through architectural lens:

- **Theme 1 — Consent-Aware Memory** (5 stories): Consent as protocol infrastructure. Captures architectural requirements: cryptographic notarization, peer-to-peer verification, time-based durability boundaries, graceful sensor fallbacks, consent observability.
  
- **Theme 2 — The Synesthetic Familiar** (5 stories): Familiar as modular state machine. Captures architectural requirements: mood/render decoupling, sensor-degradation hierarchy, cross-device roaming state, distributed mood computation, performance observability within HUD budget.

**Key insight:** Both themes surface **constraints-as-architecture** pattern. Privacy (consent), display budget, battery, and reliability are not bolt-on features; they shape mono-repo structure, BLE protocol, SDK contracts, and observability layer.

**Stories saved:** `.squad/agents/hiro/user-stories-themes-1-2-2026-06-03.md`

---

## Ideation Pass 2 — 2026-06-02

Cross-pollination complete. Key insights from team's 8 agents:

- **Resonance**: Librarian's persistent embodied agents (rewires host-peripheral model), Raven's privacy-as-first-class-constraint (changes BLE protocol design), YT's on-device tracking loop (reveals device autonomy tier beyond host command).
- **Strongest mash-up**: Self-Describing Privacy Mesh (Hiro #3 × Librarian #1 × Raven #6) — unifies distributed protocols with cryptographic consent metadata, enabling multi-wearer collaboration without central broker while keeping privacy locally enforceable.
- **New cross-cutting concern**: Device Autonomy Tiers (local, hybrid, collective) — mono-repo gains a new structural dimension. Every playground project now has an autonomy-tier assignment.
- **Practical shift**: Mono-repo becomes a consent teaching tool (Raven × Lagos lens). YT's host-app scaffold gains mandatory "Consent Initialization" section.

Full synthesis: `.squad/agents/hiro/ideation-pass2-2026-06-02.md`

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

### Key Open Questions for Aaron

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
