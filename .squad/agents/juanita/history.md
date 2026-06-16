# Juanita — QA/Test Specialist (Archived History Summary)

**Owner:** Aaron Kubly | **Project:** halo mono-repo | **Role:** Tests, test infra, edge cases, correctness review

## Pre-Week-3 Context (Archived)

**Week 1 (2026-06-09):** Learned `--cov-fail-under` without `--cov=<module>` is silently ignored; selective gate on critical modules (familiar_protocol.py at 95%) more honest than blunt global threshold.

**Week 2 (2026-06-10):** Delivered 47 new tests across 6 files (101 total, all green). Privacy gate I7, familiar-update Gate 1, intensity quantise/jitter Gate 2, confidence-hold I2, both-fail fallback all verified. Extracted FakeClock/FakeSensorStream/FakeTransport to `tests/helpers.py`.

**W2 Review-Fix Cycle (2026-06-12):** 5 regressions documented + fixed: B1 (tension vs intensity in baseline), B2 (SensorStream pacing removed), I1 (load_baseline fail-safe), I5 (_send_neutral_fallback pipeline), M6 (test double deduplication).

## Week 3 Acceptance Suite (2026-06-13)

**Phase 1 — Reset + Activation + Onboarding (48 tests → 176 passing total)**

| File | Tests | Focus |
|------|-------|-------|
| `test_week3_reset.py` | 17 | FAMILIAR_RESET protocol (14✓) + host-reaction contract (3 xfail→Ng) + W3-1 snapshot zeroing (2✓) |
| `test_week3_baseline_activation.py` | 34 | Activation gate @ sample_count ≥ 50 (all passing; Librarian landed) |
| `test_week3_onboarding.py` | 13 | 2 passing (load_baseline), 11 skipped (pending Y.T. host/onboarding.py) |

**Key discoveries:** Librarian had already landed ACTIVATION_THRESHOLD=50; main.py logs FAMILIAR_RESET but has no host-reaction logic (xfail gates Ng); get_activation_info() exportable by Y.T.

**Phase 2 — Fallback Depth + Threshold Tuning (72 new tests → 262 total)**

| File | Tests | Focus |
|------|-------|-------|
| `test_week3_fallback_depth.py` | 9 | Timeout boundaries (strict >), recovery after fallback, RESET-during-both-fail |
| `test_week3_threshold_tuning.py` | 37 | Confidence gate strict <, activation 49/50/51 boundary, quantisation 10-point parametrize, jitter ±5 clamping (55 exhaustive) |
| `test_week3_ble_flake.py` | 26 | Garbled device bytes (10 parametrized), extreme/NaN/Inf sensor values, heap-guard gap structural test |

**Result:** 262 tests all green. No rejections — all contracts (both-fail, confidence-hold, activation, quantisation, jitter, BLE flake) correct in code.

**Heap-guard finding:** FamiliarAck has no heap field. Test `test_familiar_ack_has_no_heap_field` is a structural anchor — fails if Ng adds heap field, prompting host-side handler review.

**Decision record:** `juanita-week3-fallback.md` merged to decisions.md.



**Test-first 48 new tests delivered across 3 files. Suite: 176 passing, 3 xfailed (Ng contract), 11 skipped (Y.T. pending).**

**Acceptance-test gates documented for all team members:**
- Ng: FAMILIAR_RESET must trigger NEUTRAL send + seq reset in async loop (xfail gates the PR)
- Librarian: ACTIVATION_THRESHOLD must use >= (not >); no baseline=None revert; confidence gating intact (34 tests gate merge)
- Y.T.: is_first_launch() pure; marker file created; no hardcoded ~/.vesper paths (tests gate module creation)
- Infrastructure: finally block + samples[:]=0.0 must remain (W3-1 structural gates merge)

**Key achievement:** 100% test coverage of Week 3 gate contracts. Tests are ready to drive implementation as each team member ships.

**Decision file:** `.squad/decisions.md` (merged from `.squad/decisions/inbox/juanita-week3-tests.md`)



📌 Team update (2026-06-14T05:36:23Z): Raven privacy audit APPROVED all surfaces; Ng shipped ATTENTION visuals; Y.T. host complete; docs synced (Librarian); 262 tests green — ready for ship — decided by Raven, Ng, Y.T., Librarian

---

## 2026-06-13 — Week 3 Persona-Review Fix (Cycle 1) — [MINOR M5]

**File:** `tests/test_week3_threshold_tuning.py` only.

### Finding fixed

