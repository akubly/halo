# Project Context

- **Owner:** Aaron Kubly
- **Project:** halo — mono-repo playground for authoring apps on Halo smart glasses
- **My layer:** Host apps (Python/Flutter/Web) that drive the glasses via the Brilliant SDK
- **Created:** 2026-06-01

## Learnings

### Session 2026-06-01: SDK Familiarization & Host-App Architecture

**Halo Hardware Shape:**
- Color microOLED display (circular 256×256), bone conduction audio, Bluetooth 5.3
- Runs ZephyrOS with Lua VM; cannot host native apps directly
- Acts as a *peripheral* — all logic runs on host (laptop, phone, browser)
- Pairing: button hold 10s → LED flash → scan from host app → pair

**Host-App Development Models by Platform:**

1. **Python Desktop** (`brilliant-ble` + `brilliant-msg`)
   - Async-first (asyncio); BrilliantBle for low-level, BrilliantMsg for rich messaging
   - Emulator available (`halo-emulator`) — test without hardware, pygame REPL for debugging
   - Session flow: connect → send break/reset → upload Lua libs + app → start loop → exchange messages
   - Typical UX: CLI loops, REPL-style interactions, rapid iteration

2. **Flutter Mobile** (`brilliant_ble` + `brilliant_msg` + `simple_brilliant_app` scaffolding)
   - Scaffolding package (`simple_brilliant_app`) handles lifecycle & common patterns
   - Device-aware code (detects Halo vs Frame) — click/tap input abstraction
   - FrameVisionAppState mixin handles camera + button input for Halo
   - Typical UX: single-page app, bottom/side sheet for controls, circular text layout for display

3. **Web/Browser** (`brilliant-ble` + `brilliant-msg`, TypeScript/JS)
   - Chromium-only (Chrome, Edge, Opera); browser device picker UX
   - CircularTextLayout helper for constraining text to round display
   - Rich message types (sprites, text, audio, IMU, photos, clicks) — same across all SDKs
   - Typical UX: one-page demo, file picker for images, real-time event streaming

**Session Flow (All Platforms):**
- Scan → Pair (user action) → Connect (OS-level, then BLE subscription)
- Upload Lua libraries (data, sprite, plain_text, camera, audio, imu)
- Upload main.lua app file
- Send break/reset/break to ensure REPL, then start event loop
- Exchange async messages (button clicks, photos, audio, IMU, display commands)
- Disconnect gracefully

**Key Host-Side Patterns:**
- All SDKs use same core messaging: send sprite/text/capture requests → receive photo/audio/IMU/click events
- Halo uses indexed 4-bit color palette (0–15); Frame uses color name strings
- Button events: single/double/long; Frame has tap count variant
- Circular display matters: text layout helper, 256×256 canvas
- Lua event loop runs *on Halo*; host is reactive (send requests, handle responses)

**Noa Example Patterns:**
- Real-time camera → local Lua inference → text display + cloud AI response
- Memory persistence: remembers prior context across sessions
- Multimodal: camera input + audio output (bone conduction) + button clicks

---

### Session 2026-06-01 (Follow-up): Community Projects Survey

**Community App Landscape (mostly Monocle/Frame, migrating to Halo):**

| Type | Platform | Example | Host UX Shape |
|------|----------|---------|---------------|
| **Vision/Camera** | Python | QR-code scanner (milesprovus) | CLI: `main.py` → tap to scan → results printed/linked |
| **Vision/Camera** | Web | Drawing tool (jdc-cunningham) | Single-page web app: pixel editor → generates Python code |
| **Navigation** | Web | MonoNav (semtexzv) | Live demo site: map interface → turn-by-turn on glasses |
| **Fitness/HUD** | Web (React PWA) | Workout app (simonevetere) | PWA app launcher → workout UI → active set tracking on glasses |
| **UI Prototyping** | Web (React PWA) | bl-monocle-reactjs-pwa (jdc-cunningham) | Local storage code snippets → editor → test/flash to device |
| **Teleprompter** | Python | Google Slides → display (milesprovus) | CLI script: slides sync → speaker notes on glasses |
| **GPT Client** | Python | OpenAI client (acui51) | CLI loop: prompt → glasses display LLM output |

**Language Distribution Across Community:**
- **Python:** ~40% of apps — CLI-first, heavy on image processing (QR, CV) + desktop device targeting
- **Web/React:** ~40% — PWAs with localStorage, real-time sync, mobile-responsive
- **Node.js:** ~10% — REPL editors, CLI tools for development
- **Flutter:** ~5% — emerging (Brilliant has official support now)
- **Other (Go, Java, Android):** ~5%

