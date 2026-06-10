# Project Context

- **Owner:** Aaron Kubly
- **Project:** halo — mono-repo playground for authoring apps on Halo smart glasses
- **My layer:** Tests, test infra, edge cases, correctness review
- **Testing reality:** BLE is flaky by nature; hardware-in-the-loop tests are slow — mock when possible, real device when necessary
- **Created:** 2026-06-01

## Session 2026-06-08: VESPER Test Strategy Rev 2 — All 11 Findings Closed

- Revised TEST-STRATEGY.md: B1/B2/B3 blocking (heap device-only, wire format LE/dedup, false-positive bug fixed), I4–I10 important (methodology framing, acceptance test decoupling, ownership clarity, privacy/jitter, Lua authority, quick-reset spec, story mapping), M11 minor (Appendix A split resolved/open). Review-driven remediation complete; test suite buildable.

## Learnings

### London-School Honest Framing (2026-06-08)
- Claiming "everything is mockist" is dishonest. Pure-function tests are DELIBERATELY classicist — value transformation with no collaborators to mock.
- Only acceptance tests are London-school / mockist.
- Orchestration lives in FamiliarApp, not in inference.

### Wire-Format Alignment (2026-06-08)
- ALL multi-byte fields are LITTLE-ENDIAN.
- Seq dedup: signed-16 delta window.
- FAMILIAR_RESET: Device→Host ONLY.
- FAMILIAR_ACK: Auto every 10 packets, seq-only.

### Heap Ownership is Device-Only (2026-06-08)
- Heap management entirely Lua-side. No heap state on wire.

### Quick-Reset is Device-Originated (2026-06-08)
- Double-tap detected on-device, device snaps to NEUTRAL locally (no host round-trip).

## Session 2026-06-09: VESPER Week 1 Integration & Test Suite Delivery

**Test suite delivered:** 54 paranoid tests in projects/synesthetic-familiar/tests/test_protocol.py.

**Integration reconciliation event:**
- Initial contract mismatch: tests expected Mood IntEnum + seq_is_newer export from Ng's protocol module
- Ng coordinated alignment and added both exports without changing test file
- **Result:** Test expectations locked as canonical. 54 tests now pass, 0 skipped.

**Critical insight:** Tests == executable specification. The test contract defines what the wire format means. Ng's implementation must match test expectations, not the other way around.

**Outcome:** 54-test green. Wire format fully verified. Ready for hardware validation.

## Session 2026-06-09: VESPER Test Strategy Rev 3 — Persona-Review Remediation Wave

Applied 9 persona-review findings to TEST-STRATEGY.md. All changes surgical; mixed-methodology framing preserved.

## Learnings (continued)

### Parametrize beats Hypothesis for boundary coverage (2026-06-09)
- `hypothesis` is heavyweight for a pure-function heuristic with known boundaries. An explicit `@pytest.mark.parametrize` table (~8 rows covering nominal + boundary per mood) is easier to read, faster to run, and requires no extra dependency. Use hypothesis only when you cannot enumerate the input space.

### `busted` is the SOLE Lua authority — no Python-clone oracles (2026-06-09)
- A Python reimplementation of Lua state machine logic (LuaStateMachineSim) only validates itself. It says nothing about production Lua. If cross-language fuzz is needed in Phase-2, drive it through a real Lua interpreter (busted fixtures or subprocess). Never substitute a Python clone.

### ATTENTION is overlay-and-restore, NOT overlay-and-neutral (2026-06-09)
- on_imu_peak() overlays ATTENTION briefly (<=500ms), then restores the *previous* mood (e.g., STRESSED → ATTENTION → STRESSED). It does NOT reset to NEUTRAL. This is architecturally important: ATTENTION is ephemeral emphasis, not a mood transition.

### Confidence-hold timeout belongs in Phase-1 (2026-06-09)
- The "stuck creature" scenario (prolonged sub-0.7 confidence → creature frozen) is a Phase-1 UX failure, not a Phase-2 enhancement. After ~30s of gated silence, re-send the last confirmed mood. FakeClock-driven tests can cover this without time.sleep().

### Global coverage gates are a false safety signal (2026-06-09)
- `--cov-fail-under=90` on the whole test suite can pass with 100% coverage of trivial files masking 60% on critical ones. A selective gate on the single most important module (familiar_protocol.py at 95%) is more honest and actionable than a blunt global threshold.

## Learnings
- `--cov-fail-under` without `--cov=<module>` is silently ignored by pytest-cov; always pair them: `pytest --cov=<module> --cov-fail-under=N <test_file>` (2026-06-09, T7 PR review).
