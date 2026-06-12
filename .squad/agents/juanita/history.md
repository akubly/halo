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

## Session 2026-06-10: VESPER Week 2 Test Suite Delivery

**Test suite delivered:** 47 new tests across 6 files. Total suite: 101 tests, all green.

**New / modified files:**
- `tests/test_inference.py` — 5 de-xfailed + 5 boundary parametrize tests (compute_mood contract)
- `tests/test_sensors.py` (NEW) — 3 tests covering Gate I7 (SensorSourcePort privacy)
- `tests/test_protocol.py` — `test_familiar_update_carries_no_raw_biometric_values` added (Gate 1)
- `tests/test_main.py` (NEW) — 15 tests covering Gate 2 (quantise_intensity + apply_intensity_jitter)
- `tests/test_confidence_gating.py` (NEW) — 1 test for I2 confidence-hold timeout (30s, injectable clock)
- `tests/test_fallback.py` (NEW) — 1 test for both-sensors-fail NEUTRAL fallback (10s, injectable clock)

**Gate coverage:**
- Gate I7 (merge-blocking): `test_sensor_source_port_exposes_no_raw_audio` — COVERED, PASSES
- Gate 1 (merge-blocking): `test_familiar_update_carries_no_raw_biometric_values` — COVERED, PASSES
- Gate 2 (merge-blocking): `test_intensity_quantised_before_encode` + `test_intensity_jitter_applied_before_encode` — COVERED, PASSES
- I2 (confidence-hold timeout): `test_confidence_hold_timeout_resends_after_30s` — COVERED, PASSES
- ARD §5.4 (both-fail fallback): `test_both_sensors_fail_sends_neutral_after_10s` — COVERED, PASSES

**No rejections:** Ng and Librarian landed complete Week 2 implementations. All contract invariants met.

## Learnings

### Week 2 test surface (2026-06-10)
- inference.py tested as a pure function (classicist): 5 mandatory + 5 boundary parametrize tests cover all mood transitions, sensor-failure paths, and confidence gating.
- sensors.py tested via dataclass introspection: `dataclasses.fields()` + type annotation inspection is sufficient to enforce the SensorSourcePort privacy gate without running hardware.
- protocol.py Gate 1 uses `inspect.signature()` — checking param names is faster and more reliable than testing function behavior.
- main.py Gate 2 uses injectable FixedRng (duck-typed `randint` object) to test exact clamp behavior without RNG state dependencies.

### Injectable-clock harness for main-loop timeout tests (2026-06-10)
- I2 (30s confidence-hold) and ARD §5.4 (10s both-fail) tests drive the main loop with injectable clock (`clock` kwarg to `run()`) + FakeTransport + FakeSensorStream.
- FakeClock with `step=1.0` advances 1s per clock() call. With 2 calls per normal frame, 40 frames covers 40s > 30s timeout. For the both-fail path (1 call per frame, `continue` skips elapsed), 15 frames × 1.0s = 15s > 10s timeout.
- FakeSensorStream.start() must be called before iteration; this is Ng's pattern from sensors.py's own FakeSensorStream.
- Timer re-arm: after a timeout send, `both_fail_start = tick_start` and `last_send_time = tick_start` reset the windows. Test verifies exactly 1 send in the first N frames.

### Librarian's neutral-zone confidence design (2026-06-10)
- `compute_mood()` returns `confidence=0.6` for the neutral tension band (0.35–0.65). Since `CONFIDENCE_GATE=0.7`, ALL neutral readings are gated (even with both sensors ok). This is an intentional design: the neutral zone is ambiguous, so the creature only transitions to calm/stressed (confidence=0.8 > gate). Neutral updates only fire via the 30s timeout. Tests confirm this via test_confidence_gate_sets_gated_true.

### Strict vs non-strict threshold boundary (2026-06-10)
- Contract specifies `STRESS_THRESHOLD=0.65` but NOT whether the comparison is `>` or `>=`. Librarian chose strict `>`. At exactly `tension=0.65`, mood is "neutral" not "stressed". Documented in decision juanita-week2-tests.md; no rejection because spec is silent on boundary direction.

### pytest.mark.parametrize on unittest.TestCase methods silently fails (2026-06-10)
- `@pytest.mark.parametrize` on a `unittest.TestCase` method generates ONE test that ignores the parametrize data and calls the method with no args → TypeError. Always use a plain pytest class (no TestCase inheritance) for parametrized tests.

