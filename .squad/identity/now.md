---
updated_at: 2026-06-08T06:39:00Z
focus_area: First official project (Synesthetic Familiar, Theme-2)
active_issues: []
status: ARD APPROVED — Build-ready for Week 1
---

# What We're Focused On

**First official Halo project:** Synesthetic Familiar (Theme-2).

**ARD APPROVED** at `docs/projects/synesthetic-familiar/ARD.md` (status APPROVED, finalized 2026-06-07).

**3 Decisions LOCKED by Aaron:**
1. **Sensors:** Mic + IMU (no camera in v1)
2. **Model:** Local heuristic on host (no cloud for v1)
3. **Creature form:** Abstract-with-eyes (geometric + eye, privacy-preserving)

**Build-Ready Architecture:**
- Host (Python 3.11) mood inference from mic+IMU at 10Hz
- Device (Lua) renders 24×24 breathing sprite
- BLE protocol: 6-byte FAMILIAR_UPDATE opcode (mood, intensity, confidence, sequence)
- Privacy by abstraction: abstract visual language, no labeled emotions, 5-10% visual jitter
- Tech stack finalized: Python + `sounddevice` + `numpy` + Lua 5.3 (no external models, no cloud)

**Next step:** Week 1 "It moves" — Python host harness + Lua sprite render on Halo device.
- Week 1: Creature bobbing, BLE protocol working
- Week 2: Host captures mic+IMU, mood inference active
- Week 3: UX polish, onboarding, attention moments, graceful fallback
