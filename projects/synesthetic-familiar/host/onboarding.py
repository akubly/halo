"""
First-launch and returning-user onboarding flows for VESPER (Y.T. Week 3).

Contract (YT-T2-1 / ARD §2 item 3):
  is_first_launch(baseline_path) → bool
    Pure function; no I/O side-effects.  Returns True only when the file
    does not exist — file presence (even empty/corrupt) means a prior session ran.

  run_first_launch_flow(baseline_path) → None
    Prints the introductory message and creates a baseline marker file so the
    next call to is_first_launch(same_path) returns False.
    Creates parent directories automatically (fresh machine has no ~/.vesper/).
    No BLE SDK imports — purely host UX.

  run_returning_flow(baseline) → None
    Accepts Baseline | None; logs returning-user status.  No-op for corrupt
    baseline (None) — population defaults are handled by inference.py.

Owner: Y.T.
Date:  2026-06-13
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("familiar.onboarding")


def is_first_launch(baseline_path: Path) -> bool:
    """
    Return True if no prior session has ever run.

    Pure function — only checks the filesystem, no writes.
    Any file at baseline_path (even empty or corrupt) counts as a returning
    session; content validity is load_baseline's concern.
    """
    return not baseline_path.exists()


def run_first_launch_flow(baseline_path: Path) -> None:
    """
    Run the first-launch onboarding flow.

    1. Prints an introductory banner explaining the 3-day calibration ramp.
    2. Creates baseline_path (empty marker) so is_first_launch returns False
       on the next launch.  Parent directories are created automatically.
    """
    print("")
    print("╔══════════════════════════════════════════╗")
    print("║  VESPER  —  Meet your Familiar           ║")
    print("╚══════════════════════════════════════════╝")
    print("")
    print("  Your familiar is waking up for the first time.")
    print("  It will spend the next few days learning your personal rhythm.")
    print("  Calibrating: collecting baseline samples (target: 50).")
    print("  Once calibrated, it adapts its thresholds to you personally.")
    print("")
    logger.info("[Onboarding] first launch — creating baseline marker at %s", baseline_path)
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    # Write an empty-but-valid sentinel so is_first_launch returns False next time.
    if not baseline_path.exists():
        baseline_path.write_bytes(b"")


def run_returning_flow(baseline: object) -> None:
    """
    Run the returning-user flow.

    Accepts the loaded Baseline (or None for corrupt/missing baseline) and logs
    a brief welcome-back message.  The actual calibration status string is
    surfaced via get_calibration_status() in main.py's print_onboarding().
    """
    if baseline is None:
        logger.info("[Onboarding] returning user — baseline missing or corrupt; using population defaults")
    else:
        logger.info("[Onboarding] returning user — baseline loaded")
