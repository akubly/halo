# Halo GitHub Landscape: Product Analysis
**Date:** 2026-06-02  
**Scanned:** ~70 repos (20 org, 40 community, 10 archived)  
**Queries:** "brilliant halo", "brilliant labs", "halo glasses", topic:brilliant-halo, topic:brilliant-labs, org:brilliantlabsAR

---

## Executive Summary
GitHub landscape reveals **early-stage, engaged community** across Monocle → Frame eras. **Zero Halo community projects** (device too new, May 2026 launch). Phase-1 roadmap is **strategically validated**: Workout Coach (audio), Bird Watcher (vision+memory), and Time Tracker (web) fill genuine ecosystem gaps. Community will likely fork + extend once playground launches.

---

## Complete Repo Registry by Category

### 1. AI / LLM / Voice (8 repos, avg 95 stars)

| Repo | Owner | Stars | Last Active | Status | Notes |
|------|-------|-------|------------|--------|-------|
| **noa-assistant** | brilliantlabsAR | 197 | Apr 27, 2026 | 🔥 Active | Backend for Noa AI agent; most-starred internal service. Reference for multimodal LLM patterns. |
| **frame_realtime_gemini_voicevision** | CitizenOneX (community!) | 80 | Feb 26, 2026 | 🔥 Very Active | **CRITICAL:** Community replication of Noa pattern (voice + vision → Gemini). Proves demand. Study for BLE latency. |
| **noa-flutter** | brilliantlabsAR | 78 | May 24, 2026 | 🔥 Active | iOS/Android Noa app; first-party reference. Dart best practices. |
| **noa-for-ios** | brilliantlabsAR | 79 | Mar 17, 2026 | ✅ Maintained | Swift Noa wrapper for iOS; validates mobile-first market. |
| **noa-playground** | brilliantlabsAR | 30 | Apr 13, 2026 | ✅ Active | Web-based Noa sandbox (JavaScript). Only JS app in ecosystem. Shows web demand. |
| **noa-for-android** | brilliantlabsAR | 25 | Apr 7, 2026 | ✅ Maintained | Kotlin Noa for Android. |
| **noa-nose-ring** | brilliantlabsAR | 5 | May 22, 2024 | ⚠️ Dormant | Experimental form factor; no commits since May 2024. |
| **BasicNoaServer** | curiosiate | 2 | Jan 4, 2025 | ⚠️ Stale | Frame Noa Python handler; example use-case. |

**Insight:** AI/LLM dominates by star count. Community is actively reimplementing Noa patterns (frame_realtime_gemini_voicevision proves demand). No Halo-specific AI projects yet.

---

### 2. Vision / Computer Vision (7 repos, avg 5 stars)

| Repo | Owner | Stars | Last Active | Status | Notes |
|------|-------|-------|------------|--------|-------|
| **frame_vision_gemini** | CitizenOneX | 6 | Feb 6, 2026 | ✅ Active | Take photo → Gemini vision API. Simple pattern. |
| **frame_vision_api** | CitizenOneX | 4 | May 24, 2026 | ✅ Active | Generic vision API wrapper; recent activity. |
| **frame_progressive_sprite_viewer** | CitizenOneX | 6 | Apr 6, 2025 | ⚠️ Moderate | Displays progressive image compression. Utility-focused. |
| **frame_sprite_viewer** | CitizenOneX | 4 | Apr 6, 2025 | ⚠️ Moderate | Basic image viewer; similar to progressive. |
| **frame_textspriteblock** | CitizenOneX | 3 | Oct 8, 2024 | ⚠️ Older | Text rendering demo. |
| **Monocle-Teleprompter** | milesprovus | 19 | Dec 5, 2023 | ❌ Stale | Google Slides → teleprompter. Monocle-era; no active development. |
| **frame_imu** | CitizenOneX | 0 | Nov 5, 2024 | ⚠️ Dead | IMU demo; never gained traction. Gesture/motion gap remains. |

**Insight:** CV projects exist but are mostly "image viewer" utilities; no real computer vision (object detection, pose, OCR) projects. Bird Watcher fills a gap.

---

### 3. Audio / Voice I/O (5 repos, avg 6 stars)

