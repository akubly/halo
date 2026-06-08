# Project Context

- **Owner:** Aaron Kubly
- **Project:** halo — mono-repo playground for authoring apps on Halo smart glasses
- **My layer:** Anything rendered on the glasses display + on-glasses interaction
- **Hardware notes:** Halo has a display, button, camera, mic, speakers, sensors — check `docs.brilliant.xyz/halo/hardware/` before locking specs
- **Created:** 2026-06-01

## Learnings

### 2026-06-01 — Initial Hardware Familiarization

**Display Specs (Critical)**
- 0.2" VGA020 OLEDoS micro-display (OLED on Silicon)
- **Drawable area: 256×256 px** (round/circular viewport)
- Full RGB color with **0xRRGGBB** hex values (no palette restriction)
- 10,000:1 contrast ratio — blacks are *true black*
- 256 grayscale levels per channel
- Peak brightness: **5,000 nits** — usable outdoors
- Refresh rate: **25–120 Hz** (variable)
- Pixel pitch: **6.3 µm** — extremely dense
- **No double-buffer** — all draw calls render immediately, no `show()` needed
- Pan offset adjustable ±50 px in X/Y (persists across reboot)

**Display Position**
- Mounted top of frame — appears in upper peripheral vision (monocular)
- This is NOT center-of-eye; designs must assume glance-up ergonomics

**Input Modalities**
- **Single button** (left arm): single-click, double-click, long-press (~1s)
- System overrides: 3s → deep sleep, 8s → clear bonding + pairing, 15s → ship mode
- **IMU tap detection**: single/double/triple tap via accelerometer interrupt
- **Audio Activity Detection (AAD)**: wake on sound (60–97.5 dB threshold)
- No touch, no gesture tracking, no gaze tracking

**Render Primitives**
- `text(string, x, y, color)` — UTF-8, single font (no size control documented)
- `char(codepoint, x, y, color)` — single Unicode glyph
- `set_pixel(x, y, color)`
- `line(x0, y0, x1, y1, color)`
- `rect(x, y, w, h, color, filled)`
- `circle(cx, cy, r, color, filled)`
- `polygon(points, color)`
- `bitmap(x, y, width, format, offset, data, opts)` — indexed (2/4/16bpp) or RGB
- `clear(color)` — defaults to black
- `brightness(0–100%)`
- 16-slot color palette with named defaults; assignable via RGB or YCbCr

**Power / Performance Constraints**
- 300 mAh total battery (2×150 mAh cells)
- 14-hour advertised battery life — implies ~21 mW average draw
- Arm Cortex-M55 + Ethos-U55 NPU — constrained compute
- BLE 5.3 only — all data from host goes over Bluetooth
- Camera alone: 40 mW at full frame rate — significant load
- Mic modes: 310 µA (high quality) to 20 µA (AAD only)
- Display brightness directly impacts battery; avoid sustained 100%

