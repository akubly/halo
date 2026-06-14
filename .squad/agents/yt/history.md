# Project Context

- **Owner:** Aaron Kubly
- **Project:** halo — mono-repo playground for authoring apps on Halo smart glasses
- **My layer:** Host apps (Python/Flutter/Web) that drive the glasses via the Brilliant SDK
- **Created:** 2026-06-01

## Recent Work (Week 2-3)

Pre-Week-2 learnings and context archived in `history-archive.md`.

---

---

## Week 3 "It's alive" — Onboarding UX — 2026-06-13

**Task:** First-launch onboarding UX in `host/main.py` (VESPER Phase-1 final milestone).

**What shipped:**

- `get_calibration_status(baseline)` — pure string function; returns "calibrating (no baseline yet…)" or "calibrating (day N of 3…)" or "personalized (n= …)". Testable via dataclass injection.
- `print_onboarding(baseline, *, out=None)` — first-launch banner on `baseline=None`; one-liner status on subsequent launches. Injectable `out` for Juanita's acceptance tests.
- Activation-gate call site: `try: from host.inference import is_baseline_active` with `TODO(Week3-Librarian)` marker. Falls back to age-based approximation (`_approx_baseline_active`) until Librarian wires the real gate per ARD §5.4.
- Fallback surfacing: both-fail (10 s) and confidence-hold (30 s) now print `[VESPER]` lines to stdout in addition to `logger.info`.
- ATTENTION display: `_send_update` prints `⚡ [VESPER] ATTENTION` when `mood_int == Mood.ATTENTION`. Safe now (inference never returns 3); fires when Librarian wires it or `run_mock_cycle` is used.
- FAMILIAR_RESET display: `_make_device_msg_handler` now prints user-facing gesture acknowledgement.
- `run_mock_cycle(transport, *, cycles, delay_s, sleep)` — harness that cycles NEUTRAL→CALM→STRESSED→ATTENTION. `--mock-cycle` / `--mock-cycle-count` CLI flags. Never instantiates `SensorStream`. Importable by Juanita directly.

