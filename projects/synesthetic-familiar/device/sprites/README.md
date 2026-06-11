# VESPER Sprite Assets — Week 1 (Neutral/Idle)

**Owner:** Da5id (HUD/UX)  
**Date:** 2026-06-09  
**ARD Reference:** §5.5 HUD/Render, Decision 3 (Abstract-with-Eyes)

---

## Format Specification (NEEDS NG CONFIRMATION)

**Proposed format:** 4-bit indexed (16 colors), 24×24 pixels

- **Width:** 24 px
- **Height:** 24 px
- **Bits per pixel:** 4 (indexed)
- **Byte order:** Row-major, left-to-right, top-to-bottom
- **Pixel packing:** 2 pixels per byte (high nibble = left pixel, low nibble = right)
- **Total size:** 24 × 24 / 2 = 288 bytes

**Palette (Week 1 — Neutral):**

| Index | Name       | RGB Hex     | Description |
|-------|------------|-------------|-------------|
| 0     | Transparent | `0x000000`  | Black (OLED off) |
| 1     | Body       | `0x1A2D3D`  | Dark cool blue-gray |
| 2     | Body-Mid   | `0x2E4756`  | Mid-tone body |
| 3     | Eye-White  | `0xE0F4FF`  | Bright cyan-white (attention locus) |
| 4     | Shadow     | `0x0D1820`  | Subtle edge shadow |

⚠️ **NG to confirm:** Does `frame.display.bitmap()` expect this nibble-packed format,
or does it want byte-per-pixel / RGB565 / different packing? If format differs,
Da5id will regenerate the asset.

---

## Week 1 Sprite: `familiar_neutral.txt`

The sprite is an **abstract organic blob with a single bright eye**:
- Rounded, slightly asymmetric form (alive, not geometric)
- Single eye at upper-right (attention locus per ARD Decision 3)
- No face, no mouth, no anthropomorphic features
- Peripheral-vision legible: bold silhouette, high-contrast eye

See `familiar_neutral.txt` for the 24×24 grid (ASCII art + index map).

---

## Week 1 Bob Animation Spec

**Animation:** Vertical breathing bob (idle/neutral)

| Parameter     | Value         | Rationale |
|---------------|---------------|-----------|
| Amplitude     | ±2 px         | Subtle — detectable in peripheral vision, not distracting |
| Frequency     | 0.25 Hz       | 4-second full cycle (ARD §5.5 Neutral state) |
| Easing        | Sine          | Smooth, organic — `sin(2π × 0.25 × t)` |
| Direction     | Vertical only | Horizontal drift would suggest movement, not breathing |

**Lua implementation (pseudocode — Ng owns `main.lua`):**

```
bob_offset = math.floor(2 * math.sin(2 * math.pi * 0.25 * time_sec) + 0.5)
render_y = base_y + bob_offset
```

This produces: `y = base ± 2` over a smooth 4-second cycle.

**Why 0.25Hz (not the ARD's 0.15Hz calm baseline):**
- 0.15Hz is the *calm* state (Week 2) — slower breathing when relaxed
- 0.25Hz is *neutral* — baseline resting state before mood inference kicks in
- Week 1 has no calm/stress states — neutral bob only
+ Week 1 renders all moods the host sends (neutral/calm/stressed palettes +
  per-mood bob frequency).  Genuinely deferred: halo glow (Week 2 calm),
  edge fraying (Week 2 stress), attention jump (Week 2-3).

---

## Glance-Ergonomics Constraints for Ng

1. **Position:** 7 o'clock on rim, 80% radius from center (~102px from center)
   - `x = 128 + 102 × cos(210°) ≈ 40`
   - `y = 128 + 102 × sin(210°) ≈ 179`
   - Sprite top-left: `(40-12, 179-12) = (28, 167)` (centered on 24×24)

2. **Contrast:** Eye must be ≥10:1 against body. Eye = `0xE0F4FF`, body = `0x1A2D3D`.
   Computed luminance ratio ≈ 12:1 ✓

3. **Lit pixel budget:** ~85 lit pixels = 1.4% of 256×256 canvas ✓ (under 5% idle target)

4. **What NOT to add in Week 1:**
   - No halo glow (that's Week 2 calm state)
   - No edge fraying (that's Week 2 stress state)
   - No color animation (neutral is static cool palette)
   - No attention jump (Week 2-3 feature)
   - No second eye or facial features (never — per Decision 3)

---

## Week 2+ Extension Note

This sprite will extend to calm/stressed states by:
- **Calm:** Slower bob (0.15Hz), add teal halo glow behind body
- **Stressed:** Faster bob (0.75Hz), shift palette warm (amber body), add edge fraying via `set_pixel()` noise

No structural changes to the 24×24 base form — just animation/palette parameters.