`test_gate_is_strict_less_than_not_less_than_or_equal` was a tautology: it
constructed `MoodResult` manually with `gated=(CONFIDENCE_GATE < CONFIDENCE_GATE)`
(always `False`) and asserted that field.  `compute_mood` was never called.

### Fix

Replaced with four real `compute_mood` calls producing confidence values that
straddle `CONFIDENCE_GATE` (0.7) from both sides:

| Inputs | Confidence | gated |
|--------|-----------|-------|
| stressed + both ok | 0.80 | `False` |
| stressed + imu_ok=False | 0.56 | `True` |
| stressed + mic_ok=False | 0.48 | `True` |
| neutral + both ok | 0.60 | `True` |

Each case includes a cross-check `result.gated == (result.confidence < CONFIDENCE_GATE)`
to guard against any future `<` → `<=` regression in `inference.py`.

Confidence == 0.7 is not reachable via normal `compute_mood` inputs (discrete levels
noted in lessons below).

### Result

**40/40 tests passed** (0.09 s).  All other tests untouched.

### Durable lessons

- **Reject tautologies:** any test that constructs the production dataclass and passes
  the same field it then asserts is testing itself, not the production code.
- **When exact boundary isn't reachable:** straddle from both sides + cross-check
  `result.field == formula(result.inputs)` to catch future regressions that land on the boundary.
- **compute_mood discrete confidence levels (2026-06-13):**
  0.8, 0.56, 0.48, 0.336 (stressed/calm combos); 0.6, 0.42, 0.36, 0.252 (neutral combos).

---

### Cycle 2 Re-Review (2026-06-14)

**Team decision:** All Cycle 1 findings (M5) verified ADDRESSED in Cycle 2 re-review (Correctness, Skeptic, Architect panels). Tautological test replaced with real boundary-straddling cases. Final: 265 tests passing.

**Ready for ship-to-pr:** Push branch `synesthetic-familiar/week3-its-alive`, open PR, request Copilot review, then cloud-review-cycle, then squash-merge.

**Phase-2 deferral:** Multi-threaded host test strategy (if adopted).

---

## 2026-06-14 — PR #4 Copilot Review Fixes

**Branch:** `synesthetic-familiar/week3-its-alive`  
**Files touched:** `tests/test_week3_threshold_tuning.py`, `tests/test_week3_fallback_depth.py`

### Fix 1 — Removed unused `import math` (threshold_tuning.py)

`import math` was left behind after the tautological `MoodResult` test was replaced
with real `compute_mood` boundary calls (see Cycle 1 above). The replacement used no
`math.*` calls, making the import dead. Confirmed with ripgrep — zero `math.` references
in the file.

**Durable lesson:** After a substantial test rewrite, scan remaining imports; the old
test scaffold often leaves behind helpers that the new implementation doesn't need.

### Fix 2 — Clarified off-by-one docstring wording (fallback_depth.py)

`test_reset_during_both_fail_sends_neutral_once` had a misleading summary line:
`"FAMILIAR_RESET fires after frame 3."` — ambiguous between 1-indexed "the 3rd frame"
and 0-indexed "frame index 3" (which would be the 4th frame).

`_ResetCallbackStream(reset_at=3)` fires the callback when `self._idx == 3` after
incrementing — meaning it fires after yielding frame **index 2**. The FakeClock timing
block and the inline comment already said this correctly; only the summary line was wrong.

Fixed to: `"FAMILIAR_RESET fires after frame index 2 (0-indexed)."`

**Durable lesson:** When a docstring has a summary line *and* a step-by-step timing
section, both must use the same indexing convention explicitly. If one uses 0-indexed
and the other uses English ordinals ("after frame 3"), the reader can't tell which is
authoritative without reading the implementation.

**Durable lesson:** `_ResetCallbackStream(reset_at=N)` fires after yielding frame
index **N-1** (because `_idx` is incremented before the check `_idx == reset_at`).
Document this as frame index N-1, not N.

### Result

**265/265 passed** (0.40 s). No behavior change.

📌 Team update (2026-06-14T07:59:43Z): Phase-2 plan drafted (camera + cloud refinement) — pending Aaron approval. Decisions: Enzo (capability scope), Hiro (architecture). No code written. Affected: implementation lead (Ng), privacy review (Raven), docs (Librarian), testing (Juanita), infrastructure (Da5id).

---

## 2026-06-14 — Week 4 "It sees" Acceptance Tests

**Branch:** `synesthetic-familiar/week4-it-sees`
### Suite result: 318 collected — 296 passed, 22 skipped, 0 failed.
  (265 prior tests: all still green. 53 new tests: 31 active now, 22 pending implementers.)

  **Note:** Librarian's `model_sync.py` had already landed with `download_weights`, `sync_population_weights`, and `tune_visual_weights`, so the MODEL-I5 privacy tests activated immediately and all passed against Librarian's implementation. Only Ng's camera/relay code is still pending (22 skipped).

