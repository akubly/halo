# Project Context

- **Owner:** Aaron Kubly
- **Project:** halo — mono-repo playground for authoring apps on Halo smart glasses
- **My layer:** Anything rendered on the glasses display + on-glasses interaction
- **Hardware notes:** Halo has a display, button, camera, mic, speakers, sensors — check `docs.brilliant.xyz/halo/hardware/` before locking specs
- **Created:** 2026-06-01

## Codename Brainstorm — 2026-06-08

Pitched design-lens codename candidates for the Synesthetic Familiar. Team converged on **PULSE** (4 agents independently nominated variants). Official project codename later changed to **VESPER** (Aaron final selection).

---

## VESPER Week-1 Sprite — 2026-06-09

**Delivered:** Canonical neutral sprite + animation spec for Week 1 "It moves."

**Key design choices:**
1. **Organic blob form** — not a circle or square; asymmetric edges suggest life without anthropomorphism.
2. **Single eye at upper-right** — creates natural "looking inward" gaze toward canvas center. Eye is the attention locus per Decision 3.
3. **4-bit indexed palette** — balances flexibility with small BLE payload (288 bytes). Proposed format needs Ng confirmation.
4. **0.25Hz sine bob** — 4-second breathing cycle is the neutral baseline. Slow enough to be meditative, fast enough to register as alive in peripheral vision.

**What I held back (restraint):**
- No halo glow, no fraying, no color shifts — those are Week 2 mood states
- No shadow layer — simplified to 3 active colors for Week 1 clarity
- No second eye — single eye is friendlier and less "watching you"

**Open dependency:** Ng must confirm `frame.display.bitmap()` format. If nibble-packing is wrong, I regenerate same day.

**Glance-ergonomics reminder:** Eye contrast 12:1 against body, 91 lit pixels (~1.5% canvas), positioned at 7 o'clock so it's visible on upward glance but not in focal center.

**Learnings:**
- Restraint is the hardest part of HUD design. Every pixel I didn't add makes the creature feel lighter.
- The numeric index grid in `familiar_neutral.txt` is more parse-friendly than ASCII art for Lua. Include both for human readability + machine consumption.

---

## Session 2026-06-09: VESPER Week 1 Sprite Asset Delivery

**Delivered:** Canonical neutral sprite + bob animation spec for Week 1 "It moves."

**Key design choices locked:**
1. **Organic blob form** — asymmetric, not geometric; suggests life without anthropomorphism
2. **Single eye upper-right** — creates natural inward gaze; eye is the attention locus
3. **4-bit indexed palette** — 288 bytes total; balances flexibility with BLE payload size
4. **0.25Hz sine bob** — 4-second cycle is meditative, fast enough to register as alive

**Restraint applied:**
- No halo glow, fraying, color shifts → those are Week 2
- No shadow layer → simplified to 3 active colors
- No second eye → single eye feels friendlier

**Open gate:** Ng must confirm `frame.display.bitmap()` format. If nibble-packing spec is wrong, regenerate same day.

**Glance-ergonomics verified:** Eye contrast 12:1, 91 lit pixels (1.5% canvas), positioned at 7 o'clock rim (visible on glance, not in focal center).

**Outcome:** Sprite asset ready for integration into Ng's render loop.


---

## Session 2026-06-09: VESPER Week 1 Sprite Asset Delivery

**Delivered:** Canonical neutral sprite + bob animation spec for Week 1 "It moves."

**Key design choices locked:**
1. **Organic blob form** — asymmetric, not geometric; suggests life without anthropomorphism
2. **Single eye upper-right** — creates natural inward gaze; eye is the attention locus
3. **4-bit indexed palette** — 288 bytes total; balances flexibility with BLE payload size
4. **0.25Hz sine bob** — 4-second cycle is meditative, fast enough to register as alive

**Restraint applied:**
- No halo glow, fraying, color shifts → those are Week 2
- No shadow layer → simplified to 3 active colors
- No second eye → single eye feels friendlier