**Host App Shapes:**
1. **CLI loops** — Read input → send to glasses → handle response → repeat (QR scanner, GPT client, teleprompter)
2. **Web one-pagers** — Single HTML file + JS, often live-demoed on GitHub Pages (MonoNav, drawing tool)
3. **PWA with localStorage** — Persistent code editor or state (bl-monocle-reactjs-pwa, workout app)
4. **Mobile native** (emerging) — Still nascent; `simple_brilliant_app` Flutter scaffolding is new

**No Standardized Scaffolds in Community:**
- Each project re-invents the connection lifecycle (break → upload → start loop)
- No shared patterns for Bluetooth lifecycle errors, retry logic, or disconnect handling
- No template repos that authors can fork

**Reference Implementations Worth Studying:**
1. **`fixermark/brilliant-monocle-driver-python`** — Solid asyncio wrapper, handles UART MTU overflow, touch event callbacks. Clean async context manager pattern.
2. **`bl-monocle-reactjs-pwa`** — Shows how to build a persistent code editor with localStorage + BLE sync. Good for understanding Web Bluetooth lifecycle in React.
3. **`monocle-node-cli`** — Extracted CLI communication from AR Studio; demonstrates REPL-style device interaction (could adapt for Halo CLI REPL).

**Brilliant's Official Scaffolds:**
- **Python:** `halo-emulator` package is unique — no other project provides offline hardware emulation
- **Flutter:** `simple_brilliant_app` package (official) — provides device detection + startup boilerplate; widely portable
- **Web:** No official scaffold; community fills gap with PWAs

---

### Session 2026-06-02: GitHub Scaffolds & Example Apps Survey

**Bright Labs Official Examples (brilliant_sdk monorepo):**

| Platform | Key Example | What to Borrow |
|----------|---|---|
| **Python** | `halo_emulator/examples/repl_hello.py` | REPL-style Lua command stream; emulator integration; framebuffer output; argparse CLI scaffolding |
| **Flutter** | `simple_brilliant_app/example/camera/lib/main.dart` | Device-aware mixins (`SimpleFrameAppState`, `BrilliantVisionAppState`); `ClickType` vs `taps` abstraction; full camera capture loop |
| **Flutter** | `simple_brilliant_app/template/simple_frame_app/main.dart` | Bootstrap template (copy-paste start) + pubspec dependencies |
| **Web** | brilliant_sdk/webbluetooth (no direct examples found) | CircularTextLayout for display; TxTextPage message type |

**Key Observations:**
- Python examples default to REPL mode (fast iteration) or `brilliant_msg` (full lifecycle)
- Flutter templates are copy-paste ready (simplifies first app)
- Web examples are sparse in official SDK; real patterns live in community (bl-monocle-reactjs-pwa)

**Community Examples Worth Studying:**

| Project | Platform | What It Shows | Stars |
|---------|----------|---|---|
| **CyberSyntax/AnkiLens** | Flutter | Full Halo-compatible app; spaced repetition UI + local inference + multimodal | 1 (new) |
| **CitizenOneX/frame_ble** | Dart | Alternative low-level BLE wrapper (Frame); shows architecture choices | 4 |
| **uma-shankar-gupta/brilliant_ble** | C++/Dart | BLE bridge pattern; shows non-official SDKs exist | 5 |
| **jdc-cunningham/oled-pixels-to-mpython** | Web + Python | Pixel-editor PWA → generates MicroPython; code-gen pattern | ~archived |
| **jdc-cunningham/bl-monocle-reactjs-pwa** | Web (React) | Persistent code editor + localStorage + live BLE sync (reference for Web scaffold) | popular in community |
| **milesprovus/Monocle-QR-Reader** | Python | CLI main.py → USB photo capture → QR decode → link open | minimal, works |
| **simonevetere/monocle** | Web (React PWA) | Workout HUD app; PWA launcher pattern; shows mobile native Halo UX | community reference |

**Mono-Repo Precedents:**
- **Brilliant SDK itself:** organized as `{python,flutter,webbluetooth}/packages/{brilliant_ble,brilliant_msg,simple_brilliant_app}` + examples
- Parallel structure: each platform has low-level BLE + high-level messaging + optional scaffolding
- No "playground" repo exists in Brilliant org — opportunity to pioneer this pattern

**Anti-Patterns Spotted:**
- Community projects re-implement BLE connection lifecycle (no shared lib)
- Web projects often skip structured lifecycle (ad-hoc JS)
- Frame/Monocle projects don't migrate cleanly to Halo (Halo-specific device detection needed)
- Over-engineered Halogen/PureScript examples (not AR glasses, unrelated)

---

## Ideation: Joyful Playground Projects (2026-06-02)

**PIE-IN-THE-SKY BRAINSTORM — Joy-First, No Feasibility Gate**

1. **Pet Digital Familiar** — Your Halo displays a tiny reactive creature (blob, sprite, weird thing) that lives in the corner of your vision, responding to light changes, motion, and button taps throughout the day, slowly evolving and developing quirky behaviors.

