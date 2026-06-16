# Librarian — AI/ML Specialist (Archived Context Summary)

**Owner:** Aaron Kubly | **Project:** halo mono-repo | **Role:** Anything LLM, VLM, STT, TTS, or agent-loop related

## Pre-Week-3 Context (Archived)

**Early research (2026-06-02):** 9 community AI projects catalogued; CitizenOneX for privacy-first STT. **Ideation pass 2 (2026-06-02):** 8 cross-pollinated patterns, 4 mash-ups (top: Consent-Aware Embodied Memory). **User stories Themes 1–2 (2026-06-03):** Synesthetic Familiar (real-time <500ms mood inference, 7-day calibration, confidence gating) + Consent-Aware Memory (local redaction + async cloud consent). **Codename (2026-06-08):** Team converged on **VESPER** (renamed from PULSE).

**Week 2 (2026-06-10–2026-06-12):** Implemented host/inference.py: mood heuristic (weighted tension: pitch×0.4 + accel×0.3 + rot×0.3), baseline learning via Welford online stats, confidence gating (stressed/calm 0.8, neutral 0.6), sensor-failure reductions (mic ×0.6, IMU ×0.7). Fixed regressions B1 (added MoodResult.tension field), I1 (load_baseline fail-safe), I2 (NaN/inf guards), M4 (audio_rms annotation).

## Week 3 "It's Alive" — Baseline Activation Gate (2026-06-13)

**Decision delivered:** ACTIVATION_THRESHOLD = 50 samples (not 3 calendar days).

**Why sample_count over calendar time:**
- Welford stddev stability. SE(s)/s ≈ 1/√(2n); at n=50, SE/s ≈ 10% (within ~0.15σ of asymptotic).
- Calendar time wrong for observation-count-gated estimator. A 5-day-old baseline with 8 samples should stay "calibrating."

**New exports from host.inference:**
- ACTIVATION_THRESHOLD: int = 50
- ActivationState = Literal["calibrating", "personalized"]
- ActivationInfo dataclass: {state, sample_count, samples_needed, progress}
- get_activation_info(baseline: Baseline | None) -> ActivationInfo (pure function, no I/O)

**Integration:** compute_mood() requires aseline.sample_count >= ACTIVATION_THRESHOLD for personal threshold. Y.T. calls get_activation_info() for onboarding UX progress display. Juanita: 34 tests all passing (pure function, no mocking).

## Week 3 "It's Alive" — Documentation Sync (2026-06-13)

**Task:** Bring ARD.md, TEST-STRATEGY.md, README.md in sync with Week 3 shipped reality. Cite all decision dates.

**Deliverables:**

| Document | Update | Status |
|----------|--------|--------|
| ARD.md §5.1 Gate Table | Gate 1 (IMU) GO: rame.imu.tap_callback(func) + Lua debounce 350ms; Gate 2 (heap) NO-GO: rame.system absent, manual proxy v1; Gate 3 (sprite) GO: rame.display.circle() confirmed | ✅ |
| ARD.md §10 Open Q | Q1 (IMU) RESOLVED GO (2026-06-12); Q3 (heap) RESOLVED NO-GO (2026-06-12) | ✅ |
| ARD.md Build Sequence | Week 3 row 1: ACTIVATION_THRESHOLD=50, IMU-peak render-loop, ATTENTION visual (white eye, 180ms +4px jump), onboarding, fallback verified; row 3: 190+ tests green | ✅ |
| TEST-STRATEGY.md Week 3 | Expanded success criteria: ATTENTION 500ms overlay, baseline gate 50 samples, 190+ green tests | ✅ |
| README.md | Codename PULSE → **VESPER**; status "Week 1 scaffold" → **"Week 3 complete"**; new "Week 3 Shipped" deliverables list | ✅ |

**Validation:** No code changes (docs-only). All facts cited to decisions.md (searchable source). No contradictions found between docs/decisions/code. Test count verified: 190+ green (confirmed in Juanita decision 2026-06-13).

**Decision record:** librarian-week3-docs.md merged to decisions.md.

