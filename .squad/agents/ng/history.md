# Project Context

- **Owner:** Aaron Kubly
- **Project:** halo — mono-repo playground for authoring apps on Halo smart glasses using the Brilliant SDK
- **Target device:** Brilliant Halo (BLE peripheral, Lua 5.3 VM on-device, camera/mic/speaker/display)
- **SDK surfaces:** Python (Mac/Linux/Windows), Flutter (iOS/Android), Web Bluetooth (Chromium)
- **SDK repo:** https://github.com/brilliantlabsAR/brilliant_sdk
- **Docs root:** https://docs.brilliant.xyz/halo/
- **Created:** 2026-06-01

## Role: NG (SDK Quality & Developer Experience)

**Focus:** SDK reliability, API completeness, developer friction points, cross-platform consistency.

**Previous Sessions:**
- Turn 1 (2026-06-01): SDK lineage audit (Monocle → Frame → Halo). Documented 8 breaking changes, deprecated APIs, capability gaps.
- Turn 2 (2026-06-01): Migration patterns & compatibility. Frame vs. Halo hardware differences. Web Bluetooth Chromium-only constraint.
- Turn 3 (2026-06-02): Community-discovered SDK rough edges inventory. Six architectural gaps, workaround patterns, recommendations for upstream SDK fixes. See `.squad/decisions/decisions.md` for full decision entry.

**Archived (2026-06-02):** Appended turn 3 summary to `.squad/agents/ng/history-archive.md`.

---

## Current Session: Ready for new tasks

## SDK Context (from Turn 1)

### Monocle (1st gen, legacy)
- **Model:** AR Studio (VSCode extension) + MicroPython on-device (not Lua)
- **SDK shape:** MicroPython directly on-device; no host SDK for mobile/desktop (only WebREPL)
- **BLE:** Custom implementation (no public specs documented)
- **Maintenance:** Legacy; Monocle docs show no SDK in active development, only VSCode AR Studio + WebREPL reference
- **Deprecation status:** Monocle hardware end-of-life; SDK not migrated to Brilliant SDK naming

### Frame (2nd gen, still maintained)
- **Model:** Host app + Lua 5.3 event loop on-device
- **SDK shape:** Two-layer:
  - Low-level: `frame-ble` (Bleak-based, Lua REPL, custom data callbacks)
  - High-level: `frame-msg` (richly-typed messages: TxSprite, RxPhoto, RxAudio, RxIMU)
- **Platforms:** Python (desktop), Flutter (iOS/Android); no Web Bluetooth
- **BLE Services:** Identical to Halo spec; Frame doesn't have AUDIO TX characteristic (no speaker)
- **Lua API:** Double-buffered display (`frame.display.show()` required); IMU tap input (no button)
- **Package names (pre-rebranding):** `frame-ble`, `frame-msg`, `simple_frame_app`
- **Maintenance status:** Active but superseded by Halo SDK; docs state "new projects should use updated SDK"
- **Legacy SDKs:** `frame-sdk` (PyPI), `frame_sdk` (pub.dev), `frameutils` noted as "legacy but functional"

### Halo (3rd gen, current focus)
- **Model:** Host app + Lua 5.3 event loop on-device (identical to Frame architecture)
- **SDK shape:** Three-layer (Python, Flutter, Web Bluetooth):
  - Low-level: `brilliant-ble` (Bleak, flutter_blue_plus, Web Bluetooth API respectively)
  - High-level: `brilliant-msg` (same message types as Frame + Halo-specific: RxClick, CircularTextLayout, AUDIO TX)
  - Scaffolding: `simple_brilliant_app` (Flutter only; device-aware display init)
- **Platforms:** Python (Mac/Linux/Windows), Flutter (iOS/Android), Web Bluetooth (Chromium only)
- **BLE Services:** Frame services + Halo-specific AUDIO TX characteristic + MCU-Boot OTA
- **Lua API:** Single-write display (no `show()` required); button input (no IMU tap); speaker/mic LC3 support; libmpix camera pipeline
- **Package names (rebranded):** `brilliant-ble`, `brilliant-msg`, `simple_brilliant_app`, `brilliant_sdk` (meta)
- **Maintenance status:** Actively developed; all migration guides available; Monocle/Frame treated as legacy

### Community Ecosystem & SDK Adoption Patterns (2026-06-01)

