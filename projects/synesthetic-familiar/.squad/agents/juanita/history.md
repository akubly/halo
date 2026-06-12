# Juanita Agent History

## Learnings

### 2026-06-12 — Week 2 Review-Fix Regression Wave

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