### Learnings

#### Week-4 edge cases enumerated and covered
All six §6 edge cases from the architecture draft now have test coverage:
1. **camera_ok transitions False→True and True→False** — `TestCameraContribution` in test_week4_sensorframe_camera.py
2. **BLE drop mid-JPEG reassembly** — `TestCameraRelayEdgeCases.test_mid_ble_transfer_drop_resets_reassembly`
3. **Partial / corrupt JPEG** — `TestCameraRelayEdgeCases.test_partial_or_corrupt_jpeg_returns_defaults` (4 parametrized cases)
4. **Camera present but all-dark** — `TestCameraContribution.test_all_dark_scene_does_not_crash`
5. **Model download hash mismatch** — `TestModelSyncHashMismatch` (4 parametrized tamper strategies)
6. **Model server unreachable → graceful local fallback** — `TestModelSyncServerUnreachable` (4 network error types)

#### Additive-invariant test approach
The core Week-4 gate is the **additive invariant**: camera_ok=False must produce EXACTLY Phase-1 behavior. Approach:
- `TestAdditiveInvariant.test_camera_absent_matches_phase1_output` parametrizes 6 sensor combinations, calls compute_mood twice (with and without camera params), asserts identical mood/confidence/tension/gated.
- `test_camera_ok_false_does_not_reduce_confidence_vs_phase1` is a separate regression guard against the "penalise camera absence" mistake.
- Both skip cleanly (not xfail) until Librarian adds `camera_ok` to `compute_mood`; they activate automatically.

#### Test file paths
| File | Tests | Active now | Pending |
|------|-------|-----------|---------|
| `tests/test_week4_sensorframe_camera.py` | 20 | 13 | 7 (Ng's SensorFrame camera fields + Librarian's compute_mood visual params) |
| `tests/test_week4_privacy_gates.py` | 12 | 4 | 8 (Ng's _CameraRelay + Librarian's model_sync) |
| `tests/test_week4_camera_edge_cases.py` | 21 | 2 | 19 (Ng's _CameraRelay + Librarian's model_sync) |