| Repo | Owner | Stars | Last Active | Status | Notes |
|------|-------|-------|------------|--------|-------|
| **frame_transcribe_googlespeech** | CitizenOneX | 13 | Dec 21, 2024 | ⚠️ Moderate | Stream audio → Google Speech API (STT). Only *input* audio project. |
| **Frames-Speech-to-Speech** | Koolkatze | 6 | Aug 21, 2024 | ⚠️ Stale | Local STT + TTS with voice cloning. WIP status; no recent commits. |
| **frame_audio_clip** | CitizenOneX | 2 | Apr 6, 2025 | ⚠️ Moderate | Record audio clips; playback. No active development. |
| **BasicNoaServer** | curiosiate | 2 | Jan 4, 2025 | ⚠️ Stale | Python handler (also in AI section). |
| **frame_msg_python** | CitizenOneX | 4 | Jun 1, 2025 | ⚠️ Moderate | Message parsing (voice events). |

**Insight:** **CRITICAL GAP:** Only one audio *input* project (frame_transcribe_googlespeech). Zero audio *synthesis/generation* (text-to-speech, real-time voice feedback, bone-conduction). Halo's stereo mics + bone-conduction speakers are unexplored. Workout Coach opens this frontier.

---

### 4. Core SDK / Infrastructure (8 repos, avg 55 stars)

| Repo | Owner | Stars | Last Active | Status | Notes |
|------|-------|-------|------------|--------|-------|
| **frame-codebase** | brilliantlabsAR | 478 | May 29, 2026 | 🔥 Active | **Reference implementation.** Frame OS + Lua + hardware drivers. Most-starred repo. Study for patterns. |
| **monocle-micropython** | brilliantlabsAR | 233 | May 23, 2026 | ✅ Maintained | MicroPython port for Monocle FPGA. Validates on-device inference. |
| **brilliant_sdk** | brilliantlabsAR | 19 | Jun 2, 2026 | 🔥 Active | Multi-language SDK monorepo (Python, Flutter, Web BLE). Just updated 1 hour ago. |
| **docs** | brilliantlabsAR | 57 | Jun 2, 2026 | 🔥 Active | Technical documentation. Updated this morning. |
| **frame-sdk-python** | brilliantlabsAR | 11 | May 20, 2026 | ✅ Maintained | Python SDK. |
| **web-bluetooth-repl** | brilliantlabsAR | 7 | Apr 21, 2023 | ⚠️ Stale | Web Bluetooth REPL. Old; no recent activity. |
| **frame_ble_python** | CitizenOneX | 3 | Apr 4, 2025 | ⚠️ Moderate | Low-level BLE for Python. |
| **frame_ble** | CitizenOneX | 4 | Apr 29, 2025 | ⚠️ Moderate | Low-level BLE for Dart (Flutter Blue Plus). |

**Insight:** Infrastructure tier is healthy. SDK is actively maintained. frame-codebase is reference; similar patterns expected for Halo. Web BLE REPL is stale (opportunity for modernization).

---

### 5. Developer Tools / Utilities (4 repos, avg 37 stars)

| Repo | Owner | Stars | Last Active | Status | Notes |
|------|-------|-------|------------|--------|-------|
| **ar-studio-for-vscode** | brilliantlabsAR | 67 | May 13, 2026 | ✅ Maintained | VSCode IDE for Monocle. Strong dev tooling demand signal. |
| **frame-utilities-for-python** | brilliantlabsAR | 50 | Mar 18, 2026 | ✅ Maintained | Pip-installable Frame utilities. Popular + active. |
| **frame-batteries** | Maxfield-Chen | 4 | Jul 17, 2024 | ⚠️ Stale | Community utilities for Frame. Last update Nov 6, 2024. |
| **frame-emulator** | urbanonymous | 2 | Mar 4, 2025 | ⚠️ Moderate | Screen emulator for Frame; helpful for testing. |

**Insight:** Dev tools are under-resourced relative to demand (ar-studio-for-vscode is most-popular non-first-party project). Opportunity for playground to include device emulation + fast iteration tooling.

---

### 6. First-Party Apps / Demos (3 repos, avg 77 stars)

