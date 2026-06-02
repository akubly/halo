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

Raw blue-sky ideas spanning on-device inference boundaries, multimodal patterns, context caching, edge-case LLM integration. See `.squad/agents/librarian/ideation-2026-06-02.md (no decisions promoted).
