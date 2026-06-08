---
updated_at: 2026-06-08T06:15:43Z
focus_area: First official project (Synesthetic Familiar, Theme-2)
active_issues: []
---

# What We're Focused On

**First official Halo project:** Synesthetic Familiar (Theme-2).

**ARD drafted** at `docs/projects/synesthetic-familiar/ARD.md` (status DRAFT, pending Aaron approval).

**Architecture shape locked:**
- Host (Python) mood inference from mic+IMU at 10Hz
- Device (Lua) renders 24×24 breathing sprite
- BLE protocol: 6-byte FAMILIAR_UPDATE opcode (mood, intensity, confidence, sequence)
- Privacy by abstraction: abstract visual language, no labeled emotions, visual jitter
- 8 architectural decisions locked (host-peripheral model, autonomy tier, mood/render decoupling, confidence gating, privacy model, BLE format, display budget, graceful degradation)

**Next gate:** Aaron reviews ARD Section 7 for 3 pending decisions:
1. Host platform (Python / Web Bluetooth / Flutter)
2. Sensors (Mic+IMU / Mic-only / +Camera)
3. Model location (Local / Cloud / Hybrid)
4. Creature form (Abstract-with-eyes / Full face / Particles)
5. Evolution scope (None / Simple growth / Full)

Once Aaron decides → Hiro Phase 1a (mood inference) + Phase 1b (device rendering)
