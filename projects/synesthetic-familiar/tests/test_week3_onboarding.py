"""
Week 3 acceptance tests — Onboarding flow (Y.T.).

YT-T2-1: "First launch — meet your Familiar"
ARD §2 Scope item 3: "First-launch bonding — onboarding flow that introduces
the creature and its meaning."

Contract (host.onboarding module — Y.T. Week 3):
  is_first_launch(baseline_path: Path) -> bool
    - True  if baseline_path does not exist (no prior session data).
    - False if baseline_path exists and is non-empty.

  run_first_launch_flow() -> None  (or async variant)
    - Prints/logs the introductory message.
    - Creates an empty or default baseline file so second launch detects returning.
    - Must NOT raise when baseline_path's parent directory doesn't exist (creates it).

  run_returning_flow(baseline: Baseline) -> None  (or stub if trivial)
    - Accepts the loaded Baseline for context; currently a no-op or log.

All tests in this file are xfail until Y.T. creates host/onboarding.py.

Reject criteria (Juanita → Y.T.):
  - is_first_launch must be a pure function (no side effects, no I/O).
  - is_first_launch must use the caller-supplied path (not ~/.vesper/baseline.json
    hardcoded), so tests can use tmp_path safely.
  - run_first_launch_flow must not import sounddevice, frame_sdk, or any BLE SDK;
    it is a UI concern only.
  - After run_first_launch_flow, a subsequent call to is_first_launch(same_path)
    must return False — first-launch state must be consumed on first use.

Date: 2026-06-13
"""
from __future__ import annotations

import pathlib
from pathlib import Path

import pytest

# ── Import guard — host.onboarding (Y.T. Week 3, not yet written) ─────────────
try:
    from host.onboarding import is_first_launch
    _FIRST_LAUNCH_AVAILABLE = True
    _ONBOARDING_IMPORT_ERROR: str | None = None
except ImportError as _e:
    is_first_launch = None  # type: ignore[assignment]
    _FIRST_LAUNCH_AVAILABLE = False
    _ONBOARDING_IMPORT_ERROR = str(_e)

try:
    from host.onboarding import run_first_launch_flow
    _FIRST_LAUNCH_FLOW_AVAILABLE = True
except ImportError:
    run_first_launch_flow = None  # type: ignore[assignment]
    _FIRST_LAUNCH_FLOW_AVAILABLE = False

try:
    from host.onboarding import run_returning_flow
    _RETURNING_FLOW_AVAILABLE = True
except ImportError:
    run_returning_flow = None  # type: ignore[assignment]
    _RETURNING_FLOW_AVAILABLE = False

# ── inference imports (for integration tests using Baseline) ──────────────────
try:
    from host.inference import load_baseline, save_baseline, Baseline
    _INFERENCE_AVAILABLE = True
except ImportError:
    load_baseline = save_baseline = Baseline = None  # type: ignore[assignment]
    _INFERENCE_AVAILABLE = False

_YT_W3_REASON = (
    "Y.T. Week 3: host/onboarding.py not yet written. "
    "Contract: is_first_launch(path), run_first_launch_flow(), run_returning_flow(). "
    "See ARD §2 item 3 (YT-T2-1), decisions.md 2026-06-07."
)


# ═════════════════════════════════════════════════════════════════════════════
# Group 1 — First-launch detection (is_first_launch)
# All xfail — host.onboarding not yet written.
# ═════════════════════════════════════════════════════════════════════════════

