# Session Log: Brilliant Labs Lineage Research (Monocle → Frame → Halo)

**Date:** 2026-06-02  
**Time:** ~06:52Z  
**Duration:** Turn 2 of lineage research (agents: hiro, enzo, ng, dasid, librarian)  
**Outcome:** COMPLETED

## Research Scope

Traced Brilliant Labs' product arc across 3 generations to understand architectural patterns, design principles, and strategic direction for Halo playground.

## Key Cross-Cutting Findings

1. **Hardware Trajectory:** Each generation *simplified developer path* while *improving battery + audio*.
   - Monocle: 70mAh, FPGA, MicroPython, academic focus
   - Frame: 210mAh, FPGA internalized, Lua + Noa, but limited audio
   - Halo: 300mAh all-day, no FPGA, NPU fixed, host-peripheral model, stereo mics + bone-conduction

2. **Audio is Halo's Differentiator** — First generation to invest in stereo I/O (mics + speakers). Playground Phase 1 should lead with audio apps (Workout Coach first, not Bird Watcher). This signals ecosystem intent.

3. **Host-Peripheral Model is Standard** — Halo removed on-device compute autonomy entirely. Apps are Python/Flutter/Web on host; Halo is sensor + display. This is architectural baseline, not limitation.

4. **SDK APIs are Stable; Lua APIs Break** — Host-side BLE contracts survive generations. On-device Lua APIs break between frames (Brilliant willing to force rewrites for clarity). Don't over-abstract.

5. **Silent-Failure Migration Gotchas** — Frame→Halo migration has 5 breaking changes that silently fail: power-save default, TxSprite wire format, removed `data.parsers`, IMU data type, TxTextSpriteBlock API. QA and developer guidance needed.

6. **Cloud LLM is Only Path** — All 3 generations chose cloud inference despite increasing hardware capacity. Monocle (none) → Frame (none) → Halo (NPU for gating, not reasoning). Start with hosted multimodal API; never attempt local LLM.

7. **Design is Constraint-Driven** — Halo's 256×256 round display + 300mAh battery + no buffer require ambient UI (glanceable, sparse, incremental). Not a miniaturized phone screen.

## Decisions Written

- **Hiro:** Future-device portability vs. Halo focus (design for Halo now; future devices are major versions)
- **Enzo:** Playground roadmap amendment (reorder Phase 1: Workout Coach → Bird Watcher → Time Tracker)
- **NG:** Frame→Halo migration gotchas (5 silent failures cataloged; QA checklist needed)
- **Da5id:** Sparse Radial HUD principle (5 constraints for ambient UI design)
- **Librarian:** Model tier validation (hosted multimodal API confidence increased by lineage analysis)

All decisions merged to `.squad/decisions.md` (2026-06-01 entry).
