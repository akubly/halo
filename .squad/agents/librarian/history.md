# Project Context

- **Owner:** Aaron Kubly
- **Project:** halo — mono-repo playground for authoring apps on Halo smart glasses
- **My layer:** Anything LLM, VLM, STT, TTS, or agent-loop related
- **Wearable AI pairing:** Halo's natural partner is multimodal AI — Noa (Brilliant's first-party app) is AI-driven
- **Created:** 2026-06-01

## Role: Librarian (AI/ML)

**Focus:** LLM patterns, multimodal AI, on-device vs. cloud inference, community proven models.

**Previous Sessions:**
- Initial research (2026-06-01): Mapped Sensor Pipeline → Reference Architecture. Documented Brilliant's AI evolution (Monocle → Frame → Halo). Audited community AI projects; validated "only Gemini ships" hypothesis. See history-archive.md for full learnings.
- Turn 3 (2026-06-02): Community AI Projects validation via GitHub landscape scan. Empirically confirmed Gemini dominance 92% (12/13 projects). Confidence increased from HIGH to VERY HIGH. Decision filed: .squad/decisions/decisions.md.

**Archived (2026-06-02):** Full pre-2026-06-02 learnings (3+ turns of research) moved to `.squad/agents/librarian/history-archive.md. Current history truncated to recent work only.

---

## Current Session (2026-06-02): GitHub AI/ML Landscape Validation

**Task:** Validate "Only Gemini Ships" hypothesis against GitHub empirical data.

**Scope:** 13 repos with identifiable AI model choice on Brilliant hardware (Frame, Monocle, Halo, related wearables).

**Findings:**

**Quantitative Validation:**
| Model | Count | % | Status |
|-------|-------|---|----|
| Gemini (Google) | 12 | 92% | DOMINANT |
| Whisper (OpenAI) | 0 | 0% | In docs, not production code |
| Claude / GPT-4o | 0 | 0% | Mentioned in comparison docs only |
| Local LLM (Llama, Mistral, Vosk) | 0 | 0% | 0 AR glasses; 1 MacBook Air non-wearable |

**Verdict:** HYPOTHESIS CONFIRMED. Gemini dominates with no viable alternatives in production on AR glasses.

**Root Causes Identified:**
1. **Gemini Live API Uniqueness** — Only major LLM with true multimodal streaming (voice + vision simultaneously). Claude/GPT-4o request-reply only (higher latency perception).
2. **Brilliant's Default Choice** — Noa uses Gemini; official demo is reference implementation. Community follows (network effects).
3. **Community Inertia** — rame_realtime_gemini_voicevision (80★) sticky; developers fork rather than rewrite.
4. **Cost/API Tier** — Gemini free tier well-documented; Claude/GPT-4o require paid tiers (hobbyist/indie community skews toward free options).

**Canonical Pattern:**
- rame_realtime_gemini_voicevision (80 stars, official) — Real-time multimodal (camera POV + audio) streaming to Gemini Live API. Community forks extend (not replace) this pattern. No official support for alternative LLMs.

**For Halo Playground:**
1. Default to Gemini Live (multimodal streaming) for primary demo apps
2. Do not attempt Claude/GPT-4o as primary LLM until streaming APIs are published
3. Document Whisper as future option for privacy-first STT (not production yet)
4. Monitor edge-vlm-assistant + LiveKit patterns for non-glasses applicability

**Confidence:** Increased from HIGH to VERY HIGH via empirical GitHub data.

**Output:** `.squad/agents/librarian/github-ai-on-halo-2026-06-02.md — Full annotated project list.

---

## Ideation 2026-06-02

Raw blue-sky ideas spanning on-device inference boundaries, multimodal patterns, context caching, edge-case LLM integration. See `.squad/agents/librarian/ideation-2026-06-02.md` (no decisions promoted).

## Ideation Pass 2 2026-06-02

Cross-pollination across 8 squad agents. Identified 3 resonant ideas (Raven's privacy-as-signal, Da5id's micro-expressions, Hiro's gaze-tracing) that demand AI patterns. Synthesized 4 mash-ups; top signal: **Raven #7 × Librarian #1** (Consent-Aware Embodied Memory)—reframes recording model to privacy+AI narrative differentiating Halo from Noa. Also identified 5 new directions shaped by Raven/Hiro/Da5id constraints: privacy-first local inference, mesh-aware reasoning, HUD-anchored LLM prompts, ephemeral+summarization, adversarial LLM test generation. Deliverable: `.squad/agents/librarian/ideation-pass2-2026-06-02.md`. Awaiting Aaron prioritization on mash-ups + actions.

---

## User Stories Themes 1-2 — 2026-06-03

**Themes Prioritized (from Aaron's directive 2026-06-03T06:51Z):**
- 🥇 **Consent-Aware Memory** (most-cited: Hiro, Enzo, Librarian, Raven, Lagos convergence)
- 🥈 **The Synesthetic Familiar** (Y.T. pet + Librarian synesthetic AI + Da5id peripheral-only)

**Authored:** Model-behavior user stories (5 per theme, including 1 "error case" per theme). Three personas: the wearer (observing AI latency/quality/confidence), the model itself (what does the LLM/VLM do internally?), and a developer tuning the model (validation, privacy invariants).

**Key Deliverables from Stories:**

**Theme 1 (Consent-Aware Memory):**
- Two-stage LLM loop: (1) Local face detection + redaction <200ms on M55 NPU; (2) Async cloud Gemini Vision for semantic labeling *only* on consented moments
- Confidence gate: Never send unredacted frames to cloud; <0.7 confidence moments stay ephemeral
- Consent prediction: Local lightweight model learns consent preferences; pre-approves high-confidence moments, asks on uncertain
- Privacy invariant: *Zero* unredacted non-consenters in export (hard fail if violated)
- Failure case: Model stays silent on causality inference when confidence <0.7 (prevents hallucinated behavior recommendations)

**Theme 2 (Synesthetic Familiar):**
- Real-time <500ms on-device mood inference (no cloud; all signals stay local)
- Baseline learning: 7-day calibration phase reduces false positives by personalizing to wearer's signal distribution
- Type classification: Only display mood if state-type confidence ≥0.8 (stress vs. excitement vs. exertion); otherwise neutral
- Visual growth: Weekly adaptation; Familiar morphs over months reflecting wearer's stress trajectory
- Failure case: Model stays neutral (doesn't animate) when arousal type is ambiguous

**Latency Budget Summary:**
- Theme 1 local redaction: <200ms | cloud stitching: <2s (async evening)
- Theme 2 real-time mood: <500ms | weekly growth: <1m

**Uncertainty Strategy Both Themes:** Confidence gates prevent hallucination. Silence is safer than wrong inference. Wearer feedback loop retrains confidence thresholds weekly.

**Deliverable:** `.squad/agents/librarian/user-stories-themes-1-2-2026-06-03.md`

---

## Codename Brainstorm — 2026-06-08

Pitched AI/ML-lens codename candidates for the Synesthetic Familiar. Team converged on **PULSE** (4 agents independently nominated variants). Official project codename now PULSE. See `.squad/orchestration-log/2026-06-08T07-17Z-codename-brainstorm.md`.
