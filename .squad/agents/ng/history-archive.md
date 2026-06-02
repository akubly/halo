# NG Appended Turn 3 Summary (2026-06-02T06:57Z) — SDK Rough Edges Inventory

**Append #3 — Community-Discovered SDK Rough Edges & Workarounds (Round 3)**

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