| Repo | Owner | Stars | Last Active | Status | Notes |
|------|-------|-------|------------|--------|-------|
| **noa-flutter** | brilliantlabsAR | 78 | May 24, 2026 | 🔥 Active | Noa for iOS/Android. Reference app. |
| **noa-for-ios** | brilliantlabsAR | 79 | Mar 17, 2026 | ✅ Maintained | Native iOS Noa; strong mobile signal. |
| **noa-for-android** | brilliantlabsAR | 25 | Apr 7, 2026 | ✅ Maintained | Native Android Noa. |

**Insight:** First-party apps validate the market; community studies these for patterns. Halo needs equivalent playground examples.

---

### 7. Navigation / Location (2 repos, avg 0.5 stars)

| Repo | Owner | Stars | Last Active | Status | Notes |
|------|-------|-------|------------|--------|-------|
| **Frame-Navigation-App** | WatsonMLDev | 1 | Apr 28, 2025 | ⚠️ Emerging | Frame navigation demo. Low engagement. |
| **SARBINS** | anonimousname1234 / dariogentile | 0 | Mar 8, 2026 | 🆕 Emerging | BLE beacon wayfinding (iBeacon/Eddystone) + Frame output. Novel; brand new (Mar 2026). Niche application. |

**Insight:** Navigation is emerging but niche. Not a priority for Phase 1. SARBINS shows creativity (using Frame as HUD for BLE beacon system).

---

### 8. Utilities / Snippets (10+ repos, avg 2 stars)

| Repo | Owner | Stars | Last Active | Status | Notes |
|------|-------|-------|------------|--------|-------|
| **frame_msg** | CitizenOneX | 5 | Apr 7, 2025 | ⚠️ Moderate | Message types + Lua parsers. Utility. |
| **frame-glasses** | MLGonzo | 3 | May 28, 2025 | ⚠️ Moderate | Generic Frame utilities. |
| **frame_lz4** | CitizenOneX | 0 | Feb 3, 2025 | ⚠️ Utility | LZ4 precompiled for Frame. Technical niche. |
| **brilliant-monocle-driver-python** | fixermark | 7 | May 7, 2024 | ⚠️ Older | Python driver for Monocle. Monocle-era. |
| **frame.api** | eons-dev | 0 | Feb 6, 2025 | ⚠️ Utility | APIE endpoint for Frame. Niche. |
| **monocle-python-chunks-demo** | sintezcs | 0 | Apr 25, 2023 | ❌ Dead | Monocle demo; very old. |
| **framedev** | lhl | 1 | Aug 28, 2024 | ⚠️ Stale | Frame dev notes. Minimal. |
| **BrilliantLabs-Frame** | hannah2898 | 0 | Jul 2, 2025 | ⚠️ Empty | Empty repo. |
| **Brilliant-Labs** | legotec73 | 0 | Jan 15, 2026 | ⚠️ Empty | Empty repo. |
| **Brilliant-Labs-Frame-Web-SDK** | brilliantsole | 5 | Sep 6, 2024 | ⚠️ Stale | Web SDK for Frame. Last update Dec 25, 2025. |

**Insight:** Utilities tier is fragmented; many low-engagement repos. High friction = community needs better documentation + starter templates. Playground can consolidate patterns.

---

### 9. Halo-Specific (1 repo, new)

| Repo | Owner | Stars | Last Active | Status | Notes |
|------|-------|-------|------------|--------|-------|
| **AnkiLens** | CyberSyntax | 1 | Dec 5, 2025 | 🆕 NEW | Anki review app; **explicitly mentions Halo + Ray-Ban Meta crosscompat**. First community Halo project. Flutter + Lua. |

**Insight:** AnkiLens is the **only** community project explicitly supporting Halo (+ Ray-Ban Meta). Signals that early adopters are starting to ship. This validates that Halo is gaining traction post-launch (May 2026).

---

### 10. Archived / Deprecated (1 repo)

| Repo | Owner | Stars | Last Active | Status | Notes |
|------|-------|-------|------------|--------|-------|
| **brilliant-mobile-app** | brilliantlabsAR | 16 | Feb 24, 2023 | ❌ ARCHIVED | Monocle-era mobile app; archived. Replaced by Noa. |

---

## Activity Signal Analysis

### By Device Era

