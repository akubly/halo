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