📌 Team update (2026-06-14T05:36:23Z): Da5id eye dilation addendum INCLUDED (§6 Q1); Y.T. activation gate bound; Ng ATTENTION visuals shipped; Raven privacy APPROVED all surfaces; Juanita 72 new tests; 262 tests green — docs now in sync with Week 3 reality — decided by Da5id, Y.T., Ng, Raven, Juanita

## Week 3 PR — Persona-Review Cycle 1 Fixes (2026-06-13)

**Triggered by:** Aaron Kubly after Cycle 1 persona review of branch `synesthetic-familiar/week3-its-alive`.

### M6 — README.md test count corrected
- Stale "190+" references (2 occurrences) updated to "262".
- Files touched: `projects/synesthetic-familiar/README.md` only.

### M3 — load_baseline() size guard
- Added pre-read `path.stat().st_size > 4096` check inside the existing `try` block in `host/inference.py:load_baseline()`.
- Falls into the existing `except (OSError, ..., ValueError)` handler → returns `None` + warning log. No new exception surface.
- Valid baseline is ~120 bytes; 4096 is a 33× margin, generous enough for future minor field additions.
- `OSError` from a broken symlink on `stat()` is already caught.

**Post-fix pytest:** 262 passed, 0 failed (0.42 s). No test adjustments needed.

**Decision record:** `.squad/decisions/inbox/librarian-week3-review-fixes.md`

---

### Cycle 2 Re-Review (2026-06-14)

**Team decision:** All Cycle 1 findings (M3, M6) verified ADDRESSED in Cycle 2 re-review (Correctness, Skeptic, Architect panels). Docs now in sync with Week 3 reality. Final: 265 tests passing.

**Ready for ship-to-pr:** Push branch `synesthetic-familiar/week3-its-alive`, open PR, request Copilot review, then cloud-review-cycle, then squash-merge.

**Phase-2 deferral:** Heap host-visibility wire field (infrastructure).

---

## PR #4 Copilot Review — Docs Corrections (2026-06-14)

**Triggered by:** Copilot PR review on `synesthetic-familiar/week3-its-alive` flagging stale/duplicate content in docs.

### Changes applied

| File | Issue | Fix |
|------|-------|-----|
| `projects/synesthetic-familiar/README.md` line 10 | "262 tests green" stale (Y.T. added 3 onboarding integration tests → 265) | Updated to **265** |
| `projects/synesthetic-familiar/README.md` line 23 | Same "262 tests green" stale count | Updated to **265** |
| `projects/synesthetic-familiar/README.md` lines 44–46 | Duplicate sentence "See ARD §4–§5.5…" back-to-back | Removed duplicate |
| `docs/projects/synesthetic-familiar/ARD.md` line ~562 | "190+ tests green" in build-sequence table | Replaced with **"Full Week 3 automated suite green"** (non-numeric) |
| `docs/projects/synesthetic-familiar/TEST-STRATEGY.md` line ~1361 | "190+ tests green" in milestone success criteria | Replaced with **"comprehensive Week 3 automated test coverage green"** (non-numeric) |

### ⚠️ Durable lesson: do NOT hard-code test counts in spec docs

**README status/badge lines** — exact count is useful; update it when it changes.

**ARD build-sequence tables and TEST-STRATEGY success criteria** — these are durable spec artifacts. A running test count goes stale every sprint and triggers another doc PR. Use intent-based language ("full suite green", "comprehensive coverage green") that survives incremental test additions without doc churn.

**Rule of thumb:** If the number will change every time a developer adds a test, it does not belong in a spec doc. It belongs in CI output or a README badge.

**Decision record:** `.squad/decisions/inbox/librarian-pr4-copilot-fixes.md`

📌 Team update (2026-06-14T07:59:43Z): Phase-2 plan drafted (camera + cloud refinement) — pending Aaron approval. Decisions: Enzo (capability scope), Hiro (architecture). No code written. Affected: implementation lead (Ng), privacy review (Raven), docs (Librarian), testing (Juanita), infrastructure (Da5id).

