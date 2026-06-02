# Community SDK Wrappers, BLE Drivers, and Lua Libraries — GitHub Landscape
**Date:** 2026-06-02  
**Researcher:** Ng (SDK Engineer)  
**Scope:** Community implementations, third-party bindings, and unofficial extensions for Brilliant Labs SDK (Monocle, Frame, Halo)

---

## TL;DR Verdict

| Project | Type | Device | Language | Status | Recommendation |
|---------|------|--------|----------|--------|----------------|
| **uma-shankar-gupta/brilliant_ble** | BLE Wrapper | Monocle/Frame | Dart/Flutter | Active | **USE CAUTIOUSLY** — Pre-official; now superseded by official `brilliant_ble` pub.dev package; early work only; deprecated but historical value |
| **CitizenOneX/frame_ble (Flutter)** | BLE Driver | Frame | Dart/Flutter | Active | **MONITOR** — High-quality community implementation; framework-agnostic; reference for Frame pattern |
| **CitizenOneX/frame_ble_python** | BLE Driver | Frame | Python | Active | **MONITOR** — Clean Bleak-based Frame connectivity; complements official Python SDK well; migration path ready |
| **CitizenOneX/frame_examples_python** | Reference Apps | Frame | Python | Active | **USE** — Excellent suite of Frame example apps; teaches frame_ble + frame_msg integration; directly applicable to Halo migration |
| **caic-xyz/caic** | Container/DevTools | Halo (embedded) | Kotlin | Archived | **AVOID** — Not primarily a Halo SDK; contains embedded RxClick.kt + TxSprite.kt as test fixtures; not production-ready BLE binding |
| **floren/monocle** | BLE Library | Monocle | Go | Archived | **MONITOR** — Legacy Go tools; historical interest for understanding Monocle UART/REPL control flow; no Halo/Frame support |
| **brilliantsole/Brilliant-Labs-Frame-Web-SDK** | Web SDK | Frame | JavaScript | Stale | **AVOID** — Unofficial; minimal documentation; superseded by official brilliant-ble + brilliant-msg npm packages |
| **milesprovus/Monocle-Teleprompter** | Reference App | Monocle | Python | Active | **MONITOR** — Teleprompter use-case; teaches Google Slides API integration + Monocle REPL pattern; Monocle legacy only |
| **anonimousname1234/SARBINS** | Reference App | Frame | Kotlin | Active | **USE** — Corridor wayfinding + Frame output; demonstrates real-world sensor fusion + device I/O; Frame BLE pattern |
| **bitfeed-project/bitfeed** | Client App | Unknown | JavaScript | Active | **AVOID** — Not Brilliant SDK focused; TxSprite usage is in Bitcoin blockchain explorer; unrelated |

---

## Detailed Findings

### 1. Flutter/Dart Ecosystem

#### **uma-shankar-gupta/brilliant_ble** (Pre-rebranding Community Work)
- **Status:** Active on pub.dev (v0.0.3); no recent commits post-2024-12-09
- **What it is:** Dart wrapper around `flutter_blue_plus` with device abstractions for Monocle/Frame
- **Quality signals:**
  - Clean README with setup instructions (iOS/Android permissions)
  - Monocle support functional; Frame TODO at v0.0.3
  - Well-structured: `BrilliantBle.create()` async factory, callbacks for connect/disconnect/data
  - Tests: None visible in repo
- **Gotchas:**
  - Pre-dates official rebranding (still called `brilliant_ble` but predates official `brilliant_ble` pub.dev by Brilliant Labs)
  - Published before official Flutter SDK available; now fully superseded
  - No Frame RxPhoto/RxAudio/TxSprite integration
- **Verdict:** **USE CAUTIOUSLY** — Historical interest only. New projects should use official `brilliant_ble` + `simple_brilliant_app`.

#### **CitizenOneX/frame_ble** (Flutter, Official Adoption Path)
- **Status:** Active; updated 2025-12-26 (recently)
- **What it is:** Low-level Frame BLE connectivity library for Flutter using `flutter_blue_plus`
- **Quality signals:**
  - Clear features: scanning, connection, Lua command send, data upload/receive, OTA DFU
  - References official Frame SDK docs
  - Cross-references to `frame_msg` + `simple_frame_app`
  - Clean pub.dev publishing track
- **Gotchas:**
  - Frame-only (no Halo support, no AUDIO TX characteristic)
  - Likely EOL'd in favor of official brilliant_ble
  - No Halo-specific button/click handling
- **Verdict:** **MONITOR** — Framework-agnostic BLE pattern useful for understanding cross-SDK design. Reference for Frame API shape.

#### **CitizenOneX/simple_frame_app** (Reference Framework for Flutter)
- **Status:** Active; pub.dev package maintained
- **What it is:** High-level Flutter framework providing device-aware startup, message scaffolding, example apps
- **Related:** Likely migrated to `simple_brilliant_app` for Halo
- **Verdict:** **MONITOR** — Understand device-aware branching patterns.

---

### 2. Python Ecosystem