**Open gate:** Ng must confirm `frame.display.bitmap()` format. If nibble-packing spec is wrong, regenerate same day.

**Glance-ergonomics verified:** Eye contrast 12:1, 91 lit pixels (1.5% canvas), positioned at 7 o'clock rim (visible on glance, not in focal center).

**Outcome:** Sprite asset ready for integration into Ng's render loop.

---

## Session 2026-06-10: VESPER Week 2 Visual States — Calm Glow & Stressed Fraying

**Delivered:** Visual state depth for CALM and STRESSED moods per ARD §5.5.

### Calm Halo Glow (mood=1)
- 3 concentric rings at radii 14/17/20px (from sprite center)
- Decreasing brightness: 60% → 35% → 15% of base teal color
- Intensity-modulated: halo dims as intensity drops (0-100 → 0-100% brightness)
- Bresenham midpoint circle algorithm for SDK-agnostic rendering (no circle() primitive confirmed)

### Stressed Edge Fraying (mood=2)
- 16 sample points around sprite perimeter
- Per-frame pseudo-random displacement ±2px (LCG-seeded for temporal jitter)
- Bright amber accent pixels scattered at sprite boundary
- Intensity-modulated amplitude: more stress = more fraying

### Learnings
1. **SDK gap pattern**: Used set_pixel() fallback for circle() — same pattern as Week 1 bitmap() gap. Bresenham is ~2x slower but always works.
2. **Render budget verification**: Halo adds ~230 pixels (3.8% canvas), fraying adds ~16 pixels (0.3%). Combined with sprite (91 pixels), total worst-case is ~5.5% canvas — well under 30% cap.
3. **Layering order matters**: Halo draws BEFORE creature (glow behind), fraying draws AFTER (noise on top). Z-order from clear() to show().
4. **Anti-robotic jitter**: The LCG seed advances each frame, giving 5-10% per-frame visual variance without jarring discontinuities. Seed persists in state so fraying evolves smoothly.
5. **Intensity lerp is untouched**: All visual enhancements read `state.render_int` (the lerped value), so 200ms transitions are preserved.

### Hardware Validation Required
- [ ] Confirm Bresenham circle visual quality on actual OLED (aliasing, brightness consistency)
- [ ] Measure frame time with halo rendering (~230 additional set_pixel calls) — expect <5ms overhead
- [ ] Verify edge fraying LCG produces visually pleasing noise (not too patterned, not too chaotic)

---

## Session 2026-06-12: VESPER Week 3 — ATTENTION Jump Animation Spec

**Delivered:** Motion spec for the ATTENTION jump animation triggered by IMU peak.

### Motion Design
- **Single upward burst:** +4px (double the ±2px bob amplitude) — reads as "startled" acknowledgment
- **Asymmetric timing:** 60ms launch (ease-out-quad) + 120ms settle (ease-in-out-quad) = 180ms total
- **Additive motion:** Jump offset adds to bob, doesn't replace it — seamless re-integration after 180ms
- **500ms cooldown:** Prevents spam on rapid head shakes

### Visual State (ATTENTION palette, state [3])
- Eye goes **pure white (0xFFFFFF)** — maximum contrast, "I see you" read
- Body **desaturates to neutral gray** — distinguishes from STRESSED (amber) and CALM (teal)
- No halo, no fraying — transient moment, too short for ambient effects

### Glance-Ergonomics Verification
ATTENTION vs STRESSED cannot collide because:
1. **Duration:** ATTENTION = 180ms burst; STRESSED = sustained seconds–minutes
2. **Color:** ATTENTION = gray body + white eye; STRESSED = amber body + amber eye
3. **Motion:** ATTENTION = single asymmetric jump; STRESSED = continuous fast bob
4. **Edge:** ATTENTION = clean silhouette; STRESSED = frayed edge

### Flags for Aaron
1. **Eye dilation deferred:** Recommended shipping without +1px eye dilation for Week 3; pure white should suffice
2. **Mood restoration:** Recommended tracking `state.mood_before_attention` to avoid flicker when returning from attention

