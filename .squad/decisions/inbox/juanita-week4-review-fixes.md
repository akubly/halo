# Decision Note: Juanita Week-4 Review Fixes

**Date:** 2026-06-14  
**Author:** Juanita (QA/Test Specialist)  
**Branch:** `synesthetic-familiar/week4-it-sees`  
**Status:** RESOLVED — 304 passed, 0 failed

---

## Context

Raven's persona-review of the Week-4 acceptance suite (commit pre-6f7d917) identified 6
blocking/API conditions against the tests.  Librarian had since finalized the
`model_sync`/`inference` API in commit 6f7d917, making the conditions actionable.

---

## Conditions Addressed

### [B1] Vacuous pass — test_weight_cannot_exceed_two_times_default

**Problem:** The extreme-update dict used Phase-1 IMU keys (`pitch_var`, `imu_accel`,
`imu_rot`).  `apply_weight_update` silently ignores unknown keys — only
`visual_activity` and `visual_brightness` are recognized.  The result dict contained
only visual keys at near-default EMA values; the `for key in population_defaults` loop
executed zero iterations.  The test passed every run regardless of what the function did.

**Decision:** Rewrite to use `visual_activity` and `visual_brightness` at 10× their
defaults.  Add a **presence guard** (`assert present_keys`) before the bounds loop.
If the function ever drops expected keys, the guard fails loudly instead of silently
skipping assertions.

**Rationale:** The guard is a permanent structural invariant, not a one-off workaround.
Any future refactor that renames or drops visual keys will immediately surface here
rather than silently regressing to another vacuous pass.

---

### [API-REF 1] test_hash_mismatch_does_not_modify_global_state

**Problem:** Called `_model_sync.get_current_weights()` which was removed when
`model_sync` became pure-functional (no module-level mutable state).  Test was
skipping with "Add get_current_weights() to model_sync.py".

**Decision:** Rewrite to exercise `sync_population_weights(manifest, current)` directly.
Pass a sentinel `VisualWeights(visual_activity=0.12, visual_brightness=0.04)` as
`current`, supply a manifest with `sha256="a"*64` (guaranteed mismatch), mock
`build_opener` to return valid-looking bytes, and assert `result == current`.  No getter
needed — the pure-functional contract is: on failure, return the caller's current weights
unchanged.

---

### [API-REF 2] test_weights_can_be_reset_to_defaults

**Problem:** After calling `reset_weights_to_defaults()`, the test fetched
`get_current_weights()` to verify the reset.  `get_current_weights` is gone; the
trailing block was dead code that silently returned without asserting anything.

**Decision:** Assert directly on the return value of `reset_weights_to_defaults()`.
Normalise to dict (handles both `VisualWeights` and plain-dict returns), then compare
field-by-field against `DEFAULT_VISUAL_WEIGHTS`.  This makes the test meaningful
independent of any getter.

---

### [API-REF 3+4] build_opener patching (test_download_request_contains_no_user_id, test_correct_hash_accepts_weights)

**Problem:** Both tests patched `urllib.request.urlopen`, but Librarian's `_download_bytes`
now calls `urllib.request.build_opener(_HTTPSOnlyRedirectHandler()).open(req, timeout=...)`.
The `urlopen` patch was a no-op: the real network call to `https://example.com/model.json`
fired, hit a 404, and either raised `HTTPError` (causing `test_correct_hash_accepts_weights`
to `pytest.fail`) or returned before capturing any requests (causing `assert captured_requests`
to fail in `test_download_request_contains_no_user_id`).

**Decision:** Patch `urllib.request.build_opener` to return a `MagicMock` opener.
Configure `mock_opener.open.side_effect` / `.return_value` as needed.  The `Request`
object passed to `opener.open()` is still inspectable for URL/header privacy checks.

**Rule going forward:** When Librarian (or any implementer) changes the urllib seam, grep
test files for the old patch target and update them.  The canonical seam is whichever
`urllib.request` function the *production code* calls last before the network socket opens.

---

### [NEW] Negative-scheme rejection tests (M3 + I2 coverage)

**Decision:** Add `TestModelI5_NegativeSchemeDownload` — plain pytest class (no
`TestCase`, required for `parametrize`) with four cases:

| URL | Scheme | Expected |
|-----|--------|----------|
| `file:///etc/passwd` | `file` | `ValueError` |
| `ftp://example.com/w.json` | `ftp` | `ValueError` |
| `data:application/json,{}` | `data` | `ValueError` |
| `""` | `""` | `ValueError` |

No mock needed — `_download_bytes` raises before any network I/O.

Also added `test_redirect_downgrade_to_http_raises_value_error` which mocks the opener
to raise the `ValueError` that `_HTTPSOnlyRedirectHandler.redirect_request` would emit
on a `302 https://… → http://…` redirect, verifying that `download_weights` propagates
the error rather than swallowing it.

**Rationale:** `file://` and `data:` URLs are common SSRF vectors.  The redirect
downgrade covers a subtle MODEL-I5 risk: a CDN that silently downgrades from HTTPS to
HTTP on redirect.  These cases have zero runtime cost (all fire before network I/O) and
permanently document the threat model.

---

## Final state

| Metric | Before | After |
|--------|--------|-------|
| Passing | 296 | 304 |
| Failing | 2 | **0** |
| Skipped | 20 | 19 |
| New tests | — | +6 (4 parametrized negative-scheme + redirect test, plus existing fixes) |

Skips are exclusively Ng's deferred `_CameraRelay` tests (CAMERA-I1, CAMERA-I6 relay
path, relay edge cases, mid-BLE drop) — all correctly gate on `_CAMERA_RELAY_AVAILABLE`.