#### What's active now (19 tests)
- CAMERA-I2: SensorFrame surface has no bytes/image fields or values (classicist, immediate)
- Structural anchor: Phase-1 `compute_mood` still callable without camera params
- Structural anchor: Baseline activation gate (sample_count >= 50) unchanged
- Log-emission baseline: SensorFrame construction emits no JPEG bytes at INFO+
- `test_camera_ok_false_default_means_all_sensorframes_are_phase1_compatible` (skips until Ng's fields land — activates automatically)

#### What's pending and gates which PR
- **Ng's PR** (sensors.py camera fields + `_CameraRelay`): gates 7 SensorFrame field tests + CAMERA-I1 buffer-zeroing tests + BLE relay edge cases (24 tests total)
- **Librarian's PR** (compute_mood visual params + model_sync.py): gates additive-invariant tests + MODEL-I5 tests + online weight bounds tests (28 tests total; some overlap with Ng gate)

#### Durable lessons
- `pytest.skip` (not `xfail`) for "pending implementer code" — skips are silent and turn green automatically; xfail requires you to know they'll eventually pass and adds `.xpass` churn when they do.
- Additive-invariant tests that compare Phase-1 and Phase-2 calls side-by-side are more reliable than trying to predict absolute values — they survive future heuristic tuning.
- For MODEL-I5 request-privacy tests, intercepting `urllib.request.urlopen` and inspecting the Request object is the right seam — it catches both URL query params and custom headers without requiring a real HTTP server.
- `_COMPUTE_MOOD_CAMERA_LANDED` detection via `inspect.signature()` is cleaner than try/except TypeError — it skips at the top of each test method rather than inside a try block.

---

## 2026-06-14 — Week-4 Persona-Review Fix (Raven conditions)

**Branch:** `synesthetic-familiar/week4-it-sees`

### Fixes delivered

**B1 — Vacuous pass via unknown keys (test_weight_cannot_exceed_two_times_default)**

The original test used Phase-1 IMU keys (`pitch_var`, `imu_accel`, `imu_rot`) in the
`apply_weight_update` call.  The pure-functional API silently ignores unknown keys — it
only processes `visual_activity` and `visual_brightness`.  This meant the extreme-value
update was a no-op, the result dict contained only visual keys at their EMA-blended
defaults, and the `for key in population_defaults` loop never executed a single assertion.
The test passed vacuously every run.

**Fix pattern:** (1) Use the *actual* keys the function accepts (`visual_activity`,
`visual_brightness` with 10× default values).  (2) Add a **presence guard** before any
bounds assertion: `assert present_keys` ensures the result contains at least one expected
visual key.  If the function ever drops visual keys from its output, the guard fails
loudly instead of silently skipping the assertion.

> **Lesson (HIGH confidence):** When testing a function that silently ignores unknown keys,
> always assert that at least one expected key is present in the result *before* asserting
> the value.  Without the guard, an update dict built from wrong-namespace keys will pass
> every bounds check vacuously.

**API-REF fixes — removed `get_current_weights` references**

`get_current_weights` was removed as part of making `model_sync` pure-functional.  Two
tests referenced it:

- `test_hash_mismatch_does_not_modify_global_state`: Rewrote to call
  `sync_population_weights(manifest, current)` with a mismatched hash and assert the
  return value equals the passed-in `current`.  No getter needed — the contract is
  directly expressed by the return value.
- `test_weights_can_be_reset_to_defaults`: Rewrote to assert on the return value of
  `reset_weights_to_defaults()` directly against `DEFAULT_VISUAL_WEIGHTS`.  The
  `get_current_weights` check at the end was dead code (would have skipped) — now
  replaced with a real assertion.

**build_opener patching (test_download_request_contains_no_user_id, test_correct_hash_accepts_weights)**

`_download_bytes` was updated by Librarian to use `urllib.request.build_opener(...).open(...)`
instead of `urllib.request.urlopen`.  Tests that patched `urlopen` stopped intercepting
the real code path — `captured_requests` was always empty, causing `assert captured_requests`
to fail.

**Fix:** Patch `urllib.request.build_opener` to return a `MagicMock` opener.
The mock opener's `.open(req, timeout=...)` captures the `Request` object for inspection
(privacy test) or returns a fake response (acceptance test).  The `_HTTPSOnlyRedirectHandler`
passed to `build_opener` is consumed by the call but our mock returns immediately —
sufficient because we are testing `download_weights` behaviour, not the redirect handler
itself.

> **Lesson (HIGH confidence):** When patching urllib internals, patch at the boundary the
> *production code* actually calls.  If the production code calls `build_opener().open()`,
> patch `urllib.request.build_opener`; if it calls `urlopen`, patch `urlopen`.  Patching
> the wrong seam leaves the real code path untouched and produces vacuous passes
> (network errors caught silently) or outright failures (expected mocks never fire).

**New negative-scheme tests (M3 + I2 coverage)**

Added `TestModelI5_NegativeSchemeDownload` — plain pytest class (not TestCase, so
`parametrize` works) with four parametrized cases covering `file://`, `ftp://`, `data:`,
and empty-string URLs.  Each case asserts `ValueError` is raised before any network I/O.
Also added `test_redirect_downgrade_to_http_raises_value_error` which mocks the opener to
raise the `ValueError` that `_HTTPSOnlyRedirectHandler` would emit, verifying that
`download_weights` propagates it.

### Result

**304 passed, 19 skipped, 0 failed.**  All model_sync/bounds/privacy tests active and
passing.  Skips are exclusively Ng's deferred `_CameraRelay` tests.

### Learnings

- **Vacuous pass via unknown key dict:** `apply_weight_update` silently ignores keys not in `{visual_activity, visual_brightness}`.  Using wrong-namespace keys in an extreme-update dict produces a no-op; the bounds assertion loop runs zero iterations.  Always assert key presence before asserting values.
- **build_opener patching:** After Librarian changed `_download_bytes` to `build_opener().open()`, any `urlopen` patch is a no-op.  Patch the function the production code actually invokes (`urllib.request.build_opener`) and configure its return value's `.open()` method.
- **Negative-scheme coverage:** `file://`, `ftp://`, `data:`, and `""` URLs all trigger the scheme check in `_download_bytes` before any network connection.  No mock needed for these cases — the `ValueError` fires synchronously.
- **Pure-functional state-isolation test:** For pure-functional APIs with no global state, prove fail-closed behaviour by passing a sentinel `current` and asserting `result == current` — no getter required.

---

📌 Team update (2026-06-15T05:37:29Z): Week-4 camera SDK gate resolved BLOCKED (CAMERA-I3); Librarian shipped Option-C cloud sync; Juanita delivered 53 new tests (296 passed, 22 skipped); Raven approved with 6 merge-blocking conditions. Phase-2 shipping cloud-refinement; camera deferred Phase-3 — decided by Ng, Librarian, Juanita, Raven
