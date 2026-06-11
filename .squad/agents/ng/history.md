# NG Agent History — Summarized

**Role:** SDK Quality & Developer Experience (Aaron's @akubly playground project: Halo)

## Session Timeline

| Date | Session | Key Output |
|------|---------|-----------|
| 2026-06-01 | SDK Lineage Audit | 8 breaking changes (Monocle→Frame→Halo) documented; archived |
| 2026-06-02 | GitHub Community SDK Audit | 9 projects catalogued; CitizenOneX recommended; pre-existing history archived |
| 2026-06-02 | Ideation (2 passes) | 8 cross-pollinated SDK patterns identified |
| 2026-06-03 | User Stories (Themes 1–2) | 10 stories authored; 4 SDK gaps identified |
| 2026-06-08 | VESPER BLE Wire-Format | LE endianness, uint16 seq wraparound, opcode split (0x00–7F vs 0x80–FF), ACK cadence locked |
| 2026-06-09 | Week 1 Implementation | `host/familiar_protocol.py` + `host/main.py` + `device/main.lua` shipped; 54 tests pass |
| 2026-06-09 | Persona-Review Fix Wave | 16 findings fixed (52fbd39); 1 rejected (test churn), 1 escalated (hardware validation) |
| 2026-06-10 | Polish Wave + Week-2 Logging | 3 minors applied (a9a136e); Week-2 follow-ups documented |
| 2026-06-10 | Copilot PR Review Fix Wave | 3 comments addressed (e9c8455): bitmap fast-path fallback, inference import-guard fixture, docstring typo |

**Full session history archived in `.squad/agents/ng/history-archive.md` (2026-06-02).**

---

## Current Status: Week 1 COMPLETE

**Branch:** week1-synesthetic-familiar  
**Final Commit:** e9c8455 (Copilot PR review fixes)  
**Test Results:** 59 passed, 5 xfailed, 0 failed  
**Outcome:** host-side verified (59 passed / 5 xfailed); device render loop NOT yet hardware-validated — on-device bob/render unconfirmed (Week-2 action)

### Canonical Exports (Locked by Test Contract)
- `Mood` IntEnum: NEUTRAL=0, CALM=1, STRESSED=2, ATTENTION=3
- `seq_is_newer(received, last_accepted) → bool` (signed-16 delta dedup)
- `decode_familiar_update()`, `decode_familiar_ack()`, `decode_familiar_reset()` wire format per ARD §5.2

---

## Week-2 Follow-ups

1. **Cross-language wire-format conformance** — Promote golden vectors to language-neutral fixture
2. **Sequence-reset hardening** — Post-timeout accept only seq==0 for first packet
3. **Decoder-contract symmetry** — `decode_familiar_ack` return type refactor (test coordination with Juanita)
4. **[Aaron ACTION] Hardware validation** — Real device test of BLE, sprite render, bob, timeout, ACK

---

## Key Learnings

- **Seq wraparound:** signed-16 delta dedup; reset to 0xFFFF on timeout (allows 0x0000→accept on next packet)
- **Pcall-guard pattern:** wrap event-loop callbacks to prevent transient errors from freezing
- **dt clamping + modulo:** prevent animation teleporting on wall-clock jumps
- **Error propagation contract:** decode errors → return None; caller logs and drops
- **Transport seam:** injection > monkeypatching; MockTransport enables testing without hardware
- **Bitmap fast-path footgun:** a bare `return` inside an `if SPRITE_BITMAP_READY` guard causes the familiar to silently blank — the bitmap call was commented out but the early return was not. Fix: wrap the bitmap call in `pcall` AND gate the early return on a `drawn` flag set inside the pcall body. Critical: `pcall(function() --[[ comments ]] end)` returns `true` in Lua (empty function succeeds), so `if ok then return end` alone STILL blanks. The `drawn` flag must be set on the same line as the actual bitmap call so it stays false while that line is commented — only `if ok and drawn then return end` is safe.
- **Import-guard needs enforcing fixture:** an import guard that sets `_IMPORT_ERROR` but has no autouse fixture to call `pytest.fail()` means tests silently collect and then xfail via `NotImplementedError`, masking a genuinely missing/broken module. Pattern: always pair the try/except import block with an `@pytest.fixture(autouse=True)` that calls `pytest.fail(f"... {_IMPORT_ERROR}")` when the error is set. (See test_protocol.py for the canonical shape.)

---