#### **CitizenOneX/frame_ble_python** (Pure Python BLE, Bleak-based)
- **Status:** Active; updated 2026-03-04
- **What it is:** Low-level Python Frame connectivity using Bleak (async BLE library)
- **Quality signals:**
  - Clean Bleak integration; familiar to anyone using Bleak
  - Send Lua commands with `await_print` flag (waits for REPL output)
  - Disconnection handling
  - README example works verbatim
- **Gotchas:**
  - Frame-only API (no Halo speaker/audio TX)
  - Now likely superseded by official `brilliant-ble` PyPI package
  - No message type abstractions (caller must handle TxSprite packing manually)
- **Verdict:** **MONITOR** — Bleak pattern reference; useful for understanding MTU/REPL flow control. Direct competitor to official `brilliant-ble`.

#### **CitizenOneX/frame_examples_python** (Demonstration Suite)
- **Status:** Active; updated 2026-02-02
- **What it is:** Suite of example Python programs for Frame using `frame-ble` + `frame-msg` packages
- **Quality signals:**
  - Collection of virtual environments (one per example)
  - Teaches `frame_ble` + `frame_msg` integration
  - Demonstrates sprites, audio, photos, IMU
- **Gotchas:**
  - Uses pre-Halo package names (`frame-ble`, `frame-msg`)
  - Many examples will silently fail on Halo (see migration gotchas in Ng history)
- **Verdict:** **USE** — Essential reference for Frame→Halo migration patterns. Before/after comparisons in migration guide should reference this repo.

---

### 3. Kotlin/JVM Ecosystem

#### **caic-xyz/caic** (Container Management, *Not* a Halo SDK)
- **Status:** Active; Go/Kotlin microservices framework
- **What it is:** Coding Agents in Containers — Docker-based multi-agent system
- **SDK Mention:** Contains `sdk/halo/src/main/kotlin/com/caic/halo/msg/RxClick.kt` + `TxSprite.kt`
  - These files appear to be **test fixtures or embedded protocol definitions**, not a real Halo SDK
  - RxClick.kt is ~60 lines; comment says "parse Halo button click events"
  - TxSprite.kt is ~15 lines; comment says "indexed-color sprite sent to the device"
  - Both are **incomplete stubs**, not functional implementations
- **Gotchas:**
  - Misleading; repo is NOT a Halo SDK despite SDK subdir
  - Files are likely copied from brilliant_sdk as reference; not maintained separately
  - No BLE connectivity, no Lua REPL, no device communication
- **Verdict:** **AVOID** — Not a functional SDK; files are static reference code only.

---

### 4. Go Ecosystem

#### **floren/monocle** (Legacy Go BLE Tools)
- **Status:** Archived; last activity 2024-10-23
- **What it is:** Go library + CLI tools for Monocle UART communication over BLE
- **Quality signals:**
  - Clean Go package interface (`NewMonocle()`, `ConnectToAny()`, `SendUartCommand()`)
  - Example clock app included (MicroPython REPL commands)
  - Battery life tester CLI tool
- **Gotchas:**
  - Monocle-only (legacy device; no Frame/Halo support)
  - UART handshake complexity (Ctrl-C interrupt, Ctrl-D reset) — patterns applicable to understanding BLE REPL flow control
  - No message type abstractions
- **Verdict:** **MONITOR** — Historical interest for REPL control flow patterns; not applicable to Frame/Halo.

---

### 5. JavaScript/Web Ecosystem

#### **brilliantsole/Brilliant-Labs-Frame-Web-SDK** (Unofficial Frame Web Binding)
- **Status:** Stale; minimal README
- **What it is:** Claimed to be web SDK for Frame; essentially undocumented
- **Quality signals:**
  - Exists on GitHub; pub version unknown
  - No examples, no tests visible
- **Gotchas:**
  - Predates official `brilliant-ble` npm package (Web Bluetooth)
  - Likely unmaintained
  - Would need to be completely re-evaluated against official brilliant-msg + brilliant-ble
- **Verdict:** **AVOID** — Superseded by official Web Bluetooth SDK. No value in community fork.

---

### 6. Reference Applications (Multi-Device)

#### **anonimousname1234/SARBINS** (Wayfinding + Frame Output)
- **Status:** Active; updated 2026-03-08
- **What it is:** Android Kotlin prototype for corridor wayfinding (iBeacon/Eddystone RSSI) with optional Frame smartglasses output
- **Quality signals:**
  - Real-world integration: BLE beacon scanning + sensor fusion + Frame I/O
  - Time-oriented nearest-beacon selection; hysteresis to prevent ping-pong
  - Demonstrates Frame as "heads-up display" for guidance
  - Two-list UI (targets + step-by-step guidance)
- **Gotchas:**
  - Frame-specific (no Halo, though Halo button would replace tap-to-skip)
  - Kotlin/Android-only (not generalizable to Python/Web)
  - May need Halo adaptations (button input, speaker audio for cues)
