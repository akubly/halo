# The Synesthetic Familiar

> A tiny reactive creature living in the wearer's peripheral vision on Halo's
> 256×256 round monocular display. Its form and motion mirror the wearer's
> internal state — stress, calm, attention — inferred from mic + IMU.
> No numbers, no metrics, no literal UI.

**Project codename:** VESPER  
**ARD:** `docs/projects/synesthetic-familiar/ARD.md`  
**Status:** Week 3 "It's alive" complete — 190+ tests green, shipped Week 3 implementation

---

## Week 3 Shipped

Week 3 milestone "It's alive" complete (2026-06-13):
- ✅ **IMU double-tap FAMILIAR_RESET** — device detects tap via `frame.imu.tap_callback()`, Lua debounce 350ms window, snaps to NEUTRAL on-device, sends opcode 0x01 to host
- ✅ **ATTENTION overlay on IMU peak** — render-loop poll of `frame.imu.raw()` at 20fps, threshold `IMU_PEAK_THRESH_G = 1.8`, state [3] palette (white eye + gray body + 180ms +4px jump + 500ms overlay + restore-to-previous-mood)
- ✅ **Baseline activation gate** — ACTIVATION_THRESHOLD = 50 Welford samples; population defaults <50, personal mean+1.5σ ≥50; `get_activation_info()` accessor
- ✅ **Heap monitoring (fallback)** — `frame.system.get_heap_usage()` NOT available; manual proxy (sprite rows + BLE buffer) with 80% reduce / 95% halt thresholds; firmware-swap hook documented
- ✅ **Host onboarding UX** — first-launch calibration status display, "learning your patterns" flow, ATTENTION trigger display
- ✅ **Privacy audit** — abstract visuals, no labeled text, on-device inference only, no cloud egress
- ✅ **190+ tests green** — acceptance tests for double-tap reset, baseline activation, heap thresholds, onboarding flow, graceful fallback

See `.squad/decisions.md` (2026-06-12 & 2026-06-13) for detailed decision records.

---

## Architecture Summary

- **Host (Python):** captures mic + IMU → computes mood heuristic → sends
  `FAMILIAR_UPDATE` at 10Hz via BLE; displays onboarding calibration status.
- **Device (Lua):** receives updates → interpolates state (200–500ms) → 
  renders 24×24 abstract-with-eyes sprite at 15–30fps; detects IMU taps for quick-reset and peak for attention overlay.
- **Confidence gating:** host is the single authority. If confidence < 0.7,
  no update sent (silence > hallucination).
- **Baseline learning:** Welford online mean + stddev, persisted in `~/.vesper/baseline.json`. Activates personal threshold at ≥50 samples.
- **Privacy:** raw audio/IMU never leave host. Wire format carries only
  `mood_enum + intensity + confidence` — no PII.  The confidence byte
  is transmitted as a 0–100 integer so the device can surface signal
  quality (e.g. dim the creature when confidence is low).  No raw
  biometric values are included.

See ARD §4–§5.5 for full architecture, wire format, and render spec.

See ARD §4–§5.5 for full architecture, wire format, and render spec.

---

## Credits

Built on [Brilliant Labs Halo SDK](https://brilliant.xyz).  
Dependencies: `brilliant-ble`, `brilliant-msg` (BSD-3-Clause), `numpy` (BSD),
`sounddevice` (MIT).
