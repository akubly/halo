# Archive: NG Learnings (Pre-2026-06-02)

Compressed factual learnings from SDK audit and community ecosystem review. 8 breaking changes, 5 silent failure gotchas documented separately in decisions.md.

## SDK Lineage (Monocle → Frame → Halo)
**Monocle:** MicroPython on-device (not Lua), AR Studio, custom BLE. Legacy; end-of-life.
**Frame:** Host app + Lua 5.3 on-device (identical to Halo), `frame-ble` + `frame-msg`, Python/Flutter. Maintained but superseded.
**Halo:** Host app + Lua 5.3 on-device, `brilliant-ble` + `brilliant-msg` (rebranded), Python/Flutter/Web Bluetooth. Active development.

## Breaking Changes (Documented)
1. Package/class renames (FrameBle→BrilliantBle, FrameMsg→BrilliantMsg)
2. Lua `data.lua` refactor (parsers table removed; manual dispatch now required)
3. IMU data type (int16 raw → float32 calibrated; wire format doubled)
4. TxSprite binary format incompatibility (compressed flag inserted)
5. TxTextSpriteBlock API (text in constructor → `.create_text_sprites()` method)
6. Device type detection enum (BrilliantDeviceType auto-detection at connection)
7. Halo-only methods (send_audio, send_remove_signal)
8. **Silent failure:** Halo display power-save default ON (Frame was OFF) — apps appear broken if power_save(false) not called

## SDK Gotchas Surfaced by Community
1. REPL echo interference — Monocle workaround: Ctrl-A/Ctrl-D framing
2. File size explosion — 128-char filename limit; chunking framework needed
3. Bluetooth MTU fragmentation — manual reassembly painful; SDKs abstract poorly
4. Undocumented hardware behavior — touch callbacks not in early docs; community reverse-engineered

## Community Ecosystem & Adoption Patterns
**Distribution:** ~12 Monocle apps (archived/inactive), ~5 Monocle libraries, ~1 Frame/Halo library (brilliant_ble pub.dev), no published Frame/Halo apps yet.
**SDK-as-intended vs. Reality:** Community goes BLE-direct for flexibility; invents missing abstractions (chunk loaders, vector graphics lib vgrs).
**Multi-language bindings:** Node.js, Go, unofficial Flutter predate/duplicate official SDKs.

## Lua On-Device Patterns
- Event loop architecture (host-driven)
- Custom data serialization (domain-specific message protocols)
- Minimal on-device logic (<500 lines); complex processing on host
- Device acts as sensor hub + display controller

## Reusable Community Libraries
- `fixermark/brilliant-monocle-driver-python` — Raw UART BLE handling
- `CitizenOneX/frame_examples_python` — Essential Frame→Halo migration template
- `vgrs` — Vector graphics format + Lua rasterizer
- `noa-flutter` (official) — Primary SDK reference for device-aware branching

---

## Turn 3 Summary (2026-06-02T06:57Z) — SDK Rough Edges Inventory

Six architectural SDK gaps identified through community Monocle + Frame projects:

1. **BLE-Direct Fallback** — Developers bypass official SDKs (e.g., `brilliant-monocle-driver-python` uses raw UART over BLE).
2. **Large File Upload Chunking** — Monocle filesystem limits spawned `monocle-python-chunks-demo`; no SDK abstraction.
3. **Custom Graphics Pipelines** — `vgrs` library (community vector graphics) because SDK primitives (text/bitmap) insufficient.
4. **Multi-Language SDK Redundancy** — Node.js, Go, unofficial Flutter bindings predate official SDKs; community hedges vendor lock-in.
5. **MTU Fragmentation** — Every community library implements own packet reassembly; `brilliant-msg` doesn't fully hide abstraction.
6. **Undocumented Hardware Behavior** — Touch event callbacks (Monocle), button behavior, display power-save all reverse-engineered by community.

**Recommendations:** Document BLE-direct fallback, add file upload streaming (`upload_lua_file_chunked()`), provide vector graphics optional layer, expand official SDK bindings (Rust/C#), audit Halo Lua API docs for undocumented behaviors.

**Context:** ~18 Monocle projects (0 Halo yet). Noa (official) only reference. Community libraries (e.g., python-chunks-demo) are de facto standards.

---

*See `.squad/decisions/decisions.md` for full decision entry.*
