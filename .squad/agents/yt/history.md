# Project Context

- **Owner:** Aaron Kubly
- **Project:** halo — mono-repo playground for authoring apps on Halo smart glasses
- **My layer:** Host apps (Python/Flutter/Web) that drive the glasses via the Brilliant SDK
- **Created:** 2026-06-01

## Learnings

### Recent Work (Week 2-3)

See main history section below.

### Archived Sessions

Pre-Week-2 learnings (ideation, user stories, SDK familiarization) moved to `history-archive.md`.

---
- Lua event loop runs *on Halo*; host is reactive (send requests, handle responses)

**Noa Example Patterns:**
- Real-time camera → local Lua inference → text display + cloud AI response
- Memory persistence: remembers prior context across sessions
- Multimodal: camera input + audio output (bone conduction) + button clicks

---

### Session 2026-06-01 (Follow-up): Community Projects Survey

**Community App Landscape (mostly Monocle/Frame, migrating to Halo):**

| Type | Platform | Example | Host UX Shape |
|------|----------|---------|---------------|
| **Vision/Camera** | Python | QR-code scanner (milesprovus) | CLI: `main.py` → tap to scan → results printed/linked |
| **Vision/Camera** | Web | Drawing tool (jdc-cunningham) | Single-page web app: pixel editor → generates Python code |
| **Navigation** | Web | MonoNav (semtexzv) | Live demo site: map interface → turn-by-turn on glasses |
| **Fitness/HUD** | Web (React PWA) | Workout app (simonevetere) | PWA app launcher → workout UI → active set tracking on glasses |
| **UI Prototyping** | Web (React PWA) | bl-monocle-reactjs-pwa (jdc-cunningham) | Local storage code snippets → editor → test/flash to device |
| **Teleprompter** | Python | Google Slides → display (milesprovus) | CLI script: slides sync → speaker notes on glasses |
| **GPT Client** | Python | OpenAI client (acui51) | CLI loop: prompt → glasses display LLM output |

**Language Distribution Across Community:**
- **Python:** ~40% of apps — CLI-first, heavy on image processing (QR, CV) + desktop device targeting
- **Web/React:** ~40% — PWAs with localStorage, real-time sync, mobile-responsive
- **Node.js:** ~10% — REPL editors, CLI tools for development
- **Flutter:** ~5% — emerging (Brilliant has official support now)
- **Other (Go, Java, Android):** ~5%

**Host App Shapes:**
1. **CLI loops** — Read input → send to glasses → handle response → repeat (QR scanner, GPT client, teleprompter)
2. **Web one-pagers** — Single HTML file + JS, often live-demoed on GitHub Pages (MonoNav, drawing tool)
3. **PWA with localStorage** — Persistent code editor or state (bl-monocle-reactjs-pwa, workout app)
4. **Mobile native** (emerging) — Still nascent; `simple_brilliant_app` Flutter scaffolding is new

**No Standardized Scaffolds in Community:**
- Each project re-invents the connection lifecycle (break → upload → start loop)
- No shared patterns for Bluetooth lifecycle errors, retry logic, or disconnect handling
- No template repos that authors can fork

**Reference Implementations Worth Studying:**
1. **`fixermark/brilliant-monocle-driver-python`** — Solid asyncio wrapper, handles UART MTU overflow, touch event callbacks. Clean async context manager pattern.
2. **`bl-monocle-reactjs-pwa`** — Shows how to build a persistent code editor with localStorage + BLE sync. Good for understanding Web Bluetooth lifecycle in React.
3. **`monocle-node-cli`** — Extracted CLI communication from AR Studio; demonstrates REPL-style device interaction (could adapt for Halo CLI REPL).

**Brilliant's Official Scaffolds:**
- **Python:** `halo-emulator` package is unique — no other project provides offline hardware emulation
- **Flutter:** `simple_brilliant_app` package (official) — provides device detection + startup boilerplate; widely portable
- **Web:** No official scaffold; community fills gap with PWAs

---

### Session 2026-06-02: GitHub Scaffolds & Example Apps Survey

**Key scaffolds:** Python `halo-emulator`, Flutter `simple_brilliant_app`, Web examples (sparse — see bl-monocle-reactjs-pwa community pattern).

**Community pattern:** Most projects re-implement BLE connection lifecycle; no shared library. Opportunity to pioneer playground mono-repo pattern.

### Session 2026-06-02: Ideation (8 concepts)

Pet Digital Familiar, Skeleton Pose Mirror, AI Graffiti Artist, Forehead Fortune Teller, Bioluminescent Skin Sync, Gesture-Based Draw Duel, Tiny Floating Museum, Reality Glitch Filter.

See `history-archive.md` for full ideation text.

---

**Top new mash-up to prototype:**
**Bloom Habit Tracker** (Y.T. #3 × Enzo #6 × Da5id #8) — 1-week scaffold combining habit detection, bloom reward visuals, and host-app lifecycle. Ships complete joy; becomes template for "beautiful feedback design."

**4 new ideas added:** Radial History Scrubber, Button Echo Chamber, Noa Talk Show, Distributed Gesture Language.

See `ideation-pass2-2026-06-02.md` for full synthesis, mash-ups, and amendments to original 8.

---

## User Stories Themes 1-2 — 2026-06-03

**Context:** Aaron curated two themes from cross-squad ideation:
1. **Consent-Aware Memory** (most-cited convergence: Hiro+Enzo+Librarian+Raven+Lagos)
2. **The Synesthetic Familiar** (Y.T. pet × Librarian synesthetic AI × Da5id peripheral-only)

**Authored:** 5 user stories per theme (happy path + delight moment each), focused on host-app UX:
- Theme 1 stories span pairing setup, group recording consent, memory review, bystander replay rights, and accidental-capture sharing
- Theme 2 stories cover first-launch bonding, stress-detection, personality customization, 30-day evolution, and surprise moments

**Scope:** Phone (Flutter) + web (React) + CLI (optional). All host-side surfaces (no Lua changes needed; sprites sync via BLE).

**Key Design Decisions:**
- Theme 1: Consent is a *network protocol*, not an afterthought. BLE mesh for negotiation; crypto signatures for audit.
- Theme 2: Familiar is a *vitals mirror*, not a chatbot. Motion > text. Peripheral-only, non-intrusive.

**Next Steps:** Backtesting with Aaron. Recommend Theme 1 (Consent) for security review; Theme 2 (Familiar) for UX iteration.

See `user-stories-themes-1-2-2026-06-03.md` for full stories + acceptance criteria + app-shape notes.

---

## Codename Brainstorm — 2026-06-08

Pitched UX-design-lens codename candidates for the Synesthetic Familiar. Team converged on **PULSE** (4 agents independently nominated variants). Official project codename now PULSE. See `.squad/orchestration-log/2026-06-08T07-17Z-codename-brainstorm.md`.

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