**Ecosystem Health: Mixed — Legacy Monocle projects dominate; Frame/Halo projects emerging**
- **Project distribution:** ~12 Monocle apps, ~5 Monocle libraries; ~1 Frame/Halo library (brilliant_ble pub.dev); no published Frame/Halo apps yet
- **Community maturity:** Early-stage; Monocle community active but deprecated; Frame/Halo uptake just starting
- **Maintenance status:** Monocle projects mostly archived/inactive (VSCode AR Studio community); Noa (official) is primary Frame reference implementation

**SDK-as-Intended vs. Reality: Community goes BLE-direct for flexibility, invents missing abstractions**
1. **Direct BLE adoption:** Monocle developers frequently bypass MicroPython wrapper (e.g., `brilliant-monocle-driver-python` implements raw UART over BLE + Ctrl-C/Ctrl-A/Ctrl-D handshake to avoid REPL echo). **Pattern:** When SDK feels limited, BLE-direct is more reliable than wrapper abstractions.
2. **Missing abstractions trigger workarounds:** File size limitations (128-char filename limit on Monocle) spawned `monocle-python-chunks-demo` — demonstrates dynamic chunk loading. **Pattern:** SDK doesn't support large Lua file uploads; community adds loader layer.
3. **Vector graphics library (vgrs):** Community built custom 2D graphics format + rasterizer for Monocle display because standard sprite rendering was limiting. **Pattern:** SDK primitives (text, bitmap) insufficient for complex UI; teams implement custom rendering pipelines.
4. **Multi-language bindings:** Node.js (`monocle-node-cli`), Go (`monocle` by floren), unofficial Flutter `brilliant_ble` (Uma Shankar) all predate/duplicate official SDKs. **Pattern:** Developers don't trust single-vendor SDK; hedge with alternative language bindings.

**Concrete Gotchas Surfaced by Community:**
1. **REPL echo interference:** Monocle's MicroPython REPL auto-echoes commands. Community workaround: wrap commands in Ctrl-A (start of heading) + Ctrl-D (end of transmission) to disable echo. **Impact:** Direct Lua execution fragile; wrapper abstractions needed.
2. **File size explosion:** Monocle device filesystem doesn't support >128-char filenames. Workaround: split large scripts into sub-modules (l1, l2, l3). **Impact:** Monolithic Lua apps don't port; chunking framework needed.
3. **Bluetooth MTU fragmentation:** Community libraries (Node.js, Python, Go) all implement manual packet reassembly; even official SDKs abstract this poorly. **Pattern:** MTU handling is a universal pain point; SDKs don't fully hide complexity.
4. **Touch event callback design (Monocle):** Community had to reverse-engineer touch event handling (callback registration via separate BLE writes). Not documented in early SDKs. **Pattern:** Hardware-level behavior not always obvious; community-sourced docs fill gaps.

**Reusable Community Libraries Worth Adopting:**
- `brilliant-monocle-driver-python` (fixermark): Raw UART BLE handling; teaches MTU + REPL control flow
- `vgrs` (sathibault): Vector graphics format + Lua rasterizer; could inspire Halo custom display rendering
- Chunk loader pattern (sintezcs): Applicable to Frame/Halo if Lua script size becomes limiting
- Noa Flutter app (official): **Primary reference for Frame + (now) Halo SDK usage**; shows device-aware branching, camera integration, streaming audio

**Lua On-Device Patterns Observed:**
- **Event loop architecture:** Community apps all follow host-event-loop pattern (not device-side state machine); Noa uses reactive message handling
- **Custom data serialization:** Projects implement domain-specific message protocols (e.g., telemetry batching, image chunking) on top of SDK's TxSprite/RxPhoto abstractions
- **Minimal on-device logic:** Lua scripts typically <500 lines; complex processing done on host. **Pattern:** Device acts as sensor hub + display controller, not application server.

### Learnings

**1. Package & Class Renames (Code-level)**
- Python: `FrameBle` → `BrilliantBle`, `FrameMsg` → `BrilliantMsg` (all message types `Tx*/Rx*` unchanged)
- Flutter: Package renames only (`frame_ble` → `brilliant_ble`); class names already used `Brilliant*` prefix
- Web: `FrameBle` → `BrilliantBle`, `FrameMsg` → `BrilliantMsg`
- Impact: Import statements must be updated; all examples from Frame SDK docs won't work as-is

