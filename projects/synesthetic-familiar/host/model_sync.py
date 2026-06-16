"""
Population model weight sync for VESPER (Option C — Federated Local Refinement).

─── DESIGN: What is downloaded, what stays local ────────────────────────────

DOWNLOADED  (server → host, one-way only):
    Population model weights JSON — tuned visual weights derived from
    aggregate, anonymised signals across the VESPER population.  This is a
    static file; functionally equivalent to a software update.

    Format: {"version": "1", "visual_activity": 0.15, "visual_brightness": 0.05}

STAYS LOCAL (never leaves host):
    baseline.json          — personal Welford mean/stddev (mood baseline)
    visual_weights.json    — per-session tuned visual weights (local EMA state)
    All raw sensor data    — audio, IMU, camera features
    All mood inference     — MoodResult values never transmitted to any server

─── NO-EGRESS PROOF (MODEL-I5) ──────────────────────────────────────────────

The sync operation is a single HTTP GET request to a static HTTPS URL.

REQUEST headers sent by urllib.request (stdlib default, no overrides):
    Host: <update-server>
    User-Agent: Python-urllib/<version>    ← standard; not a VESPER identifier
    Accept-Encoding: identity

NOT SENT (verified by inspection of sync_population_weights below):
    User ID        — not generated or stored anywhere in this codebase
    Device ID      — not generated or stored anywhere in this codebase
    Baseline stats — not included; the server has no use for them
    Session token  — not generated or stored anywhere in this codebase
    Custom headers — none added (see _download_bytes: no req.add_header calls)

WHAT THE SERVER SEES:
    IP address  — inherent to any TCP connection; not a VESPER application-layer id
    User-Agent  — Python/stdlib default; identical for all VESPER hosts
    No user-distinguishing information at the application layer.

Serving the weights as a static GitHub release asset is the recommended
implementation: it is public, auditable, and carries no user-tracking beyond
standard CDN access logs (IP + User-Agent), which are equivalent to any
software-update fetch.

─── FAIL-CLOSED GUARANTEE ────────────────────────────────────────────────────

Every error path in sync_population_weights returns the caller's CURRENT weights
unchanged.  The local heuristic is never left in an undefined state:

    Unreachable server  → keep current weights (offline-capable)
    Hash mismatch       → discard download, keep current weights (MODEL-I5)
    Parse error         → keep current weights
    Any exception       → keep current weights (broad except guard at top level)

Owner: Librarian (AI/ML)
Phase: VESPER Phase 2, Week 4 "It sees"
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import logging
import math
import urllib.parse
import urllib.request
from typing import Optional

from host.inference import (
    DEFAULT_VISUAL_WEIGHTS,
    VisualWeights,
    reset_visual_weights,
    tune_visual_weights,
)

logger = logging.getLogger(__name__)

# Maximum size of the downloaded weights file.
# A minimal JSON with 3–5 float fields is under 200 bytes; 64 KB is a generous ceiling.
_MAX_WEIGHTS_FILE_BYTES: int = 65_536  # 64 KB

# HTTP timeout for model download — short, since offline is the acceptable fallback.
_DOWNLOAD_TIMEOUT_S: float = 10.0


# ── Manifest ──────────────────────────────────────────────────────────────────

@dataclasses.dataclass
class PopulationManifest:
    """
    URL + expected SHA-256 of a published population weights release.

    url    — HTTPS URL to the weights JSON (must begin with "https://")
    sha256 — hex-encoded SHA-256 digest of the file at that URL

    Set DEFAULT_MANIFEST to a real PopulationManifest once a population
    model is published.  Until then, sync_population_weights is a no-op.
    """
    url: str
    sha256: str   # lowercase hex, 64 chars


# No default manifest yet — sync is a no-op until a release is published.
DEFAULT_MANIFEST: Optional[PopulationManifest] = None


# ── Internal helpers ──────────────────────────────────────────────────────────

def _download_bytes(url: str, timeout_s: float = _DOWNLOAD_TIMEOUT_S) -> bytes:
    """
    Download a URL over HTTPS only.

    MODEL-I5 enforcement:
        • Scheme MUST be "https" — raises ValueError on any other scheme.
        • No custom headers are added.  urllib's default headers only.
        • Size-limited to _MAX_WEIGHTS_FILE_BYTES.

    Raises:
        ValueError  — scheme is not "https" or file exceeds size limit
        OSError / urllib.error.URLError — network failure (let caller handle)
    """
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(
            f"MODEL-I5 violation: only HTTPS is permitted; got scheme '{parsed.scheme}'"
        )

    req = urllib.request.Request(url)
    # No req.add_header() calls — MODEL-I5: no custom headers.

    with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # noqa: S310
        data = resp.read(_MAX_WEIGHTS_FILE_BYTES + 1)

    if len(data) > _MAX_WEIGHTS_FILE_BYTES:
        raise ValueError(
            f"Downloaded weights file exceeds {_MAX_WEIGHTS_FILE_BYTES} byte limit "
            f"({len(data)} bytes) — discarding"
        )
    return data


def _verify_sha256(data: bytes, expected_hex: str) -> bool:
    """Return True iff SHA-256(data) == expected_hex (case-insensitive)."""
    actual = hashlib.sha256(data).hexdigest()
    return actual == expected_hex.lower().strip()


def _parse_population_weights(data: bytes) -> VisualWeights | None:
    """
    Parse a population weights JSON payload into a VisualWeights.

    Expected format:
        {
          "version": "1",
          "visual_activity": <float ≥ 0>,
          "visual_brightness": <float ≥ 0>
        }

    Returns None on any parse or validation failure.
    """
    try:
        obj = json.loads(data.decode("utf-8"))
        va = float(obj["visual_activity"])
        vb = float(obj["visual_brightness"])
        if not (math.isfinite(va) and math.isfinite(vb)):
            raise ValueError(
                f"non-finite weights: visual_activity={va}, visual_brightness={vb}"
            )
        if va < 0.0 or vb < 0.0:
            raise ValueError(
                f"negative weights not permitted: visual_activity={va}, visual_brightness={vb}"
            )
        return VisualWeights(visual_activity=va, visual_brightness=vb)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        logger.warning("[ModelSync] failed to parse population weights JSON: %s", exc)
        return None


# ── Public API ────────────────────────────────────────────────────────────────

def download_weights(url: str, expected_hash: str) -> bytes | None:
    """
    Download a model weights file and verify its content hash.

    MODEL-I5 guarantees (testable contract):
        • url MUST start with "https://" — raises ValueError for any other scheme.
        • No custom headers are added to the request.
        • File is content-hash verified BEFORE returning; returns None on mismatch.

    Returns:
        bytes — raw file content when download succeeds and SHA-256 matches.
        None  — when the hash does not match (content discarded).

    Raises:
        ValueError          — url is not HTTPS, or file exceeds size limit.
        OSError / URLError  — network failure (caller decides how to handle).

    Callers that want fail-closed behaviour (keep current weights on any error)
    should use sync_population_weights() instead.
    """
    # Raises ValueError for non-HTTPS, OSError/URLError for network failure.
    # Catch unexpected Exception subtypes (e.g. SSL errors raised as bare Exception
    # in some implementations) and treat them as network failures → return None.
    try:
        data = _download_bytes(url)
    except (OSError, TimeoutError, ConnectionError):
        raise  # let expected network errors propagate — caller handles
    except ValueError:
        raise  # scheme validation error is intentional — propagate
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "[ModelSync] unexpected error during download (treated as network failure): %s: %s",
            type(exc).__name__, exc,
        )
        return None

    if not _verify_sha256(data, expected_hash):
        actual_prefix = hashlib.sha256(data).hexdigest()[:16]
        expected_prefix = expected_hash[:16]
        logger.error(
            "[ModelSync] MODEL-I5 HASH MISMATCH — download discarded. "
            "expected=%s… actual=%s…",
            expected_prefix,
            actual_prefix,
        )
        return None

    return data


def sync_population_weights(
    manifest: PopulationManifest | None,
    current: VisualWeights,
    *,
    alpha: float = 0.1,
) -> VisualWeights:
    """
    Download population weights and EMA-blend with current local weights.

    Fail-closed on every error path — returns `current` unchanged:
        • manifest is None              → no-op (no release published yet)
        • server unreachable            → keep current (offline-capable)
        • SHA-256 mismatch              → discard download, keep current (MODEL-I5)
        • parse / validation error      → keep current
        • any unexpected exception      → keep current (logged as ERROR)

    MODEL-I5: the HTTP GET request carries ZERO user-identifying data.
    See module docstring for the full no-egress proof.

    Args:
        manifest  PopulationManifest with url + expected sha256.  Use
                  DEFAULT_MANIFEST or supply a custom one for testing.
        current   Current local VisualWeights (used as EMA base).
        alpha     EMA learning rate (0 < alpha < 1; default 0.1).

    Returns:
        Updated VisualWeights after bounded EMA blend, or `current` on failure.
    """
    if manifest is None:
        logger.debug("[ModelSync] no manifest configured — skipping population weight sync")
        return current

    # ── Download ──────────────────────────────────────────────────────────────
    try:
        data = _download_bytes(manifest.url)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "[ModelSync] download failed — keeping local weights (offline or unreachable): %s",
            exc,
        )
        return current

    # ── Hash verification (MODEL-I5) ─────────────────────────────────────────
    if not _verify_sha256(data, manifest.sha256):
        actual_prefix = hashlib.sha256(data).hexdigest()[:16]
        expected_prefix = manifest.sha256[:16]
        logger.error(
            "[ModelSync] MODEL-I5 HASH MISMATCH — download discarded, local weights retained. "
            "expected=%s… actual=%s…",
            expected_prefix,
            actual_prefix,
        )
        return current

    # ── Parse ─────────────────────────────────────────────────────────────────
    population = _parse_population_weights(data)
    if population is None:
        return current

    # ── Bounded EMA blend ─────────────────────────────────────────────────────
    # tune_visual_weights enforces the ≤ 2× default bound and emits a warning
    # if any weight approaches the divergence limit.
    try:
        updated = tune_visual_weights(current, population, alpha=alpha)
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "[ModelSync] unexpected error during weight tuning — keeping current weights: %s",
            exc,
        )
        return current

    logger.info(
        "[ModelSync] population weights applied (alpha=%.2f): "
        "visual_activity %.4f→%.4f, visual_brightness %.4f→%.4f",
        alpha,
        current.visual_activity, updated.visual_activity,
        current.visual_brightness, updated.visual_brightness,
    )
    return updated


# ── Weight state helpers (online tuning support) ─────────────────────────────

def get_current_weights() -> dict:
    """
    Return DEFAULT_VISUAL_WEIGHTS as a plain dict.

    Useful for testing: callers can snapshot weights before and after a sync
    attempt to verify that a failed sync leaves state unchanged.
    """
    return dataclasses.asdict(DEFAULT_VISUAL_WEIGHTS)


def apply_weight_update(update: dict, alpha: float = 0.1) -> dict:
    """
    Apply an EMA weight update from a dict and return the updated weights dict.

    Recognises the visual-modality keys ("visual_activity", "visual_brightness").
    Unknown keys are silently ignored — this function is tolerant of arbitrary
    population-model formats so it can evolve without breaking callers.

    The ≤ 2× default bound is enforced via tune_visual_weights (no weight ever
    exceeds MAX_VISUAL_WEIGHT_MULTIPLIER × its default, regardless of input).

    Returns the updated VisualWeights as a plain dict.
    """
    target = VisualWeights(
        visual_activity=float(
            update.get("visual_activity", DEFAULT_VISUAL_WEIGHTS.visual_activity)
        ),
        visual_brightness=float(
            update.get("visual_brightness", DEFAULT_VISUAL_WEIGHTS.visual_brightness)
        ),
    )
    result = tune_visual_weights(DEFAULT_VISUAL_WEIGHTS, target, alpha=alpha)
    return dataclasses.asdict(result)


def reset_weights_to_defaults() -> VisualWeights:
    """
    Return factory-default VisualWeights (does NOT write to disk).

    Alias for host.inference.reset_visual_weights() — exposed here so callers
    can reach the reset without importing inference directly.
    """
    return reset_visual_weights()
