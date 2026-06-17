# Decision: Week 4 Persona-Review Fixes — Librarian

**Date:** 2026-06-15  
**Branch:** `synesthetic-familiar/week4-it-sees`  
**Owner:** Librarian (AI/ML)  
**Files changed:** `projects/synesthetic-familiar/host/inference.py`, `projects/synesthetic-familiar/host/model_sync.py`

---

## Summary

Applied all Aaron-accepted persona-review findings to `inference.py` and `model_sync.py`.  No test files were modified.

---

## Fixes Applied

### I1 — Pure-Functional State Design (model_sync.py)

**Decision:** Remove `get_current_weights()` entirely. Update `apply_weight_update` signature to `(update: dict, alpha: float = 0.1, current: VisualWeights = DEFAULT_VISUAL_WEIGHTS) -> dict`. EMA blends FROM `current`, not from a hardcoded default.

**Rationale:** `get_current_weights()` returned a snapshot of `DEFAULT_VISUAL_WEIGHTS` — data that was never mutated. It implied the module owned weight state when it doesn't and never did. The `apply_weight_update` old signature hardcoded `DEFAULT_VISUAL_WEIGHTS` as the EMA base, making it impossible for callers to accumulate state across successive updates. The pure-functional pattern (caller owns state, module is stateless) is correct for this use case and is now explicit in the module docstring.

**Module docstring addition:** "This module is pure-functional: there is NO internal mutable weight state. Callers own and persist current weights."

---

### I2 — HTTPS Redirect Downgrade Protection (model_sync.py)

**Decision:** In `_download_bytes`, replace `urllib.request.urlopen(req, ...)` with `urllib.request.build_opener(_HTTPSOnlyRedirectHandler()).open(req, ...)`. The handler subclasses `HTTPRedirectHandler` and raises `ValueError` (referencing MODEL-I5) on any redirect whose target scheme is not `https`.

**Rationale:** The initial scheme check (`parsed.scheme != "https"`) only guards the original URL. An HTTPS URL that 301-redirects to HTTP would pass the initial check and silently download from plain HTTP. The redirect handler intercepts this before the downgraded request is made.

**Side effect:** Tests that patch `urllib.request.urlopen` will no longer intercept `_download_bytes` calls (see Juanita fix list below).

---

### I3 — Strict Camera Gate (inference.py)

**Decision:** Change `if camera_ok:` to `if camera_ok is True:` in `compute_mood`. When `camera_ok` is not `True` but non-default visual inputs are passed, emit `logger.debug` noting visual inputs are being ignored (CAMERA-I6).

**Rationale:** The additive invariant requires that only the exact bool `True` unlocks the camera path. Truthy-but-not-bool values (e.g. `1`, a non-empty string, a `MagicMock`) could accidentally activate the camera augmentation path. The strict identity check is the only way to prove the invariant structurally. The debug log is a diagnostic aid for integration: if someone passes `camera_ok=1` with visual inputs and sees no effect, the log explains why.

---

### I4 — Version Enforcement (model_sync.py)

**Decision:** In `_parse_population_weights`, check `obj.get("version") != "1"` immediately after JSON parse and raise `ValueError` with a clear message. All field extraction happens only after version is confirmed.

**Rationale:** Schema versioning is only as strong as the boundary that enforces it. A silent assumption that an unversioned or v2 payload is valid v1 data would silently accept potentially incompatible formats and make future version bumps undetectable.

---

### I5 — Document Dormant Sync (model_sync.py docstring)

**Decision:** Added a `─── DORMANT CAPABILITY (Phase-3 activation) ───` section to the module docstring:  
> "The sync capability shipped in Week 4 is NOT yet wired into the runtime loop. It will activate alongside the camera in Phase 3 — population visual-weights have nothing live to tune while the camera is deferred. This is intentional, not an oversight."

---

### I6 — Document Trust Model (model_sync.py docstring)

