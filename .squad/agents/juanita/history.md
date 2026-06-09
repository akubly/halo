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
