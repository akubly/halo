# Juanita — QA/Test Specialist (Archived Context Summary)

**Owner:** Aaron Kubly | **Project:** halo mono-repo | **Role:** Tests, test infra, edge cases, correctness review

📌 **Archived content:** Pre-Week-4 history has been moved to history-archive.md (see that file for Week 1–3 context, persona-review cycles, and prior learnings).

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
- **build_opener patch scope is ALL model_sync privacy tests:** The urlopen→build_opener patch-target lesson applies to every MODEL-I5 test in `test_week4_privacy_gates.py`, not just the two (no-user-id, correct-hash) fixed in the first pass — `test_hash_verified_before_applying_weights` required the same fix in Cycle 2.
- **Negative-scheme coverage:** `file://`, `ftp://`, `data:`, and `""` URLs all trigger the scheme check in `_download_bytes` before any network connection.  No mock needed for these cases — the `ValueError` fires synchronously.
- **Pure-functional state-isolation test:** For pure-functional APIs with no global state, prove fail-closed behaviour by passing a sentinel `current` and asserting `result == current` — no getter required.

---

📌 Team update (2026-06-15T05:37:29Z): Week-4 camera SDK gate resolved BLOCKED (CAMERA-I3); Librarian shipped Option-C cloud sync; Juanita delivered 53 new tests (296 passed, 22 skipped); Raven approved with 6 merge-blocking conditions. Phase-2 shipping cloud-refinement; camera deferred Phase-3 — decided by Ng, Librarian, Juanita, Raven

---

## 2026-06-15 — PR #5 Copilot Review Fixes (5 comments)

**Branch:** `synesthetic-familiar/week4-it-sees`
**Files touched:** `tests/test_week4_privacy_gates.py`, `tests/test_week4_camera_edge_cases.py`

### Fixes delivered

**C1 — Force logger level in `_collect_logs_above_debug`**

pytest sets the root logger to WARNING by default.  `_collect_logs_above_debug` was
adding a capture handler but not touching the target logger's level — so INFO records
were discarded by the logger before reaching the handler, making any CAMERA-I6 test
that expected INFO violations pass vacuously.

Fix: save the target logger's level, force it to `logging.INFO` if it was NOTSET or
higher than INFO, and restore it in the `finally` block.  Also set `propagate = False`
during capture to prevent double-counting via the root logger.

**C2 — Align CAMERA-I6 banned list to image content, not the word "jpeg"/"jpg"**

The previous banned list included the bare words `"jpeg"` and `"jpg"`, which would
wrongly fail a benign diagnostic message like `"JPEG decode failed"`.  CAMERA-I6 bans
image *content* (bytes, pixel data, dimensions) — not terminology.

Fix: removed `"jpeg"` and `"jpg"` from the banned word list; retained `"pixel"`,
`"raw_frame"`, `"image_data"`.  Added a regex check for `bytes` repr patterns
(`b'\xNN...`) and keyword checks for explicit dimension keys (`width=`, `height=`,
`dimensions=`, `byte_count=`).

**C3/C4/C5 — Patch `build_opener` (not `urlopen`) in camera_edge_cases.py**

`download_weights()` calls `_download_bytes()` which uses
`urllib.request.build_opener(...).open(req, timeout=...)`.  Three tests in
`test_week4_camera_edge_cases.py` were patching `urllib.request.urlopen` — a
completely different code path — so the real implementation was never intercepted.
For C3 this meant the hash-mismatch test could hit the real network or swallow
a real error.  For C4/C5, the tests could mask a crash or silently pass with
real network traffic.

Fix: replaced all three `patch("urllib.request.urlopen", ...)` patterns with
`patch("urllib.request.build_opener", return_value=mock_opener)` where
`mock_opener.open.side_effect` delivers the intended response or raises the
intended error.  Added a `assert mock_called` sentinel to each test so they
can never pass vacuously without touching the mock.

### Result

**304 passed, 19 skipped, 0 failed.**  All 19 skips are Ng's deferred `_CameraRelay`
tests.  No behaviour change to passing tests.

## Learnings

- **Force logger level for log-capture tests:** Attaching a `logging.Handler` is not
  enough — if the logger's effective level is WARNING (pytest default), INFO records
  are silently discarded before reaching any handler.  Always save and set the target
  logger to `logging.INFO` for the duration of the capture, then restore.

- **Align CAMERA-I6 assertions to image content, not the word "jpeg":** CAMERA-I6
  bans image *content* leakage (bytes repr, pixel data, dimensions) — not the English
  word "jpeg", which can appear innocuously in diagnostic messages.  Banning the word
  itself would produce false positives on benign log lines like "JPEG decode failed".

- **The `build_opener` patch lesson extends to camera_edge_cases.py too:** Every test
  that exercises `download_weights()` (or any function that calls `_download_bytes()`)
  must patch `urllib.request.build_opener`.  Patching `urlopen` leaves the production
  code path completely untouched — the test either hits the real network or silently
  ignores a crash.  Always add a `mock_called` sentinel assertion so the test fails
  loudly if the patch target drifts again.

- **Keep test docstrings aligned to the real function contract:** `download_weights` returns `bytes | None` (raw verified bytes, or `None` on hash mismatch) — it does NOT return a parsed weights dict and does NOT raise on hash mismatch (only on non-HTTPS scheme or network error).