**2. Lua `data.lua` Event Loop Refactor (CRITICAL)**
- **Old (Frame):** `data.parsers` table + global `data.app_data` dict + auto-parser dispatch
- **New (Halo/Frame+):** `data.process_raw_items()` returns ordered list of `{flag, raw_bytes}` pairs; caller manually dispatches
- **Removed APIs:** `data.parsers`, `data.app_data`, `data.app_data_block` — any reference errors at runtime
- **Impact:** Every existing `frame_app.lua` MUST be rewritten; migration guide shows before/after patterns
- **Benefit:** Guaranteed message arrival order + ACK-based receiver-paced flow control (`await_data=True` on host)

**3. IMU Data Type Change (struct-level)**
- **Old (Frame):** `RxIMU` packed 6 × `int16` (raw sensor counts)
- **New (Halo/Frame+):** `RxIMU` packs 6 × `float32` (calibrated physical units: mg, µT)
- **Wire format:** Doubles payload size; unpacking code must change from `<6h` to `<6f`
- **Impact:** Host code reading IMU directly (not via SDK) breaks; SDK handles automatically

**4. TxSprite Wire Format (binary-incompatible)**
- **Old:** Header bytes [version, size_lo, size_hi, bpp, num_colors, ...]
- **New:** Header bytes [..., compressed (flag), bpp, num_colors, ...] — `compressed` flag inserted at offset 5
- **Impact:** Old sprites won't render on new firmware; all Lua libraries must be re-uploaded
- **Dev catch:** Mixing old `brilliant-msg` host library with new on-device Lua silently produces corrupted display

**5. TxTextSpriteBlock API Change (method-level)**
- **Old:** `TxTextSpriteBlock(text="Hello", ...)` — text in constructor
- **New:** `TxTextSpriteBlock(...)` then `.create_text_sprites("Hello")` → returns `list[TxSprite]` sent individually
- **Also renamed:** `max_display_rows` → `max_display_lines`
- **Impact:** Text rendering code must be refactored; web/Flutter examples don't work directly

**6. New: Device Type Detection (enum-based)**
- **Old:** No automatic detection; code assumed single device type
- **New:** `BrilliantDeviceType` enum (`HALO` / `FRAME` / `UNKNOWN`) detected at connection via AUDIO TX characteristic probe
- **Impact:** Host code can now branch on device type; multidevice apps possible without recompilation
- **Gotcha:** Frame SDKs also migrated to this pattern; old code must add type checks

**7. New: Halo-Only Methods (platform-specific)**
- Python/Web: `send_audio(data)` + `send_remove_signal()`
- Flutter: `audioTxChannel` getter + `sendAudio()` + `sendRemoveSignal()`
- Impact: Frame apps using these methods won't work; type-checking required

**8. Halo Display Power-Save Default (behavior change)**
- **Old (Frame):** Display starts enabled
- **New (Halo):** Display starts in power-save mode (disabled); must call `frame.display.power_save(false)`
- **Silent failure:** Draw calls don't error if display off; just don't render
- **Gotcha:** Porting Frame apps to Halo may appear broken if power_save not disabled

### Deprecated APIs (Don't Use on Halo)

**Frame SDKs vs. Brilliant SDK:** Frame SDK packages (`frame-ble`, `frame-msg`, `simple_frame_app`) are marked as legacy but functional. New code should use `brilliant-*` packages. Monocle SDK (MicroPython + VSCode AR Studio) is end-of-life; no migration path to Halo.

**Removed from `data.lua` library:**
- `data.parsers` — table for global parser registration (use manual dispatch instead)
- `data.app_data` — auto-populated message dict (use `process_raw_items()` iteration)
- `data.app_data_block` — keyed storage (use local variables or custom tables)

**Removed Lua display APIs (Halo only):**
- `frame.display.show()` — not needed on Halo (direct writes)

**Removed input APIs (Halo only):**
- `frame.imu.tap_callback()` — Halo uses button instead; tap detection removed

### Learnings
- Halo is a peripheral, not a standalone app platform — host apps drive logic, Halo runs a thin event loop.
- Lua 5.3 VM on-device; `main.lua` runs at wakeup; supports Lua 5.3 stdlib minus `io` and `os` libraries.
- Two-layer communication: (1) SDK layer (Python/Flutter/Web) handles BLE boilerplate; (2) Lua layer (via SDK) calls hardware APIs.
- Host-device pattern: large objects (sprites, audio, photos) serialized via `brilliant-msg` into multi-packet sequences, reassembled on-device.