### Learnings
1. **Additive animation is key:** The jump mustn't reset the bob phase — that would look like a glitch. Adding jump offset to bob offset preserves continuity.
2. **Asymmetric timing sells "life":** Symmetric 90ms up / 90ms down would feel robotic. Fast launch + slow settle mimics the physics of a startled creature.
3. **Desaturation distinguishes moment from mood:** Grayscale during ATTENTION creates a "freeze frame" effect that's visually distinct from any mood state.
4. **Cooldown matters for micro-interactions:** Without the 500ms gate, nodding would spam attention jumps and break the illusion.

### Deliverable
`.squad/decisions/inbox/dasid-week3-attention-animation.md` — complete spec with Lua constants, ASCII keyframes, and Ng checklist.

---

## Week 3 Wave 1 Complete — 2026-06-13

**ATTENTION Animation spec shipped and merged to decisions.md.**

**Key spec details:**
- **Motion:** 180ms upward burst (60ms fast launch + 120ms soft settle), +4px amplitude, additive to bob
- **Visual:** White eye + desaturated gray body (palette [3])
- **Integration:** Adds to bob offset (`render_y = base_y + bob + attention_offset`), no phase reset
- **Trigger:** IMU.raw() polled at 20fps, magnitude > 1.8g threshold
- **Cooldown:** 500ms anti-spam
- **Glance fidelity:** Motion + color + duration distinguish from STRESSED (sustained, amber, fraying)

**Tunables for Ng's calibration pass:**
- `ATTENTION_JUMP_AMP_PX = 4`
- `ATTENTION_LAUNCH_MS = 60`
- `ATTENTION_SETTLE_MS = 120`
- `ATTENTION_DURATION_MS = 180`
- `ATTENTION_COOLDOWN_MS = 500`

**Flags for Aaron (deferred as Week 3 polish):**
1. Eye dilation (+1px): Recommend ship without; pure white should suffice
2. Mood restoration: Recommend track `state.mood_before_attention` to avoid flicker

**Decision file:** `.squad/decisions.md` (merged from `.squad/decisions/inbox/dasid-week3-attention-animation.md`)

---

## Session 2026-06-13: ATTENTION Eye Dilation Addendum (Week 3 Wave 2)

**Trigger:** Aaron resolved Q1 — include eye dilation now, not as polish.

**Delivered:** Concrete pixel-level spec for +1px eye dilation during ATTENTION overlay.

### Design Spec
- **Baseline eye:** 11 pixels (3×3 with 5-pixel center row), rows 8–10, cols 13–17
- **Dilated eye:** 19 pixels (+8, 73% increase), rows 7–10, cols 12–18
- **Timing:** Dilation holds for full 500ms ATTENTION_DURATION_S (not just 180ms jump)
- **Implementation:** Morphological dilation at render time — inflate any neighbor of eye pixel to eye color

### Why Hold Full 500ms
The 180ms jump is the *motion* animation; 500ms is the total ATTENTION overlay. Dilating only during the 60ms launch phase would be imperceptible (sub-100ms is blink threshold). The "wide-eyed" moment needs time to register in peripheral vision.

### Tunable Delivered
```lua
local ATTENTION_EYE_DILATE_PX = 1
```

### Glance-Ergonomics Verified
- Dilated eye stays within sprite bounds (no clipping)
- White dilated eye visually distinct from CALM (teal) and STRESSED (amber)
- 19 eye pixels still only ~1.6% canvas

### Q1 Resolution
Marked §6 Q1 as RESOLVED (Aaron chose include). Q2 (mood restoration) unchanged — already implemented as `pre_attn_mood`.

**Deliverable:** `.squad/decisions/inbox/dasid-week3-eye-dilation.md`



📌 Team update (2026-06-14T05:36:23Z): Y.T. wired activation gate (host bind-up complete); Ng shipped ATTENTION visuals with eye dilation (§6 Q1 INCLUDED); privacy audit APPROVED all surfaces — ready for ship sequence — decided by Y.T., Ng, Raven