## Week 4 "It sees" — Visual Weight Extension + Option-C Cloud Sync (2026-06-14)

**Branch:** `synesthetic-familiar/week4-it-sees`

### What I built

**1. Visual weight extension — `host/inference.py`**

New module-level constants:
- `_W_PITCH = 0.4`, `_W_ACCEL = 0.3`, `_W_ROT = 0.3` — Phase-1 weights extracted from inline to named constants. These are IMMUTABLE and never included in tunable state.
- `VisualWeights(visual_activity=0.15, visual_brightness=0.05)` — Phase-2 additive camera weights.
- `DEFAULT_VISUAL_WEIGHTS`, `MAX_VISUAL_WEIGHT_MULTIPLIER = 2.0`

New functions: `load_visual_weights`, `save_visual_weights`, `reset_visual_weights`, `tune_visual_weights` (bounded EMA with divergence guard).

Tension formula when `camera_ok=True`:
```
tension = pitch×0.4 + accel×0.3 + rot×0.3    ← Phase-1 (locked)
        + visual_activity × W_va              ← additive camera term
        + (1.0 − visual_brightness) × W_vb    ← dark → tense, bright → calm
```

**ADDITIVE INVARIANT proof:** the camera block is inside `if camera_ok:` — structurally unreachable when `camera_ok=False`. Phase-1 weights, threshold selection, mood classification, and confidence reductions are identical paths. Tests confirm this at 299 passing.

**2. Bounded online weight tuning**

`tune_visual_weights(current, target, alpha=0.1)`:
- EMA: `new_w = (1−α) × current + α × target`
- Hard clamp: `[0, DEFAULT × MAX_VISUAL_WEIGHT_MULTIPLIER]` — no weight ever exceeds 2× default
- Divergence guard: `logger.warning` if any weight reaches ≥ 90% of bound
- Pure function — caller is responsible for persisting via `save_visual_weights()`

`reset_visual_weights()` → returns `VisualWeights()` (factory defaults, no side effects).

Why EMA not SGD: Playground scope. EMA is transparent, bounded by construction (with clamp), and doesn't require a loss function. It smooths population suggestions toward local state over time. At alpha=0.1, 23 syncs are needed to reach 90% convergence from default.

**3. `host/model_sync.py` — Option C federated sync**

Key functions:
- `download_weights(url, expected_hash)` → `bytes | None`: HTTPS download + SHA-256 verify. Returns `None` on hash mismatch. Raises `OSError`/`ValueError` on network errors / bad scheme.
- `sync_population_weights(manifest, current, alpha)` → `VisualWeights`: fail-closed wrapper. Returns `current` unchanged on any error.
- `apply_weight_update(update_dict)` → `dict`: apply an EMA update from a plain dict.
- `reset_weights_to_defaults()` → `VisualWeights`: convenience alias.

**No-egress proof (MODEL-I5):**
The HTTP GET carries: `Host`, `User-Agent: Python-urllib/<version>`, `Accept-Encoding: identity`. Zero custom headers. Verified by inspection: `Request(url)` with no `add_header` calls. The server sees IP + standard User-Agent — no VESPER application-layer identifier of any kind.

**4. Phase-1 invariant — proved structurally and tested**

`camera_ok=False` → `if camera_ok:` block never executes → tension = Phase-1 formula only → identical threshold selection → identical classification → identical MoodResult. Test suite confirms with parametrized `TestAdditiveInvariant` covering stressed/calm/neutral/mic-only/IMU-only/both-fail paths.

### File paths
- `projects/synesthetic-familiar/host/inference.py` — visual weight extension, `compute_mood` updated
- `projects/synesthetic-familiar/host/model_sync.py` — NEW: Option-C federated sync
- Decision: `.squad/decisions/inbox/librarian-week4-inference-optionc.md`