**Key learnings:**
- `compute_mood` never returns `mood_int=3` (ATTENTION) — that path is device-side (Ng's Lua). The host's job is only to display it when it does fire, and to provide a mock-cycle harness. Don't duplicate device-side detection.
- Activation gate belongs in `inference.py` (Librarian's domain). The call-site pattern (`try/ImportError` → fallback) keeps both sides decoupled and immediately testable.
- Injectable `out: TextIO` on onboarding print is the right seam for testability without full `run()` invocation. Playground code doesn't need more than this.
- 128/128 tests green before and after — no regressions.

**Decision file:** `.squad/decisions/inbox/yt-week3-onboarding.md`

---

## Week 3 "It's alive" — Week 3 "It's alive" — Onboarding UX Full Integration (2026-06-13)

**Context:** ARD §5.4 specifies 3-day baseline warmup. Y.T. implemented first-launch detection, calibration status display, fallback surfacing, and ATTENTION/FAMILIAR_RESET acknowledgements.

**Critical dependencies resolved (2026-06-13):**
1. **Librarian's ACTIVATION_THRESHOLD gate:** `is_baseline_active(baseline)` now available. Y.T.'s try/ImportError fallback removed; direct call to `get_activation_info()` now works.
2. **Juanita's test harness:** 11 onboarding tests ready to unblock. Y.T. can ship module and tests will auto-enable.

**Integration checklist completed:**
- ✅ `get_calibration_status(baseline)` correctly dispatches to Librarian's `get_activation_info()` (no more TODO)
- ✅ `print_onboarding()` tested via StringIO injection
- ✅ Fallback/ATTENTION/FAMILIAR_RESET print statements in place
- ✅ `run_mock_cycle()` harness for manual ATTENTION testing
- ✅ 128/128 baseline tests green (zero regressions)

**Next step:** Y.T. creates `host/onboarding.py` module per Juanita's test contract (is_first_launch, run_first_launch_flow, run_returning_flow). Tests will immediately pass.

---

## Week 3 "It's alive" — Wave-2 Bind-Up (2026-06-13)

**Task:** Wire Librarian's activation accessor and Ng's FAMILIAR_RESET host reaction;
create `host/onboarding.py` for first-launch/returning-user flows.

**What shipped:**

- **BIND-UP 1:** Replaced `_is_baseline_active` import shim and age-based fallback
  (`_approx_baseline_active`, `_baseline_age_days`) with a direct import of
  `get_activation_info()` and `ACTIVATION_THRESHOLD` from `host.inference`.
  `get_calibration_status()` now shows `"calibrating (n / 50 samples)"` or
  `"personalized (n=N samples, mean=M, stddev=S)"` — sample-count progress beats
  the old day-count display. Dead imports (`datetime`, `_BASELINE_MIN_DAYS`) removed.

- **BIND-UP 3:** `_make_device_msg_handler()` now accepts a `list[bool]` reset flag.
  `run()` creates the flag, passes it to the handler, and checks it at the top of
  each frame. On flag set: `seq.reset()`, send NEUTRAL via new `_send_neutral_reset()`
  helper, clear `both_fail_start`, update `last_send_time`, then `continue` (so
  the frame's sensor data doesn't immediately overwrite the NEUTRAL).

- **`host/onboarding.py` (new):** `is_first_launch(path)` pure check;
  `run_first_launch_flow(path)` creates marker + prints banner;
  `run_returning_flow(baseline)` logs returning-user status without raising on None.

**Key learnings:**
- A `list[bool]` flag is the right cross-closure shared state in single-threaded asyncio.
  `asyncio.Event` is overkill when the callback fires synchronously inside `send()`.
- `continue` after a reset-reaction send is important — otherwise the frame's live mood
  data immediately overwrites the NEUTRAL, defeating the reset. The `finally` pacer
  still fires on `continue`.
- Removing xfail decorators (not just satisfying skip conditions) is what makes tests
  count as "passed" vs "xpass" in the pytest summary line.

**Test results:** 190 passed, 0 skipped, 0 xfailed (was 176/11/3). +14 net.

**Decision file:** `.squad/decisions/inbox/yt-week3-bindup.md`


📌 Team update (2026-06-14T05:36:23Z): Raven identified P2-4 (stdout print → --verbose); Librarian docs synced to Week 3 reality; 262 tests green; privacy audit APPROVED — ready for ship — decided by Raven, Librarian

---

### Session 2026-06-13 — Week 3 Persona-Review Cycle 1 Fixes

**Trigger:** Aaron approved fixes from Cycle 1 review findings on branch `synesthetic-familiar/week3-its-alive`.

**B1 — Onboarding dual-implementation (BLOCKING, RESOLVED):**  
`host/onboarding.py` had a correct sentinel-file strategy fully tested but never
wired into `run()`. `run()` was using a `baseline is None` proxy that caused the
welcome banner to repeat on every launch until the user accumulated 50 samples
(potentially days). Fixed by importing `is_first_launch / run_first_launch_flow /
run_returning_flow` from `host.onboarding` and making them the single onboarding
path in `run()`. Added `baseline_path: Path` as an injectable parameter so tests
can use `tmp_path`. Sentinel is written on first run — detection is now durable.

Added integration test class `TestRunOnboardingIntegration` (3 tests) that drives
`run()` end-to-end and proves: first launch shows banner, second launch shows
status, banner never repeats.

**I2 — `get_calibration_status()` leaking raw mean/stddev (IMPORTANT, RESOLVED):**  
Removed `mean={baseline.mean:.3f}, stddev={baseline.stddev:.3f}` from the
user-facing personalized status string. Status now shows activation state +
sample count only. Closes Raven P2-4.

**MINOR — `_send_neutral_reset` missing `rng` (RESOLVED):**  
Added `rng: random.Random | None = None`, matching `_send_neutral_fallback`.

**MINOR — Unused imports `ACTIVATION_THRESHOLD`, `ActivationInfo` (RESOLVED):**  
Removed from inference import block. Not referenced in main.py body.

**Lesson learned:** Writing `host/onboarding.py` without wiring it into `run()`
left a tested-but-dead module. Integration tests that drive `run()` end-to-end
would have caught this immediately. Going forward: for every new module I
introduce, add at least one integration test that calls through the production
entry point, not just unit tests on the module itself.

**Final test count:** 265 passed in 0.39s (3 new integration tests green).

**Fix note:** `.squad/decisions/inbox/yt-week3-review-fixes.md`

---

### Cycle 2 Re-Review (2026-06-14)

**Team decision:** All Cycle 1 findings (B1, I2, minors) verified ADDRESSED in Cycle 2 re-review (Correctness, Skeptic, Architect panels). Architect removed dead `print_onboarding()` from main.py (stale from B1 refactor). Final: 265 tests passing.

**Ready for ship-to-pr:** Push branch `synesthetic-familiar/week3-its-alive`, open PR, request Copilot review, then cloud-review-cycle, then squash-merge.

**Phase-2 deferral:** Reset-flag thread-safety (if multi-threaded host adopted).


---

### Session 2026-06-14: PR #4 Copilot Fix — baseline_path threading in host/main.py

**Context:** Copilot's review of PR #4 (branch synesthetic-familiar/week3-its-alive) flagged three
issues in host/main.py. Fixed host-only code; inference.py, tests, and docs untouched.

**Fixes applied:**

1. **load_baseline() missing baseline_path (~line 429)** — When the _LOAD_BASELINE_FROM_DISK
   sentinel triggered, load_baseline() was called without the injectable aseline_path, so
   an injected tmp path for sentinel detection was silently ignored for the actual disk read.
   Fixed: load_baseline(baseline_path). Production-safe because the default is _DEFAULT_BASELINE_PATH
   which equals inference._BASELINE_PATH.

2. **save_baseline() missing baseline_path (~line 531)** — Same root cause in the shutdown path.
   An injected aseline_path file would remain empty after shutdown while the default file was
   written, causing mismatched sentinel/baseline state on the next run.
   Fixed: save_baseline(baseline, baseline_path).

3. **Unused import sys (line 33)** — Confirmed zero sys. usages in file; removed the import.
   Leftover from print_onboarding removal.

**Tests:** 265 passed, 0 failed. baseline_path threading did not break any existing test.

**Durable lesson:** Injectable path parameters must flow through *all* I/O calls that use them —
sentinel-file detection and disk read/write are both affected. When adding an injectable seam,
audit all I/O call sites in the same function, not just the trigger check.