### SDK Flavors (2026-06-01)
**Python (`halo-emulator` + `brilliant-msg` 6.0.0 + `brilliant-ble` 2.0.0)**
- Low-level: `brilliant-ble` (Bleak-based async connectivity, Lua REPL, custom data callbacks)
- High-level: `brilliant-msg` (richly-typed messages: TxSprite, RxPhoto, RxAudio, RxIMU, RxClick)
- Unique: `halo-emulator` (experimental) — full Lua 5.3 runtime, virtual 256×256 framebuffer, test harness (not on PyPI yet; clone SDK repo)
- Device detect: `BrilliantBle.type` post-connection returns `BrilliantDeviceType.HALO` / `FRAME` / `UNKNOWN`
- Audio: `send_audio(data)` writes LC3/PCM to speaker characteristic; receiver-paced ACK flow control via `send_data(await_data=True)`
- Source: https://docs.brilliant.xyz/halo/halo-sdk-python/

**Flutter (`brilliant-msg` 3.0.0 + `brilliant_ble` 4.0.0 + `simple_brilliant_app` 8.0.0)**
- Low-level: `brilliant_ble` (async connectivity, MTU 517 on Android, 2M PHY, high connection priority, bond creation)
- High-level: `brilliant_msg` (same message types as Python; TxTextPage with CircularTextLayout for Halo's 256×256 round display)
- Scaffolding: `simple_brilliant_app` 8.0.0 provides device-aware startup (Halo uses `frame.display.clear()`, Frame uses bitmap fill)
- Input: `FrameVisionAppState` mixin handles device differences (Halo: RxClick with ClickType enum; Frame: RxTap with tap count)
- Android Bluetooth: MTU 517, high priority, 2M PHY automatically negotiated; bond creation via `BrilliantDevice.type` check
- Source: https://docs.brilliant.xyz/halo/halo-sdk-flutter/

**Web Bluetooth (`brilliant-ble` 0.4.0 + `brilliant-msg` 1.1.0)**
- **CRITICAL CONSTRAINT:** Web Bluetooth only available in **Chromium-based browsers** (Chrome, Edge, Opera) on desktop/Android. **NOT** Firefox, Safari, or any non-Chromium.
- Low-level: `brilliant-ble` (browser Web Bluetooth API, device picker, type detection post-connect)
- High-level: `brilliant-msg` (same message types; Halo-specific: CircularTextLayout for round display, RxClick button events)
- Browser support: Chromium only; calls `BrilliantBle.connect()` to open browser device picker (pairing handled by OS)
- Install: npm packages or import from CDN (`unpkg.com/brilliant-ble/...`)
- Source: https://docs.brilliant.xyz/halo/halo-sdk-webbluetooth/

**Lua API (Lua 5.3 on-device)**
- Display: `frame.display.text()`, `frame.display.bitmap()`, `frame.display.clear(0xRRGGBB)` — writes direct (no buffering/show() like Frame)
- Input: Button only (no IMU tap like Frame) — `frame.button.single()`, `frame.button.double()`, `frame.button.long()` callbacks
- Sensors: `frame.imu.direction()` returns {pitch, roll, heading}; `frame.imu.raw()` returns compass/accelerometer raw; tap detection
- Audio: `frame.speaker.start()` + stream PCM/LC3 to AUDIO TX characteristic; `frame.microphone.start()` + read + `bluetooth.send()` to host
- Camera: `frame.camera.capture()` → `frame.camera.image_ready()` → `frame.camera.read(mtu)` in loop + `frame.bluetooth.send()` to host
- Power: `frame.sleep()` (deep, ~10µs standby), `frame.standby()` (BLE alive), `frame.light_sleep()`, `frame.ship_mode()` (ultra-low, hardware reset wakeup)
- Filesystem: LittleFS at `/lfs/`, `frame.file.open()`, read/write/close, `require()` loads modules from `/lfs/`
- System: `frame.get_eui()`, `frame.battery_level()`, `frame.battery_charging()`, constants: `HARDWARE_VERSION="halo"`, `FIRMWARE_VERSION`, `GIT_TAG`
- Compression: LZ4 decompression only (via `frame.lz4.decompress()`)
- Source: https://docs.brilliant.xyz/halo/halo-sdk-lua/

### BLE Spec Essentials (2026-06-01)
- Pairing: Halo auto-initiates pairing on SDK connect; requires host OS pairing acceptance. Named `Halo XX` (XX = 4th byte of EUI-48 MAC).
- Un-pairing: Press button 8s → LED flashes → pairing mode; host must also remove old bonding.
- **Halo Lua Service** (`7A230001-5475-A6A4-654C-8431F6AD49C4`):
  - **LUA TX** (`7A230002...`): Host→Halo Lua commands or raw data (prefix `0x01` for callbacks)
  - **LUA RX** (`7A230003...`): Halo→Host print output and `frame.bluetooth.send()` data
  - **AUDIO TX** (`7A230005...`): Host→Halo PCM/LC3 audio (bypasses Lua for low-latency speaker)
  - Camera/mic: NOT on dedicated characteristics; sent via `bluetooth.send()` on LUA RX
- Control bytes on LUA TX: `0x03` (CTRL+C, break), `0x04` (CTRL+D, reset/run main.lua), `0x05` (CTRL+E, remove main.lua), `0x06`–`0x07` (exit/clear filesystem)
- MTU: Up to 512 bytes negotiated; max payload = MTU − 1 byte
- Battery Service: Standard BLE `0x180F` with level characteristic `0x2A19`
- OTA Service: MCU-BOOT + SMP over `8D53DC1D-1DB7-4CD3-868B-8A527460AA84`
- Lua main loop: Once running, blocks REPL; raw data (0x01 prefix) still processed. Interrupt with break (0x03).
- Source: https://docs.brilliant.xyz/halo/halo-sdk-bluetooth-specs/

### SDK Installation Prerequisites
- **Python**: `pip install brilliant-ble brilliant-msg` or `uv add brilliant-ble brilliant-msg`; `halo-emulator` requires manual clone
- **Flutter**: `flutter pub add brilliant_sdk simple_brilliant_app`; requires flutter_blue_plus setup (iOS/Android config per package docs)
- **Web Bluetooth**: `npm install brilliant-ble brilliant-msg` or CDN import; Chromium only (no Safari/Firefox)
- **Lua**: No installation; built-in Lua 5.3 on-device; loaded via `require()` from `/lfs/`

### Frame vs. Halo Hardware Differences (Lua API Layer)
| Feature | Frame | Halo |
|---------|-------|------|
| Display size | 640×400 | 256×256 (round) |
| Display mode | Double-buffered (show() required) | Direct writes (no show()) |
| Color format | Named palette colors | 0xRRGGBB hex |
| Input | IMU tap | Button (single/double/long) |
| Audio output | — | Speaker (PCM/LC3) |
| Mic encoding | PCM only | PCM + LC3 |
| Camera processing | Fixed JPEG | libmpix pipeline (configurable) |
| Sleep modes | sleep() only | sleep/standby/light_sleep/ship_mode |
| Firmware update | Nordic DFU (frame.update()) | MCU-Boot/SMP over BLE |

### Key Capability Gaps to Plan For
- **Web Bluetooth is Chromium-only** — Safari/Firefox demos impossible; desktop browser tests must use Chromium.
- **Lua REPL ↔ Main Loop trade-off** — once app loop runs, no REPL; must use raw BLE data (0x01 prefix) + callbacks for host↔device comms.
- **No native iOS support beyond Flutter SDK** — Python/Web Bluetooth don't run on iOS; Frame SDKs available but may have gaps.
- **MTU negotiation platform-dependent** — Android: 517 bytes (guaranteed); desktop: varies; plan data chunking accordingly.
- **halo-emulator not on PyPI** — test development requires cloning brilliant_sdk repository; not ideal for CI/CD without vendoring.

### Documentation Sources
- Entry: https://docs.brilliant.xyz/halo/halo/
- SDK overview: https://docs.brilliant.xyz/halo/halo-sdk/
- Python SDK: https://docs.brilliant.xyz/halo/halo-sdk-python/
- Flutter SDK: https://docs.brilliant.xyz/halo/halo-sdk-flutter/
- Web Bluetooth SDK: https://docs.brilliant.xyz/halo/halo-sdk-webbluetooth/
- Lua API: https://docs.brilliant.xyz/halo/halo-sdk-lua/
- BLE Specs: https://docs.brilliant.xyz/halo/halo-sdk-bluetooth-specs/
