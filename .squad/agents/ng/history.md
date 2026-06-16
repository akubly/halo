# NG Agent History — Week 3 Focus (Archived Pre-Week-3 Context)

**Role:** SDK Quality & Device Lua Implementation (Aaron's @akubly playground project: Halo)

**Note:** Pre-Week-3 context (Week 1-2 implementation notes, detailed learnings, SDK gate investigations) moved to `history-archive.md` (2026-06-14 summarization). This file focuses on Week 3 work.

---

## Week 3 "It's Alive" — Cycle-1 Persona Review Fixes (2026-06-13)

Aaron approved all four persona-review findings for `device/main.lua`. Applied in a single pass; 262/262 host tests green after.

| ID | Severity | Fix summary |
|----|----------|-------------|
| B2 | BLOCKING | `tap_callback` double-tap now resets `state.last_seq = 0xFFFF` (sentinel: delta = `(0x0000 - 0xFFFF) & 0xFFFF = 1 → accept`). Without this, stale `last_seq` silently rejected first post-reset host packet. |
| I1 | IMPORTANT | `heap_fraction()` returns a compile-time constant (~2%); 80%/95% guards can never fire. Made inertness explicit with WARNING comments at both the function definition and the guard sites. Structure preserved for one-line firmware-swap. |
| I3 | IMPORTANT | `pre_attn_mood` could be stashed as 3 (ATTENTION), locking the overlay permanently open. Enforced underlying-mood domain `{0,1,2}` at two sites: `on_ble_data` (`clamp(mood_in, 0, 2)`) and IMU-peak trigger (`clamp(state.mood, 0, 2)`). |
| M1 | MINOR | Added explicit clamp locals (`mood_in`, `intensity_in`, `confidence_in`) at the BLE acceptance point, making the host trust boundary explicit rather than relying on scattered downstream fallbacks. Zero behavior change for valid inputs. |

**Key sentinel insight (B2):** Correctly chose `0xFFFF` (not guessing) by tracing `is_newer_seq`'s signed-16 delta math: `(0x0000 - 0xFFFF) & 0xFFFF = 1` which falls in `[1,32767] → accept`. This is the same sentinel already used by the timeout handler and startup state.

**I3 domain invariant:** ATTENTION is a transient overlay, never a peer underlying state.  `pre_attn_mood` must ∈ `{0,1,2}` at all times.  The two stash sites now enforce this via `clamp(..., 0, 2)`.

**M1 + I3 interaction:** `mood_in = clamp(msg.mood, 0, 3)` (M1) is computed first; I3 further narrows to `clamp(mood_in, 0, 2)` only when routing to `pre_attn_mood`.  Direct `state.mood` assignments allow mood=3 from the host (host-driven ATTENTION is valid).

**Decision note:** `.squad/decisions/inbox/ng-week3-review-fixes.md`

📌 Team update (2026-06-14T05:36:23Z): Juanita documented heap-guard observability gap as structural test (will fail when heap field added — surfaced for review); host bind-up complete; privacy audit APPROVED all surfaces — ready for ship — decided by Juanita, Raven

---

### Cycle 2 Re-Review (2026-06-14)

**Team decision:** All Cycle 1 findings (B2, I1, I3, M1) verified ADDRESSED in Cycle 2 re-review (Correctness, Skeptic, Architect panels). I1's inert guards correctly left in place (structure preserved for firmware-swap one-line change). Final: 265 tests passing.

**Ready for ship-to-pr:** Push branch `synesthetic-familiar/week3-its-alive`, open PR, request Copilot review, then cloud-review-cycle, then squash-merge.

**Phase-2 deferral:** Reset-epoch BLE-timing edge (LOW advisory from Skeptic).

---

### Cycle 2 Re-Review (2026-06-14)

**Team decision:** All Cycle 1 findings (B2, I1, I3, M1) verified ADDRESSED in Cycle 2 re-review (Correctness, Skeptic, Architect panels). I1's inert guards correctly left in place (structure preserved for firmware-swap one-line change). Final: 265 tests passing.

**Ready for ship-to-pr:** Push branch `synesthetic-familiar/week3-its-alive`, open PR, request Copilot review, then cloud-review-cycle, then squash-merge.

**Phase-2 deferral:** Reset-epoch BLE-timing edge (LOW advisory from Skeptic).

📌 Team update (2026-06-14T07:59:43Z): Phase-2 plan drafted (camera + cloud refinement) — pending Aaron approval. Decisions: Enzo (capability scope), Hiro (architecture). No code written. Affected: implementation lead (Ng), privacy review (Raven), docs (Librarian), testing (Juanita), infrastructure (Da5id).

---

## Week 4 "It Sees" — SDK Feasibility Gate (2026-06-14)

### Verdict: ⛔ CAMERA BLOCKED — CAMERA-I3 (LED indicator unavailable)

Full investigation complete. Week 4 camera scaffold NOT implemented. Phase-1 baseline: 265/265 tests passing, unchanged.

### SDK Findings

| Question | Answer |
|----------|--------|
| Triggered capture API? | **CONFIRMED** — `frame.camera.capture({quality="HIGH"})` + poll `frame.camera.image_ready()` + read with `frame.camera.read(mtu)` |
| JPEG format/size? | 640px resolution only; quality configurable (VERY_HIGH/HIGH/MEDIUM/LOW/VERY_LOW); typical 10–50KB |
| Recording-indicator LED (CAMERA-I3)? | **NOT AVAILABLE** — no `frame.led` or `frame.indicator` namespace in Halo SDK; white LED is firmware-managed (charging/pairing only); Lua cannot access it |
| BLE throughput for 10–40KB JPEG? | ~1fps viable (MTU up to 512B, ~30–50KB/s practical); architecture-draft estimate of 2–4s was pessimistic for BLE 5.0 (moot given I3 block) |

### CAMERA-I3 — Why It Blocks

The complete Halo Lua API (System, Time, File, Button, Bluetooth, IMU, Compression, Speaker, Microphone, Display, Camera + libmpix) has **no LED control surface**. `frame.camera.capture()` does not auto-activate any visible indicator. Workarounds rejected: display flash ≠ hardware LED (doesn't satisfy Raven's requirement); firmware patch = custom firmware (Ng charter: "custom firmware never").

### Bonus: On-Device Stats Path (Future Reference)

`frame.camera.mpix.get_stats()` returns luminance histogram + per-channel RGB averages after any capture. This could produce `visual_brightness` and a `visual_activity` proxy **without transmitting JPEG over BLE at all** — eliminating CAMERA-I1/I2/I6 concerns. CAMERA-I3 still applies (capture must occur regardless). If a future SDK adds `frame.led.*`, this stats-only path becomes the cleanest implementation.

### Week 4 Pivot

Camera blocked → Week 4 is cloud-refinement-only (Option C federated local refinement). Librarian owns inference.py + model_sync.py. No Ng code changes required this week.

**Decision file:** `.squad/decisions/inbox/ng-week4-camera-sdk.md`

**Key file paths:**
- Lua camera API: `docs.brilliant.xyz/halo/halo-sdk-lua/` §Camera + §Camera Image Processing (libmpix)
- BLE specs: `docs.brilliant.xyz/halo/halo-sdk-bluetooth-specs/`
- Phase-2 arch: `.squad/files/phase2-architecture-draft.md`
- Host sensors: `projects/synesthetic-familiar/host/sensors.py`
- Device Lua: `projects/synesthetic-familiar/device/main.lua`

---

📌 Team update (2026-06-15T05:37:29Z): Week-4 camera SDK gate resolved BLOCKED (CAMERA-I3); Librarian shipped Option-C cloud sync; Juanita delivered 53 new tests (299/319); Raven approved with 6 merge-blocking conditions. Phase-2 shipping cloud-refinement (model_sync.py); camera deferred Phase-3 — decided by Ng, Librarian, Juanita, Raven