class TestFirstLaunchDetection:
    """
    is_first_launch(baseline_path) must return True when no prior session exists,
    False when a baseline file is present.

    Reject criteria:
    - Must accept a Path argument (no hardcoded default path that would touch
      the real ~/.vesper/baseline.json in tests).
    - Must be pure (no I/O side effects — only reads the filesystem).
    """

    def test_first_launch_when_no_baseline_file(self, tmp_path):
        """No baseline.json → first launch."""
        if not _FIRST_LAUNCH_AVAILABLE:
            pytest.skip(f"host.onboarding not importable: {_ONBOARDING_IMPORT_ERROR}")
        path = tmp_path / "baseline.json"
        assert not path.exists(), "Test setup: path must not exist."

        result = is_first_launch(path)
        assert result is True, (
            f"is_first_launch({path!s}) must return True when file does not exist. "
            "No prior session → first launch (YT-T2-1)."
        )

    def test_not_first_launch_when_baseline_exists(self, tmp_path):
        """Existing baseline.json → returning user."""
        if not _FIRST_LAUNCH_AVAILABLE:
            pytest.skip(f"host.onboarding not importable: {_ONBOARDING_IMPORT_ERROR}")

        path = tmp_path / "baseline.json"
        path.write_text('{"mean": 0.4, "stddev": 0.1, "sample_count": 5, "created_at": "2026-06-01T00:00:00"}', encoding="utf-8")
        assert path.exists(), "Test setup: path must exist."

        result = is_first_launch(path)
        assert result is False, (
            f"is_first_launch({path!s}) must return False when baseline.json exists. "
            "Returning user — do not replay the onboarding flow."
        )

    def test_is_first_launch_returns_bool(self, tmp_path):
        """is_first_launch must return a bool, not a truthy/falsy object."""
        if not _FIRST_LAUNCH_AVAILABLE:
            pytest.skip(f"host.onboarding not importable: {_ONBOARDING_IMPORT_ERROR}")
        path = tmp_path / "baseline.json"
        result = is_first_launch(path)
        assert isinstance(result, bool), (
            f"is_first_launch must return bool; got {type(result).__name__!r}. "
            "Explicit bool prevents subtle bugs when the result is used in if/assert."
        )

    def test_is_first_launch_accepts_path_argument(self, tmp_path):
        """is_first_launch must accept a pathlib.Path (not hardcode ~/.vesper/...)."""
        if not _FIRST_LAUNCH_AVAILABLE:
            pytest.skip(f"host.onboarding not importable: {_ONBOARDING_IMPORT_ERROR}")
        # Both Path and string should work; Path is the contract.
        path = tmp_path / "custom_baseline.json"
        try:
            is_first_launch(path)
        except TypeError as e:
            pytest.fail(
                f"is_first_launch must accept a Path argument; raised TypeError: {e}. "
                "If it takes no arguments or only uses a hardcoded path, tests can't "
                "use tmp_path and would touch the real ~/.vesper/baseline.json."
            )

    def test_empty_baseline_file_counts_as_returning(self, tmp_path):
        """
        An empty baseline.json (corrupted but present) must still count as returning.

        Rationale: if the file exists, a prior session ran. The corrupt content
        will be handled by load_baseline (→ None → population defaults), but the
        onboarding flow should NOT repeat just because the file is corrupted.
        """
        if not _FIRST_LAUNCH_AVAILABLE:
            pytest.skip(f"host.onboarding not importable: {_ONBOARDING_IMPORT_ERROR}")
        path = tmp_path / "baseline.json"
        path.write_bytes(b"")  # empty file — exists but corrupt
        result = is_first_launch(path)
        assert result is False, (
            "An empty baseline.json (file exists, zero bytes) must return False. "
            "File presence is the first-launch signal; content is load_baseline's problem."
        )


# ═════════════════════════════════════════════════════════════════════════════
# Group 2 — First-launch flow
# All xfail — run_first_launch_flow not yet written.
# ═════════════════════════════════════════════════════════════════════════════

class TestFirstLaunchFlow:
    """
    run_first_launch_flow(baseline_path) must:
    1. Complete without raising.
    2. Create the baseline.json file (or its parent dir) so future calls to
       is_first_launch return False.
    3. Not import any BLE SDK (onboarding is pure host UX).
    """

    def test_first_launch_flow_does_not_raise(self, tmp_path):
        """run_first_launch_flow must complete without raising any exception."""
        if not _FIRST_LAUNCH_FLOW_AVAILABLE:
            pytest.skip(f"host.onboarding.run_first_launch_flow not importable.")
        path = tmp_path / "baseline.json"
        try:
            run_first_launch_flow(baseline_path=path)
        except Exception as e:  # noqa: BLE001
            pytest.fail(
                f"run_first_launch_flow raised {type(e).__name__}: {e}. "
                "First-launch flow must complete cleanly on a fresh machine."
            )

    def test_first_launch_flow_creates_baseline_marker(self, tmp_path):
        """
        After run_first_launch_flow, is_first_launch(same_path) must return False.

        First-launch state is consumed on first use — the flow creates a marker
        (baseline.json or equivalent) so the next session is detected as returning.
        """
        if not (_FIRST_LAUNCH_FLOW_AVAILABLE and _FIRST_LAUNCH_AVAILABLE):
            pytest.skip("host.onboarding not fully importable.")
        path = tmp_path / "baseline.json"
        assert is_first_launch(path) is True, "Pre-condition: no file → first launch."
        run_first_launch_flow(baseline_path=path)
        result = is_first_launch(path)
        assert result is False, (
            "After run_first_launch_flow, is_first_launch must return False. "
            "First-launch state must be consumed (not repeated on every restart). "
            "YT-T2-1: wearer meets Familiar exactly once."
        )

    def test_first_launch_flow_creates_parent_directory(self, tmp_path):
        """
        run_first_launch_flow must create ~/.vesper/ (or caller-supplied parent)
        if it does not exist — first-run on a fresh machine has no ~/.vesper/ dir.
        """
        if not _FIRST_LAUNCH_FLOW_AVAILABLE:
            pytest.skip("host.onboarding.run_first_launch_flow not importable.")
        nested_path = tmp_path / "new_dir" / "subdir" / "baseline.json"
        assert not nested_path.parent.exists(), (
            "Test setup: parent dir must not exist to test auto-creation."
        )
        try:
            run_first_launch_flow(baseline_path=nested_path)
        except Exception as e:  # noqa: BLE001
            pytest.fail(
                f"run_first_launch_flow raised {type(e).__name__}: {e} "
                f"when parent dir doesn't exist. Must auto-create parent directories."
            )

    def test_first_launch_flow_no_ble_sdk_import(self):
        """
        run_first_launch_flow must not import frame_sdk or brilliant_ble.
        Onboarding is a pure host UX concern — no hardware dependency.

        Structural test via inspect.getsource().
        """
        if not _FIRST_LAUNCH_FLOW_AVAILABLE:
            pytest.skip("host.onboarding.run_first_launch_flow not importable.")
        import inspect
        try:
            src = inspect.getsource(run_first_launch_flow)
        except OSError:
            pytest.skip("Cannot inspect run_first_launch_flow source.")
        for banned in ("frame_sdk", "brilliant_ble", "BrilliantBle", "frame.bluetooth"):
            assert banned not in src, (
                f"run_first_launch_flow must not import '{banned}'. "
                "Onboarding is host UX only — no BLE SDK dependency."
            )


