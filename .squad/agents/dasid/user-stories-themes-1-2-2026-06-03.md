# Da5id User Stories — Themes 1 & 2
**Date:** 2026-06-03  
**Author:** Da5id (Designer)  
**Scope:** HUD behavior stories for Consent-Aware Memory + Synesthetic Familiar

---

## Theme 1 — Consent-Aware Memory

### [DASID-T1-1] Ambient Recording Indicator (Wearer)
**As a** wearer, **I want** a persistent but non-intrusive visual signal when my camera/mic is actively capturing, **so that** I have constant awareness of my recording state without it dominating my peripheral vision.

**Acceptance criteria:**
- When capture begins: a thin amber ring (2px width) fades in at canvas edge over 300ms
- Ring pulses gently at 0.5Hz (2-second cycle) — not breathing rhythm, faster, "alive" not "calm"
- Lit pixel budget: ~5% of canvas (ring circumference only)
- Refresh rate: 30fps for smooth pulse
- Ring intensity modulates 40%–60% brightness (never harsh, never invisible)
- When capture ends: ring fades out over 500ms (feels deliberate, not abrupt)

**Design note:** Uses `circle()` primitive (unfilled, stroke-width via concentric circles). Amber (#FFB000) chosen for visibility against black without red's alarm semantics.

---

### [DASID-T1-2] Consent Bloom — Bystander Grant (Wearer)
**As a** wearer, **I want** to see when a nearby bystander grants consent to be recorded, **so that** I understand my social accountability landscape in real-time.

**Acceptance criteria:**
- When consent arrives: a green petal-shape blooms from center toward edge, origin angle encodes bystander bearing (0° = ahead, 90° = right)
- Bloom duration: 400ms ease-out, then fades over 600ms
- Petal size: 20×40px wedge, reaches to 80% radius
- Multiple simultaneous consents: overlapping petals form "consent garden" (max 4 visible at once)
- Peak lit pixels during bloom: ~12% of canvas
- No audio cue — purely visual

**Design note:** Uses `polygon()` primitive with 4–5 points defining petal shape. Animation is incremental redraw (clear old petal position, draw new) at 30fps to avoid full-screen clear.

---

### [DASID-T1-3] Consent Revoke — Eclipse Warning (Wearer)
**As a** wearer, **I want** unmistakable visual feedback when a bystander revokes consent, **so that** I immediately know my recording now contains content I may need to redact.

**Acceptance criteria:**
- When revocation arrives: a black disc (20px radius) slides in from the bearing angle toward center over 600ms
- Disc stops at 60% radius from center, holds for 400ms, then fades over 300ms
- During hold: a red rim (1px) pulses once around the disc (warning accent)
- If multiple revocations within 3 seconds: discs stack/overlap, creating partial eclipse effect
- Peak lit pixels: ~8% (mostly the red rim pulse)
- Refresh: 30fps during animation, drop to 25fps after animation completes

**Design note:** Eclipse metaphor (from my pass-1 ideation) conveys gravity. Uses filled `circle()` + unfilled `circle()` for rim. The slide-in path requires 20 incremental position updates at 30fps.

---

### [DASID-T1-4] Bystander Glance Indicator (Bystander Persona)
**As a** bystander glancing at a wearer's glasses from outside, **I want** to see an unambiguous external signal indicating recording state, **so that** I can make informed decisions about consent without asking.

**Acceptance criteria:**
- External LED (outside HUD, visible to others) color matches internal ring state:
  - Amber pulsing = active capture
  - Green static = no capture, observation only
  - Off = fully private (all sensors disabled)
- Pulse rate synchronized with internal HUD ring (0.5Hz)
- LED visible from 10+ feet in indoor lighting
- State change transition: 200ms crossfade between colors

**Design note:** This story documents the HUD↔LED contract. The internal amber ring and external amber LED must pulse in sync — shared timer at 0.5Hz. Ng implements LED driver; Da5id specifies the visual contract.

---

### [DASID-T1-5] Consent Constellation — Multi-Wearer Room View (Wearer)
**As a** wearer in a room with multiple Halo users, **I want** to see everyone's consent stance as positioned stars in my peripheral vision, **so that** I understand the room's privacy landscape at a glance.

**Acceptance criteria:**
- Each detected wearer renders as a star (5-point, 8px diameter) positioned by bearing + distance (closer = larger, 8–12px)
- Star color encodes their stance: green = private, amber = observing, red = recording
- Stars positioned on outer 20% of canvas (rim zone), max 6 stars visible (overflow: oldest drops)
- When any wearer changes stance: their star flares (brightness 100% for 200ms) then settles
- Idle refresh: 10fps (low power). Flare animation: 30fps burst
- Total lit pixels: ~3% when 4 stars visible

**Design note:** Constellation uses `polygon()` for 5-point stars. Bearing derived from BLE + IMU heading sync (Ng's domain). This is a system-state-on-rim pattern per my two-zone architecture.

---

## Theme 2 — The Synesthetic Familiar

### [DASID-T2-1] Idle Familiar — Peripheral Companion (Wearer)
**As a** wearer, **I want** my familiar to rest visibly but unobtrusively in my peripheral vision during idle moments, **so that** I feel accompanied without distraction.

**Acceptance criteria:**
- Familiar renders as a 24×24px sprite in a fixed "home" position (7 o'clock on the rim, 80% radius from center)
- Idle animation: gentle bob (±2px vertical) at 0.25Hz (4-second cycle) — slower than breathing, meditative
- Sprite uses max 4 colors from palette (dark body, bright eye, accent, shadow)
- Lit pixels: ~1.5% of canvas
- Refresh rate: 15fps (power-efficient idle loop)
- Familiar faces inward toward canvas center (eyes visible in peripheral glance)

**Design note:** Uses indexed 4-bit `bitmap()` for sprite. The bob animation redraws only the sprite bounding box (24×26px with motion headroom) to avoid flicker. Home position chosen to not overlap consent constellation zone.

---

### [DASID-T2-2] Stress State — Familiar Breathing Faster (Wearer)
**As a** wearer experiencing elevated stress (detected via audio baseline or IMU micro-tremor), **I want** my familiar's visual rhythm to reflect my internal state, **so that** I gain non-verbal awareness of my own arousal level.

**Acceptance criteria:**
- When stress detected: familiar's bob accelerates from 0.25Hz → 0.75Hz over 5 seconds (easing)
- Edges of sprite "fray" — 2–3 pixels around perimeter flicker on/off at 6fps (visual noise)
- Color temperature shifts warmer: eye accent transitions from cool white (#FFFFFF) to warm amber (#FFCC66) over 3 seconds
- If stress persists >30 seconds: familiar migrates from 7 o'clock toward 6 o'clock (creeping into more visible peripheral zone)
- Recovery: reverse all effects over 8 seconds when stress signal clears
- Peak lit pixels during stress: ~2.5% (fraying adds ~50% pixel load)

**Design note:** Fraying effect uses `set_pixel()` for border noise. Color shift requires palette slot reassignment mid-animation. Migration path is 20 incremental position updates at 2fps (slow creep).

---

### [DASID-T2-3] Calm State — Familiar Settles and Glows (Wearer)
**As a** wearer in a calm, focused state, **I want** my familiar to visually communicate serenity, **so that** I receive positive reinforcement for sustained calm.

**Acceptance criteria:**
- When calm detected (sustained 60+ seconds): familiar's bob slows from 0.25Hz → 0.15Hz (7-second cycle)
- A soft halo bloom appears behind familiar: gradient ring (8px radius, fading from 40% brightness at center to 0% at edge)
- Halo color: cool teal (#66FFCC) — complementary to stress amber
- Bloom fades in over 2 seconds, persists while calm holds
- If calm breaks: bloom fades out over 1 second before stress visuals begin
- Peak lit pixels: ~3% (halo adds ~1.5%)

**Design note:** Halo bloom uses 3 concentric unfilled `circle()` calls with decreasing brightness. This is the "breathing halo" primitive from my pass-1 ideation, miniaturized behind the familiar. Visual reward, not alert.

---

### [DASID-T2-4] Attention Moment — Familiar Leaps to Event (Wearer)
**As a** wearer when something significant happens (notification, consent event, system alert), **I want** my familiar to "notice" and visually react, **so that** the event feels acknowledged by my companion, not just by UI.

**Acceptance criteria:**
- On significant event: familiar sprite "jumps" — moves 15px toward canvas center over 200ms (ease-out), pauses 300ms, returns over 400ms (ease-in)
- During jump: sprite rotates 15° toward event bearing (head turn)
- Eyes widen: eye accent pixels double in size (2×2 → 4×4) during jump
- If event is negative (revocation, error): familiar's jump is a "flinch" — recoil 10px away from center instead
- Max 1 jump per 2 seconds (debounce to prevent seizure-inducing motion)
- Refresh during jump: 30fps (smooth arc)

**Design note:** Jump arc uses quadratic easing. Rotation achieved by swapping to a rotated sprite variant (pre-rendered, not computed). Eye widening modifies sprite palette entry or swaps sprite frame. This is the familiar's "moment-of-significance" behavior.

---

### [DASID-T2-5] Bystander Perception — Familiar as External Signal (Bystander Persona)
**As a** bystander glancing at a wearer's glasses from outside, **I want** to see a gentle, non-threatening animated element on the display, **so that** I perceive the device as friendly rather than surveillance-like.

**Acceptance criteria:**
- Familiar's idle bob is visible through the lens at 2–3 foot distance (small but discernible motion)
- No rapid flashing or harsh color transitions visible externally during idle state
- Stress-state fraying should NOT be visible externally (too subtle at 24px)
- During "calm glow" state: the teal halo creates a soft ambient glow visible externally as a gentle light shift
- Overall effect: bystander sees "something small is moving gently" — curiosity, not alarm
- External appearance should never suggest "recording indicator" (familiar is content, not system state)

**Design note:** This story constrains familiar design for external perception. The 24px sprite at 80% radius means it's near the lens edge — visible but not central. Calm glow is the most externally visible state. Familiar's role is to humanize the device, distinct from consent indicators.

---

## Summary

| Theme | Stories | Key Visuals |
|-------|---------|-------------|
| T1 — Consent-Aware Memory | 5 | Amber ring pulse, green/black bloom/eclipse, constellation stars |
| T2 — Synesthetic Familiar | 5 | 24px sprite, bob rhythm, fray/glow states, jump reaction |

**Two-zone architecture confirmed:**
- **Rim (outer 20%):** System state — consent indicators, constellation, time
- **Center (inner 80%):** Content — familiar home, blooms, eclipses originate here

**Pixel budget maintained:** No story exceeds 15% lit pixels at peak. Idle states average 3–5%.

---

*Next:* Ng to review for implementation feasibility. Y.T. to confirm host-app hooks for stress/calm detection signals.