**Design Implications (Da5id's Take)**
1. **256×256 round canvas** — every pixel is premium real estate. Less is more.
2. **No buffer** — animations are direct writes; minimize redraw area to avoid flicker.
3. **Upper peripheral placement** — content must be readable in <1s glance-up. No dense text blocks.
4. **OLED power** — black pixels = no power. Dark themes are mandatory, not aesthetic.
5. **Three inputs** — button click, tap gesture, voice. Design navigation around these.
6. **High refresh available (120 Hz)** — but likely costs battery. Use 25–30 Hz baseline unless smooth motion is essential.
7. **Sunlight readable (5,000 nits)** — can punch through outdoors; contrast is your friend.

---

### 2026-06-01 — Brilliant Labs Hardware Lineage (Monocle → Frame → Halo)

**Display Evolution**

| Gen | Device | Size | Resolution | Aspect | FOV | Color Model | Buffering |
|-----|--------|------|------------|--------|-----|-------------|-----------|
| 1 | Monocle | 0.23" | 640×400 | 16:10 | 20° | RGB hex (full) | Double-buffered via `show()` |
| 2 | Frame | 0.23" | 640×400 | 16:10 | 20° | 16-color palette (YCbCr) | Double-buffered via `show()` |
| 3 | Halo | 0.20" | 256×256 | 1:1 round | N/A | RGB hex (full) | **No buffer** — immediate writes |

**Key Observations:**
- Resolution *dropped* from 640×400 to 256×256 (−75% pixels) — intentional simplification.
- Halo went **round** — breaks rectangular assumption, encourages radial layouts.
- Halo removed double-buffer — Frame's `show()` model is gone; draw calls are live.
- Color depth: Monocle/Halo allow full RGB; Frame constrained to 16-color palette (1024 YCbCr colors available but indexed).

**Form Factor Trajectory**
- Monocle: Clip-on pendant (monocular, 70 mAh, FPGA-powered)
- Frame: Glasses form (monocular display, 210 mAh, FPGA + nRF52840)
- Halo: Glasses form (monocular display, 300 mAh, Cortex-M55 + NPU, **no FPGA**)

Brilliant moved *away* from FPGA graphics acceleration toward MCU-direct rendering — simpler stack, tighter power envelope.

**Input Lineage**

| Device | Primary Input | Secondary | Tertiary |
|--------|--------------|-----------|----------|
| Monocle | 2× capacitive touch pads | — | — |
| Frame | IMU tap detection (single/double/triple) | — | — |
| Halo | Physical button (single/double/long) | IMU tap | AAD voice wake |

**Pattern:** Touch → Gesture → Button. Brilliant is *adding* input modalities, not replacing. Halo has the richest input vocabulary:
- Button: discrete, unambiguous
- Tap: eyes-free, hands-free
- AAD: voice activation without always-on mic power

**Render API Evolution**

| Primitive | Monocle | Frame | Halo |
|-----------|---------|-------|------|
| Text | `Text(str, x, y, color, justify)` | `frame.display.text(str, x, y, {color, spacing})` | `frame.display.text(str, x, y, color)` |
| Rectangle | `Rectangle(x1, y1, x2, y2, color)` | via bitmap | `frame.display.rect(x, y, w, h, color, filled)` |
| Line | `Line(x1, y1, x2, y2, color, thickness)` | — | `frame.display.line(x0, y0, x1, y1, color)` |
| Circle | — | — | `frame.display.circle(cx, cy, r, color, filled)` ✓ |
| Polygon | `Polygon([coords], color)` | — | `frame.display.polygon(points, color)` |
| Bitmap | via FPGA | `frame.display.bitmap(...)` | `frame.display.bitmap(...)` |
| Fill/Clear | `Fill(color)` | — | `frame.display.clear(color)` |
| Pixel | — | — | `frame.display.set_pixel(x, y, color)` ✓ |

**Halo adds:** `circle()`, `rect()` with filled option, `set_pixel()`. These are native primitives — no need to build circles from polygons.

**Language shift:** Monocle = MicroPython, Frame/Halo = Lua. Lighter runtime, better for constrained MCU.

**What the Trajectory Tells Us (Designer POV)**

1. **Smaller canvas, richer primitives.** Brilliant traded pixels for drawing convenience. The 256×256 round display with native `circle()` says: *design for glance, not gaze.*

2. **From "more pixels" to "less latency."** Removing double-buffer eliminates frame delay but demands incremental updates. Halo optimizes for responsiveness over visual complexity.

3. **Input diversification.** Button + tap + voice = three orthogonal input channels. Design for *mode switching* (e.g., button cycles screens, tap triggers action, voice queries).

4. **Power-aware rendering.** No FPGA means MCU does all graphics. Combined with OLED power draw, this reinforces: *every lit pixel costs battery.*

5. **Peripheral, not foveal.** 20° FOV on Monocle/Frame, Halo's round shape + top-mount placement = designed for peripheral awareness, not focal attention. HUD content should be *ambient*, not *immersive*.

**Proven Patterns to Borrow**
- **Palette-based sprites** (Frame): Even though Halo allows full RGB, indexed 2/4-bit bitmaps compress well and reduce BLE transfer time.
- **Text justification** (Monocle): `MIDDLE_CENTER`, `TOP_LEFT` etc. — Halo lacks this, so we'll need utility functions.
- **Color reassignment** (both): Change palette colors at runtime for theme shifts without re-sending sprite data.

**Patterns to Avoid**
- **Dense text layouts** (Monocle demos): 640×400 allowed paragraph-style text. 256×256 round does not.
- **Full-screen animations**: Frame's double-buffer made this safe. Halo's immediate writes mean full-screen redraws will tear/flicker.
- **Complex JPEG overlays**: Monocle's FPGA could composite images. Halo's MCU cannot. Keep camera feed separate from UI.

---

## Ideation 2026-06-02

### Pie-in-the-Sky HUD Concepts (Round × Monocular × Peripheral)

1. **Breathing Halo** — A ring at the canvas edge that expands/contracts to pace your breath, visible only in peripheral vision so it guides without demanding attention.

2. **Orbital Notifications** — Messages don't pop up; they *orbit* the outer rim like moons, drifting into the center only when you glance up, exploiting peripheral motion sensitivity.

3. **Compass Rose Navigation** — Turn-by-turn directions as a living compass: the destination arrow rotates smoothly as you turn your head, cardinal points bloom and fade at edges.

4. **Depth Rings** — Concentric circles that pulse outward = something approaching; pulse inward = receding — a monocular parallax illusion your brain reads as spatial proximity.

5. **Eclipse Transitions** — Screen changes via a black disc sliding across (moon eclipsing sun), embracing the round mask instead of rectangular wipes or fades.

6. **Radial Time** — Time displayed as a single glowing dot orbiting the rim (like a clock hand), no numbers needed — your peripheral vision learns the position = time.

7. **Pulse Poker** — A party game where only YOU see a secret color pulse in your peripheral vision; others watch your micro-expressions to catch when you "see it" — monocular asymmetry as gameplay.

8. **Bloom Alerts** — Urgent notifications don't beep; they *bloom* from center outward like a flower opening, exploiting how peripheral vision snaps to expanding motion faster than static icons.

---

## Ideation Pass 2 2026-06-02

Cross-pollinated with all 8 squad agents. Key synthesis:

- **Synesthetic Familiar** (top mash-up): fused Y.T.'s pet familiar with Librarian's synesthetic AI—the creature *is* your peripheral sense augmentation, showing internal state through form/motion rather than metrics.
- **Consent Bloom**: Raven's decentralized consent layer rendered as bloom animations with directional encoding.
- **The Wound Display**: Juanita's chaos tests become designed failure states—visual injuries that heal as systems recover.
- **Two-zone architecture emerging**: rim = system state (consent, health, time); center = content (familiars, messages).

Librarian #2 (Synesthetic AI) is the thesis I've been circling: render abstract data as peripheral-legible motion. The round canvas is a synesthetic chamber.

---

## User Stories Themes 1-2 — 2026-06-03

Authored 10 HUD behavior stories covering Aaron's top two themes from ideation curation.

**Theme 1 — Consent-Aware Memory (5 stories):**
- DASID-T1-1: Ambient Recording Indicator — amber ring pulse (2px, 0.5Hz) for active capture awareness
- DASID-T1-2: Consent Bloom — green petal-wedge blooms toward edge when bystander grants, bearing-encoded
- DASID-T1-3: Consent Revoke Eclipse — black disc slides in from bearing, red rim pulse warning
- DASID-T1-4: Bystander Glance Indicator — external LED↔internal ring sync contract (amber/green/off)
- DASID-T1-5: Consent Constellation — room's privacy stances as positioned 5-point stars on rim

**Theme 2 — Synesthetic Familiar (5 stories):**
- DASID-T2-1: Idle Familiar — 24×24 sprite at 7 o'clock, gentle 0.25Hz bob, meditative presence
- DASID-T2-2: Stress State — bob accelerates, edges fray, color warms amber, creeps toward 6 o'clock
- DASID-T2-3: Calm State — bob slows, teal halo bloom appears behind familiar as reward
- DASID-T2-4: Attention Moment — familiar "jumps" toward significant events (or flinches from negative)
- DASID-T2-5: Bystander Perception — familiar humanizes device externally, distinct from system indicators

**Key design decisions locked:**
- Two-zone architecture confirmed: rim = system state (≤20%), center = content
- Pixel budget: no story exceeds 15% lit at peak, idle averages 3–5%
- Motion grammar: bloom (400ms), eclipse (600ms slide), familiar jump (200ms out, 400ms return)
- Refresh baseline: 25–30fps for animation, 10–15fps for idle

**Favorite story:** DASID-T2-4 (Attention Moment). The familiar's jump-toward/flinch-away dichotomy makes events *felt* by a companion, not just displayed by UI. That's the synesthetic thesis in one motion.

**Next:** Ng feasibility review, Y.T. host-app signal hooks for stress/calm detection.

---

## Codename Brainstorm — 2026-06-08

Pitched design-lens codename candidates for the Synesthetic Familiar. Team converged on **PULSE** (4 agents independently nominated variants). Official project codename now PULSE. See `.squad/orchestration-log/2026-06-08T07-17Z-codename-brainstorm.md`.