### Test result
265 → 299 passed (34 new passing); 19 skipped (Ng's `_CameraRelay` — pending).

---

📌 Team update (2026-06-15T05:37:29Z): Week-4 camera SDK gate resolved BLOCKED (CAMERA-I3); Librarian shipped Option-C cloud sync (model_sync.py, VisualWeights, EMA tuning); Juanita delivered 53 new tests (296 passed, 22 skipped); Raven approved with 6 merge-blocking conditions. Phase-2 shipping cloud-refinement; camera deferred Phase-3 — decided by Ng, Librarian, Juanita, Raven

## Week 4 Persona-Review Cycle 1 Fixes (2026-06-15)

### Learnings

**Functional-API decision (I1):** `apply_weight_update` now takes an explicit `current: VisualWeights` parameter and EMA-blends FROM it, not hardcoded from `DEFAULT_VISUAL_WEIGHTS`. `get_current_weights()` was removed entirely — it encoded a lie (there IS no module-level mutable weight state). The module docstring now declares explicitly: "this module is pure-functional; callers own and persist current weights." Lesson: any helper function that hands out a snapshot of state that doesn't exist is a design smell. Callers must own state; the module must make that explicit.

**Redirect-downgrade hardening (I2):** `_download_bytes` now uses `build_opener(_HTTPSOnlyRedirectHandler()).open(...)` instead of `urlopen`. The handler subclasses `urllib.request.HTTPRedirectHandler` and raises `ValueError` (referencing MODEL-I5) on any redirect whose target scheme isn't `https`. Initial scheme validation (`parsed.scheme != "https"`) is preserved as a first-line check; the redirect handler is defense-in-depth. Side effect: tests that mock `urllib.request.urlopen` will no longer intercept these calls — they must instead mock the opener path. Worth flagging to Juanita.

**Version enforcement (I4):** `_parse_population_weights` now checks `obj.get("version") != "1"` and raises `ValueError` immediately. The payload is rejected before any field is extracted. Fail-fast with an explicit message beats a silent v1 assumption that becomes a silent v2 vulnerability later. Schema versioning is only as strong as the boundary that enforces it.

**Dormant-sync documentation (I5 + I6):** The model_sync.py docstring now declares:
  - This sync capability is NOT yet wired into the runtime loop (ships Week 4, activates Phase 3 alongside camera — intentional).
  - Trust model: integrity rests on HTTPS + SHA-256; no host allowlist, cert pinning, or signed manifest; acceptable for single-user playground; hardening path = signed manifest + host pinning.

## Learnings

**On-load clamp gap (PR #5 Copilot fix):** `load_visual_weights()` validated that disk values were non-negative and finite, but did NOT enforce the ≤ 2× default upper bound stated in the docstring. A corrupted `~/.vesper/visual_weights.json` could load arbitrarily large values that `compute_mood` would then use unclamped. Fix: clamp on load — `min(float(v), DEFAULT × MAX_MULTIPLIER)` — consistent with the existing load-error handling (fall-safe to defaults on parse error; clamp silently for values in-range but over-bound). The load path must actually enforce the bound the docstring promises.

**CAMERA-I6 mislabel lesson (PR #5 Copilot fix):** CAMERA-I6 is the "no image content in logs" privacy gate. Labeling the camera-modality additive-invariant gate (strict `is True` identity check) as "CAMERA-I6" in both the docstring and a debug log message was wrong — these are unrelated gates. Rule: do NOT reuse privacy-gate IDs for operational/architectural gates. Describe each gate accurately where it's used; don't borrow a nearby-sounding ID just because it was mentioned in the same feature spec section.

**Omitted-keys = leave-unchanged semantics (PR #5 Copilot fix):** `apply_weight_update()` originally used DEFAULT values as the EMA target for any key absent from the update dict, causing unrelated weights to drift toward defaults on every partial update. Correct semantics: omitted keys mean "leave unchanged" — use the corresponding value from `current` as the target so no drift occurs. Only keys explicitly present in the update are blended toward their stated value. This is the standard partial-update contract for incremental tuning APIs.

**Docstring log-level accuracy (PR #5 Copilot re-review):** keep docstring log-level claims in sync with actual logger calls.
