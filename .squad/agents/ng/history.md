# NG Agent History — Summarized

**Role:** SDK Quality & Device Lua Implementation (Aaron's @akubly playground project: Halo)

## Career Arc: Pre-Week-3 Context (Archived)

**Early research (2026-06-01 to 2026-06-03):** 8 breaking SDK changes (Monocle→Frame→Halo); 9 community projects catalogued (CitizenOneX); 8 cross-pollinated SDK patterns; 10 user stories authored; 4 SDK gaps identified. Full archive: `history-archive.md`.

**Week 1 (2026-06-08 to 2026-06-10):** BLE wire-format locked (LE endianness, seq wraparound, opcode split 0x00–7F vs 0x80–FF); familiar_protocol.py + host/main.py + device/main.lua shipped (54 tests); Persona-review + Copilot PR fix waves (16+3 findings).

**Week 2 (2026-06-12):** SDK gate investigation: Gate 1 (IMU) GO — API corrected from assumed `frame.imu.on_tap(n,cb)` to real `frame.imu.tap_callback(func)`, no N-count, Lua debounce 350ms. Gate 2 (heap) NO-GO — `frame.system` namespace absent, manual proxy fallback design. Gate 3 (sprite) GO — `frame.display.circle()` replaces Bresenham 8× call reduction.

## Week 3 "It's Alive" — Device Implementation (2026-06-13)

**All 4 ATTENTION visual tasks shipped:**

| Task | Details | Status |
|------|---------|--------|
| Jump Motion | `ATTENTION_JUMP_AMP_PX=4`, LAUNCH 60ms/SETTLE 120ms, ease_out_quad+ease_in_out_quad, applied as `render_y` offset | ✅ 188 tests |
| Eye Dilation | `ATTENTION_EYE_DILATE_PX=1`, two-pass morphological dilation (paint 8 neighbors of eye pixels), 11→19px, full 500ms hold | ✅ |
| Body Desaturation | Pre-existing in Wave-1 ATTENTION palette (0x1A1A1A/0x2E2E2E gray), added comments | ✅ |
| Mood Restoration | Pre-existing via `state.pre_attn_mood`, BLE updates route to pre_attn_mood during overlay, restored on expiry, no flicker | ✅ |

**State management:** Da5id's checklist proposed 3 new fields (`attention_active`, `attention_start_t`, `attention_last_t`); all covered by existing `state.attn_timer` countdown (single source of truth).

**Test status:** 188/190 pass; 2 failures in `TestFamiliarResetHostReaction` pre-existing (Y.T.'s host domain, unaffected by Lua).

**Decision record:** `ng-week3-attention-visuals.md` merged to decisions.md.

---

## Week-2 Implementation Notes

### Key file paths
- `projects/synesthetic-familiar/host/sensors.py` — SensorFrame, SensorStream, FakeSensorStream, SensorInitError
- `projects/synesthetic-familiar/host/main.py` — quantise_intensity, apply_intensity_jitter, run(transport, sensor_stream), Transport/MockTransport/BrilliantBleTransport
- `projects/synesthetic-familiar/host/inference.py` — owned by Librarian; main.py imports defensively
- `.squad/decisions/inbox/ng-week2-sensors-mainloop.md` — full decision record

### Sensor capture approach
- **Mic**: `sounddevice.InputStream` with `callback` pattern, 100ms blocks (block_size = sample_rate/10), float32 dtype. Rolling buffer = `np.zeros(sample_rate)` — exactly 1 second.
- **Buffer zeroing**: `_extract_frame()` copies buffer under `threading.Lock`, zeroes it immediately, then `del samples` after computation. Also zeroed in `stop()`. This satisfies privacy gate I7.
- **RMS**: `sqrt(mean(samples²)) / 0.707` (normalised to full-scale sine = 1.0), clamped to 1.0.
- **Pitch variance**: ZCR (zero-crossing rate) over 10 sub-frames → variance scaled by 0.01. No FFT per tick; low-latency.
- **Thread safety**: audio callback writes to buffer under `threading.Lock`; `_extract_frame` reads under the same lock.

### IMU SDK-gap handling
- `_IMURelay` class wraps the BLE characteristic subscription. Currently holds `imu_ok=False` because characteristic UUID is unconfirmed (ARD §10).
- Degradation path: `compute_mood()` is called with `imu_ok=False` → confidence ×0.7. Both-fail path (mic_ok=False AND imu_ok=False) sends NEUTRAL after 10s.
- **When to fix**: confirm characteristic UUID from Halo firmware; implement subscription in `_IMURelay.start()`; normalise accel ÷4.0g and rotation ÷500°/s.

### quantise/jitter placement
- **Gate 2 helpers live in `main.py`** (not inference.py, not protocol.py) per contract §3.
- `quantise_intensity(float) → {0,25,50,75,100}` with midpoint buckets at 0.125/0.375/0.625/0.875.
- `apply_intensity_jitter(int, rng=None) → int` clamped 0–100; injectable `random.Random` for deterministic tests.
- Pipeline: `compute_mood() → result.intensity (float) → quantise → jitter → encode_familiar_update`.
- Golden vectors test `encode_familiar_update` directly with pre-quantised values — unaffected.

### Confidence-hold timeout I2 location
- Lives in `run()` main loop, not in inference.py. `last_send_time` resets only on successfully sent frames (not gated/suppressed ones).

### Injectable clock pattern
- `run(transport, sensor_stream, *, clock=time.monotonic)` — Juanita can inject a fake clock for I2 + both-fail timeout tests without sleeping 30s/10s.

---

## Key Learnings

- **Seq wraparound:** signed-16 delta dedup; reset to 0xFFFF on timeout (allows 0x0000→accept on next packet)
- **Pcall-guard pattern:** wrap event-loop callbacks to prevent transient errors from freezing
- **dt clamping + modulo:** prevent animation teleporting on wall-clock jumps
- **Error propagation contract:** decode errors → return None; caller logs and drops
- **Transport seam:** injection > monkeypatching; MockTransport enables testing without hardware
- **Bitmap fast-path footgun:** a bare `return` inside an `if SPRITE_BITMAP_READY` guard causes the familiar to silently blank — the bitmap call was commented out but the early return was not. Fix: wrap the bitmap call in `pcall` AND gate the early return on a `drawn` flag set inside the pcall body. Critical: `pcall(function() --[[ comments ]] end)` returns `true` in Lua (empty function succeeds), so `if ok then return end` alone STILL blanks. The `drawn` flag must be set on the same line as the actual bitmap call so it stays false while that line is commented — only `if ok and drawn then return end` is safe.
- **Import-guard needs enforcing fixture:** an import guard that sets `_IMPORT_ERROR` but has no autouse fixture to call `pytest.fail()` means tests silently collect and then xfail via `NotImplementedError`, masking a genuinely missing/broken module. Pattern: always pair the try/except import block with an `@pytest.fixture(autouse=True)` that calls `pytest.fail(f"... {_IMPORT_ERROR}")` when the error is set. (See test_protocol.py for the canonical shape.)
- **Negative stddev validation gap:** `math.isfinite(v)` does NOT cover negative values — a negative stddev is finite. Always add `and v >= 0.0` explicitly when the domain is non-negative. Inline comments claiming a check is present are not a substitute for the actual guard. (Reviewer-rejection lockout: Juanita escalated, Ng fixed; commit 5d49a7f.)
- **Numpy snapshot zeroing:** `del samples` drops the reference but does NOT overwrite the memory — CPython's allocator may reuse the region before the GC collects it, leaving raw audio in freed memory. Always `samples[:] = 0.0` in-place immediately before `del` inside the finally block to satisfy I7 in-memory zeroing. Privacy comments must accurately describe ALL layers: in-buffer zero + snapshot zero + del. (cycle-2 review, commit 3bb96a3)

## Learnings

### Week 3 SDK Gate Investigation (2026-06-12)

**`frame.imu.tap_callback` — correct API name (not `frame.imu.on_tap`)**

The ARD and main.lua both assumed `frame.imu.on_tap(n, callback)` with a
built-in N-count discriminator. **This API does not exist.** The real API is
`frame.imu.tap_callback(func)` — confirmed by `halo_emulator/stubs/imu.py`
(SDK source, brilliantlabsAR/brilliant_sdk main branch). The callback fires
once per hardware tap; double-tap discrimination requires a Lua debounce
accumulator (count taps within ~350ms window). Interrupt-driven — not polling.

**IMU peak for ATTENTION trigger: polling only**

No `frame.on_imu_peak` primitive exists. ATTENTION-on-IMU-peak must be
implemented by reading `frame.imu.raw()` in the render loop and threshold-
checking `accel.z`. At 20fps the loop fires every 50ms — meets the ARD
≤50ms latency target. Not a new SDK gap; fits within existing render budget.

**`frame.system` namespace does not exist — heap API NO-GO**

`frame.system.get_heap_usage()` is not available. `frame.system` as a
sub-namespace does not exist in current Halo firmware or emulator. All system-
level functions live at the top-level `frame.*`: `sleep`, `battery_level`,
`reboot`, `wakeup_source`, etc. Heap monitoring requires the manual proxy
fallback (sprite rows + BLE MTU bytes as a pressure proxy). Thresholds stay
at 80%/95% per ARD. Gate flips to GO when `frame.system.get_heap_usage()`
appears in a firmware update — a hardware validation probe is documented in
`.squad/decisions/inbox/ng-week3-sdk-gates.md`.

**`frame.display.circle()` exists — Bresenham fallback in draw_halo_glow is redundant**

The emulator API listing confirms `frame.display.circle(cx, cy, r, color, filled)`.
The hand-rolled mid-point Bresenham in `draw_halo_glow()` was written as a
fallback for an unconfirmed API — it can be replaced with a single
`frame.display.circle()` call. Existing code is correct but ~8× more verbose.

**SDK architecture: tap events flow device→host via opcode 0x09**

The `tap.lua` stdlib module (device side) calls `frame.bluetooth.send(string.char(0x09))`
on each tap. `RxTap` on the host side aggregates taps within a 300ms window
to distinguish single vs. double. For VESPER's on-device FAMILIAR_RESET, we
bypass the host aggregation entirely — detect double-tap in Lua and send
the FAMILIAR_RESET opcode (0x01) directly, per the ARD decision (2026-06-08).

---

### Week 3 Implementation Learnings (2026-06-13)

**ATTENTION as overlay requires pre_attn_mood routing in on_ble_data**

The ARD §5.1 state machine says ATTENTION is a transient overlay, not a peer
state — it reverts to the *previous* state on expiry. This means the BLE
receive callback must NOT write `state.mood = msg.mood` while `attn_timer > 0`;
it must write to `state.pre_attn_mood` instead. Forgetting this causes the
revert to snap to whatever the *last received packet's mood* was rather than the
mood that was active before the IMU peak triggered.

**_halt flag for graceful loop exit from inside pcall**

`break` inside a `pcall` body only exits the pcall function, not the enclosing
`while true`. Pattern: set a module-upvalue `_halt = true` inside the pcall
body, return cleanly, then check `if _halt then break end` *after* the pcall
error handler in the outer loop. This preserves the error-handler path and exits
cleanly without double-running error recovery.

**frame.imu.tap_callback vs frame.imu.on_tap(n,cb) — API name matters**

The ARD-assumed `frame.imu.on_tap(2, cb)` with built-in N-count parameter does
not exist. The real API fires once per hardware tap with no count arg. Always
verify API signatures against emulator stub source before writing Lua stubs,
not just against high-level documentation or architectural notes.

**Snapshot zeroing in sensors.py was already done — check before editing**

A task instructed "add `samples[:] = 0.0` before `del samples`" — but it was
already present from the cycle-2 privacy hardening pass (commit 3bb96a3).
Pre-flight: grep for the exact pattern before making a targeted edit to avoid
a no-op diff or a confusing duplicate.

---

### Week 2 Review-Fix Wave Learnings (2026-06-12)

**B1 — Baseline must learn raw tension, not mood-transformed intensity (BLOCKING)**

`update_baseline` takes a `tension: float` parameter (Welford online stats over the raw
weighted score). The call site was passing `result.intensity` which is a mood-transformed
value (e.g. `1.0 - tension` for calm, `0.5` for neutral). This silently poisoned the
personal stress threshold (`mean + 1.5 × stddev`). Fix: switch to `result.tension` now
that `MoodResult.tension` exists (Librarian's f9c49c9). Lesson: whenever a function
parameter name and an available field name diverge, verify they mean the same thing.

**B2 — Single-pacer cadence: SensorStream must not self-pace (BLOCKING)**

Having `asyncio.sleep(0.1)` in both `SensorStream.__anext__` AND the main loop's
normal-send path caused ~200ms/iter (5 Hz) on real hardware. Invisible in tests because
`FakeSensorStream` has `delay=0`. Fix: remove sleep from `SensorStream.__anext__`
entirely — capture is driven by the audio device callback cadence. Main loop is the sole
pacer via an unconditional `try/finally` block around the loop body.

Key design choice: use `time.monotonic()` (not the injectable `clock`) for the pacing
elapsed calculation. Reason: the injectable `FakeClock` is a stateful counter that
advances once per `__call__`. Adding a second `clock()` call per frame (for elapsed)
doubles the counter advancement, shifting the confidence-hold and both-fail timeout
thresholds and breaking the existing timing tests. Using `time.monotonic()` for pacing
keeps `clock()` at exactly one call per frame for timeout logic, preserving
`FakeClock` invariants. Trade-off: tests are ~5–6s slower (0.1s sleep × N gated/fail
frames) but stay green.

- **cycle-3 review:** IMU normals (`_IMU_ACCEL_NORM`, `_IMU_ROT_NORM`) were declared but never applied — always audit normalisation constants against the code path that uses them, not just their definition. stop/close in a single try block defeats hardened-shutdown intent; use separate guards. Writing a flag outside the lock it's read under gives no real synchronisation — both sides must hold the same lock.



📌 Team update (2026-06-14T05:36:23Z): Juanita documented heap-guard observability gap as structural test (will fail when heap field added — surfaced for review); host bind-up complete; privacy audit APPROVED all surfaces — ready for ship — decided by Juanita, Raven
