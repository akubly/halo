# Librarian Agent History

## Learnings

### 2026-06-12 — Week 2 Review-Fix Wave (inference.py hardening)

**B1 — MoodResult.tension contract amendment (BLOCKING, shared)**

`compute_mood` always computed a raw `tension` float but never exposed it on
`MoodResult`. `main.py` was feeding `result.intensity` into
`update_baseline(…, tension)`, silently corrupting the persisted personal stress
threshold (mean + 1.5 σ). Fix: added `tension: float` as a new field on
`MoodResult`, populated from the computed tension. Ng's `main.py` change
switches the call-site to `result.tension`. When adding contract-critical fields
to a dataclass, check that no test constructs it positionally — here none did,
so the append-at-end placement was safe.

**I1 — load_baseline fail-safe (security+craft)**

The old guard caught `(FileNotFoundError, json.JSONDecodeError, TypeError,
KeyError)` but not `OSError` (unreadable file) or `ValueError` (bad field
values). More critically, hostile JSON could pass construction (`Baseline(**data)`)
with `mean="EVIL"` and cause a `TypeError` many frames later in `compute_mood`.
Fix: validate field types (real finite numbers, bool excluded) and non-negative
`sample_count` immediately after construction; raise `ValueError` on failure so
the broad except catches it. Added module `logger` and emit `WARNING` with path
+ exception on every failure path. Docstring already promised "returns None if
missing or corrupt" — implementation now matches the promise.

**I2 — NaN/inf and variance-floor guard (security)**

Two independent failure modes in `update_baseline`:
1. A NaN/inf tension (from a corrupt audio block) would propagate into the
   Welford running statistics and permanently poison `baseline.mean`/`stddev`.
   Fix: return the existing baseline unchanged if `not math.isfinite(tension)`.
2. Floating-point cancellation on corrupted priors can make `m2_new` slightly
   negative, causing `math.sqrt` to raise `ValueError` and kill the loop.
   Fix: clamp with `max(0.0, m2_new)` before the sqrt.

Feature-level finiteness guards in sensors.py are Ng's responsibility; the
inference-side guard is the last line of defence before the persisted file.

**M4 — audio_rms dead-param annotation (craft)**

`audio_rms` is part of the locked `compute_mood` signature (ARD §5.4 / future
confidence modulation) but absent from the tension formula. A one-line comment
prevents future readers from treating it as a bug or dead code.