# ═════════════════════════════════════════════════════════════════════════════
# Group 3 — Returning user flow
# Partially xfail (flow function) — load_baseline integration passes today.
# ═════════════════════════════════════════════════════════════════════════════

class TestReturningUserFlow:
    """
    Returning user: is_first_launch returns False, run_returning_flow called.
    The flow must load baseline successfully and not crash.
    """

    def test_returning_flow_does_not_raise_with_valid_baseline(self, tmp_path):
        """run_returning_flow must accept a Baseline and not raise."""
        if not _RETURNING_FLOW_AVAILABLE:
            pytest.skip("host.onboarding.run_returning_flow not importable.")
        if not _INFERENCE_AVAILABLE:
            pytest.skip("host.inference not importable.")
        baseline = Baseline(
            mean=0.42, stddev=0.08, sample_count=50,
            created_at="2026-06-01T00:00:00",
        )
        try:
            run_returning_flow(baseline)
        except Exception as e:  # noqa: BLE001
            pytest.fail(
                f"run_returning_flow raised {type(e).__name__}: {e}. "
                "Returning user flow must complete cleanly with a valid Baseline."
            )

    def test_returning_flow_accepts_none_baseline(self, tmp_path):
        """
        run_returning_flow(None) must not raise.

        Scenario: baseline.json existed but was corrupted (load_baseline → None).
        The flow should degrade gracefully (population defaults) rather than crashing.
        """
        if not _RETURNING_FLOW_AVAILABLE:
            pytest.skip("host.onboarding.run_returning_flow not importable.")
        try:
            run_returning_flow(None)
        except Exception as e:  # noqa: BLE001
            pytest.fail(
                f"run_returning_flow(None) raised {type(e).__name__}: {e}. "
                "Corrupt baseline → None is a valid input (population defaults fallback)."
            )


class TestOnboardingIntegrationPassingToday:
    """
    Integration checks that PASS TODAY using only host.inference (no host.onboarding).

    These guard against Week 3 changes accidentally breaking the baseline
    load/save primitives that the onboarding flow will depend on.
    """

    def test_fresh_machine_load_baseline_returns_none(self, tmp_path):
        """
        Non-existent baseline path → load_baseline returns None.

        This is the returning-user scenario where the file was expected but missing;
        host must use population defaults gracefully.
        """
        if not _INFERENCE_AVAILABLE:
            pytest.skip("host.inference not importable.")
        path = tmp_path / "no_such_file.json"
        result = load_baseline(path=path)
        assert result is None, (
            "load_baseline must return None for missing file (not raise OSError). "
            "Host onboarding must handle this gracefully — use population defaults."
        )

    def test_returning_user_baseline_loads_without_error(self, tmp_path):
        """
        Returning user with valid baseline.json: load_baseline returns Baseline.

        This confirms the inference layer's contract that onboarding will rely on.
        """
        if not _INFERENCE_AVAILABLE:
            pytest.skip("host.inference not importable.")
        import json
        path = tmp_path / "baseline.json"
        path.write_text(
            json.dumps({
                "mean": 0.41,
                "stddev": 0.09,
                "sample_count": 42,
                "created_at": "2026-06-01T00:00:00",
            }),
            encoding="utf-8",
        )
        baseline = load_baseline(path=path)
        assert baseline is not None, (
            "load_baseline must return Baseline for a well-formed file. "
            "Returning user flow depends on this succeeding."
        )
        assert baseline.sample_count == 42
        assert baseline.mean == pytest.approx(0.41)


if __name__ == "__main__":
    import unittest
    unittest.main()
