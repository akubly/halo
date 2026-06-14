# Y.T. History Archive — Pre-Week 2

## Session 2026-06-01: SDK Familiarization & Host-App Architecture

**Halo Hardware Shape:**
- Color microOLED display (circular 256×256), bone conduction audio, Bluetooth 5.3
- Runs ZephyrOS with Lua VM; acts as peripheral — all logic on host
- Pairing: button hold 10s → LED flash → scan from host → pair

**Host-App Development Models:**
1. **Python Desktop** — asyncio-first, `brilliant-ble` + `brilliant-msg`, emulator available
2. **Flutter Mobile** — scaffolding package, device-aware code detection
3. **Web/Browser** — Chromium-only, CircularTextLayout helper

**Session Flow (All Platforms):** Scan → Pair → Connect → Upload Lua → Start loop → Exchange async messages

## Session 2026-06-02: Ideation (2 passes)

Pitched 8 UX-design-lens codename candidates. Team converged on **PULSE** (4 agents nominated).

Later session renamed project to **VESPER** (2026-06-08, Aaron decision).

## Session 2026-06-03: User Stories (Themes 1-2)

Authored 5 user stories per theme (happy path + delight moment):
- **Theme 1 (Consent-Aware Memory):** Group recording consent, memory review, bystander rights
- **Theme 2 (Synesthetic Familiar):** Bonding, stress-detection, personality, 30-day evolution, surprise

## Pre-Week-2 Status

Ready for Week 1 scaffolding + Week 2 real sensors.
