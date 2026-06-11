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

## Session Timeline (continued)

| Date | Session | Key Output |
|------|---------|-----------|
| 2026-06-10 | Week 2 Sensors + Main Loop | `host/sensors.py` + `host/main.py` real loop shipped; 59 passed, 5 xfailed |

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

---
