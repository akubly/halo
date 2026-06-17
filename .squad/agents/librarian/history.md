# Librarian — AI/ML Specialist (Archived Context Summary)

**Owner:** Aaron Kubly | **Project:** halo mono-repo | **Role:** Anything LLM, VLM, STT, TTS, or agent-loop related

📌 **Archived content:** Pre-Week-4 history has been moved to history-archive.md (see that file for pre-Week-3 context, Week 3 decisions, documentation updates, and persona-review cycles).

---

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

**Gate-off/ignore paths must never raise on bad input (PR #5 Copilot re-review):** use non-throwing formatting (`%r`/`%s`) in diagnostic logs on any path whose whole purpose is to ignore an input — assume those inputs may be invalid types.
validate json.loads payload is a dict before .get() so non-object payloads fail closed as ValueError.
