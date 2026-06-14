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