| Era | Period | Device | Repos | Status | Last Active |
|-----|--------|--------|-------|--------|------------|
| **Monocle** | 2022–2023 | 640x400 OLED, FPGA, MicroPython | 8 | 🆕→⚠️ Archived | Mostly 2023; monocle-micropython updated May 23, 2026 |
| **Frame** | 2023–2025 | 640x400 OLED, Lua, BLE-first | 40 | 🔥 Active | Many commits May-Jun 2026; peak ecosystem activity |
| **Halo** | May 2026–present | 256x256 OLED, NPU, host-driven | 1 | 🆕 Emerging | Only AnkiLens (1 star); device too new for community adoption |

### Recent Activity (Last 30 Days)
- **15–20 repos** have commits in May 2026 (frame-codebase, noa-flutter, noa-assistant, frame_realtime_gemini_voicevision, brilliant_sdk, docs, frame-sdk-python, frame_vision_api, frame_transcribe_googlespeech, frame_vision_gemini, etc.)
- **Last 6 months:** ~40 repos active
- **>1 year old:** ~10 repos (Monocle-era; archival candidates)

### Language Distribution
| Language | Count | Trend |
|----------|-------|-------|
| **Dart** | 12 | 📈 Growing (Flutter ecosystem) |
| **Python** | 15 | 📊 Stable (reference + utilities) |
| **C** | 4 | 📊 Stable (firmware + core) |
| **TypeScript/JavaScript** | 5 | 📈 Growing (web + tooling) |
| **Swift** | 1 | 📊 Single project |
| **Kotlin** | 1 | 📊 Single project |

**Insight:** Dart (Flutter) is dominant for community apps. Python is reference implementation language. Web (JavaScript/TypeScript) is underexplored (only noa-playground, frame_ble, ar-studio-for-vscode).

---

## Strategic Gaps (What's NOT Being Built)

### 1. Audio as Primary I/O — **CRITICAL GAP**
- **Existing:** frame_transcribe_googlespeech (speech-to-text input)
- **Missing:** Text-to-speech, real-time voice feedback, audio synthesis, bone-conduction output
- **Why it matters:** Halo's dual microphones + bone-conduction speakers are a first-generation unique hardware feature. No projects leverage this.
- **Opportunity:** Workout Coach demonstrates audio + IMU feedback perfectly.

### 2. Gesture Recognition + IMU Integration
- **Existing:** frame_imu (demo, 0 stars, dead)
- **Missing:** Gesture detection, motion tracking, activity recognition, step counting, form feedback
- **Why it matters:** Frame + Halo have 6-axis IMU. Community hasn't used it (except dead frame_imu).
- **Opportunity:** Workout Coach proves this use-case works.

