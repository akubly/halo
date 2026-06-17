# Decision Note: PR #5 Copilot Review Fixes

**Date:** 2026-06-15  
**Branch:** `synesthetic-familiar/week4-it-sees`  
**Author:** Librarian (AI/ML specialist)  
**Files changed:** `host/inference.py`, `host/model_sync.py`

---

## Context

Copilot flagged 4 valid issues in the Librarian's files during PR #5 review. All four were addressed in this commit.

---

## Fix 1 — On-load clamp in `load_visual_weights()` (inference.py ~line 141)

**Problem:** The function validated non-negative/finite but did NOT enforce the ≤ 2× default upper bound stated in the docstring. A corrupted `~/.vesper/visual_weights.json` could deliver arbitrarily large values to `compute_mood` with no downstream clamp.

**Decision:** Clamp silently on load — `min(float(v), DEFAULT × MAX_VISUAL_WEIGHT_MULTIPLIER)` — consistent with existing load-error behavior (fall-safe to defaults on parse error; over-bound values are clamped rather than rejected, matching the pattern used by `tune_visual_weights`). The docstring promise is now enforced.

**Rationale for clamp-not-reject:** The model_sync parse path rejects out-of-bound. The load-from-disk path is a user-controlled config file; clamping silently recovers gracefully and the user retains whatever was valid. Rejecting would fall back to DEFAULT entirely, losing any valid partial state in the same file.

---

## Fix 2 — Docstring CAMERA-I6 mislabel (inference.py compute_mood ~line 384)

**Problem:** The `compute_mood` docstring attributed the strict `camera_ok is True` identity check to "CAMERA-I6". CAMERA-I6 is the "no image content in logs" privacy gate, not the modality gate.

**Decision:** Replaced "CAMERA-I6" reference in the docstring with accurate language: "strict identity (additive-invariant / modality) gate." No new gate ID invented.

---

## Fix 3 — Debug log CAMERA-I6 mislabel (inference.py ~line 435)

**Problem:** The debug log for the camera-modality skip path was tagged "CAMERA-I6", mislabeling the gate.

**Decision:** Removed "CAMERA-I6" tag from the log message prefix. Message content unchanged; the gate is now described as "camera modality gate."

---

## Fix 4 — `apply_weight_update()` partial-update semantics (model_sync.py ~line 409)

**Problem:** Omitted keys in the `update` dict defaulted to `DEFAULT_VISUAL_WEIGHTS` as the EMA target, causing the other weight to drift toward defaults on every partial update — unintended and undocumented.

**Decision:** Omitted keys now use the corresponding value from `current` as the EMA target (identity: no change). Only keys explicitly present in the update dict are blended toward their stated value. Docstring updated to state this contract explicitly. Bounds/clamp behavior via `tune_visual_weights` is preserved for all present keys.

---

## Test result

304 passed, 19 skipped (19 skips are Ng's `_CameraRelay` tests — camera SDK gate BLOCKED, not a regression).