**Decision:** Added a `─── TRUST MODEL ───` section:  
> "Integrity rests on HTTPS transport + SHA-256 content verification (MODEL-I5). There is NO host allowlist, certificate pinning, or signed manifest. This is acceptable for a single-user playground environment. Future hardening path: signed manifest (GPG/ECDSA) + host pinning."

---

### M1 — Timing-Safe SHA-256 Comparison (model_sync.py)

**Decision:** Replace `actual == expected_hex.lower().strip()` with `hmac.compare_digest(actual, expected_hex.lower().strip())`. Added `import hmac`.

**Rationale:** String equality (`==`) is not timing-safe. Although hash comparison timing side-channels are extremely unlikely to be exploitable in this single-user context, using `hmac.compare_digest` is the correct baseline — it's a one-line change that closes the theoretical attack surface with zero downside.

---

### M2 — Defense-in-Depth Bounds at Trust Boundary (model_sync.py)

**Decision:** In `_parse_population_weights`, after the `>= 0` / `isfinite` checks, also reject values exceeding `DEFAULT_VISUAL_WEIGHTS.<field> * MAX_VISUAL_WEIGHT_MULTIPLIER` with `ValueError`.

**Rationale:** `tune_visual_weights` already clamps values downstream. The trust boundary (`_parse_population_weights`) should also enforce the bound — defense in depth. A downloaded payload with `visual_activity=999.0` should be rejected at ingest, not silently accepted and clamped later.

---

### M4 — `Optional` → union type annotation (model_sync.py)

**Decision:** Change `DEFAULT_MANIFEST: Optional[PopulationManifest] = None` to `DEFAULT_MANIFEST: PopulationManifest | None = None`. Remove `from typing import Optional` (it was the only use of `Optional` in the module).

**Rationale:** `from __future__ import annotations` is already present; the PEP 604 `X | None` syntax is the modern form for Python 3.10+ and matches the style used throughout `inference.py`.

---

## Tests to Fix — Juanita

The following tests reference removed or changed API and will need to be updated:

### `projects/synesthetic-familiar/tests/test_week4_camera_edge_cases.py`

| Test | Class | Issue |
|------|-------|-------|
| `test_hash_mismatch_does_not_modify_global_state` | `TestModelI5_HashVerification` (line ~151) | References `get_current_weights()` — removed. Test uses `getattr(_model_sync, "get_current_weights", None)` and skips if absent; now always skips. Needs rewrite to verify state isolation without `get_current_weights`. |
| `test_weight_cannot_exceed_two_times_default` | `TestOnlineLearningBounds` (line ~444) | Calls `apply_weight_update(extreme_update)` with old-signature dict (Phase-1 keys). New signature requires `current: VisualWeights` as third arg but defaults to `DEFAULT_VISUAL_WEIGHTS`. The old test sends Phase-1 keys (`pitch_var`, `imu_accel`, `imu_rot`) which are unknown to the new function (silently ignored). Test will likely pass but verify its assertions still exercise the right bounds. |
| `test_weights_can_be_reset_to_defaults` | `TestOnlineLearningBounds` (line ~488) | References `get_current_weights()` at line ~514 for post-reset verification. Now always returns without verifying since the getter is gone. Needs rewrite. |

### `projects/synesthetic-familiar/tests/test_week4_privacy_gates.py`

| Test | Class | Issue |
|------|-------|-------|
| `test_download_request_contains_no_user_id` | `TestModelI5_ModelSyncPrivacy` | Patches `urllib.request.urlopen`. `_download_bytes` now uses `build_opener(...).open(...)` (required by I2); the mock is bypassed; the real HTTPS request fires and raises `HTTPError 404`. Needs to patch `urllib.request.build_opener` or mock `OpenerDirector.open`. |
| `test_correct_hash_accepts_weights` | `TestModelI5_ModelSyncPrivacy` | Same root cause as above — patches `urlopen`, which is no longer called. |

**Note on `test_week4_privacy_gates.py` failures:** These broke because the I2 fix explicitly required switching from `urlopen` to `build_opener(...).open(...)` to prevent HTTPS redirect downgrades. The security property tested (no user-ID in headers, correct hash acceptance) is preserved — only the mock target changed.