2. **Skeleton Pose Mirror** — Camera feed detects your body shape via IMU + pose inference, then Halo overlays an exaggerated dancing skeleton that mirrors and *amplifies* your movements for cartoonish comic effect.

3. **AI Graffiti Artist** — Whatever you point the camera at gets instantly annotated with absurd AI-generated labels, doodles, and callouts, turning your vision into a weird interactive comic book overlay.

4. **Forehead Fortune Teller** — Tap the button to summon a mystic card reading; the fortune is generated from random pixels of what you're looking at, cryptic and hilarious every time.

5. **Bioluminescent Skin Sync** — Phone tracks your heartbeat via camera, Halo displays pulsing light patterns on your arm/wrist in real-time, making you glow to your own rhythm.

6. **Gesture-Based Draw Duel** — Quick-draw game using Halo's IMU: both players tap to summon, then execute fastest pistol-draw motion to win; audio feedback + scorekeeper for one-upmanship.

7. **Tiny Floating Museum** — Walk around with a personal digital art gallery hovering in the corner; each button press cycles through randomly-fetched community images, memes, or your phone's photo library, curated-by-chaos style.

8. **Reality Glitch Filter** — Apply real-time corruption effects (pixelation, RGB-split, temporal lag, color inversions) to your camera feed, making the world look like the Matrix is melting around you.

---

## Ideation Pass 2 — 2026-06-02

**Cross-pollination synthesis:**

After reading the 8 other agents' ideation sets (Hiro's ambitious architecture mesh ideas, Enzo's agentic moonshots, Ng's hardware-stretching sensor loops, Da5id's radial/circular HUD principles, Librarian's embodied memory agents, Raven's privacy-as-feature frameworks, Lagos' community remix culture, Juanita's chaos-engineering stress tests), three observations crystallized:

1. **Agentic thinking is the connective tissue.** Enzo's micro-habit accelerator and Librarian's persistent memory agents reframe playground apps from "stateless tools" to "companions." This changes what I want to *build*.

2. **Da5id's radial/circular visual language is liberating, not limiting.** Bloom, orbit, pulse, radial scrubbing—motion > statics. This is how I want to think about Halo UX design.

3. **Privacy and beauty are not in tension.** Raven's selective blur + Librarian's hallucination rendering + Lagos' remix culture = permission to make apps that feel both delightful *and* empowering.

**Key resonances:**
- Enzo #6 (Micro-Habit Accelerator) — pure scaffolding energy, perfect first "real app" template
- Librarian #1 (Persistent Embodied Memory Agents) — reframes Halo as knowing *you*, not just processing queries
- Raven #3 (Selective Blur) — privacy as *playable* affordance, not restriction

**Top new mash-up to prototype:**
**Bloom Habit Tracker** (Y.T. #3 × Enzo #6 × Da5id #8) — 1-week scaffold combining habit detection, bloom reward visuals, and host-app lifecycle. Ships complete joy; becomes template for "beautiful feedback design."

**4 new ideas added:** Radial History Scrubber, Button Echo Chamber, Noa Talk Show, Distributed Gesture Language.

See `ideation-pass2-2026-06-02.md` for full synthesis, mash-ups, and amendments to original 8.

---

## User Stories Themes 1-2 — 2026-06-03

**Context:** Aaron curated two themes from cross-squad ideation:
1. **Consent-Aware Memory** (most-cited convergence: Hiro+Enzo+Librarian+Raven+Lagos)
2. **The Synesthetic Familiar** (Y.T. pet × Librarian synesthetic AI × Da5id peripheral-only)

**Authored:** 5 user stories per theme (happy path + delight moment each), focused on host-app UX:
- Theme 1 stories span pairing setup, group recording consent, memory review, bystander replay rights, and accidental-capture sharing
- Theme 2 stories cover first-launch bonding, stress-detection, personality customization, 30-day evolution, and surprise moments

**Scope:** Phone (Flutter) + web (React) + CLI (optional). All host-side surfaces (no Lua changes needed; sprites sync via BLE).

**Key Design Decisions:**
- Theme 1: Consent is a *network protocol*, not an afterthought. BLE mesh for negotiation; crypto signatures for audit.
- Theme 2: Familiar is a *vitals mirror*, not a chatbot. Motion > text. Peripheral-only, non-intrusive.

**Next Steps:** Backtesting with Aaron. Recommend Theme 1 (Consent) for security review; Theme 2 (Familiar) for UX iteration.

See `user-stories-themes-1-2-2026-06-03.md` for full stories + acceptance criteria + app-shape notes.

---

## Codename Brainstorm — 2026-06-08

Pitched UX-design-lens codename candidates for the Synesthetic Familiar. Team converged on **PULSE** (4 agents independently nominated variants). Official project codename now PULSE. See `.squad/orchestration-log/2026-06-08T07-17Z-codename-brainstorm.md`.
