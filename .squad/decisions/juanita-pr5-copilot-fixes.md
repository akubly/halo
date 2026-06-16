# Decision: PR #5 Copilot Review Fixes — Juanita (Tester)

**Date:** 2026-06-15  
**Branch:** `synesthetic-familiar/week4-it-sees`  
**Author:** Juanita  
**Status:** IMPLEMENTED — 304 passed, 19 skipped, 0 failed

---

## Context

Copilot flagged 5 test issues in the Week-4 PR (#5).  All were valid correctness
problems (vacuous passes, wrong patch targets, overly-broad assertion).  Librarian's
implementation was already correct; all 5 fixes are test-only changes.

---

## Decision 1 — Force logger level in `_collect_logs_above_debug`

**Problem:** pytest sets the root logger to WARNING.  The `_collect_logs_above_debug`
helper added a capture handler but never adjusted the target logger level.  INFO
records were therefore discarded by the logger before reaching the handler — a
CAMERA-I6 INFO-level violation would pass the test vacuously.

**Decision:** Force the target logger to `logging.INFO` for the duration of the
capture; restore original level and `propagate` flag in the `finally` block.

**Rationale:** The test is only meaningful if INFO records actually reach the handler.
Restoring the level preserves pytest's log isolation contract.

---

## Decision 2 — Narrow CAMERA-I6 "jpeg"/"jpg" word ban to content patterns

**Problem:** The banned-substring list included `"jpeg"` and `"jpg"`, which would
wrongly fail benign diagnostic messages like `"JPEG decode failed"` or
`"processing jpg input"`.  CAMERA-I6 bans image *content* leakage, not terminology.

**Decision:** Remove `"jpeg"` and `"jpg"` from the banned word list.  Retain
`"pixel"`, `"raw_frame"`, `"image_data"`.  Add a regex check for `bytes` repr
patterns (`b'\xNN'`) and keyword checks for dimension/byte-count strings
(`width=`, `height=`, `dimensions=`, `byte_count=`).

**Rationale:** Aligned to the actual CAMERA-I6 specification: *image content* (raw
bytes, pixel data, geometry) must not appear in INFO+ logs.  The word "jpeg" in a
diagnostic message is not content leakage and must not be a gate.

---

## Decision 3/4/5 — Patch `build_opener` (not `urlopen`) in camera_edge_cases.py

**Problem:** Three tests in `test_week4_camera_edge_cases.py` patched
`urllib.request.urlopen` to simulate hash mismatch rejection (C3), network errors
(C4), and fallback behaviour (C5).  The production code (`_download_bytes`) uses
`urllib.request.build_opener(...).open(req, timeout=...)` — a different call site.
The `urlopen` patch was a no-op; tests could hit the real network, silently swallow
errors, or pass vacuously.

**Decision:** Replace all three `patch("urllib.request.urlopen", ...)` with
`patch("urllib.request.build_opener", return_value=mock_opener)` where
`mock_opener.open.side_effect` delivers the intended response or error.  Add a
`assert mock_called` sentinel assertion to each test.

**Rationale:** The patch must intercept the call the *production code* actually makes.
Since `_download_bytes` was already changed (by Librarian) to use `build_opener`,
any `urlopen` patch is dead.  The sentinel assertion makes future patch drift
immediately visible rather than producing a silent vacuous pass.

**Consistency:** This is the same fix pattern already applied to `test_week4_privacy_gates.py`
in the Persona-Review fix cycle (2026-06-14).  The lesson now extends across both test files.

---

## Outcome

All 5 Copilot review comments addressed.  Suite: **304 passed, 19 skipped, 0 failed**.
Skips are exclusively Ng's `_CameraRelay` tests — no new skips introduced.
Tests are now fully offline and deterministic.