### Test doubles must mirror the typed seam they stand in for (2026-06-12)
- FakeTransport.on_receive lacked `callback: Callable[[bytes], None]` while Transport Protocol declared it; annotation-only fix caught in cycle-2 review. When adding a fake, copy the full signature (params + types + return) from the Protocol it implements.

## Week 2 Review-Fix Regression Wave Learnings (2026-06-12)

**B1 — Baseline must learn raw tension, not mood-transformed intensity**

Added `test_regression_b1.py` with two classes:
- `TestComputeMoodTensionField` (B1a): verifies `result.tension` equals the raw weighted score
  (`pitch*0.4 + accel*0.3 + rot*0.3`), and that for a calm frame `result.tension ≠ result.intensity`
  (calm: `intensity = 1 - tension`, so they're maximally different when tension ≈ 0).
- `TestRunUsesRawTensionForBaseline` (B1b): the regression test that would have *caught* the bug —
  injects a calm frame via `FakeSensorStream`, spies on `update_baseline` via `unittest.mock.patch`,
  asserts the second argument equals `result.tension (0.0)` not `result.intensity (1.0)`.
  Key insight: choose a calm frame because `intensity = 1 - tension` is maximally distinguishable.

**B2 — run() is the SOLE pacer; SensorStream must not self-pace**

Added `test_regression_b2.py` with:
- `TestSensorStreamNoPacing` (B2a): structural test via `inspect.getsource(SensorStream.__anext__)` —
  asserts no `asyncio.sleep` or `time.sleep` in the source. Non-flaky, instant.
- `TestRunPacingUnconditional` (B2b/B2c): behavioral — injects a spy `sleep` callable, feeds 5
  gated frames and 5 both-fail frames separately, asserts `sleep` was called once per frame.
  Design principle: `sleep` is injectable (no real wall-clock wait), count assertions are exact.

**B2 — Removed ~5.5s real-sleep overhead from existing timing tests**

Refactored `run()` in `host/main.py` to accept `sleep: Callable[[float], Awaitable[None]] = asyncio.sleep`
(backward-compatible default). Updated `test_confidence_gating.py` and `test_fallback.py` to pass
`sleep=noop_sleep`. Suite went from **6.11s → 0.30s** (20× speedup).

**I1 — load_baseline fail-safe (hostile/corrupt inputs)**

Added `TestLoadBaselineFailSafe` to `test_inference.py`: covers malformed JSON, bad types
(`mean="EVIL"`, `stddev="EVIL"`), negative `sample_count`, missing keys, non-existent path, and a
happy-path sanity case. Uses `tmp_path` — never touches the real `~/.vesper/baseline.json`.

**ESCALATION — I1 gap: negative stddev not rejected by load_baseline**

`inference.py` lines 78-85: the validation checks `math.isfinite(b.stddev)` but NOT `b.stddev >= 0.0`.
A negative stddev is physically impossible and would corrupt Welford stats on the next update.
`test_negative_stddev_returns_none` is marked `@pytest.mark.xfail(strict=True)` documenting the gap.
**Juanita rejects; Librarian (inference.py owner) must fix.**

**I2 — update_baseline hardened (non-finite tension, variance floor)**

Added `TestUpdateBaselineHardened` to `test_inference.py`: NaN tension → baseline unchanged;
+inf/-inf tension → unchanged; `NaN` with `None` baseline → zero-sample Baseline returned; variance
floor prevents `math.sqrt(negative)` from corrupted prior.

**I5 — _send_neutral_fallback uses quantise+jitter pipeline**

Added `TestSendNeutralFallbackPipeline` to `test_main.py`: with seeded RNG, fallback packet's
intensity byte equals `quantise_intensity(0.5) → 50 → apply_intensity_jitter(50, rng=seed)`,
within ±5 of bucket 50. Proves no special-case wire path.

**M6 — FakeTransport/FakeClock/FakeSensorStream deduplication**

Extracted into `tests/helpers.py` as the single canonical source.
`FakeSensorStream` re-exports `host.sensors.FakeSensorStream` (richer canonical version).
`conftest.py` adds `tests/` to `sys.path` so `from helpers import ...` resolves in test files.
Both `test_confidence_gating.py` and `test_fallback.py` now import from `helpers` — local class
definitions removed. `noop_sleep` added to `helpers.py` as a no-op async sleep for injection.