- **Verdict:** **USE** — Excellent reference for real-world Frame+host sensor fusion pattern. Study for Halo adaptation (e.g., audio guidance, button skip).

#### **milesprovus/Monocle-Teleprompter** (Google Slides → Monocle Display)
- **Status:** Active; updated recently
- **What it is:** Node.js + Python app; streams Google Slides speaker notes to Monocle display
- **Quality signals:**
  - Google OAuth 2.0 setup documented
  - REPL command generation for Monocle MicroPython
  - Touch pad navigation mapped to slide navigation
- **Gotchas:**
  - Monocle-only (legacy device)
  - Text length constraints (< 25 chars per line) — useful constraint for any text-on-glasses app
  - Requires VSCode AR Studio for device upload
- **Verdict:** **MONITOR** — Useful for understanding Monocle REPL pattern and Google API integration. Candidate for Halo port (uses button instead of touch pads, Lua instead of MicroPython).

---

## Community Library Search Results

### Lua Libraries (Generic)
- **actboy168/json.lua** (Pure Lua JSON library) — Useful for on-device JSON serialization if needed
- **kcwiki/lua-json** (Convert Lua tables ↔ JSON) — Same use-case
- Several other JSON parsers, JSONPATH engines, and schema validators exist

**Verdict for on-device Lua:** Standard library (io.*, os.*, etc.) is limited on Halo (io/os removed). JSON libraries are available but not specifically tailored to Halo's constrained memory. **Monitor if custom data protocols become bottleneck.**

---

## Brilliant Labs Official Ecosystem (For Context)

| Repo | Type | Status |
|------|------|--------|
| **brilliant_sdk** (monoreppo: python/, flutter/, webbluetooth/) | Master SDK | Active; daily updates |
| **docs** | Documentation | Active; mirrors code changes |
| **noa-flutter** | Reference App | Active; Halo + Frame showcase |
| **frame-codebase** | Device Firmware | Archived; Frame EOL |
| **frame-utilities-for-python** | Utilities | Active; convenience layer over frame-ble/frame-msg |
| **ar-studio-for-vscode** | IDE Plugin | Active; Monocle development |

---

## Patterns & Gotchas Summary

### What Community Implementations Got Right
1. **Clean async/await patterns** (CitizenOneX) — Flutter + Python async BLE is well-abstracted
2. **Device detection** (SARBINS) — Real-world apps branch on Halo vs. Frame
3. **Reference documentation** (frame_examples_python) — Clear before/after patterns for Frame→Halo migration

### What Community Implementations Got Wrong
1. **Incomplete frame_ble_python** — Stopped at low-level; no message abstractions (users pack TxSprite manually)
2. **Pre-rebranding bloat** (uma-shankar-gupta) — Package names and APIs changed; outdated bindings remain on pub.dev
3. **No active Halo support** (as of 2026-06-02) — Only one community repo (SARBINS) mentions Halo, and only for output

### Undocumented Gotchas in Community Code
- **MTU fragmentation:** All community BLE drivers must implement manual packet reassembly; SDK abstracts but doesn't hide the complexity
- **REPL echo handling:** Monocle projects discovered Ctrl-A/Ctrl-D handshake; Frame/Halo less documented
- **Sprite wire format:** Community code often reimplements TxSprite packing; format changed between Frame→Halo (compressed flag insertion)
- **Device type branching:** Community apps (SARBINS, early Frame apps) hardcoded device type; only recent apps use `BrilliantDeviceType` enum

---

## Recommendations

1. **Official SDK is the standard.** Do not use community wrappers for new Halo projects; use `brilliant-ble` + `brilliant-msg` + `simple_brilliant_app` (Flutter) or equivalents.

2. **Community reference apps are valuable.** Study CitizenOneX/frame_examples_python and anonimousname1234/SARBINS for patterns before designing Halo playground apps.

3. **Migration path is clear.** Frame→Halo examples (CitizenOneX) provide the before/after template. Use this for documentation.

4. **Lua library ecosystem is thin.** Community Lua libraries (JSON, etc.) exist but are not Halo-specific. If on-device complexity grows, consider vendoring standard libraries into halo/lua/ directory.

5. **No production-grade third-party Kotlin/Go/Rust SDKs exist yet.** Community interest is minimal. If non-Python/Flutter/Web targets are needed, decisions are: (A) official SDK maintainers add, (B) community initiative required, or (C) custom BLE implementation.

6. **Web Bluetooth is the gateway.** Official Web SDK (brilliant-ble + brilliant-msg npm) is the only browser option. Community forks add no value.

---

## Quality Signal Legend

| Signal | Meaning |
|--------|---------|
| **Active** | Recent commits (< 1 year); production-grade docs; active issue discussion |
| **Monitor** | Stable but slow updates; useful patterns; may diverge from official SDK over time |
| **Stale** | > 1 year without commits; docs outdated; community may have moved to official SDK |
| **Archived** | Explicitly marked archived or no commits > 2 years; historical interest only |
| **Tests** | Visible unit tests or integration tests in repo |
| **Docs** | README + inline docs; examples; setup guides |

