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
