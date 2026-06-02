# Project Context

- **Owner:** Aaron Kubly
- **Project:** halo — mono-repo playground for authoring apps on Halo smart glasses using the Brilliant SDK
- **Target device:** Brilliant Halo (BLE peripheral, Lua 5.3 VM on-device, camera/mic/speaker/display)
- **SDK surfaces:** Python (Mac/Linux/Windows), Flutter (iOS/Android), Web Bluetooth (Chromium)
- **SDK repo:** https://github.com/brilliantlabsAR/brilliant_sdk
- **Docs root:** https://docs.brilliant.xyz/halo/
- **Created:** 2026-06-01

## Role: NG (SDK Quality & Developer Experience)

**Focus:** SDK reliability, API completeness, developer friction points, cross-platform consistency.

**Previous Sessions:**
- Turn 1 (2026-06-01): SDK lineage audit (Monocle → Frame → Halo). Documented 8 breaking changes, deprecated APIs, capability gaps.
- Turn 2 (2026-06-01): Migration patterns & compatibility. Frame vs. Halo hardware differences. Web Bluetooth Chromium-only constraint.
- Turn 3 (2026-06-02): Community-discovered SDK rough edges inventory. Six architectural gaps, workaround patterns, recommendations for upstream SDK fixes. See `.squad/decisions/decisions.md for full decision entry.

**Archived (2026-06-02):** Full learnings appended to `.squad/agents/ng/history-archive.md. Current history truncated to recent work only.

---

## Current Session (2026-06-02): GitHub Landscape — Community SDK Wrappers & Libraries

**Task:** Search GitHub for community SDK wrappers, BLE drivers, and Lua libraries. Assess production-readiness and recommend adoption/avoidance.

**Summary:** Executed systematic gh searches across repo names, code patterns, and Brilliant Labs official org. Found 9 noteworthy projects.

**Key Findings:**
- Pre-Official Community Work: uma-shankar-gupta/brilliant_ble (Dart, obsolete), brilliantsole/Brilliant-Labs-Frame-Web-SDK (JS, superseded)
- High-Quality Refs: CitizenOneX/frame_ble (Flutter), CitizenOneX/frame_ble_python (Python), CitizenOneX/frame_examples_python (essential migration template)
- Real-World Usage: anonimousname1234/SARBINS (wayfinding), milesprovus/Monocle-Teleprompter (Google API pattern)
- False Positives: caic-xyz (unrelated), floren/monocle (legacy), bitfeed (unrelated)
- Lua Libraries: Generic JSON parsers; not Halo-specific

**Verdict:** USE CitizenOneX examples (migration ref). MONITOR official SDK adoption. AVOID community web/Flutter forks. ARCHIVE Monocle projects.

**Output:** `.squad/agents/ng/github-sdk-community-2026-06-02.md — Annotated catalog.

**Next Steps:** Confirm official SDK standard, flag CitizenOneX in migration guide, monitor Halo community post-launch.

---

## Ideation 2026-06-02

Raw blue-sky ideas for SDK tooling, debugging, community workflows. See `.squad/agents/ng/ideation-2026-06-02.md (no decisions promoted).