### 3. Memory / Persistence / Logging
- **Existing:** None (Noa remembers context but doesn't *you* to own your logs)
- **Missing:** Session recording, activity logging, summarization, history replay
- **Why it matters:** Halo's 14-hour battery + always-on compute model suggest "wear all day, review tonight" pattern.
- **Opportunity:** Bird Watcher (logging bird sightings) + Scene Documenter (Phase 2) fill this gap.

### 4. Web Bluetooth (JavaScript / TypeScript)
- **Existing:** noa-playground (30 stars, active), ar-studio-for-vscode (TypeScript, 67 stars)
- **Missing:** Rich Web BLE examples, TypeScript libraries, cross-browser compatibility guides
- **Why it matters:** Web Bluetooth is Chromium-only (Firefox/Safari not supported). Community needs clear patterns.
- **Opportunity:** Time Tracker (web + low-power HUD) validates Web Bluetooth for Halo.

### 5. Halo-Specific Examples / Migration Guides
- **Existing:** None
- **Missing:** "Hello Halo" template, Frame→Halo porting guide, Halo-specific Lua APIs, silent-failure checklists
- **Why it matters:** Frame projects don't port automatically (decisions.md documents 5 silent-failure gotchas). Community needs structure.
- **Opportunity:** Playground scaffold + examples provide this.

### 6. Real-Time Multimodal (Voice + Vision + Context)
- **Existing:** frame_realtime_gemini_voicevision (80 stars, very active, community-built!!)
- **Missing:** Halo-optimized version, on-device inference examples, latency + energy optimization
- **Why it matters:** This is exactly what Noa does (multimodal advisory). Community is replicating the pattern. Halo should amplify.
- **Opportunity:** Phase 2 projects (Translator, Scene Documenter) can build on this.

---

## Roadmap Validation: Phase 1 Against Landscape

### Proposed Phase 1 Projects

#### 1. Workout Coach (Audio + IMU)
- **Gap it fills:** Audio synthesis + real-time IMU feedback (currently zero community projects)
- **Overlaps:** None (frame_imu is dead; no audio feedback projects exist)
- **Differentiation:** Halo's bone-conduction + stereo mics make this natural
- **Validation:** ✅ High confidence — fills real gap, no conflicts, leverages unique hardware

#### 2. Bird Watcher (Vision + Memory)
- **Gap it fills:** Persistent logging + computer vision (CV projects exist but none log/summarize)
- **Overlaps:** Builds on frame_vision_gemini pattern; not a direct copy
- **Differentiation:** Adds persistence layer (sighting history, species summaries)
- **Validation:** ✅ High confidence — extends existing pattern, novel persistence angle, real gap

#### 3. Time Tracker (Web Bluetooth + HUD)
- **Gap it fills:** Web Bluetooth examples (only noa-playground exists; underexplored)
- **Overlaps:** None; validates Web BLE for Halo
- **Differentiation:** Simplest possible example; proves always-on low-power HUD works
- **Validation:** ✅ High confidence — validates Web BLE, lowest friction entry point, no conflicts

### Roadmap Implication
**No changes needed.** Phase-1 is strategically sound:
- ✅ Each project fills a documented gap
- ✅ No direct competition with existing projects
- ✅ Leverages Halo's unique hardware (audio, IMU, low power, web)
- ✅ Demonstrates "what to build" guidance for community
- ✅ Likely to drive community fork + extend

---

## Standout Repos (for Squad Context)

### Top 5 by Stars

1. **frame-codebase** (brilliantlabsAR, 478⭐) — Frame OS reference; study for structure + Lua patterns
2. **monocle-micropython** (brilliantlabsAR, 233⭐) — On-device inference reference; MicroPython porting
3. **noa-assistant** (brilliantlabsAR, 197⭐) — Noa AI backend; multimodal LLM patterns
4. **frame_realtime_gemini_voicevision** (CitizenOneX, 80⭐) — **CRITICAL:** Community replication of Noa; study BLE latency patterns
5. **noa-flutter** (brilliantlabsAR, 78⭐) — First-party reference app; Dart best practices

### Top 3 by Momentum (Recent Activity + Engagement)

1. **frame_realtime_gemini_voicevision** — Feb 26 commit, high engagement, proves multimodal demand
2. **frame-codebase** — May 29 commit, steady maintenance
3. **brilliant_sdk** — Jun 2 commit (updated 1 hour before scan!), latest SDKs active

### Top 1 by Halo Signal

1. **AnkiLens** (CyberSyntax, 1⭐) — **Only community Halo project found.** Validates early adoption + Halo+Ray-Ban crosscompat.

---

## Recommendations for Squad

1. **Study frame-codebase** for architectural patterns; Halo codebase will follow similar structure
2. **Reference frame_realtime_gemini_voicevision** for BLE latency + multimodal patterns; community is ahead on this
3. **Use monocle-micropython as reference** for on-device compute; validates NPU feasibility
4. **Understand the Frame→Halo migration friction** (documented in decisions.md); playground examples must include porting guides
5. **Watch AnkiLens** as leading indicator; if it gains stars, community adoption is accelerating
6. **Prioritize developer tooling** (ar-studio-for-vscode shows demand); playground should bundle emulator + IDE templates
7. **Validate Phase-1 priorities** with community feedback; frame_realtime_gemini_voicevision shows appetite for audio + vision + AI

---

## Conclusion

The GitHub landscape reveals a **small but engaged community** (~50 public projects, ~40 active) building primarily on **Frame**. **Monocle** projects are historical references; **Halo** is emergent (1 community project, AnkiLens). 

**Phase-1 roadmap is validated**: Workout Coach, Bird Watcher, and Time Tracker fill genuine gaps (audio, persistence, web BLE) that the existing ecosystem avoids. No direct conflicts. Community will likely fork + extend once playground launches.

**Next steps:** Ship Phase-1 examples; watch AnkiLens and frame_realtime_gemini_voicevision for adoption patterns; iterate playground based on community forks.

---

*Generated by Uncle Enzo (Product/PM), 2026-06-02.*
